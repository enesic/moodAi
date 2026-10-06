"""
Spotify entegrasyon katmanı.

- OAuth (Authorization Code) — kullanıcıya özel, paylaşılmayan bellek içi token yönetimi
  + HMAC imzalı `state` ile CSRF koruması + refresh token desteği
- Misafir modu için tekil (singleton) Client Credentials istemcisi
- Terapi moduna (ISO prensibi) göre aşamalı, paralel şarkı küratörlüğü
- Spotify Web API Şubat 2026 Development Mode değişiklikleriyle uyumluluk:
    * /search `limit` en fazla 10
    * POST /users/{id}/playlists  → POST /me/playlists
    * /playlists/{id}/tracks      → /playlists/{id}/items
    * track.popularity alanı kaldırıldı → sıralama arama alaka sırasına (rank) göre yapılır
"""
import base64
import hashlib
import hmac
import random
import re
import secrets
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import spotipy
from spotipy.cache_handler import MemoryCacheHandler
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth

from backend.core.config import settings
from backend.core.moods import (
    ALT_TURLER,
    MOOD_LABELS,
    build_therapy_journey,
    energy_neighbor,
    find_artist_info,
    split_count,
)

SCOPE = "playlist-modify-public playlist-modify-private"
SEARCH_LIMIT_MAX = 10          # Şubat 2026: /search limit üst sınırı
REQUEST_TIMEOUT = 10           # saniye
MAX_TRACKS_PER_ARTIST = 2      # çeşitlilik için sanatçı başına üst sınır
OAUTH_STATE_TTL = 600          # saniye

# Tek, uygulama genelinde paylaşılan arama havuzu (Spotify istekleri I/O bound)
_executor = ThreadPoolExecutor(max_workers=8, thread_name_prefix="spotify")
# Seed çözümleme ana havuzdaki bir görevin İÇİNDEN çağrıldığı için ayrı havuz kullanılır
# (iç içe submit → havuz tükenmesi / deadlock riskini ortadan kaldırır)
_seed_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="spotify-seed")


class SpotifyAuthError(Exception):
    """Kullanıcı token'ı geçersiz/süresi dolmuş (HTTP 401)."""


# ==============================================================================
# OAUTH & İSTEMCİ YÖNETİMİ
# ==============================================================================

def create_spotify_oauth(state: Optional[str] = None) -> SpotifyOAuth:
    """
    Her istek için izole OAuth nesnesi. MemoryCacheHandler sayesinde token'lar
    diske (.cache) yazılmaz ve kullanıcılar arasında ASLA paylaşılmaz.
    """
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=SCOPE,
        state=state,
        cache_handler=MemoryCacheHandler(),
        open_browser=False,
        requests_timeout=REQUEST_TIMEOUT,
    )


def _sign(payload: str) -> str:
    key = (settings.SPOTIFY_CLIENT_SECRET or "moodai").encode()
    digest = hmac.new(key, payload.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest[:18]).decode().rstrip("=")


def make_oauth_state() -> str:
    """Sunucu tarafında saklama gerektirmeyen, HMAC imzalı ve süreli OAuth state."""
    payload = f"{int(time.time())}.{secrets.token_urlsafe(8)}"
    return f"{payload}.{_sign(payload)}"


def verify_oauth_state(state: Optional[str]) -> bool:
    if not state or state.count(".") < 2:
        return False
    payload, signature = state.rsplit(".", 1)
    if not hmac.compare_digest(_sign(payload), signature):
        return False
    try:
        issued_at = int(payload.split(".", 1)[0])
    except ValueError:
        return False
    return 0 <= time.time() - issued_at <= OAUTH_STATE_TTL


def get_authorize_url() -> str:
    state = make_oauth_state()
    return create_spotify_oauth(state=state).get_authorize_url(state=state)


def _token_payload(token_info: dict, fallback_refresh: Optional[str] = None) -> dict:
    return {
        "access_token": token_info["access_token"],
        "refresh_token": token_info.get("refresh_token") or fallback_refresh,
        "expires_at": int(token_info.get("expires_at") or time.time() + int(token_info.get("expires_in", 3600))),
    }


def exchange_code(code: str) -> dict:
    """Authorization code → {access_token, refresh_token, expires_at}. Cache asla kontrol edilmez."""
    token_info = create_spotify_oauth().get_access_token(code, as_dict=True, check_cache=False)
    return _token_payload(token_info)


