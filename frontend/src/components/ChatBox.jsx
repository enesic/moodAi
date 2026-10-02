import React, { useState } from 'react';
import { analyze, searchTracks } from '../api/client';

const ALT_TURLER = {
    "neseli_pop": ["Türkçe Pop Hareketli", "Yaz Hitleri", "Dance Pop", "Road Trip", "Serdar Ortaç Pop", "90'lar Türkçe Pop", "Disco", "K-Pop", "Reggaeton"],
    "huzunlu_slow": ["Akustik Hüzün", "Melankolik Indie", "Slow Pop", "Piyano & Yağmur", "Türkçe Damar", "Alternatif Balad", "Türkü", "Arabesk", "Kırık Kalpler"],
    "enerjik_spor": ["Spor Motivasyon", "Türkçe Rap", "Phonk", "Drill", "Techno", "House", "Gym Hits", "Power Workout", "Remix"],
    "sakin_akustik": ["Lo-Fi Beats", "Chill Pop", "Akustik Cover", "Jazz Vibes", "Enstrümantal", "Kitap Okuma", "Kahve Modu", "Ambient", "Soft Rock", "Sufi/Ney"],
    "indie_alternatif": ["Alternatif Rock", "Yeni Nesil Indie", "Anadolu Rock", "Shoegaze", "Soft Indie", "Bağımsız Müzik", "Dream Pop"],
    "hard_rock_metal": ["Türkçe Rock", "Anadolu Rock", "Heavy Metal", "Nu-Metal", "Hard Rock", "Punk", "Garage Rock"],
    "rap_hiphop": ["Türkçe Rap", "Old School", "Melodic Rap", "Trap", "Arabesk Rap", "Drill", "Underground"],
    "jazz_blues": ["Smooth Jazz", "Gece Mavisi", "Blues Rock", "Soul", "Vocal Jazz", "Türkçe Caz", "Coffee Table Jazz"],
    "elektronik_synth": ["Synthwave", "Cyberpunk", "Deep House", "Minimal Techno", "EDM", "Daft Punk Vibe"]
};

const QUICK_MOODS = [
  { emoji: "☕", label: "Sakin & Dinlenme", text: "Bugün çok yoruldum, biraz sakinleşmek, kahvemi içip kafamı dinlemek istiyorum." },
  { emoji: "💔", label: "Kırık Kalp & Efkar", text: "İçimde tarif edemediğim bir hüzün ve boşluk var, canım çok sıkkın." },
  { emoji: "⚡", label: "Spor & Motivasyon", text: "Spora başlıyorum, enerjimi zirveye çıkaracak yüksek tempolu ve güçlü ritimler lazım!" },
  { emoji: "🎉", label: "Neşe & Kutlama", text: "Bugün harika bir haber aldım, modum çok yüksek, dans edip kutlamak istiyorum!" },
  { emoji: "🌧️", label: "Gece Düşünceleri", text: "Gece oldu, pencere kenarında oturup geçmişi ve hayatı düşünüyorum." },
  { emoji: "🔥", label: "Öfke & Deşarj", text: "Her şey üstüme geliyor, çok sinirliyim ve öfkemi müzikle dışarı vurmak istiyorum." },
];

