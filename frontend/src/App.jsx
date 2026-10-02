import React, { useState, useEffect } from 'react';
import Login from './components/Login';
import ChatBox from './components/ChatBox';
import MoodCard from './components/MoodCard';
import Playlist from './components/Playlist';

function App() {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem('moodai_token') || null);
  const [isGuest, setIsGuest] = useState(() => localStorage.getItem('moodai_guest') === 'true');
  const [analysisResult, setAnalysisResult] = useState(null);
  const [tracks, setTracks] = useState([]);
  const [searchParams, setSearchParams] = useState(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const token = params.get('access_token');
    const error = params.get('error');
    if (token) {
      setAccessToken(token);
      setIsGuest(false);
      localStorage.setItem('moodai_token', token);
      localStorage.removeItem('moodai_guest');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
    if (error) {
      alert(`Spotify giriş hatası: ${error}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const handleGuestLogin = () => {
    setIsGuest(true);
    setAccessToken(null);
    localStorage.setItem('moodai_guest', 'true');
    localStorage.removeItem('moodai_token');
  };

  const handleLogout = () => {
    setAccessToken(null);
    setIsGuest(false);
    setAnalysisResult(null);
    setTracks([]);
    setSearchParams(null);
    localStorage.removeItem('moodai_token');
    localStorage.removeItem('moodai_guest');
  };

  const handleAnalyzed = (result) => {
    setAnalysisResult(result);
  };

  const handleTracksReady = (newTracks, params) => {
    setTracks(newTracks);
    setSearchParams(params);
  };

  const handleTrackReplace = (index, newTrack) => {
    setTracks(prev => {
      const copy = [...prev];
      copy[index] = newTrack;
      return copy;
    });
  };

  const getMoodGradient = () => {
    if (!analysisResult?.mood) return "from-[#0f0a1e] via-[#1a1035] to-[#2d1b69]";
    const gradients = {
      neseli_pop: "from-[#1a1200] via-[#2d2200] to-[#1a1035]",
      huzunlu_slow: "from-[#0a1128] via-[#001f54] to-[#034078]",
      enerjik_spor: "from-[#2b0c0c] via-[#4a1212] to-[#1a1035]",
      sakin_akustik: "from-[#092018] via-[#133c2e] to-[#0f1f1d]",
      hard_rock_metal: "from-[#1a0505] via-[#2d0000] to-[#0d0d0d]",
      indie_alternatif: "from-[#1e0f2d] via-[#351a4f] to-[#120824]",
      rap_hiphop: "from-[#2b1704] via-[#422206] to-[#120a02]",
      jazz_blues: "from-[#081b29] via-[#0e2f44] to-[#061118]",
      elektronik_synth: "from-[#04202c] via-[#083c50] to-[#021820]"
    };
    return gradients[analysisResult.mood] || "from-[#0f0a1e] via-[#1a1035] to-[#2d1b69]";
  };

  if (!accessToken && !isGuest) {
    return <Login onGuestLogin={handleGuestLogin} />;
  }

  return (
    <div className={`min-h-screen bg-gradient-to-br ${getMoodGradient()} transition-colors duration-1000 text-white p-4 md:p-8 font-sans relative overflow-x-hidden`}>
      {/* Ambiyans Işığı */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[300px] bg-purple-500/10 blur-[120px] pointer-events-none rounded-full" />
      <header className="max-w-7xl mx-auto mb-8 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <div className="text-4xl bg-white/10 p-2 rounded-2xl backdrop-blur-sm border border-white/20 shadow-lg">🧠</div>
          <div>
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500">Mood AI</h1>
            <p className="text-xs md:text-sm text-gray-400">Yapay Zeka Müzik Terapisti</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {accessToken ? (
            <span className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1DB954]/10 border border-[#1DB954]/30 text-[#1ed760] rounded-full text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-[#1ed760] animate-pulse"></span>
              Spotify Bağlı
            </span>
          ) : (
            <a 
              href={`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/login`}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#1DB954] hover:bg-[#1ed760] text-black font-bold rounded-full text-xs transition-all shadow-md shadow-green-500/20"
            >
              <span>🎵</span>
              <span className="hidden sm:inline">Spotify ile</span> Bağlan
            </a>
          )}
          
          <button 
            onClick={handleLogout}
            className="px-3.5 py-1.5 bg-white/5 hover:bg-red-500/20 text-gray-300 hover:text-red-400 rounded-xl transition-all border border-transparent hover:border-red-500/30 text-xs font-medium cursor-pointer"
          >
            Çıkış
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-5 space-y-8">
          <ChatBox 
            accessToken={accessToken} 
            onAnalyzed={handleAnalyzed} 
            onTracksReady={handleTracksReady} 
          />
          
          {analysisResult && (
            <div className="animate-fadeIn">
              <MoodCard 
                mood={analysisResult.mood} 
                doktorNotu={analysisResult.doktor_notu}
                sarkiAdi={tracks.length > 0 ? tracks[0].name : "Reçete Hazırlanıyor..."}
              />
            </div>
          )}
        </div>

        <div className="lg:col-span-7 h-[calc(100vh-180px)] min-h-[600px]">
          {tracks.length > 0 ? (
            <div className="h-full animate-fadeIn">
              <Playlist 
                tracks={tracks} 
                accessToken={accessToken}
                mood={searchParams?.mood}
                language={searchParams?.language}
                genres={searchParams?.genres}
                onTrackReplace={handleTrackReplace}
              />
            </div>
          ) : (
            <div className="h-full bg-white/5 backdrop-blur-md rounded-3xl border border-white/10 flex flex-col items-center justify-center p-10 text-center">
              <div className="text-6xl mb-6 opacity-50">🎧</div>
              <h3 className="text-xl font-medium text-gray-300 mb-2">Çalma Listen Burada Görünecek</h3>
              <p className="text-gray-500 text-sm max-w-sm">
                Ruh halini anlatıp "Listeyi Oluştur" butonuna bastığında sana özel hazırladığımız reçete burada belirecek.
              </p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;
