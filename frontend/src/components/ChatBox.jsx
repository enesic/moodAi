import React, { useState, useEffect, useRef } from 'react';
import { analyze, searchTracks, searchAutocomplete } from '../api/client';

const ALT_TURLER = {
    "neseli_pop": ["Pop & Dans", "Disco & Retro Pop", "Yaz Hitleri", "K-Pop", "Latin Pop"],
    "huzunlu_slow": ["Slow & Balad", "Melankolik Slow", "Akustik Hüzün", "Piyano & Yağmur", "Kırık Kalpler"],
    "enerjik_spor": ["Workout & Motivasyon", "Yüksek BPM Trap", "Power Drill", "Club & Techno Hits"],
    "sakin_akustik": ["Lo-Fi Beats", "Akustik Gitar & Chill", "Soft Pop", "Coffeehouse Akustik", "Ambient & Dinginlik"],
    "indie_alternatif": ["Modern Indie Rock", "Dream Pop", "Shoegaze", "Alternatif Rock", "Bohem & Nostalji"],
    "hard_rock_metal": ["Klasik Rock", "Hard Rock", "Heavy Metal", "Nu-Metal", "Punk & Grunge"],
    "rap_hiphop": ["Modern Trap", "Old School & Boom Bap", "Melodik Rap", "Drill & Underground"],
    "jazz_blues": ["Smooth Jazz", "Vocal Jazz", "Blues & Soul", "Gece Mavisi Jazz"],
    "elektronik_synth": ["Synthwave & Neon", "Deep House", "Minimal Techno", "EDM & Festival"]
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
  const [activeTab, setActiveTab] = useState('search'); // 'search' (iLoveThatTrack) veya 'therapist'
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1); 
  const [analysisResult, setAnalysisResult] = useState(null);
  
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [language, setLanguage] = useState('mix');
  const [count, setCount] = useState(20);
  const [energyLevel, setEnergyLevel] = useState('Orta');

  // Canlı Şarkı Arama & Seçim (iLoveThatTrack Modu)
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedTracks, setSelectedTracks] = useState([]);
  const searchTimeoutRef = useRef(null);

  // Canlı Arama (Debounced Autocomplete)
  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      return;
    }

    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    searchTimeoutRef.current = setTimeout(async () => {
      setSearching(true);
      try {
        const data = await searchAutocomplete(searchQuery, accessToken);
        setSearchResults(data.tracks || []);
      } catch (err) {
        console.error(err);
      } finally {
        setSearching(false);
      }
    }, 280);

    return () => clearTimeout(searchTimeoutRef.current);
  }, [searchQuery, accessToken]);

  const handleSelectTrack = (track) => {
    if (!selectedTracks.some(t => t.id === track.id)) {
      if (selectedTracks.length >= 5) {
        alert('En fazla 5 referans şarkı seçebilirsiniz.');
        return;
      }
      setSelectedTracks([...selectedTracks, track]);
    }
    setSearchQuery('');
    setSearchResults([]);
  };

  const handleRemoveTrack = (trackId) => {
    setSelectedTracks(selectedTracks.filter(t => t.id !== trackId));
  };

  const handleAnalyzeAndDiscover = async (customText) => {
    const textToAnalyze = customText || text;
    const hasSeeds = selectedTracks.length > 0;
    
    if (!textToAnalyze.trim() && !hasSeeds) {
      alert('Lütfen ruh halinizi yazın veya arama kutusundan en az bir şarkı seçin.');
      return;
    }

    setLoading(true);
    try {
      let queryText = textToAnalyze.trim();
      if (!queryText && hasSeeds) {
        queryText = `Sevdiğim referans parçalar: ${selectedTracks.map(t => `${t.name} - ${t.artist}`).join(', ')}`;
      }

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
      const seed_inputs = selectedTracks.map(t => t.name ? `${t.name} ${t.artist}` : t.id);
      const params = {
        access_token: accessToken || null,
        mood: analysisResult.mood,
        language: language,
        genres: selectedGenres,
        count: parseInt(count),
        energy_level: energyLevel,
        seed_inputs: seed_inputs
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
      {/* Başlık ve Mod Geçiş Sekmeleri */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <h2 className="text-xl font-bold text-white flex items-center">
          <span className="mr-2">🎧</span> Müzik Keşif Motoru
        </h2>

        {step === 1 && (
          <div className="flex bg-black/40 p-1 rounded-xl border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('search')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${activeTab === 'search' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
              🔍 Şarkı Seçerek
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('therapist')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${activeTab === 'therapist' ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
            >
              🛋️ Terapi Koltuğu
            </button>
          </div>
        )}
      </div>

      {step === 1 && (
        <div className="space-y-4">
          {/* TAB 1: iLoveThatTrack Tarzı Canlı Şarkı Arama & Seçim */}
          {activeTab === 'search' && (
            <div className="space-y-3 animate-fadeIn">
              <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider">
                Sevdiğin Bir Şarkıyı Ara ve Seç (iLoveThatTrack Modu)
              </label>

              <div className="relative">
                <div className="flex items-center bg-black/40 border border-white/15 rounded-2xl px-4 py-3 focus-within:border-purple-400 focus-within:ring-2 focus-within:ring-purple-500/30 transition-all">
                  <span className="text-gray-400 mr-2.5">🔍</span>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Şarkı veya sanatçı adı yaz (Örn: Duman, The Weeknd, Mabel Matiz...)"
                    className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
                  />
                  {searching && <span className="animate-spin text-xs text-purple-400 ml-2">⏳</span>}
                </div>

                {/* Açılır Arama Sonuçları (Dropdown) */}
                {searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-[#120a24]/95 backdrop-blur-xl border border-purple-500/30 rounded-2xl shadow-2xl overflow-hidden z-50 max-h-72 overflow-y-auto divide-y divide-white/5">
                    {searchResults.map((track) => (
                      <div
                        key={track.id}
                        onClick={() => handleSelectTrack(track)}
                        className="p-2.5 flex items-center gap-3 hover:bg-purple-600/20 cursor-pointer transition-colors"
                      >
                        <img
                          src={track.image || "https://placehold.co/80x80?text=🎵"}
                          alt={track.name}
                          className="w-10 h-10 rounded-lg object-cover shadow"
                        />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-semibold text-white truncate">{track.name}</p>
                          <p className="text-xs text-gray-400 truncate">{track.artist} • {track.album}</p>
                        </div>
                        <span className="text-xs font-bold text-purple-300 bg-purple-500/20 px-2 py-1 rounded-lg">
                          + Seç
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Seçilen Şarkılar Kartı */}
              {selectedTracks.length > 0 ? (
                <div className="space-y-2 pt-1">
                  <span className="text-xs text-purple-300 font-semibold flex items-center gap-1">
                    <span>✨</span> Seçilen Referans Şarkılar ({selectedTracks.length}/5):
                  </span>
                  <div className="grid grid-cols-1 gap-2">
                    {selectedTracks.map((track) => (
                      <div
                        key={track.id}
                        className="flex items-center justify-between p-2.5 bg-purple-950/40 border border-purple-400/30 rounded-xl"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <img
                            src={track.image || "https://placehold.co/60x60?text=🎵"}
                            alt={track.name}
                            className="w-8 h-8 rounded-lg object-cover"
                          />
                          <div className="truncate">
                            <p className="text-xs font-bold text-white truncate">{track.name}</p>
                            <p className="text-[11px] text-gray-400 truncate">{track.artist}</p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleRemoveTrack(track.id)}
                          className="text-gray-400 hover:text-red-400 p-1 text-sm font-bold cursor-pointer"
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-[11px] text-gray-400 italic">
                  💡 İpucu: Sevdiğiniz 1 veya daha fazla şarkıyı seçin; yapay zeka müzikal benzerliklerine göre size özel çalma listesi oluştursun.
                </p>
              )}
            </div>
          )}

          {/* TAB 2: Terapi Koltuğu (Duygu Yazarak) */}
          {activeTab === 'therapist' && (
            <div className="space-y-3 animate-fadeIn">
              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Hızlı Duygu Seçimi
                </label>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {QUICK_MOODS.map((qm, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => handleQuickMood(qm.text)}
                      className="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-purple-600/30 border border-white/10 hover:border-purple-400/40 text-xs font-medium text-gray-200 transition-all cursor-pointer flex items-center gap-1.5"
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
                  className="w-full h-24 bg-black/30 border border-white/10 rounded-xl p-3.5 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none text-sm leading-relaxed"
                  placeholder="Örn: Bugün çok yorucu bir gündü, hiçbir şey yapmak istemiyorum..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* Keşfet Butonu */}
          <button
            onClick={() => handleAnalyzeAndDiscover()}
            disabled={loading || (!text.trim() && selectedTracks.length === 0)}
            className="w-full bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3.5 px-6 rounded-2xl transition-all duration-300 disabled:opacity-50 flex justify-center items-center gap-2 cursor-pointer shadow-lg shadow-purple-600/25 transform hover:scale-[1.01]"
          >
            {loading ? (
              <span className="animate-spin text-xl">⏳ Analiz Ediliyor...</span>
            ) : (
              <>
                <span>🚀</span>
                <span>{selectedTracks.length > 0 ? "Benzer Şarkıları & Reçeteyi Keşfet" : "Ruh Halini Analiz Et & Şarkıları Bul"}</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* ADIM 2: Kategori & Tercih Onayı */}
      {step === 2 && analysisResult && (
        <div className="space-y-6 animate-fadeIn">
          <div className="p-4 bg-purple-900/40 rounded-2xl border border-purple-500/30 flex justify-between items-center">
            <div>
              <h3 className="text-purple-300 text-xs uppercase font-bold tracking-wider mb-1">Teşhis Edilen Ruh Hali & Tarz</h3>
              <p className="text-white text-lg font-bold capitalize">{analysisResult.mood.replace(/_/g, ' ')}</p>
            </div>
            <span className="text-xs px-3 py-1 rounded-full bg-white/10 text-purple-200 border border-purple-400/30 font-medium">
              ⚡ Doğrusal Vektör Motoru
            </span>
          </div>

          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <label className="block text-gray-300 text-sm font-medium">Önerilen Müzik Türleri</label>
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
              <label className="block text-gray-300 text-sm font-medium">Dil Tercihi</label>
              <select 
                value={language} 
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
              >
                <option value="tr">🇹🇷 Türkçe (Sadece TR Sanatçılar)</option>
                <option value="en">🌍 Yabancı (Sadece Global Hitler)</option>
                <option value="mix">✨ Karışık (%50 TR / %50 Global)</option>
              </select>
            </div>
            
            <div className="space-y-2">
              <label className="block text-gray-300 text-sm font-medium">Enerji Seviyesi</label>
              <select 
                value={energyLevel} 
                onChange={(e) => setEnergyLevel(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl p-3 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
              >
                <option value="Düşük">Düşük (Sakin / Akustik)</option>
                <option value="Orta">Orta (Dengeli Tempo)</option>
                <option value="Yüksek">Yüksek (Dinamik / Dans)</option>
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="flex justify-between text-gray-300 text-sm font-medium">
              <span>Şarkı Sayısı</span>
              <span>{count} Şarkı</span>
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
              className="px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-all cursor-pointer"
            >
              Geri
            </button>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold py-3 px-6 rounded-xl transition-all disabled:opacity-50 flex justify-center items-center shadow-[0_0_15px_rgba(16,185,129,0.4)] cursor-pointer"
            >
              {loading ? <span className="animate-spin text-xl">⏳</span> : <span>Reçeteyi Oluştur 🎵</span>}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBox;
