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

# --- GÜVENLİ ŞİFRE OKUYUCU ---
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
        cache_handler=spotipy.cache_handler.MemoryCacheHandler(),
        open_browser=False 
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

# --- AKILLI ÇEVİRMEN (TÜRKÇE -> SPOTIFY DİLİ) ---
def get_optimized_query(tur_adi, dil, enerji_suffix_tr, enerji_suffix_en):
    genre_map = {
        "Türkçe Pop Hareketli": ("Türkçe Pop Hareketli", "Upbeat Pop"),
        "Yaz Hitleri": ("Türkçe Yaz Hitleri", "Summer Hits"),
        "Dance Pop": ("Türkçe Dance Pop", "Dance Pop"),
        "Road Trip": ("Türkçe Yolculuk", "Road Trip"),
        "Serdar Ortaç Pop": ("Serdar Ortaç", "90s Pop"),
        "90'lar Türkçe Pop": ("90lar Türkçe Pop", "90s Pop"),
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

    if tur_adi in genre_map:
        q_tr, q_en = genre_map[tur_adi]
    else:
        q_tr = f"Türkçe {tur_adi}"
        q_en = tur_adi

    if dil == 'tr':
        return f"{q_tr}{enerji_suffix_tr}"
    elif dil == 'yabanci':
        return f"{q_en}{enerji_suffix_en}"
    else: # mix
        return f"{q_tr}{enerji_suffix_tr}" if random.choice([True, False]) else f"{q_en}{enerji_suffix_en}"

def sarki_arastirmasi_yap(sp, mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None, sarki_sayisi=10, enerji_seviyesi="Orta"):
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    eklenen_sarkilar_unique_keys = set()
    sanatci_sayaci = {} 

    limit_per_genre = math.ceil(sarki_sayisi / len(secilen_turler)) + 3
    search_limit = min(50, limit_per_genre + 5) 

    # --- ENERJİ FİLTRELERİ ---
    enerji_suffix_tr = ""
    enerji_suffix_en = ""
    if enerji_seviyesi == "Düşük":
        enerji_suffix_tr = " sakin yavaş soft akustik"
        enerji_suffix_en = " slow calm acoustic soft"
    elif enerji_seviyesi == "Yüksek":
        enerji_suffix_tr = " hareketli hızlı tempo enerji"
        enerji_suffix_en = " upbeat high tempo energy party"

    for tur in secilen_turler:
        query = get_optimized_query(tur, dil_secenegi, enerji_suffix_tr, enerji_suffix_en)

        try:
            genre_offset = offset_random + random.randint(0, 50)
            results = sp.search(q=query, limit=search_limit, offset=genre_offset, type='track', market='TR')
            
            # Sonuç yoksa yedeğe geç
            if (not results or not results['tracks']['items']):
                 base_query = get_optimized_query(tur, dil_secenegi, "", "")
                 results = sp.search(q=base_query, limit=search_limit, offset=0, type='track', market='TR')

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
        
        # Tek şarkı için de akıllı sorgu kullan
        query = get_optimized_query(tur, dil_secenegi, "", "")
        
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