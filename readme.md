Mood AI: Yapay Zeka Destekli Müzik Terapisti

Mood AI, kullanıcının ruh halini ve duygusal durumunu analiz ederek, Spotify API entegrasyonu aracılığıyla kişiselleştirilmiş müzik reçeteleri (çalma listeleri) oluşturan web tabanlı bir uygulamadır.

Proje Hakkında

Bu proje, doğal dil işleme (NLP) tekniklerini ve müzik platformu entegrasyonlarını birleştirerek kullanıcılarına terapötik bir müzik deneyimi sunmayı amaçlar. Kullanıcının metin tabanlı girdilerini analiz eden sistem, duygu durumunu tespit eder ve bu duruma en uygun frekanstaki şarkıları belirleyerek dinamik bir çalma listesi hazırlar.

Temel Özellikler

Gelişmiş Duygu Analizi: Kullanıcının girdiği metni analiz ederek ruh halini (Hüzünlü, Enerjik, Sakin vb.) tespit eden hibrit analiz motoru.

Akıllı Müzik Seçimi: Tespit edilen moda uygun olarak Spotify veritabanından dinamik şarkı taraması ve filtreleme.

Kişiselleştirilebilir Parametreler: Kullanıcılar şarkı sayısını, enerji seviyesini (Düşük/Yüksek tempo) ve dil tercihini (Türkçe/Yabancı) özelleştirebilir.

Spotify Entegrasyonu: OAuth 2.0 protokolü ile güvenli kullanıcı girişi ve oluşturulan listelerin doğrudan kullanıcı hesabına kaydedilmesi.

Dinamik İçerik Üretimi: Analiz sonucuna göre kullanıcıya özel "Doktor Notu" ve paylaşılabilir görsel durum kartları (Mood Card) oluşturma.

Kullanılan Teknolojiler

Programlama Dili: Python

Web Framework: Streamlit

API Entegrasyonu: Spotify Web API (Spotipy Kütüphanesi)

Veri İşleme: Pandas, NumPy

Görüntü İşleme: Pillow (PIL)

HTTP İstekleri: Requests

Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için aşağıdaki adımları izleyebilirsiniz.

Repoyu Klonlayın:

git clone [https://github.com/enesic/MoodAI.git](https://github.com/enesic/MoodAI.git)
cd MoodAI


Gerekli Kütüphaneleri Yükleyin:

pip install -r requirements.txt


Ortam Değişkenlerini Ayarlayın:
.env dosyası oluşturarak Spotify API anahtarlarınızı tanımlayın.

SPOTIFY_CLIENT_ID=sizin_client_id
SPOTIFY_CLIENT_SECRET=sizin_client_secret


Uygulamayı Başlatın:

streamlit run app.py


Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için LICENSE dosyasına bakabilirsiniz.