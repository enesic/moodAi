from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import RedirectResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
import io

from backend.services.spotify import create_spotify_oauth, get_spotify_client, search_tracks, replace_single_track, save_playlist
from backend.services.ai_agent import analyze_mood
from backend.utils.image_gen import create_mood_card
from backend.core.config import settings

router = APIRouter()

class AnalyzeRequest(BaseModel):
    text: str

class SearchTracksRequest(BaseModel):
    access_token: Optional[str] = None
    mood: str
    language: str = "mix"
    genres: List[str]
    count: int = 20
    energy_level: str = "Orta"

class ReplaceTrackRequest(BaseModel):
    access_token: Optional[str] = None
    mood: str
    exclude_ids: List[str]
    language: str = "mix"
    genres: List[str]

class SavePlaylistRequest(BaseModel):
    access_token: Optional[str] = None
    track_uris: List[str]
    mood_title: str

class MoodCardRequest(BaseModel):
    mood: str
    doktor_notu: str
    sarki_adi: str


@router.get("/login")
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@router.get("/callback")
def callback(code: Optional[str] = None, error: Optional[str] = None):
    # Spotify hata ile döndüyse (kullanıcı izin vermedi veya client_id geçersiz)
    if error or not code:
        error_msg = error or "Kod alınamadı"
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?error={error_msg}")
    
    sp_oauth = create_spotify_oauth()
    try:
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info['access_token']
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?access_token={access_token}")
    except Exception as e:
        return RedirectResponse(url=f"{settings.FRONTEND_URL}?error=auth_failed")

@router.post("/analyze")
def analyze(req: AnalyzeRequest):
    result = analyze_mood(req.text)
    return result

@router.post("/search-tracks")
def do_search_tracks(req: SearchTracksRequest):
    sp = get_spotify_client(req.access_token)
    try:
        tracks = search_tracks(sp, req.mood, req.language, req.genres, req.count, req.energy_level)
        return {"tracks": tracks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/replace-track")
def do_replace_track(req: ReplaceTrackRequest):
    sp = get_spotify_client(req.access_token)
    try:
        track = replace_single_track(sp, req.mood, req.exclude_ids, req.language, req.genres)
        if track:
            return {"track": track}
        else:
            raise HTTPException(status_code=404, detail="No replacement track found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save-playlist")
def do_save_playlist(req: SavePlaylistRequest):
    if not req.access_token or req.access_token in ("null", "undefined"):
        raise HTTPException(status_code=401, detail="Çalma listesini kaydedebilmek için Spotify hesabınızla giriş yapmalısınız.")
    sp = get_spotify_client(req.access_token)
    try:
        link, name = save_playlist(sp, req.track_uris, req.mood_title)
        return {"link": link, "name": name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mood-card")
def get_mood_card(req: MoodCardRequest):
    try:
        img_bytes = create_mood_card(req.mood, req.doktor_notu, req.sarki_adi)
        return StreamingResponse(io.BytesIO(img_bytes), media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
