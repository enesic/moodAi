from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

def kart_olustur(mood, doktor_notu, sarki_adi=""):
    """
    Ruh haline özel Instagram Story boyutunda kart oluşturur.
    """
    # 1. Renk Paleti (Arka Plan, Metin)
    renkler = {
        "neseli_pop": ("#FFD700", "#FFFFFF"),       # Altın Sarısı
        "huzunlu_slow": ("#2F4F4F", "#E6E6FA"),     # Koyu Gri/Mavi
        "enerjik_spor": ("#FF4500", "#FFFFFF"),     # Turuncu Kırmızı
        "sakin_akustik": ("#556B2F", "#F5F5DC"),    # Zeytin Yeşili
        "indie_alternatif": ("#008080", "#E0FFFF"), # Teal
        "hard_rock_metal": ("#1C1C1C", "#D3D3D3"),  # Siyahımsı
        "elektronik_synth": ("#800080", "#EE82EE"), # Mor
        "jazz_blues": ("#191970", "#B0C4DE"),       # Gece Mavisi
        "rap_hiphop": ("#8B0000", "#FFC0CB")        # Koyu Kırmızı
    }
    
    bg_color, text_color = renkler.get(mood, ("#4682B4", "#FFFFFF"))
    
    # 2. Tuval Oluştur (600x1000 piksel - Story boyutu)
    W, H = 600, 1000
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 3. Font Ayarları (Sistemdeki Arial'i bulmaya çalış, yoksa varsayılanı kullan)
    try:
        # Windows için genelde bu yoldadır, Linux/Mac için farklı olabilir
        font_buyuk = ImageFont.truetype("arial.ttf", 50)
        font_orta = ImageFont.truetype("arial.ttf", 30)
        font_kucuk = ImageFont.truetype("arial.ttf", 20)
    except:
        # Font bulunamazsa basit font kullan (Görüntü biraz basit olur ama çalışır)
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
    draw.text((40, 230), mood.replace("_", " ").upper(), font=font_orta, fill=text_color)
    
    # Doktor Notu (Satır satır bölerek yaz)
    draw.text((40, 320), "DOKTOR NOTU:", font=font_kucuk, fill=text_color)
    
    # Metni kutuya sığacak şekilde parçala
    lines = textwrap.wrap(doktor_notu, width=30) 
    y_text = 350
    for line in lines:
        draw.text((40, y_text), line, font=font_orta, fill=text_color)
        y_text += 40
        
    # Şarkı Bilgisi (Varsa)
    if sarki_adi:
        y_text += 60
        draw.text((40, y_text), "♫ ÖNERİLEN PARÇA:", font=font_kucuk, fill=text_color)
        draw.text((40, y_text + 30), sarki_adi, font=font_orta, fill=text_color)

    # Alt Bilgi
    draw.text((40, H - 60), "Developed by MoodAI", font=font_kucuk, fill=text_color)

    return img