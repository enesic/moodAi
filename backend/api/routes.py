import io
import urllib.parse
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field

from backend.core.config import settings
from backend.core.moods import public_meta
from backend.services.spotify import (
    SpotifyAuthError,
    exchange_code,
    get_authorize_url,
    get_spotify_client,
    refresh_user_token,
    replace_single_track,
    save_playlist,
    search_autocomplete as spotify_search_autocomplete,
    search_tracks,
    verify_oauth_state,
)
from backend.services.ai_agent import analyze_mood
from backend.utils.image_gen import create_mood_card, create_vibe_card

router = APIRouter()


# ==============================================================================
# ŞEMALAR & DOĞRULAMA (PYDANTIC)
# ==============================================================================

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000, description="Kullanıcının iç döküşü / ruh hali metni")
    seed_artists: Optional[List[str]] = Field(default_factory=list)
    seed_tracks: Optional[List[str]] = Field(default_factory=list)


class SearchTracksRequest(BaseModel):
    access_token: Optional[str] = None
    mood: str = Field(..., min_length=2, max_length=50)
    language: str = Field(default="mix", pattern="^(tr|en|yabanci|mix)$")
    genres: List[str] = Field(default_factory=list)
    count: int = Field(default=20, ge=5, le=50)
    energy_level: str = Field(default="Orta", pattern="^(Düşük|Orta|Yüksek)$")
    therapy_mode: str = Field(default="catharsis", pattern="^(catharsis|uplift|calm)$")
    seed_inputs: Optional[List[str]] = Field(default_factory=list)


class ReplaceTrackRequest(BaseModel):
    access_token: Optional[str] = None
    mood: str = Field(..., min_length=2, max_length=50)
    exclude_ids: List[str] = Field(default_factory=list)
    exclude_artists: Optional[List[str]] = Field(default_factory=list)
    language: str = Field(default="mix", pattern="^(tr|en|yabanci|mix)$")
    genres: List[str] = Field(default_factory=list)


class SavePlaylistRequest(BaseModel):
    access_token: Optional[str] = None
    track_uris: List[str] = Field(..., min_length=1, max_length=100)
    mood_title: str = Field(..., min_length=2, max_length=100)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


class MoodCardRequest(BaseModel):
    mood: str
    doktor_notu: str = Field(..., max_length=600)
    sarki_adi: str = Field(..., max_length=200)
    sanatci_adi: Optional[str] = Field(default=None, max_length=200)
    track_count: int = Field(default=20, ge=1, le=100)
    image_url: Optional[str] = None


class VibeCardRequest(BaseModel):
    user1_name: str = Field(default="Sen", max_length=50)
    user2_name: str = Field(default="Arkadaşın", max_length=50)
    mood1_label: str = Field(..., max_length=50)
    mood2_label: str = Field(..., max_length=50)
    match_score: int = Field(default=85, ge=0, le=100)
    verdict: str = Field(..., max_length=500)
    sarki_adi: str = Field(..., max_length=200)
    sanatci_adi: Optional[str] = Field(default=None, max_length=200)
    image_url: Optional[str] = None


# ==============================================================================
# ENDPOINTLER
# ==============================================================================

@router.get("/meta")
def get_meta():
    """Uygulama genelindeki ruh halleri, türler, terapi modları ve Russell koordinatları."""
    return public_meta()


@router.get("/search-autocomplete")
def search_autocomplete(q: str = Query(..., min_length=1, max_length=100), access_token: Optional[str] = None):
    """Kullanıcı şarkı adı yazarken anlık Spotify arama önerileri (iLoveThatTrack modu)."""
    sp = get_spotify_client(access_token)
    try:
        tracks = spotify_search_autocomplete(sp, q, limit=8)
        return {"tracks": tracks}
    except SpotifyAuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception:
        return {"tracks": []}


@router.get("/login")
def login():
    """Spotify OAuth 2.0 yetkilendirme linkini (CSRF state korumalı) döner."""
    auth_url = get_authorize_url()
    return {"auth_url": auth_url}


