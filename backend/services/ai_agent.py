import json
import re
import math
import random
from typing import Dict, List, Tuple
from google import genai
from backend.core.config import settings

# 9 Ana Kategori ve Alt Türler
ALT_TURLER = {
    "neseli_pop": ["Pop & Dans", "Disco & Retro Pop", "Yaz Hitleri", "K-Pop", "Latin Pop"],
    "huzunlu_slow": ["Slow & Balad", "Melankolik Slow", "Akustik Hüzün", "Piyano & Yağmur", "Kırık Kalpler"],
    "enerjik_spor": ["Workout & Motivasyon", "Yüksek BPM Trap", "Power Drill", "Club & Techno Hits"],
    "sakin_akustik": ["Lo-Fi Beats", "Akustik Gitar & Chill", "Soft Pop", "Coffeehouse Akustik", "Ambient & Dinginlik"],
    "indie_alternatif": ["Modern Indie Rock", "Dream Pop", "Shoegaze", "Alternatif Rock", "Bohem & Nostalji"],
    "hard_rock_metal": ["Klasik Rock", "Hard Rock", "Heavy Metal", "Nu-Metal", "Punk & Grunge"],
    "rap_hiphop": ["Modern Trap", "Old School & Boom Bap", "Melodik Rap", "Drill & Underground"],
    "jazz_blues": ["Smooth Jazz", "Vocal Jazz", "Blues & Soul", "Gece Mavisi Jazz"],
    "elektronik_synth": ["Synthwave & Neon", "Deep House", "Minimal Techno", "EDM & Festival"]
}

# ==============================================================================
# RUSSELL ÇEVRESEL DUYGU MODELİ (CIRCUMPLEX MODEL OF AFFECT)
# 2 Boyutlu Doğrusal Vektör Uzayı:
# - Valence (Duygusal Değerlik): -1.0 (Aşırı Negatif / Acı) <──> +1.0 (Aşırı Pozitif / Neşe)
# - Arousal (Uyarılma / Enerji Seviyesi): 0.0 (Durgun / Uyku) <──> 1.0 (Patlayıcı Enerji / Adrenalin)
# ==============================================================================

MOOD_VECTORS = {
    "huzunlu_slow":     {"valence": -0.85, "arousal": 0.20, "weight": 1.4},
    "sakin_akustik":    {"valence":  0.45, "arousal": 0.20, "weight": 1.2},
    "neseli_pop":       {"valence":  0.85, "arousal": 0.80, "weight": 1.3},
    "enerjik_spor":     {"valence":  0.40, "arousal": 0.95, "weight": 1.3},
    "hard_rock_metal":  {"valence": -0.65, "arousal": 0.90, "weight": 1.4},
    "indie_alternatif": {"valence": -0.20, "arousal": 0.40, "weight": 1.1},
    "rap_hiphop":       {"valence":  0.05, "arousal": 0.75, "weight": 1.2},
    "jazz_blues":       {"valence":  0.25, "arousal": 0.35, "weight": 1.1},
    "elektronik_synth": {"valence":  0.55, "arousal": 0.85, "weight": 1.2}
}

# Yoğunluk Çarpanları (Intensifiers & Dampeners)
INTENSIFIERS = {
    "cok": 1.4, "asiri": 1.8, "feci": 1.7, "asiri derecede": 2.0, "inanilmaz": 1.6,
    "delicesine": 1.9, "sonsuz": 1.5, "tamamen": 1.4, "darmadagin": 1.8, "mahvoldum": 1.9,
    "baya": 1.3, "bayagi": 1.3, "hic": 1.5, "asla": 1.6
}

DAMPENERS = {
    "biraz": 0.6, "azicik": 0.5, "hafif": 0.6, "sanki": 0.7, "gibi": 0.8
}

