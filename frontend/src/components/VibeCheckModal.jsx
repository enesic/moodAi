import React, { useState } from 'react';
import { getVibeCard, searchTracks } from '../api/client';

const MOODS = [
  { id: 'neseli_pop', label: 'Neşeli & Dans', valence: 0.85, arousal: 0.75, emoji: '🎉' },
  { id: 'huzunlu_slow', label: 'Hüzünlü & Melankolik', valence: -0.85, arousal: 0.2, emoji: '💔' },
  { id: 'enerjik_spor', label: 'Enerjik & Güçlü', valence: 0.5, arousal: 0.95, emoji: '⚡' },
  { id: 'sakin_akustik', label: 'Sakin & Huzurlu', valence: 0.5, arousal: 0.15, emoji: '☕' },
  { id: 'hard_rock_metal', label: 'Öfkeli & İsyankar', valence: -0.7, arousal: 0.95, emoji: '🔥' },
  { id: 'indie_alternatif', label: 'Özgün & Derin', valence: 0.1, arousal: 0.4, emoji: '🌌' },
  { id: 'rap_hiphop', label: 'Sokak & Ritim', valence: 0.2, arousal: 0.8, emoji: '🎤' },
  { id: 'jazz_blues', label: 'Gece & Nostalji', valence: 0.2, arousal: 0.35, emoji: '🎷' },
  { id: 'elektronik_synth', label: 'Fütüristik & Rave', valence: 0.5, arousal: 0.9, emoji: '🕹️' },
];

