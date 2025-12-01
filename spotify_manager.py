import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os
import streamlit as st
from dotenv import load_dotenv

try:
    load_dotenv()
except:
    pass

# --- ŞİFRE OKUMA ---
def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

SPOTIFY_CLIENT_ID = get_secret("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = get_secret("SPOTIFY_CLIENT_SECRET")
# Cloud'daki Redirect URI (Sonu /callback ile bitmeli)
REDIRECT_URI = get_secret("REDIRECT_URI")
if not REDIRECT_URI:
    REDIRECT_URI = 'http://127.0.0.1:8080/callback'

SCOPE = "playlist-modify-public playlist-modify-private"

# --- OAUTH NESNESİ OLUŞTURUCU ---
def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=spotipy.cache_handler.MemoryCacheHandler() # Cloud için RAM'de tut
    )

# --- BAĞLANTI KURMA (TOKEN VARSA) ---
def baglanti_kur(token_info=None):
    if not token_info:
        return None
    try:
        return spotipy.Spotify(auth=token_info['access_token'])
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

def sarki_arastirmasi_yap(sp, mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None):
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    
    en_keywords = {
        "neseli_pop": "happy upbeat", "huzunlu_slow": "sad emotional",
        "enerjik_spor": "workout power", "sakin_akustik": "chill relax",
        "indie_alternatif": "indie alternative", "hard_rock_metal": "rock metal",
        "elektronik_synth": "electronic synth", "jazz_blues": "jazz blues",
        "rap_hiphop": "rap hiphop"
    }
    tr_keywords = {
        "neseli_pop": "hareketli neşeli", "huzunlu_slow": "duygusal damar",
        "enerjik_spor": "motivasyon spor", "sakin_akustik": "sakin huzurlu",
        "indie_alternatif": "alternatif", "hard_rock_metal": "anadolu rock",
        "elektronik_synth": "elektronik", "jazz_blues": "caz blues",
        "rap_hiphop": "türkçe rap"
    }

    base_mood_en = en_keywords.get(mood_kategorisi, "pop")
    base_mood_tr = tr_keywords.get(mood_kategorisi, "pop")

    for tur in secilen_turler:
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz"] # Kısaltıldı
        
        if dil_secenegi == 'tr': query = f"Türkçe {base_mood_tr} {tur}"
        elif dil_secenegi == 'yabanci': query = f"{base_mood_en} {tur}"
        else: query = f"Türkçe {base_mood_tr} {tur}" if random.choice([True, False]) else f"{base_mood_en} {tur}"

        try:
            results = sp.search(q=query, limit=5, offset=offset_random, type='track', market='TR')
            if results and 'tracks' in results:
                for item in results['tracks']['items']:
                    img = item['album']['images'][0]['url'] if item['album']['images'] else None
                    track = {
                        'uri': item['uri'], 'name': item['name'],
                        'artist': item['artists'][0]['name'], 'album': item['album']['name'],
                        'preview_url': item['preview_url'], 'image': img,
                        'link': item['external_urls']['spotify']
                    }
                    all_tracks.append(track)
        except Exception as e:
            print(f"Hata: {e}")

    random.shuffle(all_tracks)
    return all_tracks[:20]

def playlisti_kaydet(sp, track_uris, mood_title):
    if not sp: return None, "Bağlantı yok"
    try:
        user_id = sp.current_user()['id']
        name = f"Terapi Seansı: {mood_title} 🧠"
        playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description="Mood AI ile oluşturuldu.")
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        return playlist['external_urls']['spotify'], name
    except Exception as e:
        return None, str(e)