@router.get("/callback")
def callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
):
    """
    Spotify OAuth dönüşü.
    Token'lar referer / proxy loglarında görünmemesi için URL hash fragment (#) ile iletilir.
    """
    base_fe = settings.FRONTEND_URL.rstrip("/")
    if error or not code:
        err_msg = error or "Yetkilendirme kodu alınamadı"
        return RedirectResponse(url=f"{base_fe}/#error={urllib.parse.quote(err_msg)}")

    if not verify_oauth_state(state):
        return RedirectResponse(url=f"{base_fe}/#error={urllib.parse.quote('Geçersiz veya süresi dolmuş OAuth state oturumu (CSRF).')}")

    try:
        tokens = exchange_code(code)
        fragment = urllib.parse.urlencode({
            "access_token": tokens["access_token"],
            "refresh_token": tokens.get("refresh_token") or "",
            "expires_at": tokens["expires_at"],
        })
        return RedirectResponse(url=f"{base_fe}/#{fragment}")
    except Exception as e:
        return RedirectResponse(url=f"{base_fe}/#error={urllib.parse.quote(f'Token değişimi başarısız: {str(e)}')}")


@router.post("/refresh")
def refresh_token_endpoint(req: RefreshTokenRequest):
    """Süresi dolmak üzere olan Spotify access_token'ını refresh_token ile yeniler."""
    try:
        tokens = refresh_user_token(req.refresh_token)
        return tokens
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token yenilenemedi: {str(e)}")


@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = analyze_mood(
        user_text=req.text,
        seed_artists=req.seed_artists,
        seed_tracks=req.seed_tracks,
    )
    return result


@router.post("/search-tracks")
def do_search_tracks(req: SearchTracksRequest):
    sp = get_spotify_client(req.access_token)
    try:
        tracks = search_tracks(
            sp=sp,
            mood=req.mood,
            language=req.language,
            genres=req.genres,
            count=req.count,
            energy_level=req.energy_level,
            seed_inputs=req.seed_inputs,
            therapy_mode=req.therapy_mode,
        )
        return {"tracks": tracks}
    except SpotifyAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(e), "code": "TOKEN_EXPIRED"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/replace-track")
def do_replace_track(req: ReplaceTrackRequest):
    sp = get_spotify_client(req.access_token)
    try:
        track = replace_single_track(
            sp=sp,
            mood=req.mood,
            exclude_ids=req.exclude_ids,
            language=req.language,
            genres=req.genres,
            exclude_artists=req.exclude_artists,
        )
        if track:
            return {"track": track}
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Uygun alternatif şarkı bulunamadı.")
    except SpotifyAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(e), "code": "TOKEN_EXPIRED"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/save-playlist")
def do_save_playlist(req: SavePlaylistRequest):
    if not req.access_token or req.access_token in ("null", "undefined"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Çalma listesini kaydedebilmek için Spotify hesabınızla giriş yapmalısınız."
        )
    sp = get_spotify_client(req.access_token)
    try:
        link, name = save_playlist(sp, req.track_uris, req.mood_title)
        return {"link": link, "name": name}
    except SpotifyAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(e), "code": "TOKEN_EXPIRED"}
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/mood-card")
def get_mood_card(req: MoodCardRequest):
    try:
        img_bytes = create_mood_card(
            mood=req.mood,
            doktor_notu=req.doktor_notu,
            sarki_adi=req.sarki_adi,
            sanatci_adi=req.sanatci_adi,
            track_count=req.track_count,
            image_url=req.image_url,
        )
        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/vibe-card")
def get_vibe_card(req: VibeCardRequest):
    try:
        img_bytes = create_vibe_card(
            user1_name=req.user1_name,
            user2_name=req.user2_name,
            mood1_label=req.mood1_label,
            mood2_label=req.mood2_label,
            match_score=req.match_score,
            verdict=req.verdict,
            sarki_adi=req.sarki_adi,
            sanatci_adi=req.sanatci_adi,
            image_url=req.image_url,
        )
        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