const ChatBox = ({ onAnalyzed, onTracksReady, accessToken }) => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); 
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [language, setLanguage] = useState('mix');
  const [count, setCount] = useState(20);
  const [energyLevel, setEnergyLevel] = useState('Orta');

  // Referans Şarkı ve Playlist Linkleri
  const [seedInputs, setSeedInputs] = useState([]);
  const [currentSeed, setCurrentSeed] = useState('');

  const handleAddSeed = () => {
    if (!currentSeed.trim()) return;
    if (!seedInputs.includes(currentSeed.trim())) {
      setSeedInputs([...seedInputs, currentSeed.trim()]);
    }
    setCurrentSeed('');
  };

  const handleRemoveSeed = (idx) => {
    setSeedInputs(seedInputs.filter((_, i) => i !== idx));
  };

  const handleAnalyze = async (customText) => {
    const textToAnalyze = customText || text;
    if (!textToAnalyze.trim() && seedInputs.length === 0) return;
    setLoading(true);
    try {
      // Eğer metin yazılmadıysa sadece referans şarkılardan analiz üret
      const queryText = textToAnalyze.trim() || `Sevdiğim referans parçalar: ${seedInputs.join(', ')}`;
      const result = await analyze(queryText);
      setAnalysisResult(result);
      if (result.suggested_genres && result.suggested_genres.length > 0) {
          setSelectedGenres(result.suggested_genres);
      }
      onAnalyzed(result);
      setStep(2);
    } catch (error) {
      console.error(error);
      alert('Analiz sırasında bir hata oluştu. Backend bağlantısını kontrol edin.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickMood = (presetText) => {
    setText(presetText);
  };

  const handleSearch = async () => {
    setLoading(true);
    try {
      const params = {
        access_token: accessToken || null,
        mood: analysisResult.mood,
        language: language,
        genres: selectedGenres,
        count: parseInt(count),
        energy_level: energyLevel,
        seed_inputs: seedInputs
      };
      const result = await searchTracks(params);
      onTracksReady(result.tracks, { mood: analysisResult.mood, language, genres: selectedGenres });
    } catch (error) {
      console.error(error);
      alert('Şarkılar aranırken bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  const toggleGenre = (genre) => {
    setSelectedGenres(prev => 
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  return (
    <div className="bg-white/10 backdrop-blur-lg rounded-3xl p-6 shadow-xl border border-white/20">
      <h2 className="text-2xl font-bold mb-4 text-white flex items-center">
        <span className="mr-2">🛋️</span> Terapi Koltuğu
      </h2>

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
              Hızlı Duygu Seçimi
            </label>
            <div className="flex flex-wrap gap-2 mb-4">
              {QUICK_MOODS.map((qm, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleQuickMood(qm.text)}
                  className="px-3 py-1.5 rounded-xl bg-white/5 hover:bg-purple-600/30 border border-white/10 hover:border-purple-400/40 text-xs font-medium text-gray-200 transition-all cursor-pointer flex items-center gap-1.5 hover:scale-105"
                >
                  <span>{qm.emoji}</span>
                  <span>{qm.label}</span>
                </button>
              ))}
            </div>

            <label className="block text-gray-300 text-sm font-medium mb-1.5">
              Şu an nasıl hissediyorsun? İçinden geçenleri yaz...
            </label>
            <textarea
              className="w-full h-24 bg-black/30 border border-white/10 rounded-xl p-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm leading-relaxed"
              placeholder="Örn: Bugün çok yorucu bir gündü, hiçbir şey yapmak istemiyorum..."
              value={text}
              onChange={(e) => setText(e.target.value)}
            />
          </div>

          {/* Yeni Özellik: Referans Şarkı / Playlist Linkleri */}
          <div className="p-3.5 bg-black/25 rounded-2xl border border-white/10 space-y-2.5">
            <div className="flex justify-between items-center">
              <label className="text-gray-300 text-xs font-semibold flex items-center gap-1.5">
                <span>🎵</span> Referans Şarkı veya Çalma Listesi (Opsiyonel)
              </label>
              <span className="text-[10px] text-purple-300 bg-purple-900/40 px-2 py-0.5 rounded-full border border-purple-500/30">
                Benzerlik Motoru
              </span>
            </div>
            
            <div className="flex gap-2">
              <input
                type="text"
                value={currentSeed}
                onChange={(e) => setCurrentSeed(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddSeed())}
                placeholder="Spotify linki veya Şarkı Adı (Örn: Duman - Koyu)"
                className="flex-1 bg-black/40 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-purple-400"
              />
              <button
                type="button"
                onClick={handleAddSeed}
                className="px-3.5 py-2 bg-purple-600/60 hover:bg-purple-600 text-white rounded-xl text-xs font-semibold transition-all cursor-pointer"
              >
                + Ekle
              </button>
            </div>

            {seedInputs.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {seedInputs.map((seed, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-purple-950/80 border border-purple-400/40 text-purple-200 rounded-lg text-[11px]"
                  >
                    <span className="max-w-[180px] truncate">{seed}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveSeed(idx)}
                      className="text-gray-400 hover:text-red-400 font-bold ml-1"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => handleAnalyze()}
            disabled={loading || (!text.trim() && seedInputs.length === 0)}
            className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold py-3.5 px-6 rounded-xl transition-all disabled:opacity-50 flex justify-center items-center gap-2 cursor-pointer shadow-lg shadow-purple-600/20"
          >
            {loading ? <span className="animate-spin text-xl">⏳</span> : <><span>✨</span><span>Ruh Halini & Referansları Analiz Et</span></>}
          </button>
        </div>
      )}

      {step === 2 && analysisResult && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-4 bg-purple-900/40 rounded-2xl border border-purple-500/30 flex justify-between items-center">
            <div>
              <h3 className="text-purple-300 text-xs uppercase font-bold tracking-wider mb-1">Teşhis Edilen Ruh Hali</h3>
              <p className="text-white text-lg font-bold capitalize">{analysisResult.mood.replace(/_/g, ' ')}</p>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-purple-400/30 font-medium">
              {analysisResult.engine?.includes("gemini") ? "🤖 Gemini AI" : "⚡ Akıllı NLP Motoru"}
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="block text-gray-300 text-sm font-medium">Bu Ruh Hali İçin Uygun Müzik Türleri</label>
              <span className="text-xs text-purple-400 font-semibold">{selectedGenres.length} tür seçili</span>
            </div>
            <div className="flex flex-wrap gap-2 pr-1">
              {(ALT_TURLER[analysisResult.mood] || []).map(genre => {
                const isSelected = selectedGenres.includes(genre);
                return (
                  <button
                    key={genre}
                    type="button"
                    onClick={() => toggleGenre(genre)}
                    className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer border ${isSelected ? 'bg-gradient-to-r from-purple-500 to-indigo-600 border-purple-400 text-white shadow-md shadow-purple-500/30 scale-105' : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10 hover:border-white/20'}`}
                  >
                    {isSelected ? `✓ ${genre}` : `+ ${genre}`}
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="block text-gray-300 text-sm font-medium">Dil</label>
              <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="mix">Karışık</option>
                <option value="tr">Türkçe</option>
                <option value="en">Yabancı</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="block text-gray-300 text-sm font-medium">Enerji</label>
              <select 
                value={energyLevel} 
                onChange={(e) => setEnergyLevel(e.target.value)}
                className="w-full bg-black/30 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="Düşük">Düşük</option>
                <option value="Orta">Orta</option>
                <option value="Yüksek">Yüksek</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex justify-between text-gray-300 text-sm font-medium">
              <span>Şarkı Sayısı</span>
              <span>{count}</span>
            </label>
            <input 
              type="range" 
              min="5" 
              max="50" 
              value={count} 
              onChange={(e) => setCount(e.target.value)}
              className="w-full accent-purple-500 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-all"
            >
              Geri
            </button>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold py-3 px-6 rounded-xl transition-all disabled:opacity-50 flex justify-center items-center shadow-[0_0_15px_rgba(16,185,129,0.4)]"
            >
              {loading ? <span className="animate-spin text-xl">⏳</span> : <span>Listeyi Oluştur 🎵</span>}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBox;
