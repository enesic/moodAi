import io
import os
import re
import textwrap
import urllib.request
from typing import Optional
from PIL import Image, ImageDraw, ImageFont

from backend.core.moods import MOOD_LABELS

MOOD_METADATA = {
    "neseli_pop": {"name": "NEŞELİ & DANS", "tag": "DOPAMİN PATLAMASI", "top_color": (245, 158, 11), "bot_color": (15, 10, 30)},
    "huzunlu_slow": {"name": "HÜZÜNLÜ & MELANKOLİK", "tag": "İÇSEL YOLCULUK", "top_color": (14, 116, 144), "bot_color": (10, 17, 40)},
    "enerjik_spor": {"name": "ENERJİK & MOTİVASYON", "tag": "ADRENALİN & GÜÇ", "top_color": (225, 29, 72), "bot_color": (26, 10, 30)},
    "sakin_akustik": {"name": "SAKİN & HUZURLU", "tag": "ZİHİNSEL DİNGİNLİK", "top_color": (16, 185, 129), "bot_color": (9, 32, 24)},
    "hard_rock_metal": {"name": "ÖFKE & ROCK/METAL", "tag": "KATARSİS & İSYAN", "top_color": (185, 28, 28), "bot_color": (13, 13, 13)},
    "indie_alternatif": {"name": "İNDİE & DERİN DÜŞÜNCE", "tag": "ÖZGÜN & BOHEM", "top_color": (147, 51, 234), "bot_color": (18, 8, 36)},
    "rap_hiphop": {"name": "SOKAK & RAP/HİPHOP", "tag": "RİTİM & GERÇEKLER", "top_color": (234, 88, 12), "bot_color": (18, 10, 2)},
    "jazz_blues": {"name": "GECE & JAZZ/BLUES", "tag": "ZARAFET & NOSTALJİ", "top_color": (59, 130, 246), "bot_color": (6, 17, 24)},
    "elektronik_synth": {"name": "NEON & ELEKTRONİK", "tag": "FÜTÜRİSTİK FREKANS", "top_color": (6, 182, 212), "bot_color": (2, 24, 32)}
}

# PIL ile metin yazarken bozuk kutu çıkmasını önlemek için emojileri temizleme filtresi
EMOJI_REGEX = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50]', flags=re.UNICODE)


def strip_emojis(text: str) -> str:
    return EMOJI_REGEX.sub('', text).strip()


