import streamlit as st
import random
from io import BytesIO

st.set_page_config(page_title="Mood AI Therapist", page_icon="🧠", layout="wide")

try:
    import spotify_manager
    import ai_psychologist
    import mood_card
except ImportError as e:
    st.error(f"HATA: Dosyalar eksik. {e}")
    st.stop()

# --- OTURUM YÖNETİMİ (SESSION STATE) ---
if 'token_info' not in st.session_state:
    st.session_state['token_info'] = None

# URL'den gelen 'code' parametresini yakala (Spotify'dan dönünce bu çalışır)
params = st.query_params
if "code" in params and not st.session_state['token_info']:
    sp_oauth = spotify_manager.create_spotify_oauth()
    try:
        code = params["code"]
        token_info = sp_oauth.get_access_token(code)
        st.session_state['token_info'] = token_info
        # URL'i temizle
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Giriş hatası: {e}")

# --- GİRİŞ KONTROLÜ ---
token_info = st.session_state['token_info']
sp = None

if not token_info:
    # GİRİŞ YAPILMAMIŞSA SADECE BUTON GÖSTER
    st.title("🧠 Mood AI: Müzik Terapisti")
    st.markdown("Devam etmek için lütfen Spotify hesabınızla giriş yapın.")
    
    sp_oauth = spotify_manager.create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    
    st.link_button("🟢 Spotify ile Giriş Yap", auth_url, type="primary")
    st.info("Not: Uygulamanın playlist oluşturabilmesi için izin vermeniz gerekmektedir.")
    st.stop() # Kodun geri kalanını çalıştırma
else:
    # GİRİŞ YAPILMIŞSA BAĞLANTIYI KUR
    sp = spotify_manager.baglanti_kur(token_info)

# =========================================================
# ANA UYGULAMA (Giriş Yapıldıysa Burası Çalışır)
# =========================================================

ALT_TURLER = {
    "neseli_pop": ["Türkçe Pop", "Dance Pop", "Serdar Ortaç Pop", "90'lar Türkçe Pop", "Disco"],
    "huzunlu_slow": ["Akustik", "Türkü", "Arabesk", "Damar", "Indie Slow", "Piyano Ballad"],
    "enerjik_spor": ["Türkçe Rap", "Techno", "Drill", "Fitness", "Remix"],
    "sakin_akustik": ["Türk Sanat Müziği", "Enstrümantal", "Lo-Fi", "Sufi/Ney", "Akustik Cover"],
    "indie_alternatif": ["Anadolu Rock", "Alternatif Rock", "Indie Folk", "Soft Rock"],
    "hard_rock_metal": ["Türkçe Rock", "Heavy Metal", "Hard Rock", "Metal"],
    "rap_hiphop": ["Arabesk Rap", "Old School", "Melodic Rap", "Drill", "Trap"],
    "jazz_blues": ["Türkçe Caz", "Blues", "Soul", "Vocal Jazz"],
    "elektronik_synth": ["Synthwave", "Deep House", "Techno"]
}

st.title("🧠 Mood AI: Yapay Zeka Terapisti")
if st.button("Çıkış Yap"):
    st.session_state['token_info'] = None
    st.rerun()

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("1. Terapi Seansı")
    user_input = st.text_area("Ne hissediyorsunuz?", height=150, placeholder="Kahvemi aldım, hafif hüzünlü bir türkü dinlemek istiyorum...")
    
    dil = st.radio("Dil Tercihi:", ["Karışık", "Sadece Türkçe", "Sadece Yabancı"], horizontal=True)
    dil_kod = "mix"
    if dil == "Sadece Türkçe": dil_kod = "tr"
    elif dil == "Sadece Yabancı": dil_kod = "yabanci"

    if st.button("Analiz Et ✨", use_container_width=True):
        if user_input:
            with st.spinner("Nöral ağlar analiz ediyor..."):
                mod, yorum = ai_psychologist.derin_analiz(user_input)
                if mod not in ALT_TURLER: mod = "sakin_akustik"
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
        
        uygun_turler = ALT_TURLER.get(mod, ALT_TURLER["sakin_akustik"])
        varsayilan = uygun_turler[:2]
        if user_input and "türkü" in user_input.lower() and "Türkü" in uygun_turler:
            varsayilan = ["Türkü"]
            
        secilen_turler = st.multiselect("Türleri seçin:", options=uygun_turler, default=varsayilan)
        
        if st.button("Listeyi Oluştur 🎵", type="primary", use_container_width=True):
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
            st.warning(f"**🩺 Doktor Notu (Yedek):**\n{yorum}")
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