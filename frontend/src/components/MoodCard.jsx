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
    const text = `🧠 Mood AI • Müzik Reçetem:\n\n🩺 Teşhis: ${mood?.replace(/_/g, ' ').toUpperCase()}\n📝 Terapist Notu: "${doktorNotu}"\n🎵 Öne Çıkan Parça: ${sarkiAdi}${sanatciAdi ? ` - ${sanatciAdi}` : ''}\n\n✨ Sen de modunu müzikle keşfet: moodai.app`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    showToast?.('Reçete panoya kopyalandı! 📋', 'info');
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="bg-gradient-to-br from-indigo-950/70 via-purple-950/70 to-slate-950/80 backdrop-blur-xl rounded-3xl p-6 shadow-2xl border border-white/20 relative overflow-hidden group">
      <div className="absolute top-0 right-0 p-4 opacity-10 text-6xl">🩺</div>

      <div className="relative z-10">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-white flex items-center">
            <span className="mr-2">📝</span> Doktorun Terapi Notu
          </h3>
          <span className="text-[11px] px-2.5 py-1 bg-purple-500/20 text-purple-300 rounded-full font-medium border border-purple-400/30">
            9:16 Story Kartı
          </span>
        </div>

        <div className="bg-black/35 rounded-2xl p-4 md:p-5 mb-5 italic text-gray-200 border-l-4 border-purple-400 text-sm leading-relaxed shadow-inner">
          "{doktorNotu}"
        </div>

        {sarkiAdi && sarkiAdi !== "Reçete Hazırlanıyor..." && (
          <div className="mb-5 p-3 rounded-2xl bg-white/5 border border-white/10 flex items-center gap-3">
            {imageUrl ? (
              <img src={imageUrl} alt={sarkiAdi} className="w-12 h-12 rounded-xl object-cover shrink-0 shadow" />
            ) : (
              <span className="text-2xl">🎵</span>
            )}
            <div className="min-w-0 flex-1">
              <p className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">Reçetelenen Başyapıt</p>
              <p className="text-sm font-semibold text-green-400 truncate">{sarkiAdi}</p>
              {sanatciAdi && <p className="text-xs text-gray-400 truncate">{sanatciAdi}</p>}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="py-3 px-3 bg-gradient-to-r from-pink-600/80 to-purple-600/80 hover:from-pink-500 hover:to-purple-500 text-white font-semibold text-xs rounded-xl transition-all flex items-center justify-center gap-1.5 border border-pink-400/30 shadow-md shadow-pink-600/20 cursor-pointer disabled:opacity-50 hover:scale-[1.02]"
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
            className="py-3 px-3 bg-white/10 hover:bg-white/20 text-purple-200 font-semibold text-xs rounded-xl transition-all flex items-center justify-center gap-1.5 border border-white/10 hover:border-white/20 cursor-pointer"
          >
            {copied ? <span className="text-green-400">✓ Kopyalandı!</span> : <span>📋 Metni Kopyala</span>}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoodCard;
