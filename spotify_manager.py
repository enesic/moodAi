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
    """
    Belirlenen kriterlere göre şarkı havuzu oluşturur.
    sarki_sayisi: Kullanıcının slider ile seçtiği sayı (10-50)
    """
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    
    # Gelişmiş Filtreleme Hafızası
    eklenen_sarkilar_unique_keys = set() # İsim + Sanatçı (Aynı şarkının farklı versiyonlarını engeller)
    sanatci_sayaci = {} # Hangi sanatçıdan kaç tane aldık?

    # Her türden kaçar tane alacağını hesapla (+3 esneklik payı)
    limit_per_genre = math.ceil(sarki_sayisi / len(secilen_turler)) + 3
    search_limit = min(50, limit_per_genre + 5) 

    # Dil Ayarları
    tr_keywords = {
        "neseli_pop": "hareketli neşeli", "huzunlu_slow": "duygusal damar",
        "enerjik_spor": "motivasyon spor", "sakin_akustik": "sakin huzurlu",
        "indie_alternatif": "alternatif", "hard_rock_metal": "anadolu rock",
        "elektronik_synth": "elektronik", "jazz_blues": "caz blues",
        "rap_hiphop": "türkçe rap"
    }
    
    base_mood_tr = tr_keywords.get(mood_kategorisi, "pop")

    for tur in secilen_turler:
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz", "classical", "metal", "piano", "reggae", "blues", "folk", "disco", "hip-hop"]
        
        # Sorgu Oluşturma
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
            
            # Eğer Türkçe arama sonuç vermezse, global aramaya geç (Fallback)
            if (not results or not results['tracks']['items']) and dil_secenegi == 'tr':
                 query = f"{base_mood_tr} {tur}" 
                 results = sp.search(q=query, limit=search_limit, offset=0, type='track', market='TR')

            if results and 'tracks' in results:
                count = 0
                for item in results['tracks']['items']:
                    if count >= limit_per_genre: break 
                    
                    artist_name = item['artists'][0]['name']
                    track_name = item['name']
                    
                    # 1. KONTROL: Şarkı Daha Önce Eklendi mi? (İsim ve Sanatçı bazlı)
                    unique_key = f"{track_name} - {artist_name}".lower()
                    if unique_key in eklenen_sarkilar_unique_keys:
                        continue
                    
                    # 2. KONTROL: Sanatçı Kotası Doldu mu? (Max 2 Şarkı)
                    if sanatci_sayaci.get(artist_name, 0) >= 2:
                        continue

                    # Listeye Ekle
                    eklenen_sarkilar_unique_keys.add(unique_key)
                    sanatci_sayaci[artist_name] = sanatci_sayaci.get(artist_name, 0) + 1
                    
                    all_tracks.append(_create_track_obj(item))
                    count += 1
                    
        except Exception as e:
            print(f"Hata ({tur}): {e}")

    random.shuffle(all_tracks)
    # Kullanıcının istediği sayıya tam olarak kes (Fazlaları at)
    return all_tracks[:sarki_sayisi]

def tek_sarki_getir(sp, mood_kategorisi, exclude_ids=[], dil_secenegi='mix', secilen_turler=None):
    """
    'Değiştir' butonu için mevcut listede olmayan YENİ bir şarkı bulur.
    Eğer spesifik türde bulamazsa, genel moddan getirir.
    """
    if not sp: return None
    if not secilen_turler: secilen_turler = ["Pop"]
    
    max_retries = 3
    
    for _ in range(max_retries):
        tur = random.choice(secilen_turler)
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz", "classical", "metal", "piano"]
        
        offset = random.randint(0, 100)
        
        query = ""
        if dil_secenegi == 'tr':
            query = tur if "türkçe" in tur.lower() else f"Türkçe {tur}"
        elif dil_secenegi == 'yabanci':
            query = f"genre:{tur}" if is_official else f"{tur}"
        else:
            query = f"Türkçe {tur}" if random.choice([True, False]) else f"{tur}"
        
        try:
            results = sp.search(q=query, limit=10, offset=offset, type='track', market='TR')
            if results and 'tracks' in results:
                for item in results['tracks']['items']:
                    # Sadece ID kontrolü yeterli değil, isim kontrolü de yapabiliriz ama
                    # tekli değişimde ID kontrolü genellikle yeterlidir.
                    if item['id'] not in exclude_ids:
                        return _create_track_obj(item) 
        except:
            continue
            
    try:
        tr_keywords = {
            "neseli_pop": "hareketli", "huzunlu_slow": "damar",
            "enerjik_spor": "spor", "sakin_akustik": "sakin",
            "indie_alternatif": "alternatif", "hard_rock_metal": "rock",
            "elektronik_synth": "elektronik", "jazz_blues": "caz",
            "rap_hiphop": "rap"
        }
        fallback_query = tr_keywords.get(mood_kategorisi, "pop")
        results = sp.search(q=fallback_query, limit=10, offset=random.randint(0, 50), type='track', market='TR')
        if results and 'tracks' in results:
             for item in results['tracks']['items']:
                if item['id'] not in exclude_ids:
                    return _create_track_obj(item)
    except:
        pass

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