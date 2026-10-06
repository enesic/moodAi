import React, { useState } from 'react';
import { login } from '../api/client';

const Login = ({ onGuestLogin, showToast }) => {
  const [loading, setLoading] = useState(false);

  const handleSpotifyLogin = async () => {
    setLoading(true);
    try {
      await login();
    } catch (error) {
      console.error(error);
      showToast?.(error.message || 'Spotify giriş bağlantısı başlatılamadı.', 'error');
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-[#0c061a] via-[#140b2e] to-[#25134d] text-white p-6 relative overflow-hidden">
      {/* Ambiyans Işığı */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-purple-600/15 blur-[140px] pointer-events-none rounded-full animate-pulse-slow" />

      <div className="text-center max-w-lg w-full glass-panel rounded-3xl p-8 md:p-11 shadow-2xl relative z-10 transition-all">
        <div className="inline-flex text-5xl mb-5 bg-purple-500/15 p-5 rounded-3xl border border-purple-400/30 shadow-inner">
          🧠
        </div>
        
        <h1 className="text-3xl md:text-4xl font-extrabold mb-3 tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-300 via-pink-300 to-indigo-300">
          Mood AI: Müzik Terapisti
        </h1>
        
        <p className="text-sm md:text-base text-gray-300 mb-8 leading-relaxed font-normal">
          Nasıl hissettiğini doğal dille anlat; yapay zeka duygu durumunu analiz edip ruh haline en uygun müzik reçetesini hazırlasın.
        </p>

        <div className="space-y-3.5">
          <button
            onClick={handleSpotifyLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 bg-[#1DB954] hover:bg-[#1ed760] text-black font-extrabold text-base py-4 px-6 rounded-2xl transition-all duration-300 transform hover:scale-[1.02] shadow-[0_0_30px_rgba(29,185,84,0.35)] disabled:opacity-50 cursor-pointer"
          >
            <span className="text-xl">🎵</span>
            <span>{loading ? "Bağlanıyor..." : "Spotify ile Giriş Yap (Önerilen)"}</span>
          </button>

          <button
            onClick={onGuestLogin}
            className="w-full flex items-center justify-center gap-2 bg-white/5 hover:bg-white/10 text-gray-200 hover:text-white font-semibold text-sm py-3.5 px-6 rounded-2xl transition-all duration-300 border border-white/10 hover:border-white/20 cursor-pointer"
          >
            <span>🚀</span>
            <span>Giriş Yapmadan Devam Et (Misafir Modu)</span>
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-white/5 text-xs text-gray-400 space-y-1">
          <p>🔒 Spotify hesabınıza yalnızca çalma listesi ekleme izni istenir.</p>
          <p>Misafir modunda müzik reçetenizi dinleyebilir ve kartınızı oluşturabilirsiniz.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
