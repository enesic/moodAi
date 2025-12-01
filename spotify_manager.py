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

# GÜNCELLEME: enerji_seviyesi parametresi eklendi
def sarki_arastirmasi_yap(sp, mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None, sarki_sayisi=10, enerji_seviyesi="Orta"):
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    eklenen_sarkilar_unique_keys = set()
    sanatci_sayaci = {} 

    limit_per_genre = math.ceil(sarki_sayisi / len(secilen_turler)) + 3
    search_limit = min(50, limit_per_genre + 5) 

    # --- ENERJİ AYARLARI ---
    enerji_suffix_tr = ""
    enerji_suffix_en = ""
    
    if enerji_seviyesi == "Düşük":
        enerji_suffix_tr = " sakin yavaş soft akustik"
        enerji_suffix_en = " slow calm acoustic soft"
    elif enerji_seviyesi == "Yüksek":
        enerji_suffix_tr = " hareketli hızlı tempo kopmalık"
        enerji_suffix_en = " upbeat high tempo party energy"

    base_mood_tr = {
        "neseli_pop": "neşeli", "huzunlu_slow": "duygusal", "enerjik_spor": "spor",
        "sakin_akustik": "sakin", "indie_alternatif": "alternatif", "hard_rock_metal": "rock",
        "elektronik_synth": "elektronik", "jazz_blues": "caz", "rap_hiphop": "rap"
    }.get(mood_kategorisi, "pop")

    for tur in secilen_turler:
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz", "classical", "metal", "piano", "reggae", "blues", "folk", "disco", "hip-hop"]
        
        # Sorgu Oluşturma (Enerji kelimelerini ekleyerek)
        query = ""
        if dil_secenegi == 'tr':
            query = f"{tur} {enerji_suffix_tr}"
            # Eğer zaten içinde 'türkçe' yoksa ekle
            if "türkçe" not in query.lower() and "turkish" not in query.lower():
                query = f"Türkçe {query}"
                
        elif dil_secenegi == 'yabanci':
            # Yabancıysa ve resmi türse genre: kullan, değilse düz arama
            # Enerji ekini sona ekle
            if is_official:
                query = f"genre:{tur} {enerji_suffix_en}"
            else:
                query = f"{tur} {enerji_suffix_en}"
                
        else: # mix
            if random.choice([True, False]):
                query = f"Türkçe {tur} {enerji_suffix_tr}"
            else:
                query = f"{tur} {enerji_suffix_en}"

        try:
            genre_offset = offset_random + random.randint(0, 50)
            results = sp.search(q=query, limit=search_limit, offset=genre_offset, type='track', market='TR')
            
            # Sonuç yoksa yedeğe geç (Enerji ekini kaldırıp dene)
            if (not results or not results['tracks']['items']):
                 query_backup = f"{base_mood_tr} {tur}" if dil_secenegi == 'tr' else f"{tur}"
                 results = sp.search(q=query_backup, limit=search_limit, offset=0, type='track', market='TR')

            if results and 'tracks' in results:
                count = 0
                for item in results['tracks']['items']:
                    if count >= limit_per_genre: break 
                    
                    artist_name = item['artists'][0]['name']
                    track_name = item['name']
                    
                    unique_key = f"{track_name} - {artist_name}".lower()
                    if unique_key in eklenen_sarkilar_unique_keys: continue
                    if sanatci_sayaci.get(artist_name, 0) >= 2: continue

                    eklenen_sarkilar_unique_keys.add(unique_key)
                    sanatci_sayaci[artist_name] = sanatci_sayaci.get(artist_name, 0) + 1
                    
                    all_tracks.append(_create_track_obj(item))
                    count += 1
                    
        except Exception as e:
            print(f"Hata ({tur}): {e}")

    random.shuffle(all_tracks)
    return all_tracks[:sarki_sayisi]

def tek_sarki_getir(sp, mood_kategorisi, exclude_ids=[], dil_secenegi='mix', secilen_turler=None):
    if not sp: return None
    if not secilen_turler: secilen_turler = ["Pop"]
    
    max_retries = 3
    for _ in range(max_retries):
        tur = random.choice(secilen_turler)
        offset = random.randint(0, 100)
        
        query = f"Türkçe {tur}" if dil_secenegi == 'tr' else f"{tur}"
        if dil_secenegi == 'mix' and random.choice([True, False]): query = f"Türkçe {tur}"
        
        try:
            results = sp.search(q=query, limit=10, offset=offset, type='track', market='TR')
            if results and 'tracks' in results:
                for item in results['tracks']['items']:
                    if item['id'] not in exclude_ids:
                        return _create_track_obj(item) 
        except:
            continue
    return None 

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