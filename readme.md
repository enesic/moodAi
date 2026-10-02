# 🧠 Mood AI: Yapay Zeka Destekli Müzik Terapisti

Mood AI, kullanıcının iç döküşünü ve duygu durumunu analiz ederek, Spotify API entegrasyonu aracılığıyla kişiselleştirilmiş müzik reçeteleri ve paylaşılabilir Instagram Story formatında terapi kartları oluşturan modern bir web uygulamasıdır.

---

## 🌟 Öne Çıkan Özellikler

- 🩺 **Hibrit Duygu Analiz Motoru:** Google Gemini 2.5 Flash LLM ve 250+ Türkçe deyim/kelime içeren sıfır maliyetli kural tabanlı yerel NLP motoru.
- 🚀 **Misafir Modu (Guest Mode):** Spotify hesabı bağlamadan da anında ruh hali analizi yapabilme ve müzik listesini keşfedebilme.
- 🎵 **Spotify Entegrasyonu:** OAuth 2.0 ile giriş, dinamik şarkı taraması, şarkı değiştirme (replace) ve tek tıkla doğrudan Spotify kütüphanesine liste kaydetme.
- ☕ **Hızlı Duygu Seçimleri (Mood Chips):** Sakin, efkar, motivasyon, kutlama gibi hazır şablonlar ile hızlı analiz.
- 📸 **9:16 Instagram Story & Durum Kartı:** Pillow ile üretilen yüksek çözünürlüklü (1080x1920) görsel terapi kartı indirme.
- ⚡ **Kalıcı Oturum:** Sayfa yenilendiğinde kaybolmayan `localStorage` desteği.

---

## 🛠️ Teknoloji Yığını

- **Backend:** Python 3.10+, FastAPI, Uvicorn, Spotipy (Spotify Web API), Google GenAI SDK, Pillow (PIL), Pydantic Settings
- **Frontend:** React 19, Vite, Tailwind CSS v4
- **Dağıtım (0 TL):** Render.com (Backend API) + Vercel (Frontend SPA)

---

## 🚀 Yerel Geliştirme (Local Setup)

### 1. Backend Kurulumu

```bash
# Backend dizininde sanal ortam oluşturun ve bağımlılıkları yükleyin
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

`backend/.env` dosyanızı oluşturun:
```env
SPOTIFY_CLIENT_ID=spotify_dashboard_client_id
SPOTIFY_CLIENT_SECRET=spotify_dashboard_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/api/callback
GEMINI_API_KEY=google_ai_studio_api_key
FRONTEND_URL=http://localhost:5173
```

Backend'i başlatın:
```bash
python main.py
```
> API `http://localhost:8000` üzerinde çalışacaktır. Swagger dökümantasyonu: `http://localhost:8000/docs`

---

### 2. Frontend Kurulumu

```bash
cd frontend
npm install
npm run dev
```
> Uygulama `http://localhost:5173` adresinde açılacaktır.

---

## 🌐 0 TL (Sıfır Maliyetli) Canlıya Alma Rehberi

### Adım 1: Spotify Developer Dashboard Ayarları
1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard) adresine gidin.
2. Uygulamanızın ayarlarına girin (**Edit Settings**).
3. **Redirect URIs** bölümüne hem yerel hem canlı adresinizi ekleyin:
   - `http://localhost:8000/api/callback`
   - `https://<YOUR_RENDER_BACKEND_URL>.onrender.com/api/callback`

---

### Adım 2: Backend'i Render.com'a Deploy Etme (Ücretsiz)
1. [Render.com](https://render.com) üzerinde ücretsiz hesap açın ve **New Web Service** seçin.
2. GitHub reponuzu bağlayın.
3. Ayarları yapılandırın:
   - **Environment:** `Python`
   - **Build Command:** `pip install -r backend/requirements.txt`
   - **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. **Environment Variables** bölümüne şunları ekleyin:
   - `SPOTIFY_CLIENT_ID`
   - `SPOTIFY_CLIENT_SECRET`
   - `SPOTIFY_REDIRECT_URI` -> `https://<YOUR_RENDER_BACKEND_URL>.onrender.com/api/callback`
   - `GEMINI_API_KEY`
   - `FRONTEND_URL` -> `https://<YOUR_VERCEL_APP>.vercel.app`

---

### Adım 3: Frontend'i Vercel'e Deploy Etme (Ücretsiz)
1. [Vercel.com](https://vercel.com) üzerinde **Add New Project** seçeneği ile GitHub reponuzu seçin.
2. **Root Directory** olarak `frontend` seçin.
3. **Environment Variables** alanına ekleyin:
   - `VITE_API_URL` -> `https://<YOUR_RENDER_BACKEND_URL>.onrender.com`
4. **Deploy** butonuna basın.

Tebrikler! Mood AI uygulamanız tamamen ücretsiz bir şekilde canlıda yayında. 🚀

---

## 📄 Lisans
Bu proje [MIT Lisansı](LICENSE) ile lisanslanmıştır.