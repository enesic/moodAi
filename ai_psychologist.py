import random

# --- ÇEVRİMDIŞI / YEREL PSİKOLOG MOTORU ---
# Bu sürüm dış API'lara (Google/OpenAI) bağımlı değildir.
# Gelişmiş kelime eşleştirme algoritmalarıyla çalışır. %100 Stabilite sağlar.

# Türkçe karakter duyarlı küçük harfe çevirme
def tr_lower(text):
    return text.replace('I', 'ı').replace('İ', 'i').lower()

def derin_analiz(metin):
    """
    Kullanıcı metnini yerel algoritmalarla analiz eder.
    Dış bağlantı gerektirmez, hata vermez.
    """
    metin = tr_lower(metin)
    
    # GELİŞMİŞ KELİME HAVUZU
    keywords = {
        "neseli_pop": ["mutlu", "keyif", "gülmek", "harika", "süper", "dans", "eğlence", "enerji", "pozitif", "neşeli", "güzel", "cıvıl", "hayat", "party"],
        "huzunlu_slow": ["üzgün", "ağla", "hüzün", "mutsuz", "melankoli", "yalnız", "kırgın", "veda", "bitti", "özlem", "keder", "canım acıyor", "depresif", "çaresiz", "yorgun"],
        "enerjik_spor": ["hız", "spor", "güç", "koşu", "antrenman", "enerji", "bas", "motivasyon", "hareket", "kaldır", "fit", "gym", "tempo"],
        "sakin_akustik": ["huzur", "kitap", "kahve", "uyku", "sakin", "dingin", "sessiz", "mola", "dinlen", "soft", "yağmur", "şömine"],
        "hard_rock_metal": ["öfke", "bağırmak", "nefret", "kızgın", "sinir", "kaos", "gürültü", "patla", "sert", "metal", "isyan", "kırıp"],
        "indie_alternatif": ["farklı", "boşver", "uzak", "yol", "sanat", "alternatif", "hipster", "bağımsız", "yenilik", "değişik"],
        "jazz_blues": ["gece", "loş", "şarap", "yorgun", "melodi", "klasik", "ruh", "sofistike", "asil", "piyano"],
        "rap_hiphop": ["sokak", "ritim", "para", "sistem", "isyan", "beat", "mc", "rhyme", "dostum", "mahalle", "gerçek"]
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
    """Seçilen kategoriye göre rastgele bir doktor yorumu seçer."""
    yorumlar = {
        "neseli_pop": [
            "Enerjin harika görünüyor! Dopamin seviyeni yüksek tutacak ritimler seçtim.",
            "Bugün ışık saçıyorsun. Bu modu korumak için hareketli parçalar iyi gider.",
            "Pozitifliğin bulaşıcı! Kutlama tadında bir liste hazırladım."
        ],
        "huzunlu_slow": [
            "Biraz duygusal bir dönemdesin sanırım. Bazen hüzünle yüzleşmek iyileşmenin ilk adımıdır.",
            "İçindeki ağırlığı notalara bırakman için melankolik bir seçki hazırladım.",
            "Duygusal bir deşarj ihtiyacı seziyorum. Bu şarkılar sana yoldaş olacak."
        ],
        "enerjik_spor": [
            "Adrenalin arayışındasın! Nabzını yükseltecek parçalar hazır.",
            "İçindeki gücü dışarı vurma zamanı. Sınırları zorlayan bir liste oldu.",
            "Motivasyonun tavan yapmış. Bu ritimle seni kimse tutamaz!"
        ],
        "sakin_akustik": [
            "Dünyanın gürültüsünden uzaklaşıp biraz nefes almaya ihtiyacın var.",
            "Kortizol seviyeni düşürecek, zihnini pamuk gibi yapacak tınılar seçtim.",
            "Dinginlik ve huzur arıyorsun. Kendine ayırdığın bu vakit çok değerli."
        ],
        "hard_rock_metal": [
            "İçinde biriken bir öfke veya patlamaya hazır bir enerji var. Kontrollü kaos iyi gelecek!",
            "Sessiz kalmak istemiyorsun. Bırak gitarın telleri senin yerine bağırsın.",
            "Ruhundaki isyanı dışa vurmanın en iyi yolu sert ritimlerdir."
        ],
        "indie_alternatif": [
            "Sıradanlıktan sıkılmışsın, farklı ve özgün tınılar arıyorsun.",
            "Şehrin karmaşasından zihnen uzaklaşıp, sanatsal bir yolculuğa çıkalım.",
            "Ana akımdan uzak, senin gibi özel hissettiren parçalar seçtim."
        ],
        "jazz_blues": [
            "Ruhun biraz sofistike ve derinlik arıyor. Klasikleşmiş tınılar sana iyi gelecek.",
            "Günün yorgunluğunu atarken sana eşlik edecek asil melodiler hazırladım.",
            "Melankoli ile huzur arasında gidip geliyorsun. Bu liste tam o denge noktasında."
        ],
        "rap_hiphop": [
            "Sözlerin gücüne ve ritmin enerjisine ihtiyacın var.",
            "Hayatın gerçekleriyle yüzleşirken ritim tutmak sana güç verecek.",
            "Sokakların sesi ve ritmi modunu yükseltecek."
        ]
    }
    
    # İlgili kategoriden rastgele bir yorum seç
    return random.choice(yorumlar.get(kategori, ["Senin için özel bir karışım."]))