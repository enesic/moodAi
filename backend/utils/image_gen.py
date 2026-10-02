import io
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap

MOOD_METADATA = {
    "neseli_pop": {"name": "NEŞELİ & DANS", "emoji": "🎉", "top_color": (245, 158, 11), "bot_color": (15, 10, 30)},
    "huzunlu_slow": {"name": "HÜZÜNLÜ & MELANKOLİK", "emoji": "🌧️", "top_color": (14, 116, 144), "bot_color": (10, 17, 40)},
    "enerjik_spor": {"name": "ENERJİK & MOTİVASYON", "emoji": "⚡", "top_color": (225, 29, 72), "bot_color": (26, 10, 30)},
    "sakin_akustik": {"name": "SAKİN & HUZURLU", "emoji": "☕", "top_color": (16, 185, 129), "bot_color": (9, 32, 24)},
    "hard_rock_metal": {"name": "ÖFKE & ROCK/METAL", "emoji": "🔥", "top_color": (185, 28, 28), "bot_color": (13, 13, 13)},
    "indie_alternatif": {"name": "İNDİE & DERİN DÜŞÜNCE", "emoji": "🌌", "top_color": (147, 51, 234), "bot_color": (18, 8, 36)},
    "rap_hiphop": {"name": "SOKAK & RAP/HİPHOP", "emoji": "🎤", "top_color": (234, 88, 12), "bot_color": (18, 10, 2)},
    "jazz_blues": {"name": "GECE & JAZZ/BLUES", "emoji": "🎷", "top_color": (59, 130, 246), "bot_color": (6, 17, 24)},
    "elektronik_synth": {"name": "NEON & ELEKTRONİK", "emoji": "🚀", "top_color": (6, 182, 212), "bot_color": (2, 24, 32)}
}

def get_font(size: int):
    # Try loading Roboto font if available, otherwise default
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Roboto-Regular.ttf')),
        "arial.ttf",
        "segoeui.ttf",
        "DejaVuSans.ttf"
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()

def create_gradient(width: int, height: int, top_color: tuple, bot_color: tuple) -> Image.Image:
    base = Image.new('RGB', (width, height), top_color)
    top_r, top_g, top_b = top_color
    bot_r, bot_g, bot_b = bot_color
    
    # Create vertical gradient
    for y in range(height):
        factor = y / float(height)
        r = int(top_r + (bot_r - top_r) * factor)
        g = int(top_g + (bot_g - top_g) * factor)
        b = int(top_b + (bot_b - top_b) * factor)
        for x in range(width):
            base.putpixel((x, y), (r, g, b))
    return base

def create_mood_card(mood: str, doktor_notu: str, sarki_adi: str) -> bytes:
    # 9:16 Instagram Story & TikTok Resolution (1080 x 1920)
    width, height = 1080, 1920
    meta = MOOD_METADATA.get(mood, {
        "name": mood.replace("_", " ").upper(),
        "emoji": "🧠",
        "top_color": (124, 58, 237),
        "bot_color": (15, 10, 30)
    })

    # Fast vertical gradient generation using simple line drawing
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

    # Fonts
    brand_font = get_font(38)
    badge_font = get_font(32)
    title_font = get_font(60)
    section_font = get_font(36)
    body_font = get_font(42)
    song_font = get_font(52)
    footer_font = get_font(34)

    # Glassmorphism main card overlay
    card_margin_x = 70
    card_top = 260
    card_bottom = 1660
    card_w = width - (card_margin_x * 2)
    card_h = card_bottom - card_top

    # Semi-transparent card
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [(card_margin_x, card_top), (width - card_margin_x, card_bottom)],
        radius=48,
        fill=(0, 0, 0, 130),
        outline=(255, 255, 255, 60),
        width=3
    )
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    d = ImageDraw.Draw(img)

    # 1. Header (Brand)
    d.text((width // 2, 140), "🧠  M O O D  A I", fill=(255, 255, 255), font=brand_font, anchor="mm")
    d.text((width // 2, 195), "YAPAY ZEKA MÜZİK TERAPİSTİ", fill=(200, 200, 220), font=badge_font, anchor="mm")

    # 2. Diagnosis Badge & Title
    d.text((card_margin_x + 60, card_top + 80), "TEŞHİS EDİLEN RUH HALİ", fill=(180, 180, 200), font=badge_font)
    d.text((card_margin_x + 60, card_top + 150), f"{meta['emoji']}  {meta['name']}", fill=(255, 255, 255), font=title_font)

    # Separator
    d.line([(card_margin_x + 60, card_top + 230), (width - card_margin_x - 60, card_top + 230)], fill=(255, 255, 255, 40), width=2)

    # 3. Doctor's Note (Medical Box)
    d.text((card_margin_x + 60, card_top + 290), "📝  TERAPİSTİN NOTU & ANALİZİ", fill=(190, 190, 220), font=section_font)
    wrapped_note = textwrap.fill(doktor_notu, width=32)
    
    # Note box
    note_box_top = card_top + 350
    d.text((card_margin_x + 60, note_box_top), f'"{wrapped_note}"', fill=(240, 240, 255), font=body_font, spacing=14)

    # 4. Prescribed Song Box
    song_box_top = card_top + 820
    d.text((card_margin_x + 60, song_box_top), "🎵  REÇETELENEN BAŞYAPIT", fill=(190, 190, 220), font=section_font)
    
    wrapped_song = textwrap.fill(sarki_adi, width=28)
    d.text((card_margin_x + 60, song_box_top + 60), wrapped_song, fill=(134, 239, 172), font=song_font, spacing=12)

    # 5. Spotify & Playlist Info
    d.text((card_margin_x + 60, card_bottom - 220), "✨ 20 Şarkılık Tam Terapi Listesi Hazırlandı", fill=(210, 210, 230), font=body_font)
    d.text((card_margin_x + 60, card_bottom - 150), "🟢 Spotify ile dinle ve kütüphanene kaydet", fill=(100, 220, 140), font=badge_font)

    # 6. Bottom Footer
    d.text((width // 2, 1750), "Sen de kendi modunu keşfet 📲", fill=(255, 255, 255), font=footer_font, anchor="mm")
    d.text((width // 2, 1800), "moodai.app • Spotify Entegrasyonlu", fill=(180, 180, 200), font=badge_font, anchor="mm")

    # Save to PNG bytes
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG', quality=95)
    return img_byte_arr.getvalue()