# 300+ Kelime & Deyim Sözlüğü ve Vektörel Karşılıkları
LEXICON = {
    # HÜZÜNLÜ / SLOW
    "uzgun": (-0.8, 0.2, "huzunlu_slow"), "aglamak": (-0.9, 0.4, "huzunlu_slow"),
    "agliyorum": (-0.95, 0.4, "huzunlu_slow"), "huzun": (-0.8, 0.2, "huzunlu_slow"),
    "huzunlu": (-0.8, 0.2, "huzunlu_slow"), "keder": (-0.85, 0.2, "huzunlu_slow"),
    "mutsuz": (-0.85, 0.2, "huzunlu_slow"), "mutsuzum": (-0.9, 0.2, "huzunlu_slow"),
    "melankoli": (-0.7, 0.3, "huzunlu_slow"), "yalniz": (-0.75, 0.15, "huzunlu_slow"),
    "yalnizim": (-0.8, 0.15, "huzunlu_slow"), "terk edildim": (-0.95, 0.3, "huzunlu_slow"),
    "ayrildik": (-0.9, 0.3, "huzunlu_slow"), "ayrilik": (-0.85, 0.3, "huzunlu_slow"),
    "ozledim": (-0.7, 0.25, "huzunlu_slow"), "canim aciyor": (-0.95, 0.35, "huzunlu_slow"),
    "depresif": (-0.85, 0.15, "huzunlu_slow"), "tukendim": (-0.9, 0.1, "huzunlu_slow"),
    "bittim": (-0.9, 0.1, "huzunlu_slow"), "bosluk": (-0.7, 0.1, "huzunlu_slow"),
    "kalbim kirik": (-0.95, 0.25, "huzunlu_slow"), "kirgin": (-0.75, 0.2, "huzunlu_slow"),
    "efkar": (-0.75, 0.3, "huzunlu_slow"), "efkarliyim": (-0.8, 0.3, "huzunlu_slow"),
    "damar": (-0.8, 0.35, "huzunlu_slow"), "dert": (-0.8, 0.3, "huzunlu_slow"),
    "hasret": (-0.7, 0.25, "huzunlu_slow"), "moralsiz": (-0.75, 0.2, "huzunlu_slow"),
    "umutsuz": (-0.85, 0.15, "huzunlu_slow"), "canim sikkin": (-0.75, 0.2, "huzunlu_slow"),
    "icim daraliyor": (-0.85, 0.3, "huzunlu_slow"), "berbat": (-0.85, 0.3, "huzunlu_slow"),
    "kotuyum": (-0.8, 0.2, "huzunlu_slow"), "caresiz": (-0.9, 0.2, "huzunlu_slow"),

    # NEŞELİ / POP
    "mutlu": (0.85, 0.75, "neseli_pop"), "mutluyum": (0.9, 0.8, "neseli_pop"),
    "neseli": (0.85, 0.75, "neseli_pop"), "keyifli": (0.8, 0.65, "neseli_pop"),
    "harika": (0.9, 0.8, "neseli_pop"), "mukemmel": (0.9, 0.8, "neseli_pop"),
    "super": (0.85, 0.8, "neseli_pop"), "dans": (0.85, 0.85, "neseli_pop"),
    "eglence": (0.85, 0.8, "neseli_pop"), "kutlama": (0.9, 0.85, "neseli_pop"),
    "parti": (0.85, 0.9, "neseli_pop"), "tatil": (0.8, 0.7, "neseli_pop"),
    "asik oldum": (0.95, 0.8, "neseli_pop"), "kelebekler": (0.85, 0.7, "neseli_pop"),
    "sevinc": (0.85, 0.75, "neseli_pop"), "kahkaha": (0.9, 0.85, "neseli_pop"),
    "modum yuksek": (0.85, 0.8, "neseli_pop"), "coskulu": (0.85, 0.9, "neseli_pop"),
    "hayat guzel": (0.9, 0.7, "neseli_pop"), "dopamin": (0.85, 0.8, "neseli_pop"),

    # ENERJİK / SPOR
    "spor": (0.4, 0.9, "enerjik_spor"), "gym": (0.4, 0.95, "enerjik_spor"),
    "fitness": (0.4, 0.9, "enerjik_spor"), "antrenman": (0.35, 0.9, "enerjik_spor"),
    "kosu": (0.4, 0.85, "enerjik_spor"), "tempo": (0.5, 0.85, "enerjik_spor"),
    "guc": (0.5, 0.95, "enerjik_spor"), "motivasyon": (0.6, 0.9, "enerjik_spor"),
    "pump": (0.4, 0.95, "enerjik_spor"), "adrenalin": (0.5, 1.0, "enerjik_spor"),
    "pes etmek yok": (0.6, 0.95, "enerjik_spor"), "bomba gibi": (0.7, 0.9, "enerjik_spor"),
    "canavar": (0.4, 0.95, "enerjik_spor"), "hirs": (0.3, 0.95, "enerjik_spor"),
    "enerji patlamasi": (0.6, 1.0, "enerjik_spor"), "sampiyon": (0.7, 0.95, "enerjik_spor"),

    # SAKİN / AKUSTİK
    "sakin": (0.5, 0.15, "sakin_akustik"), "sakinim": (0.5, 0.15, "sakin_akustik"),
    "huzur": (0.6, 0.1, "sakin_akustik"), "huzurlu": (0.6, 0.1, "sakin_akustik"),
    "dinlenmek": (0.4, 0.1, "sakin_akustik"), "rahat": (0.5, 0.15, "sakin_akustik"),
    "chill": (0.5, 0.2, "sakin_akustik"), "kitap": (0.4, 0.15, "sakin_akustik"),
    "kahve": (0.45, 0.2, "sakin_akustik"), "yagmur": (0.2, 0.2, "sakin_akustik"),
    "uyku": (0.3, 0.05, "sakin_akustik"), "lofi": (0.4, 0.2, "sakin_akustik"),
    "dingin": (0.5, 0.1, "sakin_akustik"), "sessizlik": (0.4, 0.1, "sakin_akustik"),
    "kafa dinleme": (0.45, 0.1, "sakin_akustik"), "meditasyon": (0.5, 0.05, "sakin_akustik"),
    "gevseme": (0.5, 0.1, "sakin_akustik"),

    # HARD ROCK / METAL
    "ofke": (-0.7, 0.95, "hard_rock_metal"), "ofkeliyim": (-0.75, 0.95, "hard_rock_metal"),
    "kizgin": (-0.65, 0.9, "hard_rock_metal"), "sinirli": (-0.65, 0.9, "hard_rock_metal"),
    "bagirmak": (-0.6, 0.9, "hard_rock_metal"), "cildirmak": (-0.7, 0.95, "hard_rock_metal"),
    "isyan": (-0.6, 0.9, "hard_rock_metal"), "kaos": (-0.6, 0.95, "hard_rock_metal"),
    "nefret": (-0.8, 0.9, "hard_rock_metal"), "patlamak": (-0.65, 0.95, "hard_rock_metal"),
    "metal": (-0.3, 0.9, "hard_rock_metal"), "distortion": (-0.3, 0.9, "hard_rock_metal"),
    "biktim": (-0.7, 0.7, "hard_rock_metal"), "tahammulum kalmadi": (-0.75, 0.85, "hard_rock_metal"),
    "yeter artik": (-0.7, 0.9, "hard_rock_metal"), "agresif": (-0.65, 0.95, "hard_rock_metal"),

    # İNDİE / ALTERNATİF
    "farkli": (0.1, 0.4, "indie_alternatif"), "ozgun": (0.2, 0.4, "indie_alternatif"),
    "bosver": (-0.1, 0.3, "indie_alternatif"), "uzaklasmak": (-0.2, 0.35, "indie_alternatif"),
    "kacmak": (-0.3, 0.45, "indie_alternatif"), "alternatif": (0.0, 0.45, "indie_alternatif"),
    "gece surusu": (0.1, 0.4, "indie_alternatif"), "yildizlar": (0.3, 0.3, "indie_alternatif"),
    "retro": (0.2, 0.4, "indie_alternatif"), "nostalji": (-0.2, 0.35, "indie_alternatif"),
    "hayalperest": (0.2, 0.35, "indie_alternatif"), "bohem": (0.1, 0.35, "indie_alternatif"),
    "akisina birak": (0.3, 0.25, "indie_alternatif"),

    # RAP / HIPHOP
    "sokak": (0.0, 0.7, "rap_hiphop"), "ritim": (0.4, 0.8, "rap_hiphop"),
    "beat": (0.4, 0.8, "rap_hiphop"), "flow": (0.4, 0.8, "rap_hiphop"),
    "rhyme": (0.3, 0.75, "rap_hiphop"), "trap": (0.2, 0.85, "rap_hiphop"),
    "drill": (0.0, 0.9, "rap_hiphop"), "underground": (0.0, 0.75, "rap_hiphop"),
    "gercekler": (-0.2, 0.65, "rap_hiphop"), "flex": (0.4, 0.75, "rap_hiphop"),

    # JAZZ / BLUES
    "caz": (0.3, 0.35, "jazz_blues"), "jazz": (0.3, 0.35, "jazz_blues"),
    "blues": (-0.2, 0.35, "jazz_blues"), "los": (0.2, 0.25, "jazz_blues"),
    "viski": (0.2, 0.3, "jazz_blues"), "sarap": (0.3, 0.3, "jazz_blues"),
    "zarif": (0.5, 0.3, "jazz_blues"), "saksofon": (0.3, 0.4, "jazz_blues"),
    "gece mavisi": (0.1, 0.3, "jazz_blues"), "derinlik": (0.1, 0.35, "jazz_blues"),

    # ELEKTRONİK / SYNTH
    "tekno": (0.5, 0.9, "elektronik_synth"), "techno": (0.5, 0.9, "elektronik_synth"),
    "rave": (0.6, 0.95, "elektronik_synth"), "neon": (0.5, 0.8, "elektronik_synth"),
    "cyberpunk": (0.3, 0.85, "elektronik_synth"), "synth": (0.5, 0.8, "elektronik_synth"),
    "futuristik": (0.4, 0.75, "elektronik_synth"), "dj": (0.6, 0.85, "elektronik_synth"),
    "drop": (0.5, 0.9, "elektronik_synth"), "edm": (0.6, 0.9, "elektronik_synth")
}

