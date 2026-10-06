import pytest
import httpx
from unittest.mock import MagicMock, patch

from backend.main import app
from backend.core.moods import (
    MOOD_VECTORS,
    ALT_TURLER,
    THERAPY_MODES,
    build_therapy_journey,
    split_count,
    energy_neighbor,
    public_meta,
)
from backend.services.ai_agent import (
    to_ascii_normalize,
    calculate_linear_mood_vector,
    analyze_mood_local,
)
from backend.services.spotify import (
    make_oauth_state,
    verify_oauth_state,
    _create_track_obj,
    search_tracks,
    replace_single_track,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ==============================================================================
# 1. MOOD MODEL & THERAPY JOURNEY (ISO PRINCIPLE) TESTS
# ==============================================================================

def test_mood_vectors_and_genres_integrity():
    for mood, data in MOOD_VECTORS.items():
        assert -1.0 <= data["valence"] <= 1.0
        assert 0.0 <= data["arousal"] <= 1.0
        assert mood in ALT_TURLER
        assert len(ALT_TURLER[mood]) >= 4


def test_build_therapy_journey():
    # Catharsis stays in original mood
    catharsis = build_therapy_journey("huzunlu_slow", "catharsis")
    assert catharsis == ["huzunlu_slow", "huzunlu_slow", "huzunlu_slow"]

    # Uplift moves towards neseli_pop via an intermediate bridge mood
    uplift = build_therapy_journey("huzunlu_slow", "uplift")
    assert len(uplift) == 3
    assert uplift[0] == "huzunlu_slow"
    assert uplift[2] == "neseli_pop"

    # Calm moves towards sakin_akustik
    calm = build_therapy_journey("enerjik_spor", "calm")
    assert calm[0] == "enerjik_spor"
    assert calm[2] == "sakin_akustik"


def test_split_count():
    assert sum(split_count(20, 3)) == 20
    assert sum(split_count(7, 3)) == 7
    assert sum(split_count(50, 3, [0.35, 0.30, 0.35])) == 50


def test_energy_neighbor():
    high_pop = energy_neighbor("sakin_akustik", "Yüksek")
    assert high_pop is not None
    assert MOOD_VECTORS[high_pop]["arousal"] > MOOD_VECTORS["sakin_akustik"]["arousal"]

    low_rock = energy_neighbor("hard_rock_metal", "Düşük")
    assert low_rock is not None
    assert MOOD_VECTORS[low_rock]["arousal"] < MOOD_VECTORS["hard_rock_metal"]["arousal"]


# ==============================================================================
# 2. LOCAL NLP VECTOR ENGINE & TURKISH LINGUISTICS
# ==============================================================================

def test_ascii_normalization():
    assert to_ascii_normalize("Çok Şaşkın ve Üzgünüm!") == "cok saskin ve uzgunum"
    assert to_ascii_normalize("İSTANBUL / Şişli") == "istanbul sisli"


def test_nlp_sentiment_detection():
    # Sadness / heartbreak
    sad = analyze_mood_local("Bugün terk edildim, kalbim darmadağın ve çok ağlıyorum.")
    assert sad["mood"] == "huzunlu_slow"
    assert sad["valence"] < 0
    assert sad["engine"] == "linear_vector_space_nlp"

    # Celebration / happiness
    happy = analyze_mood_local("Harika bir haber aldım, modum çok yüksek, dans edip kutlama yapıyoruz!")
    assert happy["mood"] == "neseli_pop"
    assert happy["valence"] > 0

    # Workout / pump
    gym = analyze_mood_local("Gym vakti, bomba gibi motiveyim, pes etmek yok!")
    assert gym["mood"] == "enerjik_spor"
    assert gym["arousal"] > 0.7

    # Calm / tea
    calm = analyze_mood_local("Kahvemi aldım, sakin ve huzurlu bir akşam geçirmek istiyorum.")
    assert calm["mood"] == "sakin_akustik"


def test_nlp_turkish_post_negation():
    # "mutlu değilim" should shift from positive to negative (huzunlu_slow)
    val_not_happy, _, _ = calculate_linear_mood_vector("mutlu değilim")
    val_happy, _, _ = calculate_linear_mood_vector("mutluyum")
    assert val_happy > 0
    assert val_not_happy < 0


def test_nlp_seed_artist_consistency():
    # Pera seed tracks must diagnose as indie_alternatif, not jazz_blues
    res = analyze_mood_local("Sevdiğim referans parçalar: Sensiz Ben - Pera, Ne Ala - Pera", seed_artists=["Pera"])
    assert res["mood"] == "indie_alternatif"

    # Even with text only mentioning Pera
    res2 = analyze_mood_local("Pera dinliyorum, benzer şarkılar bul")
    assert res2["mood"] == "indie_alternatif"

    # Default neutral text without words must fall back to sakin_akustik, never jazz_blues
    res_empty = analyze_mood_local("xyz abc 123")
    assert res_empty["mood"] == "sakin_akustik"


# ==============================================================================
# 3. SPOTIFY SECURITY & TOKEN MANAGEMENT
# ==============================================================================

def test_oauth_state_hmac_tamper_proofing():
    state = make_oauth_state()
    assert verify_oauth_state(state) is True

    # Tampered state must be rejected
    tampered = state[:-4] + "abcd"
    assert verify_oauth_state(tampered) is False
    assert verify_oauth_state("invalid.state") is False
    assert verify_oauth_state(None) is False


def test_track_obj_filtering():
    raw_valid = {
        "id": "11dFghVXANMlKmJXsNCbNl",
        "name": "Cut To The Feeling",
        "artists": [{"name": "Carly Rae Jepsen"}],
        "album": {"name": "Emotion", "images": [{"url": "https://img.jpg"}]},
        "duration_ms": 207959,
        "external_urls": {"spotify": "https://open.spotify.com/track/11dFghVXANMlKmJXsNCbNl"},
    }
    track = _create_track_obj(raw_valid, rank=0)
    assert track is not None
    assert track["name"] == "Cut To The Feeling"

    # ASMR blacklist filter
    raw_asmr = {**raw_valid, "name": "Whispering ASMR Relaxation"}
    assert _create_track_obj(raw_asmr) is None

    # Too short duration filter (< 60s)
    raw_short = {**raw_valid, "duration_ms": 30000}
    assert _create_track_obj(raw_short) is None


# ==============================================================================
# 4. API ENDPOINT INTEGRATION TESTS (ASYNC)
# ==============================================================================

@pytest.mark.anyio
async def test_meta_endpoint(client):
    res = await client.get("/api/meta")
    assert res.status_code == 200
    data = res.json()
    assert "moods" in data
    assert "neseli_pop" in data["moods"]
    assert "therapy_modes" in data
    assert "catharsis" in data["therapy_modes"]


@pytest.mark.anyio
async def test_analyze_endpoint(client):
    res = await client.post("/api/analyze", json={"text": "Gece oldu kahvemi yaptım kitap okuyorum."})
    assert res.status_code == 200
    data = res.json()
    assert "mood" in data
    assert "doktor_notu" in data
    assert "suggested_genres" in data
    assert "valence" in data
    assert "arousal" in data


@pytest.mark.anyio
async def test_analyze_endpoint_validation(client):
    # Empty text must be rejected with HTTP 422
    res = await client.post("/api/analyze", json={"text": ""})
    assert res.status_code == 422


@pytest.mark.anyio
async def test_search_tracks_mocked(client):
    mock_sp = MagicMock()

    def mock_search(**kwargs):
        q = kwargs.get("q", "Artist")
        art = q.replace('artist:"', '').replace('"', '').strip() or "Sanatci"
        return {
            "tracks": {
                "items": [
                    {
                        "id": f"track_{abs(hash(art))}_{i}",
                        "name": f"{art} Song {i}",
                        "artists": [{"name": art}],
                        "album": {"name": "Album 1", "images": []},
                        "duration_ms": 180000,
                        "external_urls": {"spotify": f"https://spotify.com/{i}"},
                    }
                    for i in range(5)
                ]
            }
        }

    mock_sp.search.side_effect = mock_search

    with patch("backend.api.routes.get_spotify_client", return_value=mock_sp):
        res = await client.post("/api/search-tracks", json={
            "mood": "neseli_pop",
            "language": "tr",
            "genres": ["Pop & Dans"],
            "count": 10,
            "energy_level": "Yüksek",
            "therapy_mode": "uplift",
        })
        assert res.status_code == 200
        tracks = res.json()["tracks"]
        assert len(tracks) > 0
        assert "id" in tracks[0]


@pytest.mark.anyio
async def test_mood_card_endpoint(client):
    res = await client.post("/api/mood-card", json={
        "mood": "sakin_akustik",
        "doktor_notu": "Zihnini dinlendir, derin nefes al.",
        "sarki_adi": "Gözleri Aşka Gülen",
        "sanatci_adi": "Münir Nurettin",
        "track_count": 20,
    })
    assert res.status_code == 200
    assert res.headers["content-type"] == "image/png"
    assert len(res.content) > 1000
