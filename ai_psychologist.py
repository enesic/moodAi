import os
import requests
import json
import random
import streamlit as st
from dotenv import load_dotenv

try:
    load_dotenv(override=True)
except:
    pass

def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

TARGET_MODELS = [
    "gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"
]

def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

# --- YEREL MOTOR (FALLBACK) ---
def yerel_analiz(metin, hata_mesaji=""):
    metin = tr_lower(metin)
    
    keywords = {
        "neseli_pop": ["mutlu", "keyif", "gülmek", "harika", "süper", "dans", "eğlence", "enerji", "pozitif", "neşeli", "güzel"],
        "huzunlu_slow": ["üzgün", "ağla", "hüzün", "mutsuz", "melankoli", "yalnız", "kırgın", "veda", "bitti", "özlem", "keder", "canım acıyor", "depresif"],
        "enerjik_spor": ["hız", "spor", "güç", "koşu", "antrenman", "enerji", "bas", "motivasyon", "hareket", "kaldır", "fit"],
        "sakin_akustik": ["huzur", "kitap", "kahve", "uyku", "sakin", "dingin", "sessiz", "mola", "dinlen", "soft"],
        "hard_rock_metal": ["öfke", "bağırmak", "nefret", "kızgın", "sinir", "kaos", "gürültü", "patla", "sert", "metal"],
        "indie_alternatif": ["farklı", "boşver", "uzak", "yol", "sanat", "alternatif", "hipster", "bağımsız"],
        "jazz_blues": ["gece", "loş", "şarap", "yorgun", "melodi", "klasik", "ruh", "sofistike"],
        "rap_hiphop": ["sokak", "ritim", "para", "sistem", "isyan", "beat", "mc", "rhyme", "dostum"],
        "elektronik_synth": ["parti", "robot", "uzay", "tekno", "gelecek", "neon"]
    }
    
    puanlar = {k:0 for k in keywords.keys()}
    for cat, keys in keywords.items():
        for k in keys:
            if k in metin: puanlar[cat] += 1
            
    en_yuksek_skor = max(puanlar.values())
    not_ek = f" ({hata_mesaji})" if hata_mesaji else ""

    kategori = "sakin_akustik"
    if en_yuksek_skor > 0:
        kategori = max(puanlar, key=puanlar.get)
        
    # Yerel yorum üretici
    yorumlar = {
        "neseli_pop": "Enerjin harika! Bu modu korumak için hareketli parçalar seçtim.",
        "huzunlu_slow": "Biraz duygusal bir dönemdesin. İçini dökeceğin parçalar hazırladım.",
        "enerjik_spor": "Adrenalin arayışındasın! Sınırları zorlayan bir liste oldu.",
        "sakin_akustik": "Zihinsel bir mola ihtiyacı. Huzurlu tınılar sana iyi gelecek.",
        "hard_rock_metal": "İçindeki enerjiyi ve öfkeyi kontrollü bir kaosla atalım.",
        "indie_alternatif": "Sıradanlıktan uzaklaşmak isteyen ruhuna özel bir seçki.",
        "jazz_blues": "Sofistike ve derinlikli bir moddasın. Keyfini çıkar.",
        "rap_hiphop": "Sokağın ritmi ve sözlerin gücü sana eşlik edecek.",
        "elektronik_synth": "Geleceğin sesleriyle modunu yükseltelim."
    }
    
    yorum = yorumlar.get(kategori, "Sana özel bir karışım.") + not_ek
    return kategori, yorum

# --- ANA ANALİZ FONKSİYONU ---
def derin_analiz(metin):
    # Eğer API anahtarı yoksa direkt yerel motoru çalıştır
    if not GEMINI_API_KEY:
        return yerel_analiz(metin, "Çevrimdışı Mod")

    headers = {'Content-Type': 'application/json'}
    prompt = f"""
    Sen bir müzik terapistisin. Metni analiz et: "{metin}"
    Çıktı formatı: KATEGORI::DOKTOR_NOTU
    Kategoriler: [neseli_pop, huzunlu_slow, enerjik_spor, sakin_akustik, indie_alternatif, hard_rock_metal, elektronik_synth, jazz_blues, rap_hiphop]
    Not kısa ve samimi olsun.
    """
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    
    last_error = ""
    for model in TARGET_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=5)
            
            if response.status_code == 200:
                try:
                    res = response.json()
                    sonuc = res['candidates'][0]['content']['parts'][0]['text'].strip()
                    if "::" in sonuc:
                        kat, yor = sonuc.split("::", 1)
                        return kat.strip().lower(), yor.strip()
                except:
                    continue
            else:
                last_error = f"{model} ({response.status_code})"
        except Exception as e:
            last_error = str(e)
            continue

    # Hiçbiri çalışmazsa yerel motora dön (Halisünasyon yok, gerçek kod çalışır)
    return yerel_analiz(metin, f"Yapay Zeka Bağlanamadı: {last_error}")