def refresh_user_token(refresh_token: str) -> dict:
    token_info = create_spotify_oauth().refresh_access_token(refresh_token)
    return _token_payload(token_info, fallback_refresh=refresh_token)


_guest_client: Optional[spotipy.Spotify] = None
_guest_lock = threading.Lock()


def _is_valid_token(access_token: Optional[str]) -> bool:
    if not access_token:
        return False
    token = str(access_token).strip()
    return bool(token) and token.lower() not in ("null", "none", "undefined")


def get_spotify_client(access_token: Optional[str] = None) -> spotipy.Spotify:
    """Kullanıcı token'ı varsa kullanıcı yetkisiyle, yoksa paylaşılan Misafir (Client Credentials) istemcisi."""
    global _guest_client
    if _is_valid_token(access_token):
        return spotipy.Spotify(auth=str(access_token).strip(), requests_timeout=REQUEST_TIMEOUT, retries=2)

    if _guest_client is None:
        with _guest_lock:
            if _guest_client is None:
                manager = SpotifyClientCredentials(
                    client_id=settings.SPOTIFY_CLIENT_ID,
                    client_secret=settings.SPOTIFY_CLIENT_SECRET,
                    cache_handler=MemoryCacheHandler(),
                    requests_timeout=REQUEST_TIMEOUT,
                )
                _guest_client = spotipy.Spotify(
                    client_credentials_manager=manager, requests_timeout=REQUEST_TIMEOUT, retries=2
                )
    return _guest_client


def is_user_client(sp: spotipy.Spotify) -> bool:
    return bool(getattr(sp, "_auth", None))


# ==============================================================================
# ŞARKI NESNESİ & FİLTRELER
# ==============================================================================

BLACKLIST_KEYWORDS = [
    "asmr", "nursery", "lullaby", "baby sleep", "white noise",
    "sound effect", "karaoke", "ringtone", "medya konya", "çocuk şarkı",
    "children", "lullabies", "sleep sound", "rain sounds for sleep",
    "instrumental version", "8d audio", "slowed + reverb", "sped up",
]


def _create_track_obj(item: Optional[dict], rank: int = 0) -> Optional[dict]:
    if not item or not item.get("id") or item.get("type", "track") != "track":
        return None

    name = item.get("name", "")
    artists = item.get("artists") or []
    artist_name = artists[0]["name"] if artists else "Unknown"

    # Süre Filtresi (1 dakika ile 9 dakika arası gerçek şarkılar)
    duration_ms = item.get("duration_ms", 0) or 0
    if duration_ms < 60000 or duration_ms > 540000:
        return None

    # Spam / ASMR / Çocuk şarkısı / Karaoke filtresi
    name_lower = name.lower()
    artist_lower = artist_name.lower()
    for kw in BLACKLIST_KEYWORDS:
        if kw in name_lower or kw in artist_lower:
            return None

    album = item.get("album") or {}
    images = album.get("images") or []
    return {
        "id": item["id"],
        "uri": item.get("uri") or f"spotify:track:{item['id']}",
        "name": name,
        "artist": artist_name,
        "artists": ", ".join(a.get("name", "") for a in artists) or artist_name,
        "album": album.get("name", "Unknown"),
        "preview_url": item.get("preview_url"),
        "image": images[0]["url"] if images else None,
        "duration_ms": duration_ms,
        "popularity": item.get("popularity"),  # Şubat 2026 sonrası çoğunlukla None
        "rank": rank,
        "link": (item.get("external_urls") or {}).get("spotify") or f"https://open.spotify.com/track/{item['id']}",
    }


def _search_items(sp: spotipy.Spotify, query: str, market: Optional[str] = None, limit: int = SEARCH_LIMIT_MAX) -> List[dict]:
    """Güvenli arama: 401 dışındaki hataları yutar, limit'i API sınırına kırpar."""
    limit = max(1, min(int(limit), SEARCH_LIMIT_MAX))
    try:
        kwargs = {"q": query, "type": "track", "limit": limit}
        if market:
            kwargs["market"] = market
        res = sp.search(**kwargs) or {}
        return (res.get("tracks") or {}).get("items") or []
    except spotipy.SpotifyException as e:
        if e.http_status == 401:
            raise SpotifyAuthError("Spotify oturumunun süresi doldu.") from e
        return []
    except Exception:
        return []


