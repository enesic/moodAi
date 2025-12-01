import streamlit as st
import random
import os
from io import BytesIO

st.set_page_config(page_title="Mood AI Therapist", page_icon="🧠", layout="wide")

try:
    import spotify_manager
    import ai_psychologist
    import mood_card
except ImportError as e:
    st.error(f"HATA: Dosyalar eksik. {e}")
    st.stop()

# --- OTURUM YÖNETİMİ ---
if 'token_info' not in st.session_state:
    st.session_state['token_info'] = None

params = st.query_params
if "code" in params and not st.session_state['token_info']:
    sp_oauth = spotify_manager.create_spotify_oauth()
    try:
        code = params["code"]
        token_info = sp_oauth.get_access_token(code)
        st.session_state['token_info'] = token_info
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Giriş hatası: {e}")

# --- GİRİŞ KONTROLÜ ---
token_info = st.session_state['token_info']
sp = None

if not token_info:
    st.title("🧠 Mood AI: Müzik Terapisti")
    st.markdown("Devam etmek için lütfen Spotify hesabınızla giriş yapın.")
    sp_oauth = spotify_manager.create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    st.link_button("🟢 Spotify ile Giriş Yap", auth_url, type="primary")
    st.info("Not: Uygulamanın playlist oluşturabilmesi için izin vermeniz gerekmektedir.")
    st.stop()
else:
    sp = spotify_manager.baglanti_kur(token_info)

# =========================================================
# GENİŞLETİLMİŞ VE MODERNİZE EDİLMİŞ TÜR LİSTESİ
# =========================================================
ALT_TURLER = {
    "neseli_pop": [
        "Türkçe Pop Hareketli", "Yaz Hitleri", "Dance Pop", "Road Trip", 
        "Serdar Ortaç Pop", "90'lar Türkçe Pop", "Disco", "K-Pop", "Reggaeton"
    ],
    "huzunlu_slow": [
        "Akustik Hüzün", "Melankolik Indie", "Slow Pop", "Piyano & Yağmur", 
        "Türkçe Damar", "Alternatif Balad", "Türkü", "Arabesk", "Kırık Kalpler"
    ],
    "enerjik_spor": [
        "Spor Motivasyon", "Türkçe Rap", "Phonk", "Drill", "Techno", 
        "House", "Gym Hits", "Remix", "Power Workout"
    ],
    "sakin_akustik": [
        "Lo-Fi Beats", "Chill Pop", "Akustik Cover", "Jazz Vibes", 
        "Enstrümantal", "Kitap Okuma", "Kahve Modu", "Ambient", "Soft Rock", "Sufi/Ney"
    ],
    "indie_alternatif": [
        "Alternatif Rock", "Yeni Nesil Indie", "Anadolu Rock", "Shoegaze", 
        "Soft Indie", "Bağımsız Müzik", "Dream Pop"
    ],
    "hard_rock_metal": [
        "Türkçe Rock", "Anadolu Rock", "Heavy Metal", "Nu-Metal", 
        "Hard Rock", "Punk", "Garage Rock"
    ],
    "rap_hiphop": [
        "Türkçe Rap", "Old School", "Melodic Rap", "Trap", 
        "Arabesk Rap", "Drill", "Underground"
    ],
    "jazz_blues": [
        "Smooth Jazz", "Gece Mavisi", "Blues Rock", "Soul", 
        "Vocal Jazz", "Türkçe Caz", "Coffee Table Jazz"
    ],
    "elektronik_synth": [
        "Synthwave", "Cyberpunk", "Deep House", "Minimal Techno", 
        "EDM", "Daft Punk Vibe"
    ]
}

# --- AKILLI VARSAYILAN SEÇİCİ ---
def akilli_tur_oner(text, tur_listesi):
    text = text.lower()
    oneriler = []
    
    # Anahtar kelime eşleştirmeleri (GÜNCELLENDİ)
    mappings = {
        "lo-fi": ["chill", "sakin", "ders", "odak", "lofi"],
        "jazz vibes": ["kahve", "yağmur", "akşam", "şık"],
        # DÜZELTME: "yürüyüş" kelimesini Spordan çıkardık
        "spor motivasyon": ["koşu", "spor", "hız", "bas", "antrenman", "gym"], 
        # DÜZELTME: "yürüyüş" artık Akustik ve Chill modda
        "akustik cover": ["doğa", "yürüyüş", "manzara", "hafif", "gezi", "sahil"], 
        "chill pop": ["cadde", "şehir", "gezinti", "alışveriş", "mood", "yürüyorum"],
        "türkü": ["türkü", "bağlama", "halk", "köy"],
        "arabesk": ["damar", "baba", "dert", "efkar"],
        "türkçe rap": ["sokak", "mahalle", "hız", "ritim"]
    }
    
    for tur, keywords in mappings.items():
        # Tür listesinde bu tür var mı kontrol et (Büyük/küçük harf duyarsız)
        mevcut_tur = next((t for t in tur_listesi if t.lower() == tur.lower()), None)
        if mevcut_tur:
            for kw in keywords:
                if kw in text:
                    oneriler.append(mevcut_tur)
                    break
    
    if not oneriler:
        return tur_listesi[:2]
    
    return list(set(oneriler))[:3]


