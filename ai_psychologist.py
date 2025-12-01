import random

# --- YEREL PSİKOLOG MOTORU (OFFLINE & STABLE) ---
# Dış API'lara (Google/OpenAI) bağımlılığı kaldırdık.
# Gelişmiş kelime eşleştirme algoritmalarıyla çalışır.

def tr_lower(text):
    """Türkçe karakter uyumlu küçük harfe çevirme."""
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def derin_analiz(metin):
    """
    Kullanıcı metnini yerel algoritmalarla analiz eder.
    """
    metin = tr_lower(metin)
    
    # GELİŞMİŞ VE GENİŞLETİLMİŞ KELİME HAVUZU
    keywords = {
        "neseli_pop": [
            "mutlu", "keyif", "gülmek", "harika", "süper", "dans", "eğlence", "enerji", 
            "pozitif", "neşeli", "güzel", "cıvıl", "hayat", "party", "muhteşem", "bomba", "yıkılıyor"
        ],
        "huzunlu_slow": [
            "üzgün", "ağla", "hüzün", "mutsuz", "melankoli", "yalnız", "kırgın", "veda", 
            "bitti", "özlem", "keder", "canım acıyor", "depresif", "çaresiz", "yorgun", 
            "ayrılık", "üstüme geliyor", "istemiyorum", "bunalım", "sıkıldım", "boşluk", 
            "tavan", "duvar", "karanlık", "bitik", "tükendim", "dibe", "modum düşük"
        ],
        "enerjik_spor": [
            "hız", "spor", "güç", "koşu", "antrenman", "enerji", "bas", "motivasyon", 
            "hareket", "kaldır", "fit", "gym", "tempo", "pump", "kardiyo", "rekor", "salonu"
        ],
        "sakin_akustik": [
            "huzur", "kitap", "kahve", "uyku", "sakin", "dingin", "sessiz", "mola", 
            "dinlen", "soft", "yağmur", "şömine", "battaniye", "mum", "huzurlu", "dinlenme"
        ],
        "hard_rock_metal": [
            "öfke", "bağırmak", "nefret", "kızgın", "sinir", "kaos", "gürültü", "patla", 
            "sert", "metal", "isyan", "kırıp", "dökme", "intikam", "bağır", "delirmek"
        ],
        "indie_alternatif": [
            "farklı", "boşver", "uzak", "yol", "sanat", "alternatif", "hipster", "bağımsız", 
            "yenilik", "değişik", "şehirden kaçış", "kamp", "ormanda", "bilinmeyen"
        ],
        "jazz_blues": [
            "gece", "loş", "şarap", "yorgun", "melodi", "klasik", "ruh", "sofistike", 
            "asil", "piyano", "saksofon", "eski zaman", "plak", "viski"
        ],
        "rap_hiphop": [
            "sokak", "ritim", "para", "sistem", "isyan", "beat", "mc", "rhyme", "dostum", 
            "mahalle", "gerçek", "mücadele", "başarı", "araba", "gang"
        ],
        "elektronik_synth": [
            "parti", "robot", "uzay", "tekno", "gelecek", "neon", "lazer", "dans pisti", "festival", "kopmalık"
        ]
    }
    
    # 1. Puanlama Yap
    puanlar = {k:0 for k in keywords.keys()}
    
    for cat, keys in keywords.items():
        for k in keys:
            if k in metin: puanlar[cat] += 1
            
    en_yuksek_skor = max(puanlar.values())
    
    # 2. Sonucu Belirle
    if en_yuksek_skor == 0:
        # Hiçbir kelime yakalayamazsa varsayılan mod
        kategori = "sakin_akustik"
        yorum = "Ruh halini tam çıkaramadım ama sana iyi gelecek sakin bir liste hazırladım."
    else:
        kategori = max(puanlar, key=puanlar.get)
        yorum = doktor_yorumu_uret(kategori)

    return kategori, yorum

def doktor_yorumu_uret(kategori):
    """Seçilen kategoriye göre rastgele ve çeşitli bir doktor yorumu seçer."""
    yorumlar = {
        "neseli_pop": [
            "Enerjin harika görünüyor! Dopamin seviyeni yüksek tutacak ritimler seçtim.",
            "Bugün ışık saçıyorsun. Bu modu korumak için hareketli parçalar iyi gider."
        ],
        "huzunlu_slow": [
            "Biraz duygusal bir dönemdesin sanırım. Bazen hüzünle yüzleşmek iyileşmenin ilk adımıdır.",
            "İçindeki ağırlığı notalara bırakman için melankolik bir seçki hazırladım.",
            "Duygusal bir deşarj ihtiyacı seziyorum. Bu şarkılar sana yoldaş olacak."
        ],
        "enerjik_spor": [
            "Adrenalin arayışındasın! Nabzını yükseltecek parçalar hazır.",
            "İçindeki gücü dışarı vurma zamanı. Sınırları zorlayan bir liste oldu."
        ],
        "sakin_akustik": [
            "Dünyanın gürültüsünden uzaklaşıp biraz nefes almaya ihtiyacın var.",
            "Kortizol seviyeni düşürecek, zihnini pamuk gibi yapacak tınılar seçtim."
        ],
        "hard_rock_metal": [
            "İçinde biriken bir öfke veya patlamaya hazır bir enerji var. Kontrollü kaos iyi gelecek!",
            "Sessiz kalmak istemiyorsun. Bırak gitarın telleri senin yerine bağırsın."
        ],
        "indie_alternatif": [
            "Sıradanlıktan sıkılmışsın, farklı ve özgün tınılar arıyorsun.",
            "Şehrin karmaşasından zihnen uzaklaşıp, sanatsal bir yolculuğa çıkalım."
        ],
        "jazz_blues": [
            "Ruhun biraz sofistike ve derinlik arıyor. Klasikleşmiş tınılar sana iyi gelecek.",
            "Günün yorgunluğunu atarken sana eşlik edecek asil melodiler hazırladım."
        ],
        "rap_hiphop": [
            "Sözlerin gücüne ve ritmin enerjisine ihtiyacın var.",
            "Hayatın gerçekleriyle yüzleşirken ritim tutmak sana güç verecek."
        ],
        "elektronik_synth": [
            "Geleceğin sesleri ve dijital ritimler zihnini açacak.",
            "Enerjini dijital frekanslarla birleştirip modunu yükseltelim."
        ]
    }
    return random.choice(yorumlar.get(kategori, ["Senin için özel bir karışım."]))