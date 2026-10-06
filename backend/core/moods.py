"""
Mood AI — Paylaşılan Duygu Modeli
=================================
Backend'in tüm katmanlarının (NLP motoru, Spotify küratörlüğü, story kartı, API meta)
ortak kullandığı tek doğruluk kaynağı (single source of truth).

- 9 ana müzikal ruh hali kategorisi ve alt türleri
- Russell Çevresel Duygu Modeli (Valence / Arousal) koordinatları
- Terapi modları (ISO prensibi) ve duygu yolculuğu (journey) planlayıcısı
- Enerji seviyesine göre komşu ruh hali seçimi
"""
import math
from typing import Dict, List, Optional, Tuple

# 9 Ana Kategori ve Alt Türler
ALT_TURLER: Dict[str, List[str]] = {
    "neseli_pop": ["Pop & Dans", "Disco & Retro Pop", "Yaz Hitleri", "K-Pop", "Latin Pop"],
    "huzunlu_slow": ["Slow & Balad", "Melankolik Slow", "Akustik Hüzün", "Piyano & Yağmur", "Kırık Kalpler"],
    "enerjik_spor": ["Workout & Motivasyon", "Yüksek BPM Trap", "Power Drill", "Club & Techno Hits"],
    "sakin_akustik": ["Lo-Fi Beats", "Akustik Gitar & Chill", "Soft Pop", "Coffeehouse Akustik", "Ambient & Dinginlik"],
    "indie_alternatif": ["Modern Indie Rock", "Dream Pop", "Shoegaze", "Alternatif Rock", "Bohem & Nostalji"],
    "hard_rock_metal": ["Klasik Rock", "Hard Rock", "Heavy Metal", "Nu-Metal", "Punk & Grunge"],
    "rap_hiphop": ["Modern Trap", "Old School & Boom Bap", "Melodik Rap", "Drill & Underground"],
    "jazz_blues": ["Smooth Jazz", "Vocal Jazz", "Blues & Soul", "Gece Mavisi Jazz"],
    "elektronik_synth": ["Synthwave & Neon", "Deep House", "Minimal Techno", "EDM & Festival"],
}

# ==============================================================================
# RUSSELL ÇEVRESEL DUYGU MODELİ (CIRCUMPLEX MODEL OF AFFECT)
# - Valence (Duygusal Değerlik): -1.0 (Aşırı Negatif) <──> +1.0 (Aşırı Pozitif)
# - Arousal (Uyarılma / Enerji): 0.0 (Durgun) <──> 1.0 (Patlayıcı Enerji)
# ==============================================================================
MOOD_VECTORS: Dict[str, Dict[str, float]] = {
    "huzunlu_slow":     {"valence": -0.85, "arousal": 0.20, "weight": 1.4},
    "sakin_akustik":    {"valence":  0.45, "arousal": 0.20, "weight": 1.2},
    "neseli_pop":       {"valence":  0.85, "arousal": 0.80, "weight": 1.3},
    "enerjik_spor":     {"valence":  0.40, "arousal": 0.95, "weight": 1.3},
    "hard_rock_metal":  {"valence": -0.65, "arousal": 0.90, "weight": 1.4},
    "indie_alternatif": {"valence": -0.20, "arousal": 0.40, "weight": 1.1},
    "rap_hiphop":       {"valence":  0.05, "arousal": 0.75, "weight": 1.2},
    "jazz_blues":       {"valence":  0.25, "arousal": 0.35, "weight": 1.1},
    "elektronik_synth": {"valence":  0.55, "arousal": 0.85, "weight": 1.2},
}

# Kullanıcıya gösterilen etiketler (frontend + story kartı)
MOOD_LABELS: Dict[str, Dict[str, str]] = {
    "neseli_pop":       {"name": "Neşeli & Dans",          "emoji": "🎉"},
    "huzunlu_slow":     {"name": "Hüzünlü & Melankolik",   "emoji": "🌧️"},
    "enerjik_spor":     {"name": "Enerjik & Motivasyon",   "emoji": "⚡"},
    "sakin_akustik":    {"name": "Sakin & Huzurlu",        "emoji": "☕"},
    "hard_rock_metal":  {"name": "Öfke & Rock/Metal",      "emoji": "🔥"},
    "indie_alternatif": {"name": "İndie & Derin Düşünce",  "emoji": "🌌"},
    "rap_hiphop":       {"name": "Sokak & Rap/Hip-Hop",    "emoji": "🎤"},
    "jazz_blues":       {"name": "Gece & Jazz/Blues",      "emoji": "🎷"},
    "elektronik_synth": {"name": "Neon & Elektronik",      "emoji": "🚀"},
}

