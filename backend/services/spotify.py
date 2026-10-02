import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from typing import Optional
import random
import os
import math
from backend.core.config import settings

SCOPE = "playlist-modify-public playlist-modify-private"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET,
        redirect_uri=settings.SPOTIFY_REDIRECT_URI,
        scope=SCOPE
    )

def get_spotify_client(access_token: Optional[str] = None):
    """Kullanıcı token'ı varsa kullanıcı yetkisiyle, yoksa Misafir Modu (Client Credentials) ile Spotify istemcisi oluşturur."""
    if access_token and str(access_token).strip() and str(access_token).strip().lower() not in ("null", "none", "undefined"):
        return spotipy.Spotify(auth=access_token)
    
    # Misafir Modu: Spotify Developer API credentials ile arama desteği
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

BLACKLIST_KEYWORDS = [
    "asmr", "nursery", "lullaby", "baby sleep", "white noise",
    "sound effect", "karaoke", "ringtone", "medya konya", "çocuk şarkı"
]

def _create_track_obj(item):
    if not item or not item.get('id'):
        return None
        
    name = item.get('name', '')
    artists = item.get('artists', [])
    artist_name = artists[0]['name'] if artists else 'Unknown'
    
    # Süre Filtresi (1 dakika ile 9 dakika arası gerçek şarkılar)
    duration_ms = item.get('duration_ms', 0)
    if duration_ms < 60000 or duration_ms > 540000:
        return None

    # Spam / ASMR / Çocuk şarkısı / Karaoke filtresi
    name_lower = name.lower()
    artist_lower = artist_name.lower()
    for kw in BLACKLIST_KEYWORDS:
        if kw in name_lower or kw in artist_lower:
            return None

    img = item['album']['images'][0]['url'] if item.get('album') and item['album'].get('images') else None
    return {
        'id': item['id'],
        'uri': item['uri'], 
        'name': name,
        'artist': artist_name, 
        'album': item['album']['name'] if item.get('album') else 'Unknown',
        'preview_url': item.get('preview_url'), 
        'image': img,
        'popularity': item.get('popularity', 50),
        'link': item['external_urls']['spotify'] if item.get('external_urls') else None
    }

def get_optimized_query(genre_name, language, energy_suffix_tr, energy_suffix_en):
    """Türkçe tür adını Spotify'da aranabilir sorguya çevirir."""
    genre_map = {
        "Türkçe Pop Hareketli": ("Türkçe Pop Hareketli", "Upbeat Pop"),
        "Yaz Hitleri": ("Türkçe Yaz Hitleri", "Summer Hits"),
        "Dance Pop": ("Türkçe Dance Pop", "Dance Pop"),
        "Road Trip": ("Türkçe Yolculuk", "Road Trip"),
        "Serdar Ortaç Pop": ("Serdar Ortaç", "90s Pop"),
        "90'lar Türkçe Pop": ("90lar Türkçe Pop", "90s Pop"),
        "Disco": ("Disco", "Disco"),
        "K-Pop": ("K-Pop", "K-Pop"),
        "Reggaeton": ("Reggaeton", "Reggaeton"),
        "Akustik Hüzün": ("Türkçe Akustik Hüzün", "Sad Acoustic"),
        "Melankolik Indie": ("Türkçe Melankolik Indie", "Sad Indie"),
        "Slow Pop": ("Türkçe Slow Pop", "Slow Pop"),
        "Piyano & Yağmur": ("Piyano Yağmur", "Piano Rain"),
        "Türkçe Damar": ("Damar", "Sad Songs"),
        "Alternatif Balad": ("Türkçe Alternatif", "Alternative Ballads"),
        "Türkü": ("Türkü", "Folk"),
        "Arabesk": ("Arabesk", "Oriental Strings"),
        "Kırık Kalpler": ("Ayrılık", "Breakup"),
        "Spor Motivasyon": ("Türkçe Spor Motivasyon", "Workout Motivation"),
        "Türkçe Rap": ("Türkçe Rap", "Rap"),
        "Phonk": ("Türkçe Phonk", "Phonk"),
        "Drill": ("Türkçe Drill", "Drill"),
        "Techno": ("Türkçe Techno", "Techno"),
        "House": ("Türkçe House", "House"),
        "Gym Hits": ("Türkçe Gym", "Gym Hits"),
        "Power Workout": ("Türkçe Power", "Power Workout"),
        "Remix": ("Remix", "Remix"),
        "Lo-Fi Beats": ("Türkçe Lofi", "Lo-Fi Beats"),
        "Chill Pop": ("Türkçe Chill Pop", "Chill Pop"),
        "Akustik Cover": ("Türkçe Akustik Cover", "Acoustic Covers"),
        "Jazz Vibes": ("Türkçe Caz", "Jazz Vibes"),
        "Enstrümantal": ("Enstrümantal", "Instrumental"),
        "Kitap Okuma": ("Kitap Okuma", "Reading"),
        "Kahve Modu": ("Türkçe Kahve", "Coffee House"),
        "Ambient": ("Ambient", "Ambient"),
        "Soft Rock": ("Türkçe Soft Rock", "Soft Rock"),
        "Sufi/Ney": ("Ney", "Sufi"),
        "Alternatif Rock": ("Türkçe Alternatif Rock", "Alternative Rock"),
        "Yeni Nesil Indie": ("Türkçe Yeni Nesil Indie", "Modern Indie"),
        "Anadolu Rock": ("Anadolu Rock", "Psychedelic Rock"),
        "Shoegaze": ("Türkçe Shoegaze", "Shoegaze"),
        "Soft Indie": ("Türkçe Soft Indie", "Soft Indie"),
        "Bağımsız Müzik": ("Türkçe Bağımsız", "Indie"),
        "Dream Pop": ("Türkçe Dream Pop", "Dream Pop"),
        "Türkçe Rock": ("Türkçe Rock", "Rock"),
        "Heavy Metal": ("Türkçe Metal", "Heavy Metal"),
        "Nu-Metal": ("Türkçe Nu-Metal", "Nu-Metal"),
        "Hard Rock": ("Türkçe Hard Rock", "Hard Rock"),
        "Punk": ("Türkçe Punk", "Punk"),
        "Garage Rock": ("Türkçe Garage", "Garage Rock"),
        "Old School": ("Türkçe Old School Rap", "Old School Hip Hop"),
        "Melodic Rap": ("Türkçe Melodic Rap", "Melodic Rap"),
        "Trap": ("Türkçe Trap", "Trap"),
        "Arabesk Rap": ("Arabesk Rap", "Melodic Rap"),
        "Underground": ("Türkçe Underground", "Underground Hip Hop"),
        "Smooth Jazz": ("Türkçe Caz", "Smooth Jazz"),
        "Gece Mavisi": ("Gece", "Late Night Jazz"),
        "Blues Rock": ("Türkçe Blues", "Blues Rock"),
        "Soul": ("Türkçe Soul", "Soul"),
        "Vocal Jazz": ("Türkçe Vokal Caz", "Vocal Jazz"),
        "Türkçe Caz": ("Türkçe Caz", "Jazz"),
        "Coffee Table Jazz": ("Türkçe Caz", "Coffee Jazz"),
        "Synthwave": ("Türkçe Synthwave", "Synthwave"),
        "Cyberpunk": ("Türkçe Cyberpunk", "Cyberpunk"),
        "Deep House": ("Türkçe Deep House", "Deep House"),
        "Minimal Techno": ("Türkçe Minimal", "Minimal Techno"),
        "EDM": ("Türkçe EDM", "EDM"),
        "Daft Punk Vibe": ("Elektronik", "Daft Punk Style")
    }

    if genre_name in genre_map:
        q_tr, q_en = genre_map[genre_name]
    else:
        q_tr = f"Türkçe {genre_name}"
        q_en = genre_name

    if language == 'tr':
        return f"{q_tr}{energy_suffix_tr}"
    elif language in ('yabanci', 'en'):
        return f"{q_en}{energy_suffix_en}"
    else:  # mix
        return f"{q_tr}{energy_suffix_tr}" if random.choice([True, False]) else f"{q_en}{energy_suffix_en}"