# Olumsuzluk Kalıpları
NEGATIONS = [
    "degil", "degilim", "yok", "istemiyorum", "sevmiyorum", "hissetmiyorum", "olmuyor"
]

DOCTOR_NOTES = {
    "neseli_pop": [
        "Işıl ışıl bir enerjin var! Dopamin seviyeni zirvede tutacak, adımlarını dansa çevirecek ritimler reçetene yazıldı.",
        "Bugün hayatın tadını çıkarma günü. Bu pozitif dalgayı kaybetmemek için ritmik ve neşeli parçalar seçtim."
    ],
    "huzunlu_slow": [
        "Bazen ruhun sadece durup duygularını yaşamaya ihtiyacı vardır. Yalnız olmadığını hissettirecek, yaralarına merhem olacak tınılar hazırladım.",
        "İçindeki ağırlığı sözlere ve melodilere dökme vakti. Bu melankolik ve derin şarkılar sana en sadık dert ortağı olacak."
    ],
    "enerjik_spor": [
        "Nabzın yükselsin, hedeflerine giden yolda seni hiçbir şey durduramasın! Yüksek tempolu ve güç aşılayan bir motivasyon listesi hazır.",
        "Sınırlarını aşmaya hazır görünüyorsun. Adrenalin seviyeni tepeye çıkaracak dinamik bir müzik reçetesi yazdım."
    ],
    "sakin_akustik": [
        "Dünyanın tüm gürültüsünü dışarıda bırakıp derin bir nefes alma zamanı. Zihnini dinlendirecek huzurlu melodiler seçtim.",
        "Kortizol seviyeni düşürecek, bir fincan kahve veya kitap eşliğinde ruhunu dinlendirecek akustik frekanslar hazır."
    ],
    "hard_rock_metal": [
        "İçinde biriken öfkeyi kontrollü bir enerjiye dönüştürelim. Bırak distortion ve gitarlar senin yerine haykırsın!",
        "Sessiz kalmak zorunda değilsin. Ruhundaki ateşi serbest bırakacak sert tınılar reçetene eklendi."
    ],
    "indie_alternatif": [
        "Sıradan kalıplardan uzak, özgür ve kendine has bir ruh hali seziyorum. Sana özel alternatif ve derin tınılar seçtim.",
        "Kendi iç dünyana sanatsal bir yolculuk yapman için özgün ve bağımsız melodiler hazırladım."
    ],
    "rap_hiphop": [
        "Sözlerin gücüne ve sokakların ritmine ihtiyacın var. Gerçeklerle yüzleşirken sana güç katacak beat'ler hazır.",
        "Mücadeleci ruhunu besleyecek, her satırında kararlılık bulacağın bir seçki oluşturdum."
    ],
    "jazz_blues": [
        "Ruhun biraz zarafet, loş ışıklar ve derinlik arıyor. Geceye ve duygularına asilce eşlik edecek melodiler seçtim.",
        "Günün yorgunluğunu kaliteli bir tınıyla taçlandırıyoruz. Saksofon ve piyanonun büyüsüne bırak kendini."
    ],
    "elektronik_synth": [
        "Geleceğin ritimleri ve neon frekanslar zihnini tazeleyecek. Dijital ses dalgalarıyla modunu yükseltelim!",
        "Kendini müziğin hipnotik akışına bırak. Elektronik dünyanın enerjisi sana iyi gelecek."
    ]
}

