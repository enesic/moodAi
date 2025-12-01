import os
import requests
import json
import streamlit as st # Streamlit eklendi
from dotenv import load_dotenv

# Local için .env
try:
    load_dotenv(override=True)
except:
    pass

# --- GÜVENLİ KEY OKUYUCU ---
def get_secret(key_name):
    if key_name in st.secrets:
        return st.secrets[key_name]
    return os.getenv(key_name)

# API Anahtarını al
GEMINI_API_KEY = get_secret("GEMINI_API_KEY")

# Debug için (Streamlit loglarına yazar)
if GEMINI_API_KEY:
    print(f"DEBUG: API Key OK.")
else:
    print("DEBUG: API Key YOK.")

# Modeller
TARGET_MODELS = [
    "gemini-1.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-pro", "gemini-1.0-pro", "gemini-pro"
]

def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def yedek_analiz(metin, hata_sebebi=""):
    metin = tr_lower(metin)
    
    keywords = {
        "neseli_pop": ["mutlu", "keyif", "gülmek", "harika", "süper", "dans", "eğlence", "enerji", "pozitif", "neşeli", "güzel"],
        "huzunlu_slow": ["üzgün", "ağla", "hüzün", "mutsuz", "melankoli", "yalnız", "kırgın", "veda", "bitti", "özlem", "keder", "canım acıyor", "depresif"],
        "enerjik_spor": ["hız", "spor", "güç", "koşu", "antrenman", "enerji", "bas", "motivasyon", "hareket", "kaldır", "fit"],
        "sakin_akustik": ["huzur", "kitap", "kahve", "uyku", "sakin", "dingin", "sessiz", "mola", "dinlen", "soft"],
        "hard_rock_metal": ["öfke", "bağırmak", "nefret", "kızgın", "sinir", "kaos", "gürültü", "patla", "sert", "metal"],
        "indie_alternatif": ["farklı", "boşver", "uzak", "yol", "sanat", "alternatif", "hipster", "bağımsız"],
        "jazz_blues": ["gece", "loş", "şarap", "yorgun", "melodi", "klasik", "ruh", "sofistike"],
        "rap_hiphop": ["sokak", "ritim", "para", "sistem", "isyan", "beat", "mc", "rhyme", "dostum"]
    }
    
    puanlar = {k:0 for k in keywords.keys()}
    for cat, keys in keywords.items():
        for k in keys:
            if k in metin: puanlar[cat] += 1
            
    en_yuksek_skor = max(puanlar.values())
    ek_mesaj = f" ({hata_sebebi})" if hata_sebebi else " (Çevrimdışı Mod)"

    if en_yuksek_skor == 0:
        return "sakin_akustik", f"Net bir duygu tespit edilemedi, standart sakin liste seçildi.{ek_mesaj}"
        
    return max(puanlar, key=puanlar.get), f"Anahtar kelimelere göre analiz yapıldı.{ek_mesaj}"

def derin_analiz(metin):
    if not GEMINI_API_KEY:
        return yedek_analiz(metin, "API Key Eksik (Secrets)")

    headers = {'Content-Type': 'application/json'}
    
    prompt_text = f"""
    Sen uzman bir müzik terapistisin.
    Kullanıcının girdiği şu metni analiz et: "{metin}"

    Görevin:
    1. Kullanıcının ruh halini en iyi yansıtan MÜZİK KATEGORİSİNİ şunlardan biri olarak seç:
       [neseli_pop, huzunlu_slow, enerjik_spor, sakin_akustik, indie_alternatif, hard_rock_metal, elektronik_synth, jazz_blues, rap_hiphop]
    
    2. Kullanıcıya 1-2 cümlelik, derinlikli, psikolojik bir tespit içeren bir "Doktor Notu" yaz.
    
    Çıktıyı SADECE şu formatta ver (araya :: koy):
    KATEGORI::DOKTOR_NOTU
    """
    
    data = {"contents": [{"parts": [{"text": prompt_text}]}]}
    last_error = ""
    
    for model_name in TARGET_MODELS:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
            response = requests.post(url, headers=headers, data=json.dumps(data), timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    sonuc = result['candidates'][0]['content']['parts'][0]['text'].strip()
                    if "::" in sonuc:
                        kategori, yorum = sonuc.split("::", 1)
                        return kategori.strip().lower(), yorum.strip()
                    else:
                        return yedek_analiz(metin, "AI Format Hatası")
                except (KeyError, IndexError):
                     last_error = f"{model_name} Cevap Boş"
                     continue
            else:
                last_error = f"{model_name} ({response.status_code})"
                continue

        except Exception as e:
            last_error = f"Bağlantı: {str(e)}"
            continue

    return yedek_analiz(metin, f"Yapay Zeka Bağlanamadı: {last_error}")