import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyClientCredentials
from typing import Optional, List, Tuple, Dict
import random
import os
import re
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
    
    client_credentials_manager = SpotifyClientCredentials(
        client_id=settings.SPOTIFY_CLIENT_ID,
        client_secret=settings.SPOTIFY_CLIENT_SECRET
    )
    return spotipy.Spotify(client_credentials_manager=client_credentials_manager)

BLACKLIST_KEYWORDS = [
    "asmr", "nursery", "lullaby", "baby sleep", "white noise",
    "sound effect", "karaoke", "ringtone", "medya konya", "çocuk şarkı",
    "children", "lullabies", "sleep sound", "rain sounds for sleep"
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

# ==============================================================================
# SEKTÖR STANDARDI TÜRKÇE VE YABANCI KÜRATÖRLÜK MATRİSİ (ANCHOR ARTISTS & GENRES)
# ==============================================================================

GENRE_CURATION_MATRIX = {
    "neseli_pop": {
        "tr": ["Tarkan", "Edis", "Simge", "Gülşen", "Mabel Matiz", "Kenan Doğulu", "Yalın", "Zeynep Bastık", "Buray", "Hadise", "Murat Boz", "Aleyna Tilki", "Emir Can İğrek", "Derya Uluğ", "Sertab Erener"],
        "en": ["Dua Lipa", "The Weeknd", "Taylor Swift", "Harry Styles", "Ariana Grande", "Bruno Mars", "Billie Eilish", "Ed Sheeran", "Olivia Rodrigo", "Sabrina Carpenter", "Lady Gaga", "Miley Cyrus", "Katy Perry"]
    },
    "huzunlu_slow": {
        "tr": ["Sezen Aksu", "Model", "Sıla", "Kalben", "Mavi Gri", "Pinhani", "Madrigal", "Dolu Kadehi Ters Tut", "Dedublüman", "Fatma Turgut", "Toygar Işıklı", "Feridun Düzağaç", "Cem Adrian", "Yüzyüzeyken Konuşuruz", "Emre Aydın"],
        "en": ["Adele", "Sam Smith", "Lewis Capaldi", "Lana Del Rey", "Tom Odell", "James Arthur", "Phoebe Bridges", "Cigarettes After Sex", "Conan Gray", "Kodaline", "Dean Lewis", "Coldplay", "Finneas"]
    },
    "enerjik_spor": {
        "tr": ["Lvbel C5", "Motive", "BLOK3", "UZI", "Ati242", "Ceza", "Mahmut Orhan", "Batuflex", "Heijan", "Massaka", "Çakal", "Ezhel"],
        "en": ["Eminem", "Travis Scott", "Drake", "Metro Boomin", "David Guetta", "Tiësto", "Martin Garrix", "Skrillex", "Kanye West", "Post Malone", "21 Savage", "Fred again.."]
    },
    "sakin_akustik": {
        "tr": ["Manuş Baba", "Evdeki Saat", "Deniz Tekin", "Cihan Mürtezaoğlu", "Birsen Tezer", "Jehan Barbur", "Can Ozan", "Nilipek", "Bülent Ortaçgil", "Yeni Türkü"],
        "en": ["Jack Johnson", "Boyce Avenue", "Vance Joy", "Norah Jones", "Jason Mraz", "Ben Howard", "Passenger", "Iron & Wine", "Lofi Girl", "Lauv", "Jeremy Zucker"]
    },
    "indie_alternatif": {
        "tr": ["Adamlar", "Mor ve Ötesi", "Büyük Ev Ablukada", "Son Feci Bisiklet", "Jakuzi", "Lalalar", "Sedef Sebüktekin", "Yaşlı Amca", "Kaan Boşnak", "Hedonutopia", "Perdenin Ardındakiler", "Duman"],
        "en": ["Arctic Monkeys", "The Neighbourhood", "Tame Impala", "The Strokes", "Foster The People", "Gorillaz", "Radiohead", "The 1975", "Wallows", "Beach House", "Mac DeMarco", "Foals", "Lorde"]
    },
    "hard_rock_metal": {
        "tr": ["Şebnem Ferah", "Duman", "Hayko Cepkin", "Pentagram", "Kurban", "Ogün Sanlısoy", "Teoman", "Manga", "Barış Akarsu", "Gripin", "Yüksek Sadakat", "Athena"],
        "en": ["Linkin Park", "Metallica", "Guns N' Roses", "Green Day", "Nirvana", "Red Hot Chili Peppers", "Bring Me The Horizon", "Muse", "Foo Fighters", "System Of A Down", "Slipknot", "AC/DC", "Rammstein"]
    },
    "rap_hiphop": {
        "tr": ["Ezhel", "Ceza", "Sagopa Kajmer", "Şanışer", "Lvbel C5", "Motive", "BLOK3", "UZI", "Sefo", "Ati242", "Gazapizm", "Khontkar", "Anıl Piyancı", "Defkhan"],
        "en": ["Drake", "Travis Scott", "Kendrick Lamar", "Eminem", "J. Cole", "Metro Boomin", "Future", "21 Savage", "Jack Harlow", "Lil Baby", "Playboi Carti", "A$AP Rocky", "Post Malone"]
    },
    "jazz_blues": {
        "tr": ["İlhan Erşahin", "Kerem Görsev", "Karsu", "Jülide Özçelik", "Elif Çağlar", "Fatih Erkoç", "Ayşe Tütüncü", "Önder Focan"],
        "en": ["Miles Davis", "Frank Sinatra", "Chet Baker", "Gregory Porter", "B.B. King", "Nina Simone", "John Coltrane", "Norah Jones", "Amy Winehouse", "Michael Bublé", "Bill Withers"]
    },
    "elektronik_synth": {
        "tr": ["Mahmut Orhan", "Burak Yeter", "Deeperise", "Hey Douglas", "Faruk Sabancı", "İlkay Şencan", "Arem Özgüç", "Arman Aydın"],
        "en": ["Calvin Harris", "Avicii", "David Guetta", "Daft Punk", "Swedish House Mafia", "Kygo", "Peggy Gou", "Disclosure", "The Chainsmokers", "Kavinsky", "Gesaffelstein", "Justice"]
    }
}

def get_similar_tracks_from_seeds(sp, seed_inputs: List[str], count: int) -> List[dict]:
    """
    Verilen referans şarkı, sanatçı veya playlist linklerinden benzer şarkıları çeker.
    """
    similar_tracks = []
    artist_names = []
    
    for raw in seed_inputs:
        if not raw or not str(raw).strip():
            continue
        cleaned = str(raw).strip()

        # 1. Spotify Track Link
        track_match = re.search(r'spotify\.com/track/([a-zA-Z0-9]+)', cleaned)
        if track_match:
            try:
                t_info = sp.track(track_match.group(1))
                if t_info and t_info.get('artists'):
                    artist_names.append(t_info['artists'][0]['name'])
            except Exception:
                pass
            continue

        # 2. Spotify Playlist Link
        pl_match = re.search(r'spotify\.com/playlist/([a-zA-Z0-9]+)', cleaned)
        if pl_match:
            try:
                pl_data = sp.playlist_tracks(pl_match.group(1), limit=10)
                for item in pl_data.get('items', []):
                    t = item.get('track')
                    if t and t.get('artists'):
                        artist_names.append(t['artists'][0]['name'])
            except Exception:
                pass
            continue

        # 3. Düz Metin Arama
        try:
            res = sp.search(q=cleaned, type='track', limit=1)
            items = res.get('tracks', {}).get('items', [])
            if items and items[0].get('artists'):
                artist_names.append(items[0]['artists'][0]['name'])
        except Exception:
            pass

    # Sanatçılar üzerinden kaliteli parçalar topla
    unique_artists = list(dict.fromkeys(artist_names))[:5]
    for artist in unique_artists:
        try:
            results = sp.search(q=f'{artist}', type='track', limit=6)
            for item in results.get('tracks', {}).get('items', []):
                t = _create_track_obj(item)
                if t:
                    similar_tracks.append(t)
        except Exception:
            continue

    return similar_tracks

def search_tracks(sp, mood, language, genres, count, energy_level, seed_inputs: Optional[List[str]] = None):
    """
    Kesin Türkçe / Yabancı Ayrımı ve Standart Müzik Türleri Kümelendirmesi ile Şarkı Arama.
    """
    all_tracks = []
    
    # 1. Referans Şarkılardan Benzer Şarkılar (Varsa)
    if seed_inputs and len(seed_inputs) > 0:
        seed_similars = get_similar_tracks_from_seeds(sp, seed_inputs, count)
        all_tracks.extend(seed_similars)

    # 2. Dil Modunu Belirle (TR / Yabancı / Mix)
    curation_data = GENRE_CURATION_MATRIX.get(mood, GENRE_CURATION_MATRIX["sakin_akustik"])
    
    selected_targets = []
    if language == 'tr':
        # Yalnızca Türkçe Sanatçılar ve TR Market
        tr_artists = curation_data["tr"]
        random.shuffle(tr_artists)
        selected_targets = [(artist, "TR") for artist in tr_artists[:8]]
    elif language in ('yabanci', 'en'):
        # Yalnızca Yabancı Sanatçılar ve US Market
        en_artists = curation_data["en"]
        random.shuffle(en_artists)
        selected_targets = [(artist, "US") for artist in en_artists[:8]]
    else: # mix (50% TR, 50% Yabancı)
        tr_sample = random.sample(curation_data["tr"], min(4, len(curation_data["tr"])))
        en_sample = random.sample(curation_data["en"], min(4, len(curation_data["en"])))
        selected_targets = [(a, "TR") for a in tr_sample] + [(a, "US") for a in en_sample]
        random.shuffle(selected_targets)

    # 3. Spotify Arama Motorunu Çalıştır
    for artist_name, market in selected_targets:
        try:
            results = sp.search(q=f"{artist_name}", type='track', limit=5, market=market)
            items = results.get('tracks', {}).get('items', [])
            for item in items:
                # Sanatçı eşleşmesi doğrulaması (Gerçek şarkı kontrolü)
                artists = [a['name'].lower() for a in item.get('artists', [])]
                if any(artist_name.lower() in a for a in artists) or item.get('popularity', 0) >= 30:
                    track = _create_track_obj(item)
                    if track:
                        all_tracks.append(track)
        except Exception:
            continue

    # 4. Tekrar edenleri temizle ve popülariteye göre sırala
    unique_tracks = {t['id']: t for t in all_tracks}.values()
    final_list = list(unique_tracks)
    
    # Yüksek dinlenmeli gerçek parçaları öne al ve karıştır
    final_list.sort(key=lambda t: t.get('popularity', 0), reverse=True)
    top_pool = final_list[:count * 2] if len(final_list) > count else final_list
    random.shuffle(top_pool)
    return top_pool[:count]

def replace_single_track(sp, mood, exclude_ids, language, genres):
    curation_data = GENRE_CURATION_MATRIX.get(mood, GENRE_CURATION_MATRIX["sakin_akustik"])
    artists = curation_data["tr"] if language == 'tr' else (curation_data["en"] if language in ('en', 'yabanci') else curation_data["tr"] + curation_data["en"])
    market = "TR" if language == 'tr' else "US"
    
    random_artist = random.choice(artists)
    try:
        results = sp.search(q=f"{random_artist}", type='track', limit=20, market=market)
        for item in results.get('tracks', {}).get('items', []):
            if item['id'] not in exclude_ids:
                t = _create_track_obj(item)
                if t:
                    return t
    except Exception:
        pass
        
    return None

def save_playlist(sp, track_uris, mood_title):
    if not getattr(sp, 'auth', None) and not getattr(sp, '_auth', None):
        raise Exception("Çalma listesini hesabınıza kaydetmek için Spotify ile giriş yapmalısınız.")
    try:
        user_id = sp.current_user()['id']
        playlist = sp.user_playlist_create(user=user_id, name=f"Mood AI: {mood_title}", public=False)
        
        batch_size = 100
        for i in range(0, len(track_uris), batch_size):
            sp.playlist_add_items(playlist_id=playlist['id'], items=track_uris[i:i+batch_size])
            
        return playlist['external_urls']['spotify'], playlist['name']
    except Exception as e:
        raise Exception(f"Playlist kaydetme hatası: {str(e)}")