def to_ascii_normalize(text: str) -> str:
    """Türkçe ve ASCII karakterleri tam uyumlu küçük harf ve noktalama temizliğine tabi tutar."""
    charmap = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'c', 'Ğ': 'g', 'İ': 'i', 'I': 'i', 'Ö': 'o', 'Ş': 's', 'Ü': 'u'
    }
    for k, v in charmap.items():
        text = text.replace(k, v)
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)
    return ' '.join(text.split())

def calculate_linear_mood_vector(user_text: str) -> Tuple[float, float, Dict[str, float]]:
    """
    Doğrusal Vektör Analizi:
    Cümledeki kelimelerin Valence (X) ve Arousal (Y) koordinatlarını, yoğunluk çarpanları ve
    olumsuzluk terslemeleriyle ağırlıklı ortalama alarak hesaplar.
    """
    norm_text = to_ascii_normalize(user_text)
    words = norm_text.split()
    
    total_weight = 0.0
    weighted_valence = 0.0
    weighted_arousal = 0.0
    category_votes: Dict[str, float] = {m: 0.0 for m in MOOD_VECTORS}
    
    has_negation_context = False
    current_multiplier = 1.0

    for i, word in enumerate(words):
        # Yoğunluk Çarpanı Kontrolü
        if word in INTENSIFIERS:
            current_multiplier = INTENSIFIERS[word]
            continue
        elif word in DAMPENERS:
            current_multiplier = DAMPENERS[word]
            continue
            
        # Olumsuzluk Tespiti
        if word in NEGATIONS:
            has_negation_context = True
            continue

        # Çok kelimeli deyim kontrolü (2'li ngram)
        bigram = f"{words[i-1]} {word}" if i > 0 else ""
        matched_key = None
        
        if bigram in LEXICON:
            matched_key = bigram
        elif word in LEXICON:
            matched_key = word
            
        if matched_key:
            val, aro, cat = LEXICON[matched_key]
            
            # Olumsuzluk etkisi: Pozitifse negatife çek, enerjiyi düşür
            if has_negation_context:
                if val > 0:
                    val = -abs(val) * 0.9
                    aro = max(0.15, aro * 0.5)
                    cat = "huzunlu_slow"
                has_negation_context = False # Tüketildi
                
            weight = current_multiplier * 1.5
            weighted_valence += val * weight
            weighted_arousal += aro * weight
            total_weight += weight
            category_votes[cat] += weight
            
            # Çarpanı sıfırla
            current_multiplier = 1.0

    # Varsayılan nötr koordinat
    if total_weight == 0.0:
        return 0.2, 0.25, category_votes
        
    final_valence = max(-1.0, min(1.0, weighted_valence / total_weight))
    final_arousal = max(0.0, min(1.0, weighted_arousal / total_weight))
    return final_valence, final_arousal, category_votes

