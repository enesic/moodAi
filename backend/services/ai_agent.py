import json
import re
import random
from typing import Dict, List, Tuple
from google import genai
from backend.core.config import settings

# 9 Ana Kategori ve Alt Türler
ALT_TURLER = {
    "neseli_pop": ["Türkçe Pop Hareketli", "Yaz Hitleri", "Dance Pop", "Road Trip", "Serdar Ortaç Pop", "90'lar Türkçe Pop", "Disco", "K-Pop", "Reggaeton"],
    "huzunlu_slow": ["Akustik Hüzün", "Melankolik Indie", "Slow Pop", "Piyano & Yağmur", "Türkçe Damar", "Alternatif Balad", "Türkü", "Arabesk", "Kırık Kalpler"],
    "enerjik_spor": ["Spor Motivasyon", "Türkçe Rap", "Phonk", "Drill", "Techno", "House", "Gym Hits", "Power Workout", "Remix"],
    "sakin_akustik": ["Lo-Fi Beats", "Chill Pop", "Akustik Cover", "Jazz Vibes", "Enstrümantal", "Kitap Okuma", "Kahve Modu", "Ambient", "Soft Rock", "Sufi/Ney"],
    "indie_alternatif": ["Alternatif Rock", "Yeni Nesil Indie", "Anadolu Rock", "Shoegaze", "Soft Indie", "Bağımsız Müzik", "Dream Pop"],
    "hard_rock_metal": ["Türkçe Rock", "Anadolu Rock", "Heavy Metal", "Nu-Metal", "Hard Rock", "Punk", "Garage Rock"],
    "rap_hiphop": ["Türkçe Rap", "Old School", "Melodic Rap", "Trap", "Arabesk Rap", "Drill", "Underground"],
    "jazz_blues": ["Smooth Jazz", "Gece Mavisi", "Blues Rock", "Soul", "Vocal Jazz", "Türkçe Caz", "Coffee Table Jazz"],
    "elektronik_synth": ["Synthwave", "Cyberpunk", "Deep House", "Minimal Techno", "EDM", "Daft Punk Vibe"]
}