def search_autocomplete(sp: spotipy.Spotify, query: str, limit: int = 8) -> List[dict]:
    items = _search_items(sp, query.strip(), limit=limit)
    tracks = []
    for i, item in enumerate(items):
        t = _create_track_obj(item, rank=i)
        if t:
            tracks.append(t)
    return tracks


# ==============================================================================
# SEKTÖR STANDARDI TÜRKÇE VE YABANCI KÜRATÖRLÜK MATRİSİ (ANCHOR ARTISTS & GENRES)
# ==============================================================================

GENRE_CURATION_MATRIX = {
    "neseli_pop": {
        "tr": ["Tarkan", "Edis", "Simge", "Gülşen", "Mabel Matiz", "Kenan Doğulu", "Yalın", "Zeynep Bastık", "Buray", "Hadise", "Murat Boz", "Aleyna Tilki", "Emir Can İğrek", "Derya Uluğ", "Sertab Erener"],
        "en": ["Dua Lipa", "The Weeknd", "Taylor Swift", "Harry Styles", "Ariana Grande", "Bruno Mars", "Billie Eilish", "Ed Sheeran", "Olivia Rodrigo", "Sabrina Carpenter", "Lady Gaga", "Miley Cyrus", "Katy Perry"]
    },
    "huzunlu_slow": {
        "tr": ["Sezen Aksu", "Model", "Sıla", "Kalben", "Mavi Gri", "Pinhani", "Madrigal", "Dolu Kadehi Ters Tut", "Dedublüman", "Fatma Turgut", "Toygar Işıklı", "Feridun Düzağaç", "Cem Adrian", "Yüzyüzeyken Konuşuruz", "Emre Aydın"],
        "en": ["Adele", "Sam Smith", "Lewis Capaldi", "Lana Del Rey", "Tom Odell", "James Arthur", "Phoebe Bridgers", "Cigarettes After Sex", "Conan Gray", "Kodaline", "Dean Lewis", "Coldplay", "Finneas"]
    },
    "enerjik_spor": {
        "tr": ["Lvbel C5", "Motive", "BLOK3", "UZI", "Ati242", "Ceza", "Mahmut Orhan", "Batuflex", "Heijan", "Massaka", "Çakal", "Ezhel"],
        "en": ["Eminem", "Travis Scott", "Drake", "Metro Boomin", "David Guetta", "Tiësto", "Martin Garrix", "Skrillex", "Kanye West", "Post Malone", "21 Savage", "Fred again.."]
    },
    "sakin_akustik": {
        "tr": ["Manuş Baba", "Evdeki Saat", "Deniz Tekin", "Cihan Mürtezaoğlu", "Birsen Tezer", "Jehan Barbur", "Can Ozan", "Nilipek", "Bülent Ortaçgil", "Yeni Türkü"],
        "en": ["Jack Johnson", "Boyce Avenue", "Vance Joy", "Norah Jones", "Jason Mraz", "Ben Howard", "Passenger", "Iron & Wine", "Lofi Girl", "Lauv", "Jeremy Zucker"]
    },
    "indie_alternatif": {
        "tr": ["Pera", "Adamlar", "Mor ve Ötesi", "Büyük Ev Ablukada", "Son Feci Bisiklet", "Jakuzi", "Lalalar", "Sedef Sebüktekin", "Yaşlı Amca", "Kaan Boşnak", "Hedonutopia", "Perdenin Ardındakiler", "Duman", "Model"],
        "en": ["Arctic Monkeys", "The Neighbourhood", "Tame Impala", "The Strokes", "Foster The People", "Gorillaz", "Radiohead", "The 1975", "Wallows", "Beach House", "Mac DeMarco", "Foals", "Lorde"]
    },
    "hard_rock_metal": {
        "tr": ["Şebnem Ferah", "Duman", "Hayko Cepkin", "Pentagram", "Kurban", "Ogün Sanlısoy", "Teoman", "Manga", "Barış Akarsu", "Gripin", "Yüksek Sadakat", "Athena"],
        "en": ["Linkin Park", "Metallica", "Guns N' Roses", "Green Day", "Nirvana", "Red Hot Chili Peppers", "Bring Me The Horizon", "Muse", "Foo Fighters", "System Of A Down", "Slipknot", "AC/DC", "Rammstein"]
    },
    "rap_hiphop": {
        "tr": ["Ezhel", "Ceza", "Sagopa Kajmer", "Şanışer", "Lvbel C5", "Motive", "BLOK3", "UZI", "Sefo", "Ati242", "Gazapizm", "Khontkar", "Anıl Piyancı", "Defkhan"],
        "en": ["Drake", "Travis Scott", "Kendrick Lamar", "Eminem", "J. Cole", "Metro Boomin", "Future", "21 Savage", "Jack Harlow", "Lil Baby", "Playboi Carti", "A$AP Rocky", "Post Malone"]
    },
    "jazz_blues": {
        "tr": ["İlhan Erşahin", "Kerem Görsev", "Karsu", "Jülide Özçelik", "Elif Çağlar", "Fatih Erkoç", "Ayşe Tütüncü", "Önder Focan"],
        "en": ["Miles Davis", "Frank Sinatra", "Chet Baker", "Gregory Porter", "B.B. King", "Nina Simone", "John Coltrane", "Norah Jones", "Amy Winehouse", "Michael Bublé", "Bill Withers"]
    },
    "elektronik_synth": {
        "tr": ["Mahmut Orhan", "Burak Yeter", "Deeperise", "Hey Douglas", "Faruk Sabancı", "İlkay Şencan", "Arem Özgüç", "Arman Aydın"],
        "en": ["Calvin Harris", "Avicii", "David Guetta", "Daft Punk", "Swedish House Mafia", "Kygo", "Peggy Gou", "Disclosure", "The Chainsmokers", "Kavinsky", "Gesaffelstein", "Justice"]
    }
}

