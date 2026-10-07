import React, { useState } from 'react';

const MOOD_EMOJIS = {
  neseli_pop: '🎉',
  huzunlu_slow: '💔',
  enerjik_spor: '⚡',
  sakin_akustik: '☕',
  hard_rock_metal: '🔥',
  indie_alternatif: '🌌',
  rap_hiphop: '🎤',
  jazz_blues: '🎷',
  elektronik_synth: '🕹️',
};

const MOOD_NAMES = {
  neseli_pop: 'Neşeli & Pop',
  huzunlu_slow: 'Hüzünlü & Slow',
  enerjik_spor: 'Enerjik & Spor',
  sakin_akustik: 'Sakin & Akustik',
  hard_rock_metal: 'Rock & Metal',
  indie_alternatif: 'İndie & Alternatif',
  rap_hiphop: 'Rap & HipHop',
  jazz_blues: 'Jazz & Blues',
  elektronik_synth: 'Elektronik & Synth',
};

const MoodJournalModal = ({ isOpen, onClose, history = [], onRestoreItem, isPro, onOpenProModal, showToast }) => {
  const [currentMonth] = useState(() => new Date());

  if (!isOpen) return null;

  // Tarihe göre gruplanmış kayıtlar
  const historyByDate = {};
  history.forEach((item) => {
    // format date as YYYY-MM-DD or use raw date
    const dStr = item.isoDate || (item.id ? new Date(item.id).toISOString().slice(0, 10) : null);
    if (dStr) {
      if (!historyByDate[dStr]) historyByDate[dStr] = [];
      historyByDate[dStr].push(item);
    }
  });

  // Mod dağılımı hesaplama
  const moodCounts = {};
  history.forEach((h) => {
    moodCounts[h.mood] = (moodCounts[h.mood] || 0) + 1;
  });
  const totalEntries = history.length;

  // Takvim günleri (Bu ay)
  const year = currentMonth.getFullYear();
  const month = currentMonth.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstDayIndex = new Date(year, month, 1).getDay(); // 0 is Sunday
  const monthNames = [
    'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
    'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
  ];

  const handleDownloadReport = () => {
    if (!isPro) {
      onOpenProModal?.('Kişiselleştirilmiş 30 Günlük Ruh Hali & Terapi PDF Raporu Pro üyelere özeldir.');
      return;
    }
    showToast?.('Detaylı Terapi & Müzik Analiz Raporunuz PDF olarak hazırlanıyor... 📄', 'success');
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 animate-fadeIn">
      <div className="bg-[#120a26] border border-purple-500/30 rounded-3xl p-5 sm:p-7 max-w-3xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col space-y-6 scrollbar-thin scrollbar-thumb-purple-500/30">
        {/* Başlık ve Kapat */}
        <div className="flex justify-between items-start border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">📅</span>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                Mood Journal & Duygu Takvimi
              </h2>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              Ruh halinin zaman içindeki yolculuğu, duygu ritmin ve sana iyi gelen melodiler.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl p-1.5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Özet İstatistik Kartları */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white/5 border border-white/10 rounded-2xl p-3.5 text-center">
            <span className="text-xl">🩺</span>
            <p className="text-lg font-black text-white mt-1">{totalEntries}</p>
            <p className="text-[10px] text-gray-400 uppercase font-semibold">Toplam Reçete</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-3.5 text-center">
            <span className="text-xl">🔥</span>
            <p className="text-lg font-black text-purple-300 mt-1">
              {totalEntries > 0 ? (
                MOOD_EMOJIS[Object.keys(moodCounts).sort((a,b) => moodCounts[b]-moodCounts[a])[0]] || '🎵'
              ) : '-'}
            </p>
            <p className="text-[10px] text-gray-400 uppercase font-semibold">Baskın Mod</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-3.5 text-center">
            <span className="text-xl">📈</span>
            <p className="text-lg font-black text-emerald-300 mt-1">
              %{totalEntries > 0 ? Math.round((history.filter(h => (h.analysisResult?.valence || 0) > 0).length / totalEntries) * 100) : 0}
            </p>
            <p className="text-[10px] text-gray-400 uppercase font-semibold">Pozitif Günler</p>
          </div>
          <div className="bg-white/5 border border-white/10 rounded-2xl p-3.5 text-center">
            <span className="text-xl">👑</span>
            <p className="text-lg font-black text-amber-300 mt-1">{isPro ? 'Aktif' : 'Free'}</p>
            <p className="text-[10px] text-gray-400 uppercase font-semibold">Üyelik Durumu</p>
          </div>
        </div>

        {/* Takvim Görünümü */}
        <div className="bg-black/40 border border-white/10 rounded-2xl p-4 sm:p-5">
          <div className="flex justify-between items-center mb-3">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <span>🗓️</span> {monthNames[month]} {year}
            </h3>
            <span className="text-[11px] text-purple-300 font-medium">Günlük Duygu Haritası</span>
          </div>

          <div className="grid grid-cols-7 gap-1.5 text-center">
            {['Pzt', 'Sal', 'Çar', 'Per', 'Cum', 'Cmt', 'Paz'].map((d) => (
              <span key={d} className="text-[10px] font-bold text-gray-400 py-1 uppercase">
                {d}
              </span>
            ))}

            {/* Ayın ilk gününden önceki boşluklar */}
            {Array.from({ length: (firstDayIndex + 6) % 7 }).map((_, i) => (
              <div key={`empty-${i}`} className="h-10 rounded-xl bg-white/[0.02]" />
            ))}

            {/* Günler */}
            {Array.from({ length: daysInMonth }).map((_, i) => {
              const dayNum = i + 1;
              const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
              const dayItems = historyByDate[dateStr] || [];
              const topItem = dayItems[0];
              const emoji = topItem ? MOOD_EMOJIS[topItem.mood] || '🎵' : null;

              return (
                <div
                  key={dayNum}
                  onClick={() => topItem && onRestoreItem(topItem)}
                  className={`h-10 rounded-xl flex flex-col items-center justify-center text-xs relative transition-all ${
                    topItem
                      ? 'bg-purple-600/30 border border-purple-400/50 hover:bg-purple-600/60 cursor-pointer shadow-sm'
                      : 'bg-white/5 text-gray-400'
                  }`}
                  title={topItem ? `${dayNum} ${monthNames[month]}: ${MOOD_NAMES[topItem.mood] || topItem.mood}` : `${dayNum} ${monthNames[month]}`}
                >
                  <span className="text-[9px] font-bold opacity-60 absolute top-1 left-1.5">{dayNum}</span>
                  {emoji && <span className="text-sm mt-1">{emoji}</span>}
                </div>
              );
            })}
          </div>
        </div>

        {/* Duygu Dağılım Barları */}
        <div className="bg-black/40 border border-white/10 rounded-2xl p-4 sm:p-5 space-y-3">
          <h3 className="text-sm font-bold text-white flex items-center gap-2">
            <span>📊</span> Duygu Dağılım Oranları
          </h3>

          {totalEntries === 0 ? (
            <p className="text-xs text-gray-400 italic">Henüz kaydedilmiş reçete yok. Reçete oluşturdukça grafiğiniz dolacaktır.</p>
          ) : (
            <div className="space-y-2">
              {Object.entries(moodCounts).map(([mKey, count]) => {
                const pct = Math.round((count / totalEntries) * 100);
                return (
                  <div key={mKey} className="space-y-1">
                    <div className="flex justify-between text-xs text-gray-300">
                      <span className="flex items-center gap-1.5">
                        <span>{MOOD_EMOJIS[mKey] || '🎵'}</span>
                        <span>{MOOD_NAMES[mKey] || mKey}</span>
                      </span>
                      <span className="font-mono text-purple-300 font-bold">{count} kez (%{pct})</span>
                    </div>
                    <div className="w-full h-2 rounded-full bg-white/10 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Pro Banner: Terapist PDF Raporu */}
        <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-900/40 via-pink-900/40 to-indigo-900/40 border border-purple-400/40 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <h4 className="text-sm font-bold text-white flex items-center gap-1.5">
              <span>📄</span> 30 Günlük Kapsamlı Psikoloji & Müzik Analiz Raporu
            </h4>
            <p className="text-xs text-gray-300 mt-0.5">
              Ruh halinin dalgalanmaları, stres haritan ve terapötik müzik tavsiyeleri içeren kişiye özel PDF rapor.
            </p>
          </div>
          <button
            onClick={handleDownloadReport}
            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-pink-500 hover:from-amber-400 hover:to-pink-400 text-black font-extrabold text-xs rounded-xl shadow-lg transition-transform hover:scale-105 cursor-pointer shrink-0"
          >
            {isPro ? 'PDF Raporu İndir ↗' : '👑 Pro ile Rapor Al'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MoodJournalModal;
