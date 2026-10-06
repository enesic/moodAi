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