# Kullanıcının seçtiği alt türlerin Spotify arama sorgusu karşılıkları (global katalog)
SUBGENRE_QUERIES: Dict[str, str] = {
    "Pop & Dans": 'genre:"dance pop"', "Disco & Retro Pop": 'genre:"disco"', "Yaz Hitleri": "summer hits",
    "K-Pop": 'genre:"k-pop"', "Latin Pop": 'genre:"latin pop"',
    "Slow & Balad": "ballad", "Melankolik Slow": "sad songs", "Akustik Hüzün": "sad acoustic",
    "Piyano & Yağmur": "sad piano", "Kırık Kalpler": "heartbreak",
    "Workout & Motivasyon": "workout motivation", "Yüksek BPM Trap": 'genre:"trap"',
    "Power Drill": 'genre:"drill"', "Club & Techno Hits": 'genre:"techno"',
    "Lo-Fi Beats": 'genre:"lo-fi"', "Akustik Gitar & Chill": "acoustic chill", "Soft Pop": "soft pop",
    "Coffeehouse Akustik": "coffeehouse acoustic", "Ambient & Dinginlik": 'genre:"ambient"',
    "Modern Indie Rock": 'genre:"indie rock"', "Dream Pop": 'genre:"dream pop"', "Shoegaze": 'genre:"shoegaze"',
    "Alternatif Rock": 'genre:"alternative rock"', "Bohem & Nostalji": 'genre:"indie folk"',
    "Klasik Rock": 'genre:"classic rock"', "Hard Rock": 'genre:"hard rock"', "Heavy Metal": 'genre:"heavy metal"',
    "Nu-Metal": 'genre:"nu metal"', "Punk & Grunge": 'genre:"grunge"',
    "Modern Trap": 'genre:"trap"', "Old School & Boom Bap": 'genre:"boom bap"',
    "Melodik Rap": 'genre:"melodic rap"', "Drill & Underground": 'genre:"drill"',
    "Smooth Jazz": 'genre:"smooth jazz"', "Vocal Jazz": 'genre:"vocal jazz"',
    "Blues & Soul": 'genre:"soul"', "Gece Mavisi Jazz": 'genre:"cool jazz"',
    "Synthwave & Neon": 'genre:"synthwave"', "Deep House": 'genre:"deep house"',
    "Minimal Techno": 'genre:"minimal techno"', "EDM & Festival": 'genre:"edm"',
}


def _artist_pool(mood: str, language: str) -> List[Tuple[str, str]]:
    """(sanatçı, market) çiftleri. Global matris ASLA mutasyona uğratılmaz (kopya üzerinde çalışılır)."""
    curation = GENRE_CURATION_MATRIX.get(mood, GENRE_CURATION_MATRIX["sakin_akustik"])
    tr = [(a, "TR") for a in curation["tr"]]
    en = [(a, "US") for a in curation["en"]]
    if language == "tr":
        return tr
    if language in ("en", "yabanci"):
        return en
    return tr + en


