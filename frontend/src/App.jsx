import React, { useState, useEffect, useCallback } from 'react';
import Login from './components/Login';
import ChatBox from './components/ChatBox';
import MoodCard from './components/MoodCard';
import Playlist from './components/Playlist';
import {
  getMeta,
  getStoredAuth,
  setStoredAuth,
  clearStoredAuth,
  refreshAccessToken,
} from './api/client';

function App() {
  const [auth, setAuth] = useState(() => getStoredAuth());
  const [isGuest, setIsGuest] = useState(() => localStorage.getItem('moodai_guest') === 'true');
  const [meta, setMeta] = useState(null);

  const [analysisResult, setAnalysisResult] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [searchParams, setSearchParams] = useState(null);

  // Reçete Geçmişi & Russell Modal
  const [history, setHistory] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('moodai_history') || '[]');
    } catch (_) {
      return [];
    }
  });
  const [showHistory, setShowHistory] = useState(false);
  const [showRussellMap, setShowRussellMap] = useState(false);

  // Toast Bildirim Sistemi
  const [toasts, setToasts] = useState([]);
  const showToast = useCallback((message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  // 1. Meta veriyi yükle
  useEffect(() => {
    getMeta()
      .then(setMeta)
      .catch((err) => console.error('Meta veri yüklenemedi:', err));
  }, []);

  // 2. OAuth Callback (#access_token=... veya ?access_token=...)
  useEffect(() => {
    // Önce hash fragment kontrolü (yeni güvenli akış)
    const hash = window.location.hash.replace(/^#/, '');
    const hashParams = new URLSearchParams(hash);
    const queryParams = new URLSearchParams(window.location.search);

    const accessToken = hashParams.get('access_token') || queryParams.get('access_token');
    const refreshToken = hashParams.get('refresh_token') || queryParams.get('refresh_token');
    const expiresAt = hashParams.get('expires_at') || queryParams.get('expires_at');
    const error = hashParams.get('error') || queryParams.get('error');

    if (accessToken) {
      const newAuth = {
        access_token: accessToken,
        refresh_token: refreshToken || null,
        expires_at: expiresAt ? parseInt(expiresAt, 10) : null,
      };
      setAuth(newAuth);
      setStoredAuth(newAuth);
      setIsGuest(false);
      localStorage.removeItem('moodai_guest');
      showToast('Spotify hesabınız başarıyla bağlandı! 🎵', 'success');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (error) {
      showToast(`Spotify bağlantı hatası: ${error}`, 'error');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [showToast]);

  // 3. Otomatik Token Yenileme Kontrolü (1 saatlik Spotify token'ı)
  useEffect(() => {
    if (!auth?.refresh_token || !auth?.expires_at) return;

    const interval = setInterval(async () => {
      const remainingSeconds = auth.expires_at - Math.floor(Date.now() / 1000);
      if (remainingSeconds < 300) {
        // 5 dakikadan az kaldıysa yenile
        const newToken = await refreshAccessToken();
        if (newToken) {
          setAuth(getStoredAuth());
        }
      }
    }, 60000);

    return () => clearInterval(interval);
  }, [auth]);

  const handleGuestLogin = () => {
    setIsGuest(true);
    setAuth(null);
    clearStoredAuth();
    localStorage.setItem('moodai_guest', 'true');
    showToast('Misafir modunda devam ediliyor.', 'info');
  };

  const handleLogout = () => {
    setAuth(null);
    setIsGuest(false);
    setAnalysisResult(null);
    setTracks([]);
    setSearchParams(null);
    clearStoredAuth();
    showToast('Oturum kapatıldı.', 'info');
  };

  const handleAnalyzed = (result) => {
    setAnalysisResult(result);
  };

  const handleTracksReady = (newTracks, params) => {
    setTracks(newTracks);
    setSearchParams(params);

    // Reçete geçmişine kaydet
    if (analysisResult && newTracks.length > 0) {
      const entry = {
        id: Date.now(),
        date: new Date().toLocaleString('tr-TR', { dateStyle: 'short', timeStyle: 'short' }),
        mood: analysisResult.mood,
        doktor_notu: analysisResult.doktor_notu,
        therapy_mode: params.therapy_mode,
        count: newTracks.length,
        firstTrack: newTracks[0],
        analysisResult,
        tracks: newTracks,
        params,
      };
      const updated = [entry, ...history.filter(h => h.id !== entry.id)].slice(0, 8);
      setHistory(updated);
      try {
        localStorage.setItem('moodai_history', JSON.stringify(updated));
      } catch (_) {}
    }
  };

  const handleRestoreHistory = (item) => {
    setAnalysisResult(item.analysisResult);
    setTracks(item.tracks);
    setSearchParams(item.params);
    setShowHistory(false);
    showToast(`"${item.mood.replace(/_/g, ' ')}" reçetesi geri yüklendi!`, 'success');
  };

  const handleTrackReplace = (index, newTrack) => {
    setTracks((prev) => {
      const copy = [...prev];
      copy[index] = newTrack;
      return copy;
    });
  };

  const getMoodGradient = () => {
    if (!analysisResult?.mood) return 'from-[#0f0a1e] via-[#1a1035] to-[#2d1b69]';
    const gradients = {
      neseli_pop: 'from-[#1a1200] via-[#2d2200] to-[#1a1035]',
      huzunlu_slow: 'from-[#0a1128] via-[#001f54] to-[#034078]',
      enerjik_spor: 'from-[#2b0c0c] via-[#4a1212] to-[#1a1035]',
      sakin_akustik: 'from-[#092018] via-[#133c2e] to-[#0f1f1d]',
      hard_rock_metal: 'from-[#1a0505] via-[#2d0000] to-[#0d0d0d]',
      indie_alternatif: 'from-[#1e0f2d] via-[#351a4f] to-[#120824]',
      rap_hiphop: 'from-[#2b1704] via-[#422206] to-[#120a02]',
      jazz_blues: 'from-[#081b29] via-[#0e2f44] to-[#061118]',
      elektronik_synth: 'from-[#04202c] via-[#083c50] to-[#021820]',
    };
    return gradients[analysisResult.mood] || 'from-[#0f0a1e] via-[#1a1035] to-[#2d1b69]';
  };

  const accessToken = auth?.access_token || null;

  if (!accessToken && !isGuest) {
    return <Login onGuestLogin={handleGuestLogin} showToast={showToast} />;
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br ${getMoodGradient()} transition-colors duration-1000 text-white p-4 md:p-8 font-sans relative overflow-x-hidden`}>
      {/* Ambiyans Işığı */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-purple-500/10 blur-[120px] pointer-events-none rounded-full" />

      {/* Toast Bildirimleri */}
      <div className="fixed top-5 right-5 z-50 space-y-2 max-w-sm pointer-events-none">
        {toasts.map((t) => {
          const colors = {
            success: 'bg-emerald-900/90 border-emerald-500/50 text-emerald-200',
            error: 'bg-rose-900/90 border-rose-500/50 text-rose-200',
            warning: 'bg-amber-900/90 border-amber-500/50 text-amber-200',
            info: 'bg-purple-900/90 border-purple-500/50 text-purple-200',
          };
          return (
            <div
              key={t.id}
              className={`p-3.5 rounded-2xl border backdrop-blur-xl shadow-2xl text-xs font-semibold animate-fadeIn pointer-events-auto ${colors[t.type] || colors.info}`}
            >
              {t.message}
            </div>
          );
        })}
      </div>

      {/* Header */}
      <header className="max-w-7xl mx-auto mb-8 flex justify-between items-center pb-2">
        <div className="flex items-center gap-3.5">
          <div className="text-3xl sm:text-4xl bg-purple-500/15 p-2 sm:p-2.5 rounded-2xl border border-purple-400/25 shadow-lg backdrop-blur-md">
            🧠
          </div>
          <div>
            <h1 className="text-xl sm:text-2xl font-black tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-300 via-pink-300 to-indigo-300">
              Mood AI
            </h1>
            <p className="text-[11px] sm:text-xs text-gray-400 font-medium">Yapay Zeka Destekli Müzik Terapisti</p>
          </div>
        </div>

        <div className="flex items-center gap-2 sm:gap-3">
          {/* Russell Modeli Haritası Butonu */}
          {analysisResult && (
            <button
              onClick={() => setShowRussellMap(true)}
              className="px-3.5 py-2 bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-400/30 rounded-xl text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5 shadow-sm"
              title="Russell Çevresel Duygu Haritası"
            >
              <span>🧭</span>
              <span className="hidden md:inline">Duygu Haritası</span>
            </button>
          )}

          {/* Geçmiş Reçeteler Butonu */}
          {history.length > 0 && (
            <button
              onClick={() => setShowHistory(true)}
              className="px-3.5 py-2 bg-white/5 hover:bg-white/10 text-gray-300 hover:text-white border border-white/10 rounded-xl text-xs font-semibold cursor-pointer transition-all flex items-center gap-1.5 shadow-sm"
            >
              <span>📜</span>
              <span className="hidden sm:inline">Geçmiş</span>
              <span className="px-2 py-0.5 rounded-full bg-purple-500/30 text-[10px] font-bold text-purple-200">{history.length}</span>
            </button>
          )}

          {/* Spotify Durumu / Giriş */}
          {accessToken ? (
            <span className="inline-flex items-center gap-2 px-3.5 py-2 bg-[#1DB954]/10 border border-[#1DB954]/30 text-[#1ed760] rounded-full text-xs font-bold shadow-sm">
              <span className="w-2 h-2 rounded-full bg-[#1ed760] animate-pulse" />
              <span className="hidden sm:inline">Spotify</span> Bağlı
            </span>
          ) : (
            <a
              href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/login`}
              className="inline-flex items-center gap-2 px-4 py-2 bg-[#1DB954] hover:bg-[#1ed760] text-black font-extrabold rounded-full text-xs transition-all shadow-md shadow-green-500/20 hover:scale-105"
            >
              <span>🎵</span>
              <span className="hidden sm:inline">Spotify ile</span> Bağlan
            </a>
          )}

          <button
            onClick={handleLogout}
            className="px-3.5 py-2 bg-white/5 hover:bg-rose-500/20 text-gray-400 hover:text-rose-300 rounded-xl transition-all border border-transparent hover:border-rose-500/30 text-xs font-semibold cursor-pointer"
          >
            Çıkış
          </button>
        </div>
      </header>

      {/* Ana Grid */}
      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5 space-y-6">
          <ChatBox
            accessToken={accessToken}
            meta={meta}
            onAnalyzed={handleAnalyzed}
            onTracksReady={handleTracksReady}
            showToast={showToast}
          />

          {analysisResult && (
            <div className="animate-fadeIn">
              <MoodCard
                mood={analysisResult.mood}
                doktorNotu={analysisResult.doktor_notu}
                sarkiAdi={tracks.length > 0 ? tracks[0].name : 'Reçete Hazırlanıyor...'}
                sanatciAdi={tracks.length > 0 ? tracks[0].artist : null}
                trackCount={tracks.length || 20}
                imageUrl={tracks.length > 0 ? tracks[0].image : null}
                showToast={showToast}
              />
            </div>
          )}
        </div>

        <div className="lg:col-span-7 h-[calc(100vh-170px)] min-h-[600px]">
          {tracks.length > 0 ? (
            <div className="h-full animate-fadeIn">
              <Playlist
                tracks={tracks}
                accessToken={accessToken}
                mood={searchParams?.mood}
                language={searchParams?.language}
                genres={searchParams?.genres}
                onTrackReplace={handleTrackReplace}
                showToast={showToast}
              />
            </div>
          ) : (
            <div className="h-full glass-panel rounded-3xl flex flex-col items-center justify-center p-10 text-center relative overflow-hidden group">
              <div className="w-20 h-20 rounded-3xl bg-purple-500/10 border border-purple-400/20 flex items-center justify-center text-4xl mb-5 shadow-inner">
                🎧
              </div>
              <h3 className="text-xl font-bold text-white mb-2 tracking-tight">
                Müzik Reçeten Burada Belirecek
              </h3>
              <p className="text-gray-400 text-sm max-w-sm leading-relaxed">
                Ruh halini yazıp veya sevdiğin parçaları seçip <strong className="text-purple-300">"Reçeteyi Oluştur"</strong> butonuna bastığında sana özel hazırladığımız terapi listesi ve Spotify çaları burada açılacak.
              </p>
            </div>
          )}
        </div>
      </main>

      {/* Reçete Geçmişi Drawer/Modal */}
      {showHistory && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex justify-end animate-fadeIn">
          <div className="w-full max-w-md bg-[#120a24] border-l border-white/10 p-6 flex flex-col h-full shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <span>📜</span> Geçmiş Reçetelerim
              </h3>
              <button
                onClick={() => setShowHistory(false)}
                className="text-gray-400 hover:text-white text-lg p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {history.map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-2xl bg-white/5 hover:bg-white/10 border border-white/10 transition-all flex flex-col gap-2"
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-bold text-purple-300 capitalize">
                      {item.mood.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-gray-400">{item.date}</span>
                  </div>
                  <p className="text-xs text-gray-300 line-clamp-2 italic">"{item.doktor_notu}"</p>
                  <div className="flex justify-between items-center pt-1 border-t border-white/5 text-[11px]">
                    <span className="text-gray-400">{item.count} Şarkı</span>
                    <button
                      onClick={() => handleRestoreHistory(item)}
                      className="px-3 py-1 bg-purple-600/40 hover:bg-purple-600 text-purple-200 hover:text-white rounded-lg font-semibold transition-all cursor-pointer"
                    >
                      Reçeteyi Aç ↗
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Russell Çevresel Duygu Modeli Modal */}
      {showRussellMap && analysisResult && (
        <div className="fixed inset-0 z-50 bg-black/75 backdrop-blur-md flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-[#120a24] border border-purple-500/30 rounded-3xl p-6 max-w-lg w-full shadow-2xl relative">
            <div className="flex justify-between items-center mb-4">
              <div>
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <span>🧭</span> Russell Duygu Modeli Haritası
                </h3>
                <p className="text-xs text-gray-400">Circumplex Model of Affect (Valence & Arousal)</p>
              </div>
              <button
                onClick={() => setShowRussellMap(false)}
                className="text-gray-400 hover:text-white text-lg p-1 cursor-pointer"
              >
                ✕
              </button>
            </div>

            {/* 2D Kartezyen Koordinat Grafiği */}
            <div className="relative w-full h-64 bg-black/40 rounded-2xl border border-white/10 p-4 mb-4 overflow-hidden">
              {/* Eksenler */}
              <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/20" />
              <div className="absolute top-1/2 left-0 right-0 h-px bg-white/20" />

              {/* Eksen Etiketleri */}
              <span className="absolute top-2 left-1/2 -translate-x-1/2 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Yüksek Enerji (Arousal)
              </span>
              <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Düşük Enerji
              </span>
              <span className="absolute left-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Negatif
              </span>
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gray-400 font-bold uppercase tracking-wider">
                Pozitif
              </span>

              {/* Kullanıcının Noktası */}
              {(() => {
                const v = typeof analysisResult.valence === 'number' ? analysisResult.valence : 0;
                const a = typeof analysisResult.arousal === 'number' ? analysisResult.arousal : 0.5;
                // v: -1..1 -> left: 10%..90%
                const leftPct = 50 + (v * 40);
                // a: 0..1 -> bottom: 10%..90%
                const bottomPct = 10 + (a * 80);
                return (
                  <div
                    className="absolute -translate-x-1/2 translate-y-1/2 z-20 flex flex-col items-center"
                    style={{ left: `${leftPct}%`, bottom: `${bottomPct}%` }}
                  >
                    <div className="w-5 h-5 rounded-full bg-pink-500 border-2 border-white shadow-lg animate-ping absolute" />
                    <div className="w-5 h-5 rounded-full bg-pink-500 border-2 border-white shadow-lg relative" />
                    <span className="mt-1 px-2 py-0.5 rounded-full bg-black/80 text-[10px] font-bold text-white whitespace-nowrap border border-white/20">
                      Senin Modun
                    </span>
                  </div>
                );
              })()}
            </div>

            <div className="p-3 bg-white/5 rounded-2xl text-xs text-gray-300 space-y-1">
              <p>
                <strong>Valence (Değerlik):</strong> {analysisResult.valence} (Duygunun pozitif/negatif yönü)
              </p>
              <p>
                <strong>Arousal (Uyarılma):</strong> {analysisResult.arousal} (Fizyolojik enerji ve tempo)
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
