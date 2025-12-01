import streamlit as st
import random
import os
from io import BytesIO # Resmi bellekte tutmak için

# Sayfa Ayarını EN BAŞA koymak zorundayız
st.set_page_config(page_title="Mood AI Therapist", page_icon="🧠", layout="wide")

try:
    import spotify_manager
    import ai_psychologist
    import mood_card # YENİ MODÜL
except ImportError as e:
    st.error(f"HATA: Gerekli dosyalar eksik. 'pip install -r requirements.txt' yaptınız mı? Detay: {e}")
    st.stop()

# --- AYARLAR ---
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

# --- ARAYÜZ ---
st.title("🧠 Mood AI: Yapay Zeka Terapisti")
st.markdown("Duygularınızı analiz edip size özel müzik reçetesi yazan asistanınız.")

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
        
        uygun_turler = ALT_TURLER.get(mod, ALT_TURLER["sakin_akustik"])
        
        varsayilan_secim = uygun_turler[:2]
        if user_input and "türkü" in user_input.lower() and "Türkü" in uygun_turler:
            varsayilan_secim = ["Türkü"]
            
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
                    mod, 
                    offset_random=0, 
                    dil_secenegi=st.session_state['dil'],
                    secilen_turler=secilen_turler
                )

with col2:
    if st.session_state.get('sarkilari_goster'):
        tracks = st.session_state.get('tracks', [])
        yorum = st.session_state.get('yorum', "")
        
        # Doktor notu
        if "(Çevrimdışı Mod)" in yorum:
            st.warning(f"**🩺 Doktor Notu (Yedek Sistem):**\n{yorum}")
        else:
            st.success(f"**🩺 Doktor Notu (AI):**\n{yorum}")
            
        # --- MOOD CARD (SOL KENAR ÇUBUĞU VEYA ÜST KISIM) ---
        # İlk şarkının adını karta yazalım
        sarki_ismi = tracks[0]['name'] if tracks else ""
        
        with st.expander("📸 Mood Kartını Görüntüle (Instagram'da Paylaş)", expanded=True):
            col_card_img, col_card_btn = st.columns([1, 1])
            
            # Kartı oluştur
            img = mood_card.kart_olustur(st.session_state['mod'], yorum, sarki_ismi)
            
            # Resmi belleğe kaydet (Diske değil)
            buf = BytesIO()
            img.save(buf, format="PNG")
            byte_im = buf.getvalue()

            with col_card_img:
                st.image(byte_im, caption="Senin Mood Kartın", width=250)
            
            with col_card_btn:
                st.write("Bu kartı indirip Instagram Story'de paylaşabilirsin!")
                st.download_button(
                    label="📥 Kartı İndir",
                    data=byte_im,
                    file_name="mood_ai_card.png",
                    mime="image/png"
                )
        
        st.divider()

        if tracks:
            st.subheader("💊 Müzik Reçetesi")
            
            track_uris = []
            for t in tracks:
                track_uris.append(t['uri'])
                c_img, c_info = st.columns([1, 4])
                
                with c_img:
                    if t['image']:
                        st.image(t['image'], use_container_width=True)
                    else:
                        st.write("🎵")
                
                with c_info:
                    st.markdown(f"**{t['name']}**")
                    st.caption(f"{t['artist']} • {t['album']}")
                    if t['preview_url']:
                        st.audio(t['preview_url'], format="audio/mp3")
                st.divider()
            
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🔄 Yeniden Karıştır"):
                    st.session_state['offset'] += 5
                    new_off = st.session_state['offset'] + random.randint(1, 20)
                    with st.spinner("Alternatifler aranıyor..."):
                        st.session_state['tracks'] = spotify_manager.sarki_arastirmasi_yap(
                            st.session_state['mod'], 
                            offset_random=new_off, 
                            dil_secenegi=st.session_state['dil'],
                            secilen_turler=st.session_state.get('secilen_turler')
                        )
                    st.rerun()
            
            with b2:
                if st.button("✅ Spotify'a Kaydet"):
                    with st.spinner("Kaydediliyor..."):
                        link, name = spotify_manager.playlisti_kaydet(track_uris, st.session_state['mod'])
                        if link:
                            st.success(f"Kaydedildi: {name}")
                            st.markdown(f"[👉 Spotify'da Aç]({link})")
        else:
            st.warning("Bu kriterlere uygun sonuç bulunamadı.")