def get_font(size: int, bold: bool = False):
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Roboto-Regular.ttf')),
        "segoeuib.ttf" if bold else "segoeui.ttf",
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _fetch_album_image(url: str, size: int = 160) -> Optional[Image.Image]:
    """Albüm kapağını güvenli bir şekilde indirip yuvarlatılmış küçük resim döner."""
    if not url or not url.startswith("http"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MoodAI/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((size, size), Image.Resampling.LANCZOS)
        
        # Yuvarlatılmış köşe maskesi
        mask = Image.new("L", (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle([(0, 0), (size, size)], radius=24, fill=255)
        
        rounded = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        rounded.paste(img, (0, 0), mask)
        return rounded
    except Exception:
        return None


def create_mood_card(
    mood: str,
    doktor_notu: str,
    sarki_adi: str,
    sanatci_adi: Optional[str] = None,
    track_count: int = 20,
    image_url: Optional[str] = None
) -> bytes:
    # 9:16 Instagram Story & TikTok Çözünürlüğü (1080 x 1920)
    width, height = 1080, 1920
    meta = MOOD_METADATA.get(mood, {
        "name": mood.replace("_", " ").upper(),
        "tag": "ÖZEL REÇETE",
        "top_color": (124, 58, 237),
        "bot_color": (15, 10, 30)
    })

    # Dikey yumuşak degrade arka plan
    img = Image.new('RGB', (width, height))
    d = ImageDraw.Draw(img)
    
    top_r, top_g, top_b = meta["top_color"]
    bot_r, bot_g, bot_b = meta["bot_color"]
    for y in range(height):
        factor = y / float(height)
        r = int(top_r + (bot_r - top_r) * factor)
        g = int(top_g + (bot_g - top_g) * factor)
        b = int(top_b + (bot_b - top_b) * factor)
        d.line([(0, y), (width, y)], fill=(r, g, b))

    # Fontlar
    brand_font = get_font(38, bold=True)
    badge_font = get_font(28, bold=True)
    title_font = get_font(56, bold=True)
    section_font = get_font(32, bold=True)
    body_font = get_font(38)
    song_font = get_font(48, bold=True)
    artist_font = get_font(36)
    footer_font = get_font(32)

    # Glassmorphism ana kart paneli
    card_margin_x = 70
    card_top = 250
    card_bottom = 1680

    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(card_margin_x, card_top), (width - card_margin_x, card_bottom)],
        radius=48,
        fill=(0, 0, 0, 140),
        outline=(255, 255, 255, 55),
        width=3
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(img)

    # 1. Header (Brand)
    d.text((width // 2, 130), "M O O D   A I", fill=(255, 255, 255), font=brand_font, anchor="mm")
    d.text((width // 2, 185), "YAPAY ZEKA DESTEKLİ MÜZİK TERAPİSTİ", fill=(200, 200, 230), font=badge_font, anchor="mm")

    # 2. Teşhis Rozeti & Başlık
    d.text((card_margin_x + 60, card_top + 70), f"TEŞHİS: {meta['tag']}", fill=(180, 180, 210), font=badge_font)
    d.text((card_margin_x + 60, card_top + 130), meta['name'], fill=(255, 255, 255), font=title_font)

    # Ayırıcı Çizgi
    d.line([(card_margin_x + 60, card_top + 215), (width - card_margin_x - 60, card_top + 215)], fill=(255, 255, 255, 40), width=2)

    # 3. Doktorun Notu
    clean_note = strip_emojis(doktor_notu or "Sana özel müzikal reçete oluşturuldu.")
    d.text((card_margin_x + 60, card_top + 270), "TERAPİSTİN ANALİZİ", fill=(190, 190, 225), font=section_font)
    wrapped_note = textwrap.fill(clean_note, width=32)
    note_box_top = card_top + 330
    d.text((card_margin_x + 60, note_box_top), f'"{wrapped_note}"', fill=(240, 240, 255), font=body_font, spacing=16)

    # 4. Reçetelenen Başyapıt Kutusu
    song_box_top = card_top + 800
    d.text((card_margin_x + 60, song_box_top), "ÖNE ÇIKAN BAŞYAPIT", fill=(190, 190, 225), font=section_font)
    
    # Albüm kapağı varsa çiz
    album_img = _fetch_album_image(image_url, size=160) if image_url else None
    text_offset_x = card_margin_x + 60
    if album_img:
        img.paste(album_img, (card_margin_x + 60, song_box_top + 55), album_img)
        d = ImageDraw.Draw(img)
        text_offset_x = card_margin_x + 250

    clean_song = strip_emojis(sarki_adi or "Reçete Parçası")
    wrapped_song = textwrap.fill(clean_song, width=22 if album_img else 28)
    d.text((text_offset_x, song_box_top + 55), wrapped_song, fill=(134, 239, 172), font=song_font, spacing=10)
    
    if sanatci_adi:
        clean_artist = strip_emojis(sanatci_adi)
        d.text((text_offset_x, song_box_top + 155), clean_artist, fill=(210, 210, 230), font=artist_font)

    # 5. Çalma Listesi Detayı
    count_text = f"{max(1, track_count)} Şarkılık Tam Terapi Listesi Hazırlandı"
    d.text((card_margin_x + 60, card_bottom - 220), count_text, fill=(210, 210, 235), font=body_font)
    d.text((card_margin_x + 60, card_bottom - 150), "Spotify ile dinle ve kütüphanene ekle", fill=(100, 225, 140), font=badge_font)

    # 6. Alt Bilgi
    d.text((width // 2, 1760), "Sen de kendi modunu keşfet", fill=(255, 255, 255), font=footer_font, anchor="mm")
    d.text((width // 2, 1810), "moodai.app • Spotify Entegrasyonlu", fill=(180, 180, 205), font=badge_font, anchor="mm")

    # PNG çıktısı
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95)
    return img_byte_arr.getvalue()


def create_vibe_card(
    user1_name: str,
    user2_name: str,
    mood1_label: str,
    mood2_label: str,
    match_score: int,
    verdict: str,
    sarki_adi: str,
    sanatci_adi: Optional[str] = None,
    image_url: Optional[str] = None
) -> bytes:
    """İki kişinin frekans uyumunu ve ortak parçasını gösteren viral 9:16 Instagram Story kartı."""
    width, height = 1080, 1920

    # Arka plan: Modern mor-pembe-gece gradyanı
    img = Image.new('RGB', (width, height))
    d = ImageDraw.Draw(img)

    top_r, top_g, top_b = (120, 20, 140)
    bot_r, bot_g, bot_b = (10, 8, 28)
    for y in range(height):
        factor = y / float(height)
        r = int(top_r + (bot_r - top_r) * factor)
        g = int(top_g + (bot_g - top_g) * factor)
        b = int(top_b + (bot_b - top_b) * factor)
        d.line([(0, y), (width, y)], fill=(r, g, b))

    # Fontlar
    brand_font = get_font(38, bold=True)
    badge_font = get_font(28, bold=True)
    score_num_font = get_font(120, bold=True)
    score_label_font = get_font(34, bold=True)
    title_font = get_font(50, bold=True)
    section_font = get_font(30, bold=True)
    body_font = get_font(36)
    song_font = get_font(44, bold=True)
    artist_font = get_font(34)
    footer_font = get_font(30)

    # Glassmorphism kart paneli
    card_margin_x = 70
    card_top = 230
    card_bottom = 1700

    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(card_margin_x, card_top), (width - card_margin_x, card_bottom)],
        radius=48,
        fill=(0, 0, 0, 150),
        outline=(236, 72, 153, 90),
        width=3
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(img)

    # 1. Header
    d.text((width // 2, 120), "M O O D   A I", fill=(255, 255, 255), font=brand_font, anchor="mm")
    d.text((width // 2, 175), "VIBE CHECK & FREKANS UYUMU", fill=(244, 114, 182), font=badge_font, anchor="mm")

    # 2. İki Kişinin İsimleri & Modları
    u1 = strip_emojis(user1_name or "1. Kişi").upper()
    u2 = strip_emojis(user2_name or "2. Kişi").upper()
    m1 = strip_emojis(mood1_label or "Ruh Hali")
    m2 = strip_emojis(mood2_label or "Ruh Hali")

    names_top = card_top + 60
    d.text((card_margin_x + 60, names_top), u1, fill=(255, 255, 255), font=title_font)
    d.text((card_margin_x + 60, names_top + 65), f"Mod: {m1}", fill=(216, 180, 254), font=body_font)

    d.text((width // 2, names_top + 130), "⚡ FREKANS KESİŞİMİ ⚡", fill=(244, 114, 182), font=badge_font, anchor="mm")

    d.text((width - card_margin_x - 60, names_top + 180), u2, fill=(255, 255, 255), font=title_font, anchor="ra")
    d.text((width - card_margin_x - 60, names_top + 245), f"Mod: {m2}", fill=(216, 180, 254), font=body_font, anchor="ra")

    # Ayırıcı
    divider_y = names_top + 330
    d.line([(card_margin_x + 60, divider_y), (width - card_margin_x - 60, divider_y)], fill=(255, 255, 255, 40), width=2)

    # 3. Skor Kutusu
    score_y = divider_y + 110
    score_str = f"%{min(100, max(0, match_score))}"
    d.text((width // 2, score_y), score_str, fill=(244, 114, 182), font=score_num_font, anchor="mm")
    d.text((width // 2, score_y + 90), "MÜZİKAL VE RUHSAL UYUM", fill=(255, 255, 255), font=score_label_font, anchor="mm")

    # 4. Yorum / Teşhis (Verdict)
    verdict_top = score_y + 160
    d.text((card_margin_x + 60, verdict_top), "TERAPİSTİN UYUM RAPORU", fill=(190, 190, 225), font=section_font)
    clean_verdict = strip_emojis(verdict or "İki ruh hali birbirini mükemmel dengeliyor.")
    wrapped_verdict = textwrap.fill(clean_verdict, width=32)
    d.text((card_margin_x + 60, verdict_top + 50), f'"{wrapped_verdict}"', fill=(240, 240, 255), font=body_font, spacing=14)

    # 5. Ortak Başyapıt Kutusu
    song_box_top = verdict_top + 350
    d.text((card_margin_x + 60, song_box_top), "ORTAK FREKANS PARÇASI", fill=(244, 114, 182), font=section_font)

    album_img = _fetch_album_image(image_url, size=150) if image_url else None
    text_offset_x = card_margin_x + 60
    if album_img:
        img.paste(album_img, (card_margin_x + 60, song_box_top + 50), album_img)
        d = ImageDraw.Draw(img)
        text_offset_x = card_margin_x + 230

    clean_song = strip_emojis(sarki_adi or "Ortak Şarkı")
    wrapped_song = textwrap.fill(clean_song, width=22 if album_img else 28)
    d.text((text_offset_x, song_box_top + 50), wrapped_song, fill=(134, 239, 172), font=song_font, spacing=8)
    if sanatci_adi:
        clean_artist = strip_emojis(sanatci_adi)
        d.text((text_offset_x, song_box_top + 140), clean_artist, fill=(210, 210, 230), font=artist_font)

    # 6. Alt Bilgi
    d.text((card_margin_x + 60, card_bottom - 110), "Spotify ile ortak listeyi dinle", fill=(100, 225, 140), font=badge_font)
    d.text((width // 2, 1780), "Sen de arkadaşınla frekansını test et!", fill=(255, 255, 255), font=footer_font, anchor="mm")
    d.text((width // 2, 1830), "moodai.app/vibe • Vibe Check", fill=(244, 114, 182), font=badge_font, anchor="mm")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95)
    return img_byte_arr.getvalue()

