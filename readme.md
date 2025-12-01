🧠 Mood AI: Yapay Zeka Destekli Müzik Terapisti

Bu proje, kullanıcının ruh halini analiz eden ve buna uygun, kişiselleştirilmiş müzik reçeteleri (Spotify Çalma Listeleri) hazırlayan yapay zeka destekli bir uygulamadır.

🚀 Özellikler

Psikolojik Analiz: Kullanıcının metin girdisini analiz ederek ruh halini ve yoğunluğunu tespit eder.

Akıllı Mikser: Indie, Rock, Rap, Caz gibi farklı türleri kullanıcının moduna göre harmanlar.

Spotify Entegrasyonu: Hazırlanan reçeteyi tek tıkla kullanıcının Spotify hesabına kaydeder.

Modern Arayüz: Streamlit ile geliştirilmiş, kontrol panelli web arayüzü.

🛠️ Kurulum

Repoyu klonlayın:

git clone [https://github.com/enesic/MoodAI.git](https://github.com/enesic/MoodAI.git)
cd MoodAI


Gerekli kütüphaneleri yükleyin:

pip install -r requirements.txt


.env dosyası oluşturun ve Spotify API anahtarlarınızı içine ekleyin:

SPOTIFY_CLIENT_ID=sizin_client_id
SPOTIFY_CLIENT_SECRET=sizin_client_secret


Uygulamayı başlatın:

streamlit run app.py


📜 Lisans

MIT License