const VibeCheckModal = ({
  isOpen,
  onClose,
  currentUserMood,
  accessToken,
  showToast,
  onCommonTracksReady
}) => {
  const [person1Name, setPerson1Name] = useState('Ben');
  const [person2Name, setPerson2Name] = useState('Arkadaşım');
  const [selectedMood1, setSelectedMood1] = useState(currentUserMood || 'sakin_akustik');
  const [selectedMood2, setSelectedMood2] = useState('neseli_pop');

  const [result, setResult] = useState(null);
  const [downloadingCard, setDownloadingCard] = useState(false);
  const [copiedLink, setCopiedLink] = useState(false);
  const [calculating, setCalculating] = useState(false);

  if (!isOpen) return null;

  const handleCalculateVibe = async () => {
    setCalculating(true);
    try {
      const m1Obj = MOODS.find(m => m.id === selectedMood1) || MOODS[0];
      const m2Obj = MOODS.find(m => m.id === selectedMood2) || MOODS[1];

      // Valence ve arousal farkına göre mesafe
      const dv = m1Obj.valence - m2Obj.valence;
      const da = m1Obj.arousal - m2Obj.arousal;
      const dist = Math.sqrt(dv * dv + da * da); // max around 2.2
      // Normalize score between 40% and 99%
      let score = Math.round(98 - (dist * 26));
      score = Math.max(45, Math.min(99, score));

      // Teşhis ve yorum metni
      let verdict = '';
      if (m1Obj.id === m2Obj.id) {
        score = 99;
        verdict = 'Aynı dalga boyundasınız! İki ruh hali kusursuz bir ahenkle birbirini kopyalıyor ve büyütüyor.';
      } else if (score >= 80) {
        verdict = 'Mükemmel bir frekans rezonansı! Farklı duygularda olsanız bile birbirinizi anında şifalandıran ve tamamlayan bir çekim var.';
      } else if (score >= 65) {
        verdict = 'Zıt kutuplar birbirini çeker! Biri sakin liman olurken diğeri kıvılcım çakıyor; birbirinizi dengeleyen tatlı bir kontrast.';
      } else {
        verdict = 'Farklı dünyaların tınıları! Biriniz fırtınayı yaşarken diğeriniz dinginlik arıyor; ortak müzik sizi tam ortada buluşturacak.';
      }

      // Ortak şarkı arama
      let tracks = [];
      try {
        const searchRes = await searchTracks({
          access_token: accessToken,
          mood: m1Obj.id,
          language: 'mix',
          genres: [],
          count: 10,
          energy_level: 'Orta',
          therapy_mode: 'uplift',
        });
        tracks = searchRes.tracks || [];
      } catch (_) {}

      const featuredTrack = tracks[0] || {
        name: 'Duygusal Rezonans',
        artist: 'Mood AI Frekansı',
        image: null,
      };

      setResult({
        user1: person1Name,
        user2: person2Name,
        mood1: m1Obj,
        mood2: m2Obj,
        score,
        verdict,
        featuredTrack,
        tracks,
      });

      showToast?.(`Frekans uyumunuz hesaplandı: %${score}! ⚡`, 'success');
    } catch (err) {
      console.error(err);
      showToast?.('Uyum hesaplanırken bir sorun oluştu.', 'error');
    } finally {
      setCalculating(false);
    }
  };

  const handleDownloadVibeCard = async () => {
    if (!result) return;
    setDownloadingCard(true);
    try {
      const blob = await getVibeCard({
        user1_name: result.user1,
        user2_name: result.user2,
        mood1_label: result.mood1.label,
        mood2_label: result.mood2.label,
        match_score: result.score,
        verdict: result.verdict,
        sarki_adi: result.featuredTrack?.name || 'Ortak Frekans',
        sanatci_adi: result.featuredTrack?.artist || 'Mood AI',
        image_url: result.featuredTrack?.image || null,
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vibe-match-${result.user1}-${result.user2}.png`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
      showToast?.('Vibe Match Instagram Story kartı indirildi! 📸', 'success');
    } catch (err) {
      console.error(err);
      showToast?.('Kart indirilemedi.', 'error');
    } finally {
      setDownloadingCard(false);
    }
  };

  const handleCopyShareLink = () => {
    const shareUrl = `${window.location.origin}/?vibe_from=${encodeURIComponent(person1Name)}&vibe_mood=${selectedMood1}`;
    navigator.clipboard.writeText(shareUrl);
    setCopiedLink(true);
    showToast?.('Özel Vibe Check davet linki panoya kopyalandı! 📋', 'info');
    setTimeout(() => setCopiedLink(false), 3000);
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-5 animate-fadeIn">
      <div className="bg-[#120a26] border border-pink-500/30 rounded-3xl p-5 sm:p-7 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl flex flex-col space-y-5 scrollbar-thin scrollbar-thumb-pink-500/30">
        {/* Header */}
        <div className="flex justify-between items-start border-b border-white/10 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-2xl">⚡</span>
              <h2 className="text-xl sm:text-2xl font-black text-white tracking-tight">
                Vibe Check: Çift & Arkadaş Frekans Uyumu
              </h2>
            </div>
            <p className="text-xs text-gray-400 mt-1">
              İki kişinin ruh halini çarpıştırın; frekans uyumunuzu ve ortak terapi reçetenizi keşfedin.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl p-1.5 rounded-xl hover:bg-white/10 transition-colors cursor-pointer"
          >
            ✕
          </button>
        </div>

        {/* Karşılaştırma Formu */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/* 1. Kişi */}
          <div className="p-4 rounded-2xl bg-purple-950/30 border border-purple-500/30 space-y-3">
            <span className="text-[11px] font-bold text-purple-300 uppercase tracking-wider">1. Kişi (Sen)</span>
            <input
              type="text"
              value={person1Name}
              onChange={(e) => setPerson1Name(e.target.value)}
              placeholder="Adın veya takma adın"
              className="w-full glass-input rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none"
            />
            <label className="block text-[11px] text-gray-400 font-medium">Ruh Hali:</label>
            <select
              value={selectedMood1}
              onChange={(e) => setSelectedMood1(e.target.value)}
              className="w-full glass-input rounded-xl p-2.5 text-xs text-white focus:outline-none cursor-pointer"
            >
              {MOODS.map(m => (
                <option key={m.id} value={m.id}>
                  {m.emoji} {m.label}
                </option>
              ))}
            </select>
          </div>

          {/* 2. Kişi */}
          <div className="p-4 rounded-2xl bg-pink-950/30 border border-pink-500/30 space-y-3">
            <span className="text-[11px] font-bold text-pink-300 uppercase tracking-wider">2. Kişi (Arkadaşın / Sevgilin)</span>
            <input
              type="text"
              value={person2Name}
              onChange={(e) => setPerson2Name(e.target.value)}
              placeholder="Arkadaşının adı"
              className="w-full glass-input rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none"
            />
            <label className="block text-[11px] text-gray-400 font-medium">Onun Ruh Hali:</label>
            <select
              value={selectedMood2}
              onChange={(e) => setSelectedMood2(e.target.value)}
              className="w-full glass-input rounded-xl p-2.5 text-xs text-white focus:outline-none cursor-pointer"
            >
              {MOODS.map(m => (
                <option key={m.id} value={m.id}>
                  {m.emoji} {m.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Aksiyon Butonları */}
        <div className="flex flex-col sm:flex-row gap-2.5">
          <button
            onClick={handleCalculateVibe}
            disabled={calculating}
            className="flex-1 py-3 px-5 rounded-2xl bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-extrabold text-sm shadow-lg shadow-pink-600/25 transition-all cursor-pointer flex items-center justify-center gap-2"
          >
            {calculating ? (
              <span className="animate-spin">⏳ Frekanslar Hesaplanıyor...</span>
            ) : (
              <>
                <span>⚡</span> <span>Frekans Uyumunu Hesapla</span>
              </>
            )}
          </button>

          <button
            onClick={handleCopyShareLink}
            className="py-3 px-4 rounded-2xl bg-white/5 hover:bg-white/10 text-pink-200 border border-white/10 text-xs font-semibold transition-all cursor-pointer flex items-center justify-center gap-1.5 shrink-0"
          >
            <span>🔗</span>
            <span>{copiedLink ? 'Link Kopyalandı!' : 'Davet Linki Kopyala'}</span>
          </button>
        </div>

        {/* Sonuç Kartı */}
        {result && (
          <div className="mt-2 p-5 rounded-3xl bg-black/50 border border-pink-500/40 space-y-4 animate-fadeIn">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-3 border-b border-white/10 pb-4">
              <div>
                <span className="text-[10px] text-pink-400 uppercase font-black tracking-widest">
                  FREKANS UYUM RAPORU
                </span>
                <h3 className="text-xl font-black text-white flex items-center gap-2 mt-0.5">
                  <span>{result.user1}</span>
                  <span className="text-pink-400">⚡</span>
                  <span>{result.user2}</span>
                </h3>
              </div>
              <div className="text-center sm:text-right">
                <span className="text-4xl sm:text-5xl font-black bg-clip-text text-transparent bg-gradient-to-r from-pink-400 via-purple-300 to-indigo-300">
                  %{result.score}
                </span>
                <p className="text-[10px] text-gray-400 font-bold uppercase tracking-wider">Uyum Skoru</p>
              </div>
            </div>

            <div className="bg-white/5 rounded-2xl p-4 text-xs text-gray-200 leading-relaxed italic border-l-2 border-pink-400">
              "{result.verdict}"
            </div>

            {/* Öne Çıkan Parça */}
            {result.featuredTrack && (
              <div className="p-3 bg-pink-950/20 border border-pink-500/20 rounded-2xl flex items-center justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-xl bg-pink-500/20 flex items-center justify-center text-lg shrink-0">
                    🎵
                  </div>
                  <div className="truncate">
                    <p className="text-[10px] uppercase font-bold text-gray-400">Ortak Frekans Parçası</p>
                    <p className="text-xs font-bold text-white truncate">{result.featuredTrack.name}</p>
                    <p className="text-[11px] text-gray-400 truncate">{result.featuredTrack.artist}</p>
                  </div>
                </div>

                {result.tracks.length > 0 && (
                  <button
                    onClick={() => {
                      onCommonTracksReady?.(result.tracks, {
                        mood: result.mood1.id,
                        language: 'mix',
                        genres: [],
                        energy_level: 'Orta',
                        therapy_mode: 'uplift',
                      });
                      onClose();
                    }}
                    className="px-3 py-1.5 bg-purple-600/40 hover:bg-purple-600 text-purple-200 hover:text-white rounded-xl text-xs font-bold transition-all cursor-pointer shrink-0"
                  >
                    Listeyi Aç ↗
                  </button>
                )}
              </div>
            )}

            {/* Story Kartı İndir */}
            <div className="pt-2">
              <button
                onClick={handleDownloadVibeCard}
                disabled={downloadingCard}
                className="w-full py-3.5 bg-gradient-to-r from-pink-600 via-purple-600 to-indigo-600 hover:from-pink-500 hover:to-indigo-500 text-white font-extrabold text-xs rounded-2xl transition-all flex items-center justify-center gap-2 shadow-lg shadow-pink-600/30 cursor-pointer disabled:opacity-50"
              >
                {downloadingCard ? (
                  <span className="animate-spin">⏳ Instagram Story Kartı Hazırlanıyor...</span>
                ) : (
                  <>
                    <span>📸</span> <span>9:16 Instagram Story Uyum Kartı İndir</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VibeCheckModal;
