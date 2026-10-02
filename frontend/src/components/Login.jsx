import React, { useState } from 'react';
import { login } from '../api/client';

const Login = ({ onGuestLogin }) => {
  const [loading, setLoading] = useState(false);

  const handleSpotifyLogin = async () => {
    setLoading(true);
    try {
      await login();
    } catch (error) {
      console.error(error);
      alert('Spotify giriş bağlantısı başlatılamadı. Backend sunucusunun çalıştığından emin olun.');
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-[#0f0a1e] via-[#1a1035] to-[#2d1b69] text-white p-6 relative overflow-hidden">
      {/* Ambiyans Işığı */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[500px] h-[300px] bg-purple-600/20 blur-[130px] pointer-events-none rounded-full" />

      <div className="text-center max-w-lg w-full bg-white/5 backdrop-blur-xl rounded-3xl p-8 md:p-10 shadow-2xl border border-white/10 relative z-10">
        <div className="inline-block text-6xl mb-4 bg-white/10 p-4 rounded-3xl backdrop-blur-sm border border-white/20 shadow-lg">
          🧠
        </div>
        
        <h1 className="text-3xl md:text-4xl font-extrabold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-purple-400 via-pink-400 to-indigo-400">
          Mood AI: Müzik Terapisti
        </h1>
        
        <p className="text-sm md:text-base text-gray-300 mb-8 leading-relaxed">
          Nasıl hissettiğini doğal dille anlat; yapay zeka duygu durumunu analiz edip ruh haline en uygun müzik reçetesini hazırlasın.
        </p>

        <div className="space-y-3.5">
          <button
            onClick={handleSpotifyLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 bg-[#1DB954] hover:bg-[#1ed760] text-black font-bold text-base py-3.5 px-6 rounded-2xl transition-all duration-300 transform hover:scale-[1.02] shadow-[0_0_25px_rgba(29,185,84,0.35)] disabled:opacity-50 cursor-pointer"
          >
            <span className="text-xl">🎵</span>
            <span>{loading ? "Bağlanıyor..." : "Spotify ile Giriş Yap (Önerilen)"}</span>
          </button>

          <button
            onClick={onGuestLogin}
            className="w-full flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 text-white font-semibold text-sm py-3.5 px-6 rounded-2xl transition-all duration-300 border border-white/15 hover:border-white/30 cursor-pointer"
          >
            <span>🚀</span>
            <span>Giriş Yapmadan Devam Et (Misafir Modu)</span>
          </button>
        </div>

        <div className="mt-8 pt-6 border-t border-white/10 text-xs text-gray-400 space-y-1">
          <p>🔒 Spotify hesabınıza yalnızca çalma listesi ekleme izni istenir.</p>
          <p>Misafir modunda müzik reçetenizi dinleyebilir ve kartınızı oluşturabilirsiniz.</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