LANGUAGES = ("tr", "en", "yabanci", "mix")
ENERGY_LEVELS = ("Düşük", "Orta", "Yüksek")

# ==============================================================================
# TERAPİ MODLARI — Müzik terapisindeki "ISO Prensibi":
# Önce dinleyicinin mevcut ruh haline eşlik edilir (match), sonra müzik kademeli
# olarak hedeflenen duygu durumuna doğru yönlendirilir (bridge → target).
# ==============================================================================
THERAPY_MODES: Dict[str, Dict[str, Optional[str]]] = {
    "catharsis": {
        "label": "Katarsis",
        "emoji": "🌊",
        "description": "Duygunla kal ve onu tamamen yaşa. Liste baştan sona ruh haline eşlik eder.",
        "target": None,
    },
    "uplift": {
        "label": "Moda Yükselt",
        "emoji": "🌅",
        "description": "ISO prensibi: önce seninle aynı tonda başlar, adım adım daha pozitif ve enerjik bir yere taşır.",
        "target": "neseli_pop",
    },
    "calm": {
        "label": "Sakinleştir",
        "emoji": "🍃",
        "description": "ISO prensibi: mevcut enerjinle başlar, nabzını kademeli olarak düşürüp huzura indirir.",
        "target": "sakin_akustik",
    },
}

JOURNEY_STAGE_LABELS = ["Eşlik", "Geçiş", "Hedef"]