# 250+ Kapsamlı Türkçe Duygu, Durum, Argo ve Deyim Sözlüğü (Yerel Sıfır Maliyetli Motor)
EMOTION_DATASET = {
    "huzunlu_slow": {
        "keywords": [
            "üzgün", "üzgünüm", "ağlamak", "ağlıyorum", "hüzün", "hüzünlü", "keder", "kederli", "mutsuz",
            "mutsuzum", "mutsuzluk", "melankoli", "melankolik", "yalnız", "yalnızım", "terk edildim",
            "ayrıldık", "ayrılık", "özledim", "özlem", "canım acıyor", "depresif", "depresyondayım",
            "tükendim", "bittim", "darmadağın", "içim acıyor", "boşluk", "tavanı izliyorum", "kalbim kırık",
            "kırgın", "kırgınım", "yaram var", "efkar", "efkarlıyım", "rakı", "damar", "dert", "dertli",
            "sızı", "gözyaşı", "gözyaşları", "unutamadım", "hasret", "bunalım", "bunalımdayım",
            "hayat bitti", "hiçbir şey istemiyorum", "karanlık", "vazgeçtim", "yıkıldım", "acı",
            "keyifsiz", "keyifsizim", "huzursuz", "huzursuzum", "moralsiz", "moralsizim", "umutsuz",
            "umutsuzum", "isteksiz", "tatsız", "tatsızım", "hevesim yok", "hevesim kaçtı", "canım sıkkın",
            "içim daralıyor", "içim sıkılıyor", "içim kan ağlıyor", "berbat", "berbatım", "kötü", "kötüyüm",
            "ağlamaklı", "çaresiz", "çaresizim", "yalnızlık", "acı çekiyorum", "kalp kırıklığı", "yasta"
        ],
        "weight": 1.5
    },
    "neseli_pop": {
        "keywords": [
            "mutlu", "mutluyum", "neşeli", "neşeliyim", "keyifli", "keyifliyim", "harika", "mükemmel",
            "süper", "bomba", "dans", "eğlence", "eğleniyorum", "pozitif", "enerji", "cıvıl cıvıl",
            "gülmek", "gülüyorum", "kutlama", "parti", "yıkılıyor", "keyfim yerinde", "yaz geldi",
            "tatil", "güneş", "aşık oldum", "kelebekler", "sevinç", "sevinçli", "kahkaha",
            "modum yüksek", "bayram", "şenlik", "heyecanlı", "coşkulu", "parlıyorum", "fıkır fıkır",
            "hayat güzel", "çılgın", "şen", "dopamin", "gözlerimin içi gülüyor", "şanslıyım", "bayıldım"
        ],
        "weight": 1.2
    },
    "enerjik_spor": {
        "keywords": [
            "spor", "gym", "fitness", "antrenman", "koşu", "hız", "tempo", "güç", "motivasyon",
            "rekor", "bas", "pump", "kardiyo", "ağırlık", "adrenalin", "fit", "savaş", "yüksel",
            "pes etmek yok", "ter dökmek", "patlama", "bomba gibi", "canavar", "odaklan", "dinamik",
            "güçlü", "hırslı", "hırs", "koşuyorum", "enerji patlaması", "limitleri zorla", "ateş",
            "canlan", "yıkıp geç", "şampiyon", "bastır"
        ],
        "weight": 1.3
    },
    "sakin_akustik": {
        "keywords": [
            "sakin", "sakinim", "huzur", "huzurlu", "huzurluyum", "dinlenmek", "dinleniyorum",
            "rahat", "rahatladım", "chill", "kitap", "kahve", "yağmur", "şömine", "battaniye",
            "pencere kenarı", "uyku", "uyumak", "lofi", "soft", "dingin", "sessizlik", "kafa dinleme",
            "mola", "nefes almak", "doğa", "orman", "deniz sesi", "sahil yürüyüşü", "yorgunluk atmak",
            "çay", "ılık", "hafif", "akşamüstü", "meditasyon", "gevşeme", "yavaş"
        ],
        "weight": 1.1
    },
    "hard_rock_metal": {
        "keywords": [
            "öfke", "öfkeliyim", "kızgın", "kızgınım", "sinirli", "sinirliyim", "bağırmak", "çıldırmak",
            "delirmek", "isyan", "isyan etmek", "kaos", "nefret", "kırıp dökmek", "patlamak", "sert",
            "metal", "gitar", "bıktım", "tahammülüm kalmadı", "sitem", "deliye döndüm", "çıldırtmayın",
            "yeter artık", "baskı", "stres", "agresif", "volkan", "patlayacağım", "çığlık",
            "kan beynime sıçradı", "sinir krizi", "delirdim"
        ],
        "weight": 1.4
    },
    "indie_alternatif": {
        "keywords": [
            "farklı", "özgün", "boşver", "uzaklaşmak", "kaçmak", "sanat", "alternatif", "hipster",
            "bağımsız", "yolculuk", "gece sürüşü", "yıldızlar", "retro", "vintage", "derin",
            "düşünceli", "hayal", "hayalperest", "gece yürüyüşü", "şehir ışıkları", "nostalji",
            "kendi halimde", "şiir", "bohem", "içe dönük", "soyut", "akışına bırak"
        ],
        "weight": 1.1
    },
    "rap_hiphop": {
        "keywords": [
            "sokak", "mahalle", "ritim", "beat", "flow", "para", "sistem", "mücadele", "gerçekler",
            "rhyme", "trap", "drill", "underground", "araba", "gang", "flex", "tarz",
            "sokaklar", "yaşam savaşı", "laf sokma", "hesaplaşma", "kazanmak", "zirve"
        ],
        "weight": 1.1
    },
    "jazz_blues": {
        "keywords": [
            "caz", "jazz", "blues", "gece", "loş", "viski", "şarap", "zarif", "sofistike", "klasik",
            "piyano", "saksofon", "plak", "gece mavisi", "yağmurlu gece", "retro bar", "nostaljik",
            "asil", "derinlik", "ruh", "melodi", "eski zamanlar", "büyüleyici"
        ],
        "weight": 1.1
    },
    "elektronik_synth": {
        "keywords": [
            "tekno", "techno", "rave", "festival", "neon", "cyberpunk", "synth", "fütüristik",
            "kulüp", "dj", "dans pisti", "lazer", "uzay", "kopmalık", "gece kulübü", "baslar",
            "elektronik", "drop", "trans", "after party"
        ],
        "weight": 1.1
    }
}

