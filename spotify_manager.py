import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os
from dotenv import load_dotenv

# .env yükle (Localde çalışırken lazım, Cloud'da otomatik secrets'tan okur)
try:
    load_dotenv()
except:
    pass

# --- AYARLAR ---
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# KRİTİK GÜNCELLEME:
# Eğer internetteyse oradaki ayarı kullan, yoksa local adresi kullan.
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://127.0.0.1:8080/callback")

SCOPE = "playlist-modify-public playlist-modify-private"

def baglanti_kur():
    if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
        print("HATA: Spotify API anahtarları bulunamadı.")
        return None
    try:
        return spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope=SCOPE
        ))
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

def sarki_arastirmasi_yap(mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None):
    sp = baglanti_kur()
    if not sp: return []

    if not secilen_turler:
        secilen_turler = ["Pop"]

    all_tracks = []
    
    en_keywords = {
        "neseli_pop": "happy upbeat",
        "huzunlu_slow": "sad emotional",
        "enerjik_spor": "workout power",
        "sakin_akustik": "chill relax",
        "indie_alternatif": "indie alternative",
        "hard_rock_metal": "rock metal",
        "elektronik_synth": "electronic synth",
        "jazz_blues": "jazz blues",
        "rap_hiphop": "rap hiphop"
    }

    tr_keywords = {
        "neseli_pop": "hareketli neşeli",
        "huzunlu_slow": "duygusal damar",
        "enerjik_spor": "motivasyon spor",
        "sakin_akustik": "sakin huzurlu",
        "indie_alternatif": "alternatif",
        "hard_rock_metal": "anadolu rock",
        "elektronik_synth": "elektronik",
        "jazz_blues": "caz blues",
        "rap_hiphop": "türkçe rap"
    }

    base_mood_en = en_keywords.get(mood_kategorisi, "pop")
    base_mood_tr = tr_keywords.get(mood_kategorisi, "pop")

    for tur in secilen_turler:
        is_official_genre = tur.lower() in [
            "acoustic", "afrobeat", "alt-rock", "alternative", "ambient", "black-metal", "blues", 
            "classical", "club", "country", "dance", "death-metal", "deep-house", "disco", "drum-and-bass", 
            "dubstep", "edm", "electro", "electronic", "emo", "folk", "funk", "gospel", "goth", "grunge", 
            "hard-rock", "heavy-metal", "hip-hop", "house", "indie", "indie-pop", "industrial", "jazz", 
            "k-pop", "latin", "metal", "metalcore", "minimal-techno", "new-age", "opera", "party", "piano", 
            "pop", "punk", "punk-rock", "r-n-b", "reggae", "reggaeton", "rock", "rock-n-roll", "rockabilly", 
            "romance", "sad", "salsa", "samba", "show-tunes", "singer-songwriter", "ska", "soul", 
            "soundtracks", "synth-pop", "techno", "trance", "trip-hop", "turkish", "work-out", "world-music"
        ]
        
        if dil_secenegi == 'tr':
            query = f"Türkçe {base_mood_tr} {tur}"
        
        elif dil_secenegi == 'yabanci':
            if is_official_genre:
                query = f"genre:{tur} {base_mood_en}"
            else:
                query = f"{base_mood_en} {tur}"
        
        else: # mix
            if random.choice([True, False]):
                query = f"Türkçe {base_mood_tr} {tur}"
            else:
                if is_official_genre:
                    query = f"genre:{tur} {base_mood_en}"
                else:
                    query = f"{base_mood_en} {tur}"

        try:
            results = sp.search(q=query, limit=5, offset=offset_random, type='track', market='TR')
            
            if results and 'tracks' in results:
                for item in results['tracks']['items']:
                    img = item['album']['images'][0]['url'] if item['album']['images'] else None
                    track = {
                        'uri': item['uri'],
                        'name': item['name'],
                        'artist': item['artists'][0]['name'],
                        'album': item['album']['name'],
                        'preview_url': item['preview_url'],
                        'image': img,
                        'link': item['external_urls']['spotify']
                    }
                    all_tracks.append(track)
        except Exception as e:
            print(f"Arama Hatası ({tur}): {e}")

    random.shuffle(all_tracks)
    return all_tracks[:20]

def playlisti_kaydet(track_uris, mood_title):
    sp = baglanti_kur()
    if not sp: return None, "Bağlantı hatası"

    try:
        user_id = sp.current_user()['id']
        name = f"Terapi Seansı: {mood_title} 🧠"
        
        playlist = sp.user_playlist_create(user=user_id, name=name, public=False, description="Mood AI ile oluşturuldu.")
        sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris)
        
        return playlist['external_urls']['spotify'], name
    except Exception as e:
        return None, str(e)