def _distance(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def _vec(mood: str) -> Tuple[float, float]:
    v = MOOD_VECTORS[mood]
    return v["valence"], v["arousal"]


def nearest_mood(point: Tuple[float, float], exclude: Optional[List[str]] = None) -> Optional[str]:
    """Verilen (valence, arousal) noktasına en yakın ruh hali kategorisi."""
    exclude = exclude or []
    candidates = [m for m in MOOD_VECTORS if m not in exclude]
    if not candidates:
        return None
    return min(candidates, key=lambda m: _distance(point, _vec(m)))


def build_therapy_journey(mood: str, therapy_mode: str = "catharsis") -> List[str]:
    """
    Terapi moduna göre 3 aşamalı duygu yolculuğu üretir: [eşlik, geçiş, hedef].
    Geçiş aşaması; başlangıç ve hedef vektörlerinin orta noktasına en yakın
    ruh hali kategorisidir (Russell uzayında doğrusal interpolasyon).
    """
    if mood not in MOOD_VECTORS:
        mood = "sakin_akustik"
    mode = THERAPY_MODES.get(therapy_mode, THERAPY_MODES["catharsis"])
    target = mode["target"]

    if not target or target == mood:
        return [mood, mood, mood]

    start_v, target_v = _vec(mood), _vec(target)
    midpoint = ((start_v[0] + target_v[0]) / 2, (start_v[1] + target_v[1]) / 2)
    bridge = nearest_mood(midpoint, exclude=[mood, target]) or mood
    return [mood, bridge, target]


def split_count(total: int, parts: int = 3, weights: Optional[List[float]] = None) -> List[int]:
    """Toplam şarkı sayısını aşamalara (ağırlıklı) böler; toplam her zaman korunur."""
    weights = weights or [1.0] * parts
    s = sum(weights)
    raw = [total * w / s for w in weights]
    counts = [int(math.floor(r)) for r in raw]
    # Kalanları en büyük ondalık kısma göre dağıt
    remainder = total - sum(counts)
    order = sorted(range(parts), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[:remainder]:
        counts[i] += 1
    return counts


def energy_neighbor(mood: str, energy_level: str) -> Optional[str]:
    """
    Enerji tercihine göre aynı duygusal değerliğe (valence) en yakın, ancak
    daha düşük ya da daha yüksek uyarılmaya (arousal) sahip komşu kategori.
    'Orta' için komşu yoktur.
    """
    if mood not in MOOD_VECTORS or energy_level not in ("Düşük", "Yüksek"):
        return None
    val, aro = _vec(mood)
    if energy_level == "Düşük":
        candidates = [m for m in MOOD_VECTORS if m != mood and MOOD_VECTORS[m]["arousal"] < aro - 0.1]
    else:
        candidates = [m for m in MOOD_VECTORS if m != mood and MOOD_VECTORS[m]["arousal"] > aro + 0.1]
    if not candidates:
        return None
    return min(candidates, key=lambda m: abs(MOOD_VECTORS[m]["valence"] - val) + 0.3 * abs(MOOD_VECTORS[m]["arousal"] - aro))


def public_meta() -> dict:
    """Frontend'in tek kaynaktan çektiği meta veri (/api/meta)."""
    return {
        "moods": {
            key: {
                **MOOD_LABELS[key],
                "genres": ALT_TURLER[key],
                "valence": MOOD_VECTORS[key]["valence"],
                "arousal": MOOD_VECTORS[key]["arousal"],
            }
            for key in ALT_TURLER
        },
        "therapy_modes": {key: dict(data) for key, data in THERAPY_MODES.items()},
        "energy_levels": list(ENERGY_LEVELS),
        "journey_stage_labels": JOURNEY_STAGE_LABELS,
    }


# ==============================================================================
# SANATÇI DUYGU & BENZERLİK VERİTABANI (ARTIST CLUSTERING DIRECTORY)
# Kullanıcı şarkı veya sanatçı seçtiğinde, şarkının türünü ve benzer sanatçılarını
# doğrudan tespit ederek tutarlı öneri yapılmasını sağlar.
# ==============================================================================
ARTIST_DIRECTORY: Dict[str, Dict[str, any]] = {
    # Türk Alternatif / Rock / Indie
    "pera": {"mood": "indie_alternatif", "similar": ["Model", "Manga", "Duman", "Gripin", "Seksendört", "Kolpa", "Zakkum", "Madrigal", "Mor ve Ötesi", "Dedublüman"]},
    "duman": {"mood": "hard_rock_metal", "similar": ["Mor ve Ötesi", "Adamlar", "Manga", "Şebnem Ferah", "Pera", "Gripin", "Teoman", "Son Feci Bisiklet"]},
    "manga": {"mood": "hard_rock_metal", "similar": ["Duman", "Mor ve Ötesi", "Gripin", "Pera", "Hayko Cepkin", "Model", "Athena"]},
    "mor ve otesi": {"mood": "indie_alternatif", "similar": ["Duman", "Manga", "Adamlar", "Büyük Ev Ablukada", "Pera", "Şebnem Ferah", "Teoman"]},
    "model": {"mood": "indie_alternatif", "similar": ["Pera", "Madrigal", "Fatma Turgut", "Gripin", "Kolpa", "Dolu Kadehi Ters Tut", "Seksendört"]},
    "gripin": {"mood": "hard_rock_metal", "similar": ["Pera", "Model", "Manga", "Seksendört", "Kolpa", "Duman", "Zakkum", "Gökhan Türkmen"]},
    "seksendort": {"mood": "indie_alternatif", "similar": ["Pera", "Kolpa", "Gripin", "Zakkum", "Model", "Manga", "Emre Aydın"]},
    "kolpa": {"mood": "indie_alternatif", "similar": ["Pera", "Seksendört", "Gripin", "Zakkum", "Model", "Manga"]},
    "zakkum": {"mood": "indie_alternatif", "similar": ["Pera", "Seksendört", "Gripin", "Kolpa", "Model", "Feridun Düzağaç"]},
    "madrigal": {"mood": "indie_alternatif", "similar": ["Dolu Kadehi Ters Tut", "Pera", "Dedublüman", "Mavi Gri", "Yüzyüzeyken Konuşuruz", "Adamlar"]},
    "dolu kadehi ters tut": {"mood": "indie_alternatif", "similar": ["Madrigal", "Yüzyüzeyken Konuşuruz", "Adamlar", "Sedef Sebüktekin", "Kaan Boşnak"]},
    "adamlar": {"mood": "indie_alternatif", "similar": ["Mor ve Ötesi", "Büyük Ev Ablukada", "Son Feci Bisiklet", "Yaşlı Amca", "Duman", "Lalalar"]},
    "yuzyuzeyken konusuruz": {"mood": "indie_alternatif", "similar": ["Dolu Kadehi Ters Tut", "Madrigal", "Kaan Boşnak", "Dedublüman", "Son Feci Bisiklet"]},
    "yasli amca": {"mood": "indie_alternatif", "similar": ["Adamlar", "Son Feci Bisiklet", "Madrigal", "Dolu Kadehi Ters Tut"]},
    "son feci bisiklet": {"mood": "indie_alternatif", "similar": ["Adamlar", "Yaşlı Amca", "Büyük Ev Ablukada", "Yüzyüzeyken Konuşuruz"]},
    "dedubluman": {"mood": "huzunlu_slow", "similar": ["Madrigal", "Mavi Gri", "Pera", "Pinhani", "Canozan"]},
    "mavi gri": {"mood": "huzunlu_slow", "similar": ["Dedublüman", "Madrigal", "Pera", "Pinhani", "İki Kardesh"]},
    "teoman": {"mood": "indie_alternatif", "similar": ["Duman", "Şebnem Ferah", "Gripin", "Mor ve Ötesi", "Kaan Tangöze"]},
    "sebnem ferah": {"mood": "hard_rock_metal", "similar": ["Duman", "Mor ve Ötesi", "Hayko Cepkin", "Pentagram", "Teoman", "Manga"]},
    "hayko cepkin": {"mood": "hard_rock_metal", "similar": ["Pentagram", "Şebnem Ferah", "Manga", "Kurban", "Ogün Sanlısoy"]},
    "emre aydin": {"mood": "huzunlu_slow", "similar": ["Pera", "Seksendört", "Model", "Gripin", "Feridun Düzağaç"]},
    "fatma turgut": {"mood": "indie_alternatif", "similar": ["Model", "Pera", "Gripin", "Manga", "Şebnem Ferah"]},

    # Pop (Türkçe & Yabancı)
    "tarkan": {"mood": "neseli_pop", "similar": ["Edis", "Kenan Doğulu", "Murat Boz", "Gülşen", "Simge", "Mustafa Sandal"]},
    "edis": {"mood": "neseli_pop", "similar": ["Tarkan", "Murat Boz", "Aleyna Tilki", "Zeynep Bastık", "Mabel Matiz"]},
    "simge": {"mood": "neseli_pop", "similar": ["Edis", "Tarkan", "Gülşen", "Derya Uluğ", "İrem Derici"]},
    "gulsen": {"mood": "neseli_pop", "similar": ["Simge", "Tarkan", "Edis", "Hande Yener", "Demet Akalın"]},
    "mabel matiz": {"mood": "neseli_pop", "similar": ["Edis", "Tarkan", "Zeynep Bastık", "Buray", "Emir Can İğrek"]},
    "dua lipa": {"mood": "neseli_pop", "similar": ["The Weeknd", "Harry Styles", "Ariana Grande", "Taylor Swift", "Sabrina Carpenter"]},
    "the weeknd": {"mood": "neseli_pop", "similar": ["Dua Lipa", "Bruno Mars", "Post Malone", "Travis Scott", "Harry Styles"]},
    "taylor swift": {"mood": "neseli_pop", "similar": ["Olivia Rodrigo", "Sabrina Carpenter", "Ariana Grande", "Billie Eilish"]},

    # Hüzünlü & Melankolik Slow
    "sezen aksu": {"mood": "huzunlu_slow", "similar": ["Sıla", "Sertab Erener", "Kalben", "Levent Yüksel", "Toygar Işıklı"]},
    "sila": {"mood": "huzunlu_slow", "similar": ["Sezen Aksu", "Gökhan Türkmen", "Sertab Erener", "Kalben"]},
    "cem adrian": {"mood": "huzunlu_slow", "similar": ["Cihan Mürtezaoğlu", "Feridun Düzağaç", "Deniz Tekin", "Kalben", "Halil Sezai"]},
    "adele": {"mood": "huzunlu_slow", "similar": ["Sam Smith", "Lewis Capaldi", "Lana Del Rey", "Tom Odell", "James Arthur"]},
    "lana del rey": {"mood": "huzunlu_slow", "similar": ["Cigarettes After Sex", "Billie Eilish", "Phoebe Bridgers", "The Neighbourhood"]},
    "cigarettes after sex": {"mood": "huzunlu_slow", "similar": ["Lana Del Rey", "Beach House", "Tom Odell", "The Neighbourhood"]},

    # Rap & Hiphop / Spor
    "ezhel": {"mood": "rap_hiphop", "similar": ["Ceza", "Sagopa Kajmer", "Motive", "UZI", "BLOK3", "Ati242"]},
    "ceza": {"mood": "rap_hiphop", "similar": ["Sagopa Kajmer", "Ezhel", "Şanışer", "Defkhan", "Massaka"]},
    "sagopa kajmer": {"mood": "rap_hiphop", "similar": ["Ceza", "Kolera", "Şanışer", "Gazapizm"]},
    "lvbel c5": {"mood": "enerjik_spor", "similar": ["BLOK3", "UZI", "Çakal", "Batuflex", "Motive"]},
    "motive": {"mood": "enerjik_spor", "similar": ["UZI", "BLOK3", "Lvbel C5", "Ati242", "Ezhel"]},
    "uzi": {"mood": "enerjik_spor", "similar": ["BLOK3", "Motive", "Lvbel C5", "Çakal", "Ati242"]},
    "eminem": {"mood": "enerjik_spor", "similar": ["50 Cent", "Dr. Dre", "Travis Scott", "Kendrick Lamar", "Eminem"]},
    "travis scott": {"mood": "enerjik_spor", "similar": ["Metro Boomin", "21 Savage", "Drake", "Future", "Playboi Carti"]},
    "drake": {"mood": "rap_hiphop", "similar": ["Travis Scott", "Kendrick Lamar", "J. Cole", "Post Malone", "Future"]},

    # Sakin & Akustik
    "manus baba": {"mood": "sakin_akustik", "similar": ["Can Ozan", "Deniz Tekin", "Evdeki Saat", "Nilipek", "Birsen Tezer"]},
    "can ozan": {"mood": "sakin_akustik", "similar": ["Deniz Tekin", "Sedef Sebüktekin", "Nova Norda", "Evdeki Saat"]},
    "deniz tekin": {"mood": "sakin_akustik", "similar": ["Can Ozan", "Cihan Mürtezaoğlu", "Birsen Tezer", "Manuş Baba"]},
    "jack johnson": {"mood": "sakin_akustik", "similar": ["Jason Mraz", "Vance Joy", "Ben Howard", "Passenger", "Boyce Avenue"]},

    # Hard Rock & Metal (Global)
    "arctic monkeys": {"mood": "indie_alternatif", "similar": ["The Neighbourhood", "The Strokes", "Tame Impala", "Wallows", "Gorillaz"]},
    "the neighbourhood": {"mood": "indie_alternatif", "similar": ["Arctic Monkeys", "Chase Atlantic", "The 1975", "Lana Del Rey"]},
    "linkin park": {"mood": "hard_rock_metal", "similar": ["Bring Me The Horizon", "Evanescence", "Green Day", "System Of A Down", "Slipknot"]},
    "metallica": {"mood": "hard_rock_metal", "similar": ["Megadeth", "Iron Maiden", "Guns N' Roses", "Slipknot", "Rammstein"]},
    "green day": {"mood": "hard_rock_metal", "similar": ["Blink-182", "The Offspring", "Linkin Park", "My Chemical Romance"]},

    # Jazz / Blues
    "miles davis": {"mood": "jazz_blues", "similar": ["John Coltrane", "Chet Baker", "Bill Evans", "Thelonious Monk"]},
    "julide ozcelik": {"mood": "jazz_blues", "similar": ["Elif Çağlar", "İlhan Erşahin", "Kerem Görsev", "Karsu"]},
    "elif caglar": {"mood": "jazz_blues", "similar": ["Jülide Özçelik", "Karsu", "Kerem Görsev", "İlhan Erşahin"]},
    "karsu": {"mood": "jazz_blues", "similar": ["Jülide Özçelik", "Elif Çağlar", "Kerem Görsev"]},

    # Elektronik
    "mahmut orhan": {"mood": "elektronik_synth", "similar": ["Burak Yeter", "Deeperise", "İlkay Şencan", "Hey Douglas"]},
    "calvin harris": {"mood": "elektronik_synth", "similar": ["Avicii", "David Guetta", "Tiësto", "Kygo", "Swedish House Mafia"]},
}


def _norm_artist(name: str) -> str:
    import re
    charmap = {'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u', 'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'I': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'}
    for k, v in charmap.items():
        name = name.replace(k, v)
    name = re.sub(r'[^\w\s]', ' ', name).lower()
    return ' '.join(name.split())


def find_artist_info(artist_name: str) -> Optional[dict]:
    """Sanatçı adına göre duygu kategorisini ve benzer sanatçılar kümesini döner."""
    if not artist_name:
        return None
    target = _norm_artist(artist_name)
    if target in ARTIST_DIRECTORY:
        return ARTIST_DIRECTORY[target]

    # Kısmi eşleşme (örn: "Pera" in "Pera Grubu", "Duman" in "Kaan Tangöze (Duman)")
    for key, data in ARTIST_DIRECTORY.items():
        if key in target or target in key:
            return data
    return None