def analyze_mood_local(user_text: str) -> dict:
    """
    Doğrusal Öklid Uzayı ve Vektör Mesafesi Tabanlı Kararlı NLP Motoru.
    """
    u_val, u_aro, votes = calculate_linear_mood_vector(user_text)
    
    # 9 Duygu Noktasına Olan Öklid Mesafesini Hesapla
    # Distance = sqrt((v_user - v_target)^2 + (a_user - a_target)^2)
    scores: Dict[str, float] = {}
    for mood, data in MOOD_VECTORS.items():
        dist = math.sqrt((u_val - data["valence"])**2 + (u_aro - data["arousal"])**2)
        # Mesafeyi yakınlık skoruna dönüştür (Yakın olan yüksek puan alır)
        proximity_score = (1.0 / (dist + 0.15)) * data["weight"]
        # Sözlük doğrudan oy vermişse ek güven puanı
        vote_bonus = votes.get(mood, 0.0) * 1.2
        scores[mood] = proximity_score + vote_bonus

    best_mood = max(scores, key=scores.get)
    doctor_note = random.choice(DOCTOR_NOTES.get(best_mood, DOCTOR_NOTES["sakin_akustik"]))
    suggested_genres = random.sample(ALT_TURLER[best_mood], min(3, len(ALT_TURLER[best_mood])))

    return {
        "mood": best_mood,
        "doktor_notu": doctor_note,
        "suggested_genres": suggested_genres,
        "valence": round(u_val, 2),
        "arousal": round(u_aro, 2),
        "engine": "linear_vector_space_nlp"
    }

