import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import os
import math
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
REDIRECT_URI = get_secret("REDIRECT_URI")
if not REDIRECT_URI:
    REDIRECT_URI = 'http://127.0.0.1:8080/callback'

SCOPE = "playlist-modify-public playlist-modify-private"

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        cache_handler=spotipy.cache_handler.MemoryCacheHandler()
    )

def baglanti_kur(token_info=None):
    if not token_info:
        return None
    try:
        return spotipy.Spotify(auth=token_info['access_token'])
    except Exception as e:
        print(f"Bağlantı Hatası: {e}")
        return None

# YARDIMCI FONKSİYON: Şarkı nesnesi oluşturur
def _create_track_obj(item):
    img = item['album']['images'][0]['url'] if item['album']['images'] else None
    return {
        'id': item['id'],
        'uri': item['uri'], 
        'name': item['name'],
        'artist': item['artists'][0]['name'], 
        'album': item['album']['name'],
        'preview_url': item['preview_url'], 
        'image': img,
        'link': item['external_urls']['spotify']
    }

def sarki_arastirmasi_yap(sp, mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None, sarki_sayisi=10):
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    eklenen_sarkilar_ids = set()
    
    # Her türden kaçar tane alacağını hesapla (Örn: 20 şarkı, 4 tür -> Her türden 5 şarkı)
    limit_per_genre = math.ceil(sarki_sayisi / len(secilen_turler))
    # Spotify API max limit 50'dir, garanti olsun diye max 20 çekip içinden seçelim
    search_limit = min(50, limit_per_genre + 5) 

    # Dil Ayarları
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
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz", "classical", "metal", "piano", "reggae", "blues", "folk", "disco", "hip-hop"]
        
        query = ""
        if dil_secenegi == 'tr':
            query = tur if "türkçe" in tur.lower() else f"Türkçe {tur}"
        elif dil_secenegi == 'yabanci':
            query = f"genre:{tur}" if is_official else f"{tur}"
        else: # mix
            if random.choice([True, False]):
                query = tur if "türkçe" in tur.lower() else f"Türkçe {tur}"
            else:
                query = f"genre:{tur}" if is_official else f"{tur}"

        try:
            # Rastgelelik katmak için offset kullan
            genre_offset = offset_random + random.randint(0, 50)
            results = sp.search(q=query, limit=search_limit, offset=genre_offset, type='track', market='TR')
            
            if results and 'tracks' in results:
                count = 0
                for item in results['tracks']['items']:
                    if count >= limit_per_genre: break # Kotayı doldurduysak dur
                    
                    track_id = item['id']
                    if track_id in eklenen_sarkilar_ids: continue
                    
                    eklenen_sarkilar_ids.add(track_id)
                    all_tracks.append(_create_track_obj(item))
                    count += 1
                    
        except Exception as e:
            print(f"Hata ({tur}): {e}")

    random.shuffle(all_tracks)
    # Kullanıcının istediği sayıya tam olarak kes
    return all_tracks[:sarki_sayisi]

def tek_sarki_getir(sp, mood_kategorisi, exclude_ids=[], dil_secenegi='mix', secilen_turler=None):
    """Mevcut listede olmayan YENİ bir şarkı bulur."""
    if not sp: return None
    if not secilen_turler: secilen_turler = ["Pop"]
    
    # Rastgele bir tür seç
    tur = random.choice(secilen_turler)
    
    # Rastgele bir offset ile arama yap (Daha önce gelmeyeni bulmak için)
    offset = random.randint(0, 200)
    
    # Sorgu oluşturma (Yukarıdakiyle benzer)
    query = f"Türkçe {tur}" if dil_secenegi == 'tr' else f"{tur}"
    if dil_secenegi == 'mix' and random.choice([True, False]): query = f"Türkçe {tur}"
    
    try:
        results = sp.search(q=query, limit=20, offset=offset, type='track', market='TR')
        if results and 'tracks' in results:
            for item in results['tracks']['items']:
                if item['id'] not in exclude_ids:
                    return _create_track_obj(item) # Bulduk!
    except:
        pass
        
    return None # Bulamazsa None döner

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