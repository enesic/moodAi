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

def sarki_arastirmasi_yap(sp, mood_kategorisi, offset_random=0, dil_secenegi='mix', secilen_turler=None):
    if not sp: return []
    if not secilen_turler: secilen_turler = ["Pop"]

    all_tracks = []
    eklenen_sarkilar_ids = set()
    
    # DÜZELTME: Mood kelimelerini (base_mood) kaldırdık. 
    # Artık arama sadece "Tür" ve "Dil" odaklı yapılacak. 
    # Bu sayede "Sakin" kelimesi yüzünden Rap şarkısı gelmeyecek.

    for tur in secilen_turler:
        # Spotify'ın resmi türleri (genre: ile aratmak için)
        is_official = tur.lower() in ["acoustic", "rock", "pop", "jazz", "classical", "metal", "piano", "reggae", "blues", "folk", "disco", "hip-hop"]
        
        # SORGULARI TEMİZLEŞTİRDİK
        query = ""
        
        if dil_secenegi == 'tr':
            # "Türkçe Pop" gibi zaten içinde Türkçe geçen türleri bozma
            if "türkçe" in tur.lower() or "turkish" in tur.lower():
                query = tur
            else:
                query = f"Türkçe {tur}"
                
        elif dil_secenegi == 'yabanci':
            if is_official:
                query = f"genre:{tur}"
            else:
                query = f"{tur}"
                
        else: # mix
            # Karışık modda %50 şansla Türkçe ekle
            if random.choice([True, False]):
                if "türkçe" in tur.lower():
                    query = tur
                else:
                    query = f"Türkçe {tur}"
            else:
                if is_official:
                    query = f"genre:{tur}"
                else:
                    query = f"{tur}"

        try:
            # market='TR' ile Türkiye'de erişilebilir şarkıları getir
            results = sp.search(q=query, limit=5, offset=offset_random, type='track', market='TR')
            
            if results and 'tracks' in results:
                for item in results['tracks']['items']:
                    track_id = item['id']
                    
                    # Tekrar kontrolü
                    if track_id in eklenen_sarkilar_ids:
                        continue
                    
                    # Şarkı isminde aradığımız kelime var mı diye basit bir kontrol (Opsiyonel Güvenlik)
                    # Rap istemiyorsak ve listede Rapozof varsa eleyebiliriz ama şimdilik tür araması yeterli olacaktır.
                    
                    eklenen_sarkilar_ids.add(track_id)
                    
                    img = item['album']['images'][0]['url'] if item['album']['images'] else None
                    track = {
                        'uri': item['uri'], 'name': item['name'],
                        'artist': item['artists'][0]['name'], 'album': item['album']['name'],
                        'preview_url': item['preview_url'], 'image': img,
                        'link': item['external_urls']['spotify']
                    }
                    all_tracks.append(track)
        except Exception as e:
            print(f"Hata ({tur}): {e}")

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