def search_tracks(sp, mood, language, genres, count, energy_level):
    all_tracks = []
    # Mocking energetic suffixes
    en_suffix = ""
    tr_suffix = ""
    if energy_level == "Yüksek":
        en_suffix = " upbeat"
        tr_suffix = " hareketli"
    elif energy_level == "Düşük":
        en_suffix = " acoustic"
        tr_suffix = " yavaş"

    for genre in genres:
        query = get_optimized_query(genre, language, tr_suffix, en_suffix)
        try:
            results = sp.search(q=query, type='track', limit=min(50, count * 2))
            items = results.get('tracks', {}).get('items', [])
            for item in items:
                track = _create_track_obj(item)
                if track:
                    all_tracks.append(track)
        except Exception:
            continue

    # Remove duplicates and prioritize quality tracks (popularity > 15)
    unique_tracks = {t['id']: t for t in all_tracks}.values()
    final_list = list(unique_tracks)
    
    # Sort with preference for popular tracks, then shuffle slightly for freshness
    final_list.sort(key=lambda t: t.get('popularity', 0), reverse=True)
    top_pool = final_list[:count * 2] if len(final_list) > count else final_list
    random.shuffle(top_pool)
    return top_pool[:count]

def replace_single_track(sp, mood, exclude_ids, language, genres):
    if not genres:
        return None
    
    genre = random.choice(genres)
    query = get_optimized_query(genre, language, "", "")
    
    try:
        results = sp.search(q=query, type='track', limit=50)
        items = results.get('tracks', {}).get('items', [])
        
        for item in items:
            if item['id'] not in exclude_ids:
                return _create_track_obj(item)
    except Exception:
        pass
        
    return None

def save_playlist(sp, track_uris, mood_title):
    if not getattr(sp, 'auth', None) and not getattr(sp, '_auth', None):
        raise Exception("Çalma listesini hesabınıza kaydetmek için Spotify ile giriş yapmalısınız.")
    try:
        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(user=user_id, name=f"Mood AI: {mood_title}", public=False)
        
        # Spotipy can add max 100 tracks per request
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris[i:i+batch_size])
            
        return playlist['external_urls']['spotify'], playlist['name']
    except Exception as e:
        raise Exception(f"Playlist kaydetme hatası: {str(e)}")
