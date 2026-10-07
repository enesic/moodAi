import React, { useState } from 'react';
import { getMoodCard } from '../api/client';

const MoodCard = ({ mood, doktorNotu, sarkiAdi, sanatciAdi, trackCount = 20, imageUrl, showToast }) => {
  const [downloading, setDownloading] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleDownload = async () => {
    setDownloading(true);
    try {
      const blob = await getMoodCard({
        mood,
        doktor_notu: doktorNotu,
        sarki_adi: sarkiAdi,
        sanatci_adi: sanatciAdi || null,
        track_count: trackCount || 20,
        image_url: imageUrl || null,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mood-ai-story-${mood || 'recete'}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast?.('Story kartı başarıyla indirildi! 📸', 'success');
    } catch (error) {
      console.error(error);
      showToast?.(error.message || 'Reçete kartı indirilemedi.', 'error');
    } finally {
      setDownloading(false);
    }
  };

  const handleCopyText = () => {
    const text = `🧠 Mood AI • Müzik Reçetem:\n\n🩺 Teşhis: ${mood?.replace(/_/g, ' ').toUpperCase()}\n📝 Terapist Notu: "${doktorNotu}"\n🎵 Öne Çıkan Parça: ${sarkiAdi}${sanatciAdi ? ` - ${sanatciAdi}` : ''}\n\n✨ Sen de modunu keşfet: moodai.app`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    showToast?.('Reçete panoya kopyalandı! 📋', 'info');
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-7 shadow-2xl relative overflow-hidden group transition-all">
      {/* Arka Plan Glow Efekti */}
      <div className="absolute top-0 right-0 w-36 h-36 bg-purple-500/10 rounded-full blur-2xl pointer-events-none" />

      <div className="relative z-10">
        <div className="flex justify-between items-center mb-4 pb-3 border-b border-white/5">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-purple-500/20 border border-purple-400/30 flex items-center justify-center text-sm">
              📝
            </div>
            <div>
              <h3 className="text-sm sm:text-base font-black text-white tracking-tight">
                Terapistin Teşhis Özeti
              </h3>
              <p className="text-[10px] text-gray-400">Yapay zeka analiz raporu</p>
            </div>
          </div>
          <span className="text-[10px] px-2.5 py-1 bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-pink-300 rounded-full font-black border border-pink-400/30 uppercase tracking-wider shadow-sm flex items-center gap-1">
            <span>📸</span> 9:16 Story
          </span>
        </div>

        {/* Doktor Notu Alıntı Kutusu */}
        <div className="bg-black/50 rounded-2xl p-4 md:p-5 mb-4 italic text-gray-200 border-l-3 border-purple-400 text-xs sm:text-sm leading-relaxed shadow-inner">
          "{doktorNotu}"
        </div>

        {/* Öne Çıkan Başyapıt Kutusu */}
        {sarkiAdi && sarkiAdi !== "Reçete Hazırlanıyor..." && (
          <div className="mb-4 p-3 rounded-2xl bg-white/5 hover:bg-white/[0.08] transition-colors border border-white/10 flex items-center gap-3">
            {imageUrl ? (
              <img src={imageUrl} alt={sarkiAdi} className="w-12 h-12 rounded-xl object-cover shrink-0 shadow-md ring-1 ring-white/10" />
            ) : (
              <div className="w-12 h-12 rounded-xl bg-purple-500/20 flex items-center justify-center text-xl shrink-0">
                🎵
              </div>
            )}
            <div className="min-w-0 flex-1">
              <span className="text-[9px] uppercase font-black text-emerald-400 tracking-wider">Öne Çıkan Başyapıt</span>
              <p className="text-xs sm:text-sm font-bold text-white truncate">{sarkiAdi}</p>
              {sanatciAdi && <p className="text-xs text-gray-400 truncate">{sanatciAdi}</p>}
            </div>
          </div>
        )}

        {/* Butonlar */}
        <div className="grid grid-cols-2 gap-3 pt-1">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="py-3 px-3 bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-extrabold text-xs rounded-xl transition-all flex items-center justify-center gap-1.5 border border-pink-400/30 shadow-lg shadow-pink-600/20 cursor-pointer disabled:opacity-50 hover:scale-[1.02] active:scale-[0.98]"
          >
            {downloading ? (
              <span className="animate-spin">⏳ Hazırlanıyor...</span>
            ) : (
              <>
                <span>📸</span> <span>Story Kartı İndir</span>
              </>
            )}
          </button>

          <button
            onClick={handleCopyText}
            className="py-3 px-3 bg-white/5 hover:bg-white/15 text-purple-200 hover:text-white font-bold text-xs rounded-xl transition-all flex items-center justify-center gap-1.5 border border-white/10 hover:border-white/20 cursor-pointer active:scale-[0.98]"
          >
            {copied ? <span className="text-emerald-400 font-bold">✓ Kopyalandı!</span> : <span>📋 Metni Kopyala</span>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoodCard;