from concurrent.futures import ThreadPoolExecutor, TimeoutError

def _call_gemini(prompt: str) -> dict:
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
    )
    text = response.text.strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    if text.startswith('```json'):
        text = text[7:]
    elif text.startswith('```'):
        text = text[3:]
    if text.endswith('```'):
        text = text[:-3]
    return json.loads(text.strip())

def analyze_mood(user_text: str) -> dict:
    """Hibrit Analiz: Gemini LLM denenir, gecikme veya API yokluğunda Doğrusal Vektör NLP motoruna düşer."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
        return analyze_mood_local(user_text)

    prompt = f"""
Sen uzman ve analitik bir Müzik Terapistisin. Kullanıcının iç döküşünü analiz et:
"{user_text}"

Aşağıdaki 9 kategoriden Russell Çevresel Duygu Modeline (Valence/Arousal) göre en uygun KESİN BİR kategoriyi seç:
- neseli_pop (Pozitif, yüksek enerji, dans, parti)
- huzunlu_slow (Negatif, düşük enerji, melankoli, yalnızlık, dert)
- enerjik_spor (Yüksek enerji, motivasyon, antrenman, güç)
- sakin_akustik (Pozitif/Nötr, düşük enerji, chill, huzur, kahve)
- hard_rock_metal (Negatif, yüksek enerji, öfke, isyan, sert)
- indie_alternatif (Derin düşünce, gece yürüyüşü, bohem, özgün)
- rap_hiphop (Ritmik, sözlerin gücü, sokak, beat)
- jazz_blues (Zarif, loş ışıklar, gece mavisi, saksafon)
- elektronik_synth (Neon, rave, tekno, fütüristik)

Seçtiğin kategoriye göre YALNIZCA o kategoriye ait tür listesinden en uygun 2-3 adet alt tür seç:
{json.dumps(ALT_TURLER, ensure_ascii=False, indent=2)}

Kullanıcıya özel 2 cümlelik empatik Türkçe bir "doktor_notu" yaz.

Sadece geçerli bir JSON döndür:
{{
    "mood": "kategori_adi",
    "doktor_notu": "Kullanıcıya özel terapist notu...",
    "suggested_genres": ["Alt Tür 1", "Alt Tür 2"]
}}
"""

    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_gemini, prompt)
            data = future.result(timeout=4.0)

        mood = data.get("mood")
        if mood in ALT_TURLER:
            valid_genres = ALT_TURLER[mood]
            genres = [g for g in data.get("suggested_genres", []) if g in valid_genres]
            if not genres:
                genres = random.sample(valid_genres, min(3, len(valid_genres)))
            
            return {
                "mood": mood,
                "doktor_notu": data.get("doktor_notu", "Sana özel müzik reçetesi hazırlandı."),
                "suggested_genres": genres,
                "engine": "gemini_2.5_flash"
            }

        return analyze_mood_local(user_text)

    except Exception:
        return analyze_mood_local(user_text)
