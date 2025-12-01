from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Proje klasöründeki font dosyasının yolu
FONT_PATH = "Roboto-Regular.ttf"

def kart_olustur(mood, doktor_notu, sarki_adi=""):
    """
    Ruh haline özel Instagram Story boyutunda kart oluşturur.
    """
    # 1. Renk Paleti (Arka Plan, Metin)
    renkler = {
        "neseli_pop": ("#FFD700", "#FFFFFF"),       # Altın Sarısı / Beyaz
        "huzunlu_slow": ("#2F4F4F", "#E6E6FA"),     # Koyu Gri-Mavi / Lavanta
        "enerjik_spor": ("#FF4500", "#FFFFFF"),     # Turuncu Kırmızı / Beyaz
        "sakin_akustik": ("#556B2F", "#F5F5DC"),    # Zeytin Yeşili / Bej
        "indie_alternatif": ("#008080", "#E0FFFF"), # Teal / Açık Camgöbeği
        "hard_rock_metal": ("#1C1C1C", "#D3D3D3"),  # Siyahımsı / Açık Gri
        "elektronik_synth": ("#800080", "#EE82EE"), # Mor / Menekşe
        "jazz_blues": ("#191970", "#B0C4DE"),       # Gece Mavisi / Açık Mavi
        "rap_hiphop": ("#8B0000", "#FFC0CB")        # Koyu Kırmızı / Pembe
    }
    
    # Mod listesinde olmayan bir durum gelirse varsayılan renkleri kullan
    bg_color, text_color = renkler.get(mood, ("#4682B4", "#FFFFFF"))
    
    # 2. Tuval Oluştur (600x1000 piksel - Story boyutu)
    W, H = 600, 1000
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 3. Font Ayarları (Proje içindeki özel fontu kullan)
    try:
        # Font boyutlarını belirle
        font_buyuk = ImageFont.truetype(FONT_PATH, 50)
        font_orta = ImageFont.truetype(FONT_PATH, 30)
        font_kucuk = ImageFont.truetype(FONT_PATH, 22)
    except OSError:
        # Eğer font dosyası proje klasörüne atılmamışsa uyarı ver ve varsayılanı kullan
        print(f"UYARI: '{FONT_PATH}' dosyası bulunamadı. Varsayılan font kullanılıyor.")
        font_buyuk = ImageFont.load_default()
        font_orta = ImageFont.load_default()
        font_kucuk = ImageFont.load_default()

    # 4. Çizim İşlemleri
    
    # Başlık
    draw.text((40, 60), "MOOD AI", font=font_kucuk, fill=text_color)
    draw.text((40, 90), "TERAPİSTİ", font=font_buyuk, fill=text_color)
    
    # Çizgi
    draw.line((40, 160, 560, 160), fill=text_color, width=3)
    
    # Teşhis
    draw.text((40, 200), "TEŞHİS:", font=font_kucuk, fill=text_color)
    # Mod ismindeki alt çizgileri boşlukla değiştir ve büyük harf yap
    clean_mood = mood.replace("_", " ").upper()
    draw.text((40, 230), clean_mood, font=font_orta, fill=text_color)
    
    # Doktor Notu
    draw.text((40, 320), "DOKTOR NOTU:", font=font_kucuk, fill=text_color)
    
    # Metni kutuya sığacak şekilde parçala (Her satırda ~28 karakter)
    lines = textwrap.wrap(doktor_notu, width=28) 
    y_text = 350
    for line in lines:
        draw.text((40, y_text), line, font=font_orta, fill=text_color)
        y_text += 40
        
    # Şarkı Bilgisi (Varsa)
    if sarki_adi:
        y_text += 60
        # Şarkı ismi çok uzunsa kısalt
        if len(sarki_adi) > 30:
            sarki_adi = sarki_adi[:27] + "..."
            
        draw.text((40, y_text), "♫ ÖNERİLEN PARÇA:", font=font_kucuk, fill=text_color)
        draw.text((40, y_text + 30), sarki_adi, font=font_orta, fill=text_color)

    # Alt Bilgi
    draw.text((40, H - 60), "Developed by MoodAI", font=font_kucuk, fill=text_color)

    return img