# --- ANA SAYFA ---
st.title("🧠 Mood AI: Yapay Zeka Terapisti")
if st.button("Çıkış Yap"):
    st.session_state['token_info'] = None
    st.rerun()

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("1. Terapi Seansı")
    user_input = st.text_area("Ne hissediyorsunuz?", height=150, placeholder="Cadde de yürüyorum, hava serin ve chill bir moddayım...")
    
    dil = st.radio("Dil Tercihi:", ["Karışık", "Sadece Türkçe", "Sadece Yabancı"], horizontal=True)
    dil_kod = "mix"
    if dil == "Sadece Türkçe": dil_kod = "tr"
    elif dil == "Sadece Yabancı": dil_kod = "yabanci"

    if st.button("Analiz Et ✨", use_container_width=True):
        if user_input:
            with st.spinner("Nöral ağlar analiz ediyor..."):
                mod, yorum = ai_psychologist.derin_analiz(user_input)
                
                if mod not in ALT_TURLER:
                    mod = "sakin_akustik"

                st.session_state['mod'] = mod
                st.session_state['yorum'] = yorum
                st.session_state['analiz_yapildi'] = True
                st.session_state['dil'] = dil_kod
                st.session_state['tracks'] = [] 

    if st.session_state.get('analiz_yapildi'):
        st.divider()
        st.subheader("2. Reçete Detayları")
        
        mod = st.session_state['mod']
        st.info(f"**Teşhis:** {mod.replace('_', ' ').title()}")
        
        # Seçenekleri getir
        uygun_turler = ALT_TURLER.get(mod, ALT_TURLER["sakin_akustik"])
        
        # Akıllı seçim yap
        varsayilan_secim = akilli_tur_oner(user_input, uygun_turler)
            
        secilen_turler = st.multiselect(
            "Hangi türleri ekleyelim?", 
            options=uygun_turler,
            default=varsayilan_secim
        )
        
        if st.button("Tedavi Listesini Oluştur 🎵", type="primary", use_container_width=True):
            st.session_state['secilen_turler'] = secilen_turler
            st.session_state['sarkilari_goster'] = True
            st.session_state['offset'] = 0
            
            with st.spinner("Şarkılar seçiliyor..."):
                st.session_state['tracks'] = spotify_manager.sarki_arastirmasi_yap(
                    sp, mod, 0, st.session_state['dil'], secilen_turler
                )

with col2:
    if st.session_state.get('sarkilari_goster'):
        tracks = st.session_state.get('tracks', [])
        yorum = st.session_state.get('yorum', "")
        
        if "(Çevrimdışı Mod)" in yorum:
            st.warning(f"**🩺 Doktor Notu (Yedek Sistem):**\n{yorum}")
        else:
            st.success(f"**🩺 Doktor Notu (AI):**\n{yorum}")
            
        # Mood Card
        sarki_ismi = tracks[0]['name'] if tracks else ""
        with st.expander("📸 Mood Kartını Görüntüle"):
            col_c1, col_c2 = st.columns([1,1])
            img = mood_card.kart_olustur(st.session_state['mod'], yorum, sarki_ismi)
            buf = BytesIO()
            img.save(buf, format="PNG")
            with col_c1: st.image(buf.getvalue(), width=200)
            with col_c2: 
                st.download_button("📥 Kartı İndir", buf.getvalue(), "mood_card.png", "image/png")
        
        st.divider()

        if tracks:
            st.subheader("💊 Müzik Reçetesi")
            track_uris = []
            for t in tracks:
                track_uris.append(t['uri'])
                c1, c2 = st.columns([1, 4])
                with c1:
                    if t['image']: st.image(t['image'], use_container_width=True)
                    else: st.write("🎵")
                with c2:
                    st.markdown(f"**{t['name']}**")
                    st.caption(f"{t['artist']}")
                    if t['preview_url']: st.audio(t['preview_url'], format="audio/mp3")
                st.divider()
            
            if st.button("✅ Spotify'a Kaydet", type="primary", use_container_width=True):
                with st.spinner("Kaydediliyor..."):
                    link, name = spotify_manager.playlisti_kaydet(sp, track_uris, st.session_state['mod'])
                    if link:
                        st.success(f"Kaydedildi: {name}")
                        st.markdown(f"[👉 Dinlemek İçin Tıkla]({link})")
                        st.balloons()
                    else:
                        st.error(f"Hata: {name}")