def _sample_targets(mood: str, language: str, n: int) -> List[Tuple[str, str]]:
    """Dil moduna göre dengeli sanatçı örneklemi (mix → %50 TR / %50 global)."""
    if n <= 0:
        return []
    curation = GENRE_CURATION_MATRIX.get(mood, GENRE_CURATION_MATRIX["sakin_akustik"])
    if language == "mix":
        half = max(1, n // 2)
        tr = random.sample(curation["tr"], min(half, len(curation["tr"])))
        en = random.sample(curation["en"], min(n - len(tr), len(curation["en"])))
        targets = [(a, "TR") for a in tr] + [(a, "US") for a in en]
        random.shuffle(targets)
        return targets
    pool = _artist_pool(mood, language)
    return random.sample(pool, min(n, len(pool)))


def _artist_query_tracks(sp, artist_name: str, market: str, limit: int = SEARCH_LIMIT_MAX) -> List[dict]:
    """Sanatçı filtresiyle arama yapar ve gerçekten o sanatçıya ait parçaları döndürür."""
    items = _search_items(sp, f'artist:"{artist_name}"', market=market, limit=limit)
    if not items:
        items = _search_items(sp, artist_name, market=market, limit=limit)
    target = artist_name.lower()
    tracks = []
    for i, item in enumerate(items):
        names = [a.get("name", "").lower() for a in item.get("artists") or []]
        if any(target in n or n in target for n in names if n):
            t = _create_track_obj(item, rank=i)
            if t:
                tracks.append(t)
    return tracks


def _genre_query_tracks(sp, query: str, market: str = "US") -> List[dict]:
    tracks = []
    for i, item in enumerate(_search_items(sp, query, market=market)):
        t = _create_track_obj(item, rank=i)
        if t:
            tracks.append(t)
    return tracks


# ==============================================================================
# REFERANS (SEED) ŞARKILAR
# ==============================================================================

_TRACK_ID_RE = re.compile(r"(?:spotify\.com/(?:intl-[a-z]+/)?track/|spotify:track:)([a-zA-Z0-9]{22})")
_PLAYLIST_ID_RE = re.compile(r"(?:spotify\.com/(?:intl-[a-z]+/)?playlist/|spotify:playlist:)([a-zA-Z0-9]+)")


def _resolve_seed_artists(sp, raw: str) -> Tuple[List[str], List[str]]:
    """Tek bir seed girdisinden (link / URI / düz metin) sanatçı adlarını ve seed şarkı ID'lerini çıkarır."""
    cleaned = str(raw or "").strip()
    if not cleaned:
        return [], []

    track_match = _TRACK_ID_RE.search(cleaned)
    if track_match:
        try:
            info = sp.track(track_match.group(1))
            if info and info.get("artists"):
                return [info["artists"][0]["name"]], [info["id"]]
        except spotipy.SpotifyException as e:
            if e.http_status == 401:
                raise SpotifyAuthError("Spotify oturumunun süresi doldu.") from e
        except Exception:
            pass
        return [], [track_match.group(1)]

    pl_match = _PLAYLIST_ID_RE.search(cleaned)
    if pl_match:
        try:
            data = sp._get(f"playlists/{pl_match.group(1)}/items", limit=10) or {}
            names = []
            for entry in data.get("items", []):
                t = entry.get("item") or entry.get("track")
                if t and t.get("artists"):
                    names.append(t["artists"][0]["name"])
            return names, []
        except Exception:
            return [], []

    items = _search_items(sp, cleaned, limit=1)
    if items and items[0].get("artists"):
        return [items[0]["artists"][0]["name"]], [items[0]["id"]]
    return [], []


def get_similar_tracks_from_seeds(sp, seed_inputs: List[str], count: int = 20) -> List[dict]:
    """
    Referans şarkı, sanatçı veya playlist linklerinden benzer şarkıları çeker.
    Sanatçı kümeleme (artist directory) sayesinde referans sanatçıların tarzına
    tam uyumlu benzer sanatçıları da sorguya dahil eder.
    """
    seeds = [s for s in (seed_inputs or []) if s and str(s).strip()][:5]
    if not seeds:
        return []

    artist_names: List[str] = []
    seed_ids: set = set()
    for names, ids in _seed_executor.map(lambda s: _resolve_seed_artists(sp, s), seeds):
        artist_names.extend(names)
        seed_ids.update(ids)

    unique_seed_artists = list(dict.fromkeys(artist_names))[:5]
    
    # Kümelenmiş benzer sanatçıları topla
    cluster_artists: List[str] = []
    for art in unique_seed_artists:
        info = find_artist_info(art)
        if info and "similar" in info:
            cluster_artists.extend(info["similar"][:4])

    all_target_artists = list(dict.fromkeys(unique_seed_artists + cluster_artists))[:10]

    similar: List[dict] = []
    for tracks in _seed_executor.map(lambda a: _artist_query_tracks(sp, a, market=None), all_target_artists):
        similar.extend(t for t in tracks if t["id"] not in seed_ids)
    return similar



# ==============================================================================
# ANA KÜRATÖRLÜK MOTORU
# ==============================================================================

def _run_parallel(tasks: List[Tuple]) -> List[Tuple[int, str, List[dict]]]:
    """tasks: (stage_idx, source, callable). 401 hatası tüm işlemi durdurur."""
    futures = [(stage, source, _executor.submit(fn)) for stage, source, fn in tasks]
    results = []
    for stage, source, fut in futures:
        try:
            results.append((stage, source, fut.result(timeout=REQUEST_TIMEOUT + 5)))
        except SpotifyAuthError:
            raise
        except Exception:
            results.append((stage, source, []))
    return results


def _pick_diverse(candidates: List[dict], n: int, used_ids: set, artist_counts: Dict[str, int]) -> List[dict]:
    """Alaka sırası + rastgelelik ile sıralar, tekrar ve sanatçı yığılmasını engeller."""
    # _seed olan şarkılara yüksek öncelik ver (skor ne kadar küçükse o kadar öne geçer)
    scored = sorted(candidates, key=lambda t: t.get("rank", 0) + random.uniform(0, 3) - (15 if t.get("_seed") else 0))
    picked = []
    for t in scored:
        if len(picked) >= n:
            break
        key_name = f"{t['name'].lower()}|{t['artist'].lower()}"
        artist_key = t["artist"].lower()
        if t["id"] in used_ids or key_name in used_ids:
            continue
        if artist_counts.get(artist_key, 0) >= MAX_TRACKS_PER_ARTIST:
            continue
        picked.append(t)
        used_ids.add(t["id"])
        used_ids.add(key_name)
        artist_counts[artist_key] = artist_counts.get(artist_key, 0) + 1
    return picked


def search_tracks(
    sp,
    mood: str,
    language: str,
    genres: Optional[List[str]],
    count: int,
    energy_level: str = "Orta",
    seed_inputs: Optional[List[str]] = None,
    therapy_mode: str = "catharsis",
) -> List[dict]:
    """
    Terapi moduna göre aşamalı (eşlik → geçiş → hedef) çalma listesi üretir.

    - Dil: tr / en(yabanci) / mix — kesin ayrımlı sanatçı havuzları
    - Türler: seçilen alt türler global katalogda `genre:` sorgularıyla aranır
    - Enerji: Düşük/Yüksek seçiminde aynı valence'a yakın komşu ruh hali havuza karıştırılır
    - Referans şarkılar: ilk aşamaya (eşlik) öncelikli olarak eklenir
    """
    count = max(1, int(count))
    genres = [g for g in (genres or []) if g in ALT_TURLER.get(mood, [])]
    journey = build_therapy_journey(mood, therapy_mode)

    # Ardışık aynı aşamaları birleştir: katarsis → tek aşama
    if journey[0] == journey[1] == journey[2]:
        stages = [journey[0]]
        stage_counts = [count]
    else:
        stages = journey
        stage_counts = split_count(count, 3, [0.35, 0.30, 0.35])

    tasks: List[Tuple] = []
    for idx, (stage_mood, stage_count) in enumerate(zip(stages, stage_counts)):
        if stage_count <= 0:
            continue
        # Her aşama için ihtiyaçtan fazla aday topla (filtre kayıplarını telafi)
        n_artists = max(3, min(8, (stage_count // 2) + 3))
        neighbor = energy_neighbor(stage_mood, energy_level)
        n_neighbor = (n_artists * 3) // 10 if neighbor else 0

        for artist, market in _sample_targets(stage_mood, language, n_artists - n_neighbor):
            tasks.append((idx, "artist", lambda a=artist, m=market: _artist_query_tracks(sp, a, m)))
        if neighbor:
            for artist, market in _sample_targets(neighbor, language, n_neighbor):
                tasks.append((idx, "energy", lambda a=artist, m=market: _artist_query_tracks(sp, a, m)))

        # Kullanıcının seçtiği alt türler yalnızca analiz edilen ruh haline ait aşamada kullanılır
        if stage_mood == mood and language != "tr":
            for g in genres[:3]:
                q = SUBGENRE_QUERIES.get(g)
                if q:
                    tasks.append((idx, "genre", lambda q=q: _genre_query_tracks(sp, q)))

    if seed_inputs:
        tasks.append((0, "seed", lambda: get_similar_tracks_from_seeds(sp, seed_inputs, count)))

    pools: Dict[int, List[dict]] = {i: [] for i in range(len(stages))}
    for stage, source, tracks in _run_parallel(tasks):
        for t in tracks:
            t = dict(t)
            if source == "seed":
                t["_seed"] = True
            pools.setdefault(stage, []).append(t)

    used: set = set()
    artist_counts: Dict[str, int] = {}
    final: List[dict] = []
    leftovers: List[Tuple[int, dict]] = []

    for idx, stage_mood in enumerate(stages):
        picked = _pick_diverse(pools.get(idx, []), stage_counts[idx], used, artist_counts)
        for t in picked:
            t["mood_segment"] = stage_mood
            t["stage"] = idx if len(stages) > 1 else None
        final.extend(picked)
        leftovers.extend((idx, t) for t in pools.get(idx, []))

    # Eksik kalırsa (az sonuç dönen sanatçılar) sanatçı sınırını gevşeterek doldur
    if len(final) < count:
        artist_counts = {k: 0 for k in artist_counts}
        for idx, t in leftovers:
            if len(final) >= count:
                break
            extra = _pick_diverse([t], 1, used, artist_counts)
            for e in extra:
                e["mood_segment"] = stages[idx]
                e["stage"] = idx if len(stages) > 1 else None
                final.append(e)

    if len(stages) > 1:
        final.sort(key=lambda t: t.get("stage") or 0)
    for t in final:
        t.pop("_seed", None)
    return final[:count]


def replace_single_track(
    sp,
    mood: str,
    exclude_ids: List[str],
    language: str,
    genres: Optional[List[str]] = None,
    exclude_artists: Optional[List[str]] = None,
) -> Optional[dict]:
    """Listede olmayan, mümkünse listedeki sanatçılardan da farklı tek bir şarkı bulur."""
    excluded = set(exclude_ids or [])
    excluded_artists = {a.lower() for a in (exclude_artists or [])}
    pool = _artist_pool(mood, language)
    random.shuffle(pool)

    fallback: Optional[dict] = None
    for artist, market in pool[:5]:
        tracks = _artist_query_tracks(sp, artist, market)
        random.shuffle(tracks)
        for t in tracks:
            if t["id"] in excluded:
                continue
            t["mood_segment"] = mood
            if t["artist"].lower() not in excluded_artists:
                return t
            fallback = fallback or t
    return fallback


def save_playlist(sp, track_uris: List[str], mood_title: str) -> Tuple[str, str]:
    """Kullanıcı hesabına özel (private) çalma listesi oluşturur — Şubat 2026 endpoint'leri."""
    if not is_user_client(sp):
        raise SpotifyAuthError("Çalma listesini hesabınıza kaydetmek için Spotify ile giriş yapmalısınız.")

    label = MOOD_LABELS.get(mood_title, {}).get("name") or mood_title.replace("_", " ").title()
    name = f"Mood AI: {label} • {datetime.now().strftime('%d.%m.%Y')}"
    try:
        playlist = sp._post("me/playlists", payload={
            "name": name,
            "public": False,
            "description": "Mood AI — Yapay Zeka Müzik Terapisti tarafından ruh haline özel hazırlandı.",
        })
        uris = [u for u in track_uris if isinstance(u, str) and u.startswith("spotify:track:")]
        for i in range(0, len(uris), 100):
            sp._post(f"playlists/{playlist['id']}/items", payload={"uris": uris[i:i + 100]})
        return playlist["external_urls"]["spotify"], playlist["name"]
    except spotipy.SpotifyException as e:
        if e.http_status == 401:
            raise SpotifyAuthError("Spotify oturumunun süresi doldu.") from e
        raise Exception(f"Playlist kaydetme hatası: {e.msg}") from e