# Olumsuzluk & Zıtlık Kalıpları (Pozitif kelimeleri negate edip hüzne yönlendirir)
NEGATION_PHRASES = [
    "mutlu değil", "mutlu değilim", "iyi değil", "iyi değilim", "keyfim yok",
    "huzurlu değil", "neşeli değil", "güzel değil", "tatsız", "hevesim yok",
    "moralim bozuk", "moralim sıfır", "canım istemiyor", "hiç iyi hissetmiyorum",
    "hiç mutlu değilim", "hiç neşem yok", "sevmiyorum", "istemiyorum"
]

DOCTOR_NOTES = {
    "neseli_pop": [
        "Işıl ışıl bir enerjin var! Dopamin seviyeni zirvede tutacak, adımlarını dansa çevirecek ritimler reçetene yazıldı.",
        "Bugün hayatın tadını çıkarma günü. Bu pozitif dalgayı kaybetmemek için ritmik ve neşeli parçalar seçtim."
    ],
    "huzunlu_slow": [
        "Bazen ruhun sadece durup duygularını yaşamaya ihtiyacı vardır. Yalnız olmadığını hissettirecek, yaralarına merhem olacak tınılar hazırladım.",
        "İçindeki ağırlığı sözlere ve melodilere dökme vakti. Bu melankolik ve derin şarkılar sana en sadık dert ortağı olacak.",
        "Duygusal bir deşarj ihtiyacı seziyorum. Ağır tınılar ve dokunaklı melodilerle bu anı birlikte atlatacağız."
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
        "İçinde biriken öfkeyi veya isyanı kontrollü bir enerjiye dönüştürelim. Bırak distortion ve gitarlar senin yerine haykırsın!",
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

def analyze_mood_local(user_text: str) -> dict:
    """Tam tutarlı, olumsuzluk duyarlı ve Türkçe/İngilizce klavye uyumlu yerel NLP motoru."""
    norm_text = to_ascii_normalize(user_text)
    tokens = set(norm_text.split())
    scores: Dict[str, float] = {mood: 0.0 for mood in EMOTION_DATASET}
    
    # 1. Olumsuzluk Kontrolü ("mutlu değilim", "iyi değilim", "keyfim yok", "daralıyor" vb.)
    has_negation = False
    for phrase in NEGATION_PHRASES:
        norm_phrase = to_ascii_normalize(phrase)
        if norm_phrase in norm_text:
            has_negation = True
            scores["huzunlu_slow"] += 8.0

    # 2. Tam Kelime ve Deyim Eşleşmesi
    for mood, data in EMOTION_DATASET.items():
        # Olumsuz bir duygu varsa pozitif kategorileri tamamen engelle!
        if has_negation and mood in ("neseli_pop", "sakin_akustik"):
            continue

        weight = data["weight"]
        for kw in data["keywords"]:
            norm_kw = to_ascii_normalize(kw)
            
            # Çok kelimeli deyim mi yoksa tek kelime mi?
            if " " in norm_kw:
                # Deyim tam cümle içinde geçiyor mu?
                if norm_kw in norm_text:
                    scores[mood] += 3.5 * weight
            else:
                # Tek kelime: Tam kelime olarak tokens içinde var mı? ("mutlu" -> "mutsuz" ile ÇAKIŞMAZ!)
                if norm_kw in tokens:
                    scores[mood] += 2.0 * weight
                    
    # En yüksek puanı alan modu belirle
    best_mood = max(scores, key=scores.get)
    
    # Hiçbir kelime eşleşmediyse varsayılan 'sakin_akustik'
    if scores[best_mood] == 0.0:
        best_mood = "sakin_akustik"
        doctor_note = "Bugün biraz nötr veya karmaşık hissediyor olabilirsin. Zihnini dinlendirecek ve sana iyi gelecek sakinleştirici bir reçete hazırladım."
    else:
        doctor_note = random.choice(DOCTOR_NOTES.get(best_mood, DOCTOR_NOTES["sakin_akustik"]))
        
    # KESİN KATEGORİ İZOLASYONU: Sadece o moda ait alt türler
    suggested_genres = random.sample(ALT_TURLER[best_mood], min(3, len(ALT_TURLER[best_mood])))
    
    return {
        "mood": best_mood,
        "doktor_notu": doctor_note,
        "suggested_genres": suggested_genres,
        "engine": "local_nlp_dataset"
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
    """Hibrit Analiz: Önce Gemini LLM dener (4s timeout), hata veya gecikmede Gelişmiş Yerel NLP'ye geçer."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("your_"):
        return analyze_mood_local(user_text)

    prompt = f"""
Sen uzman ve empatik bir Müzik Terapistisin. Kullanıcının paylaştığı şu iç döküşü analiz et:
"{user_text}"

Aşağıdaki 9 ana kategoriden kullanıcının duygusuna KESİN olarak en uygun BİR TANESİNİ seç:
- neseli_pop (Mutlu, neşeli, kutlama, dans, parti, enerjik pozitif)
- huzunlu_slow (Mutsuz, üzgün, kırgın, ayrılık, keder, yalnızlık, dert, efkar)
- enerjik_spor (Spor, antrenman, koşu, motivasyon, yüksek tempo, güç)
- sakin_akustik (Huzur, dinlenme, chill, kitap, kahve, doğa, meditasyon)
- hard_rock_metal (Öfke, sinir, isyan, nefret, patlama, sert)
- indie_alternatif (Farklı, özgün, gece yürüyüşü, nostalji, soyut, bohem)
- rap_hiphop (Sokak, beat, mücadele, sözlerin gücü, trap)
- jazz_blues (Gece, şarap, piyano, caz, loş ışıklar, zarafet)
- elektronik_synth (Rave, tekno, neon, fütüristik, elektronik)

DİKKAT:
- "mutsuz", "keyifsiz", "kötüyüm", "üzgünüm" gibi ifadeler KESİNLİKLE 'huzunlu_slow' kategorisine girmelidir.
- "mutlu değilim" gibi olumsuzluk kalıpları pozitif kategorilere değil 'huzunlu_slow' kategorisine girmelidir.

Seçtiğin kategoriye göre YALNIZCA o kategoriye ait tür listesinden en uygun 2-3 adet alt tür seç:
{json.dumps(ALT_TURLER, ensure_ascii=False, indent=2)}

Kullanıcıya samimi, empatik, terapötik ve doğrudan yazdığı duruma atıfta bulunan 2 cümlelik Türkçe bir "doktor_notu" yaz.

Sadece geçerli bir JSON formatında yanıt ver:
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

        # Doğrulama ve Kategori İzolasyonu
        mood = data.get("mood")
        if mood in ALT_TURLER:
            valid_genres = ALT_TURLER[mood]
            # Alt türlerin yalnızca o moda ait olduğundan emin ol
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

    except TimeoutError:
        print("Gemini API zaman aşımına uğradı (4s), yerel NLP motoruna geçildi.")
        return analyze_mood_local(user_text)
    except Exception as e:
        print(f"Gemini API uyarısı (Yerel NLP motoruna geçiliyor): {e}")
        return analyze_mood_local(user_text)

