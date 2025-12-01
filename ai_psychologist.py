import os
import requests
import json
import streamlit as st
from dotenv import load_dotenv

# Local için .env yükle
try:
    load_dotenv(override=True)
except:
    pass

# --- GÜVENLİ KEY OKUYUCU ---
def get_secret(key_name):
    # 1. Streamlit Secrets (Cloud)
    if key_name in st.secrets:
        return st.secrets[key_name]
    # 2. Environment Variable (Local)
    return os.getenv(key_name)

# API Anahtarını al
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

# Modeller (Genişletilmiş Liste - Biri mutlaka çalışır)
TARGET_MODELS = [
    "gemini-1.5-flash",          # Standart
    "gemini-1.5-flash-latest",   # En güncel
    "gemini-1.5-flash-001",      # Sürüm 1
    "gemini-1.5-flash-002",      # Sürüm 2 (Yeni)
    "gemini-1.5-flash-8b",       # Hafif sürüm
    "gemini-1.5-pro",            # Pro Standart
    "gemini-1.5-pro-latest",     # Pro Güncel
    "gemini-1.5-pro-001",        # Pro Sürüm 1
    "gemini-1.5-pro-002",        # Pro Sürüm 2
    "gemini-1.0-pro",            # Eski Stabil
    "gemini-pro",                # Legacy Alias
    "gemini-pro-vision"          # Yedek (Bazen metin de kabul eder)
]

def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def yedek_analiz(metin, hata_sebebi=""):
    metin = tr_lower(metin)
    
    # Kelime havuzu (Özet)
    keywords = {
        "neseli_pop": ["mutlu", "keyif", "gülmek", "enerji", "pozitif", "neşeli", "dans"],
        "huzunlu_slow": ["üzgün", "hüzün", "mutsuz", "melankoli", "yalnız", "kırgın", "özlem", "ağla"],
        "enerjik_spor": ["hız", "spor", "güç", "koşu", "motivasyon", "hareket", "fit"],
        "sakin_akustik": ["huzur", "kahve", "uyku", "sakin", "dingin", "sessiz", "dinlen"],
        "hard_rock_metal": ["öfke", "bağırmak", "nefret", "sinir", "kaos", "sert", "isyan"],
        "indie_alternatif": ["farklı", "boşver", "uzak", "yol", "sanat", "alternatif"],
        "jazz_blues": ["gece", "loş", "şarap", "yorgun", "melodi", "klasik", "ruh"],
        "rap_hiphop": ["sokak", "ritim", "sistem", "isyan", "beat", "mücadele"],
        "elektronik_synth": ["parti", "robot", "uzay", "tekno", "gelecek"]
    }
    
    puanlar = {k:0 for k in keywords.keys()}
    for cat, keys in keywords.items():
        for k in keys:
            if k in metin: puanlar[cat] += 1
            
    en_yuksek_skor = max(puanlar.values())
    
    # HATA MESAJINI KULLANICIYA GÖSTER (DEBUG İÇİN)
    key_durumu = "VAR" if GEMINI_API_KEY else "YOK"
    ek_mesaj = f"(HATA: {hata_sebebi} | Key Durumu: {key_durumu})"

    if en_yuksek_skor == 0:
        return "sakin_akustik", f"Net bir duygu tespit edilemedi. {ek_mesaj}"
        
    return max(puanlar, key=puanlar.get), f"Yedek sistem analiz yaptı. {ek_mesaj}"

def derin_analiz(metin):
    if not GEMINI_API_KEY:
        return yedek_analiz(metin, "API Anahtarı Bulunamadı")

    headers = {'Content-Type': 'application/json'}
    
    prompt = f"""
    Sen bir müzik terapistisin. Metni analiz et: "{metin}"
    Çıktı formatı: KATEGORI::DOKTOR_NOTU
    Kategoriler: [neseli_pop, huzunlu_slow, enerjik_spor, sakin_akustik, indie_alternatif, hard_rock_metal, elektronik_synth, jazz_blues, rap_hiphop]
    Doktor notu samimi ve kısa olsun.
    """
    
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    log_hatalar = []

    for model in TARGET_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=5) # 5sn zaman aşımı
            
            if response.status_code == 200:
                try:
                    res_json = response.json()
                    sonuc = res_json['candidates'][0]['content']['parts'][0]['text'].strip()
                    if "::" in sonuc:
                        kategori, yorum = sonuc.split("::", 1)
                        # Başarılı olduğunda hangi modelin çalıştığını loglayalım (Gelecekte onu kullanmak için)
                        print(f"BAŞARILI MODEL: {model}")
                        return kategori.strip().lower(), yorum.strip()
                except:
                    log_hatalar.append(f"{model}: Format Hatası")
                    continue
            else:
                log_hatalar.append(f"{model}: {response.status_code}")
                
        except Exception as e:
            log_hatalar.append(f"{model}: {str(e)}")
            continue

    # Hiçbiri çalışmadıysa
    return yedek_analiz(metin, f"Tüm modeller başarısız: {log_hatalar}")