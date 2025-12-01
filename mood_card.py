from PIL import Image, ImageDraw, ImageFont
import textwrap
import os

# Proje klasöründeki font dosyasının yolu
FONT_PATH = "Roboto-Regular.ttf"

def kart_olustur(mood, doktor_notu, sarki_adi=""):
    """
    Ruh haline özel psikolojik renklerle Instagram Story kartı oluşturur.
    """
    # --- PSİKOLOJİK RENK PALETİ (Arka Plan, Metin) ---
    renkler = {
        # Neşeli: Sarı (Enerji, Güneş) -> Yazı: Siyah (Okunabilirlik için)
        "neseli_pop": ("#FFD700", "#000000"),       
        
        # Hüzünlü: Koyu Mavi/Gri (Melankoli, Derinlik) -> Yazı: Beyaz
        "huzunlu_slow": ("#2C3E50", "#ECF0F1"),     
        
        # Enerjik: Turuncu/Kırmızı (Adrenalin, Hareket) -> Yazı: Beyaz
        "enerjik_spor": ("#FF4500", "#FFFFFF"),     
        
        # Sakin: Açık Yeşil/Bej (Doğa, Huzur) -> Yazı: Koyu Yeşil
        "sakin_akustik": ("#D4EFDF", "#145A32"),    
        
        # Indie: Mor (Yaratıcılık, Gizem) -> Yazı: Beyaz
        "indie_alternatif": ("#8E44AD", "#F4ECF7"), 
        
        # Metal: Siyah (Güç, İsyan) -> Yazı: Kırmızımsı Beyaz
        "hard_rock_metal": ("#000000", "#E74C3C"),  
        
        # Elektronik: Neon/Koyu (Fütüristik) -> Yazı: Neon Yeşili
        "elektronik_synth": ("#1F1F1F", "#00FF00"), 
        
        # Caz: Lacivert/Altın (Sofistike, Lüks) -> Yazı: Altın Sarısı
        "jazz_blues": ("#154360", "#F1C40F"),       
        
        # Rap: Koyu Gri/Altın (Sokak, Prestij) -> Yazı: Altın
        "rap_hiphop": ("#1C2833", "#D4AC0D")        
    }
    
    # Mod listesinde olmayan bir durum gelirse varsayılan renkleri kullan (Mavi/Beyaz)
    bg_color, text_color = renkler.get(mood, ("#3498DB", "#FFFFFF"))
    
    # 2. Tuval Oluştur (600x1000 piksel - Story boyutu)
    W, H = 600, 1000
    img = Image.new('RGB', (W, H), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 3. Font Ayarları
    try:
        font_buyuk = ImageFont.truetype(FONT_PATH, 50)
        font_orta = ImageFont.truetype(FONT_PATH, 30)
        font_kucuk = ImageFont.truetype(FONT_PATH, 22)
    except OSError:
        # Font yoksa varsayılanı kullan (Görüntü kalitesi düşebilir)
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
    clean_mood = mood.replace("_", " ").upper()
    draw.text((40, 230), clean_mood, font=font_orta, fill=text_color)
    
    # Doktor Notu
    draw.text((40, 320), "DOKTOR NOTU:", font=font_kucuk, fill=text_color)
    
    # Metni kutuya sığacak şekilde parçala (Parantez içindeki hata mesajlarını temizle)
    clean_note = doktor_notu.split("(")[0].strip() # Hata mesajlarını kartta gösterme, şık dursun
    
    lines = textwrap.wrap(clean_note, width=28) 
    y_text = 350
    for line in lines:
        draw.text((40, y_text), line, font=font_orta, fill=text_color)
        y_text += 40
        
    # Şarkı Bilgisi (Varsa)
    if sarki_adi:
        y_text += 60
        if len(sarki_adi) > 30:
            sarki_adi = sarki_adi[:27] + "..."
            
        draw.text((40, y_text), "♫ ÖNERİLEN PARÇA:", font=font_kucuk, fill=text_color)
        draw.text((40, y_text + 30), sarki_adi, font=font_orta, fill=text_color)

    # Alt Bilgi (Instagram @kullaniciadi gibi eklenebilir)
    draw.text((40, H - 60), "Developed by MoodAI", font=font_kucuk, fill=text_color)

    return img