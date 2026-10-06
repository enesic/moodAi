import React, { useState, useEffect, useRef } from 'react';
import { analyze, searchTracks, searchAutocomplete } from '../api/client';

const DEFAULT_QUICK_MOODS = [
  { emoji: "☕", label: "Sakin & Dinlenme", text: "Bugün çok yoruldum, biraz sakinleşmek, kahvemi içip kafamı dinlemek istiyorum." },
  { emoji: "💔", label: "Kırık Kalp & Efkar", text: "İçimde tarif edemediğim bir hüzün ve boşluk var, canım çok sıkkın." },
  { emoji: "⚡", label: "Spor & Motivasyon", text: "Spora başlıyorum, enerjimi zirveye çıkaracak yüksek tempolu ve güçlü ritimler lazım!" },
  { emoji: "🎉", label: "Neşe & Kutlama", text: "Bugün harika bir haber aldım, modum çok yüksek, dans edip kutlamak istiyorum!" },
  { emoji: "🌧️", label: "Gece Düşünceleri", text: "Gece oldu, pencere kenarında oturup geçmişi ve hayatı düşünüyorum." },
  { emoji: "🔥", label: "Öfke & Deşarj", text: "Her şey üstüme geliyor, çok sinirliyim ve öfkemi müzikle dışarı vurmak istiyorum." },
];

const ChatBox = ({ onAnalyzed, onTracksReady, accessToken, meta, showToast }) => {
  const [activeTab, setActiveTab] = useState('therapist'); // 'therapist' veya 'search'
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(1);
  const [analysisResult, setAnalysisResult] = useState(null);

  // Reçete Ayarları
  const [selectedGenres, setSelectedGenres] = useState([]);
  const [language, setLanguage] = useState('mix');
  const [count, setCount] = useState(20);
  const [energyLevel, setEnergyLevel] = useState('Orta');
  const [therapyMode, setTherapyMode] = useState('catharsis');

  // iLoveThatTrack modu
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [selectedTracks, setSelectedTracks] = useState([]);
  const searchTimeoutRef = useRef(null);
  const dropdownContainerRef = useRef(null);

  // Dışarı tıklandığında veya Escape basıldığında arama sonuçlarını kapat
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownContainerRef.current && !dropdownContainerRef.current.contains(e.target)) {
        setSearchResults([]);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSearchResults([]);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

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
    }, 250);

    return () => clearTimeout(searchTimeoutRef.current);
  }, [searchQuery, accessToken]);

  const handleSelectTrack = (track) => {
    if (!selectedTracks.some(t => t.id === track.id)) {
      if (selectedTracks.length >= 5) {
        showToast?.('En fazla 5 referans şarkı seçebilirsiniz.', 'warning');
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
      showToast?.('Lütfen ruh halinizi anlatın veya en az bir şarkı seçin.', 'warning');
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
      showToast?.(error.message || 'Analiz sırasında hata oluştu.', 'error');
    } finally {
      setLoading(false);
    }
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
        count: parseInt(count, 10),
        energy_level: energyLevel,
        therapy_mode: therapyMode,
        seed_inputs: seed_inputs,
      };
      const result = await searchTracks(params);
      onTracksReady(result.tracks, {
        mood: analysisResult.mood,
        language,
        genres: selectedGenres,
        energy_level: energyLevel,
        therapy_mode: therapyMode,
      });
      showToast?.(`${result.tracks.length} şarkılık reçeteniz hazırlandı! 🎧`, 'success');
    } catch (error) {
      console.error(error);
      showToast?.(error.message || 'Şarkılar aranırken bir hata oluştu.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const toggleGenre = (genre) => {
    setSelectedGenres(prev =>
      prev.includes(genre) ? prev.filter(g => g !== genre) : [...prev, genre]
    );
  };

  const currentMoodMeta = meta?.moods?.[analysisResult?.mood] || {};
  const currentGenres = currentMoodMeta.genres || [];

  return (
    <div className="bg-white/10 backdrop-blur-xl rounded-3xl p-6 shadow-2xl border border-white/20 relative z-30">
      {/* Başlık ve Mod Geçiş Sekmeleri */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-5">
        <h2 className="text-xl font-bold text-white flex items-center">
          <span className="mr-2">🎧</span> Müzik Keşif Motoru
        </h2>

        {step === 1 && (
          <div className="flex bg-black/40 p-1 rounded-xl border border-white/10 text-xs">
            <button
              type="button"
              onClick={() => setActiveTab('therapist')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                activeTab === 'therapist'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              🛋️ Terapi Koltuğu
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('search')}
              className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                activeTab === 'search'
                  ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              🔍 Şarkı Seçerek
            </button>
          </div>
        )}
      </div>

      {step === 1 && (
        <div className="space-y-4">
          {/* TAB 1: Terapi Koltuğu (Duygu Yazarak) */}
          {activeTab === 'therapist' && (
            <div className="space-y-3 animate-fadeIn">
              <div>
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider mb-2">
                  Hızlı Ruh Hali Şablonları
                </label>
                <div className="flex flex-wrap gap-1.5 mb-3">
                  {DEFAULT_QUICK_MOODS.map((qm, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => setText(qm.text)}
                      className="px-2.5 py-1.5 rounded-xl bg-white/5 hover:bg-purple-600/30 border border-white/10 hover:border-purple-400/40 text-xs font-medium text-gray-200 transition-all cursor-pointer flex items-center gap-1.5"
                    >
                      <span>{qm.emoji}</span>
                      <span>{qm.label}</span>
                    </button>
                  ))}
                </div>

                <label className="block text-gray-300 text-sm font-medium mb-1.5">
                  Şu an nasıl hissediyorsun? İçinden geçenleri serbestçe yaz...
                </label>
                <textarea
                  className="w-full h-28 bg-black/35 border border-white/15 rounded-2xl p-4 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-400 resize-none text-sm leading-relaxed"
                  placeholder="Örn: Çok yoğun bir haftaydı, kahvemi alıp arkama yaslanmak istiyorum..."
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                />
              </div>
            </div>
          )}

          {/* TAB 2: iLoveThatTrack Canlı Şarkı Arama */}
          {activeTab === 'search' && (
            <div className="space-y-3 animate-fadeIn">
              <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider">
                Sevdiğin Şarkıları Seç (Müzikal Benzerlik Motoru)
              </label>

              <div ref={dropdownContainerRef} className="relative z-40">
                <div className="flex items-center bg-black/40 border border-white/15 rounded-2xl px-4 py-3 focus-within:border-purple-400 focus-within:ring-2 focus-within:ring-purple-500/30 transition-all">
                  <span className="text-gray-400 mr-2.5">🔍</span>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Şarkı veya sanatçı adı yaz (Örn: Tarkan, Arctic Monkeys, Sezen Aksu...)"
                    className="w-full bg-transparent text-sm text-white placeholder-gray-500 focus:outline-none"
                  />
                  {searching && <span className="animate-spin text-xs text-purple-400 ml-2">⏳</span>}
                  {searchQuery && !searching && (
                    <button
                      type="button"
                      onClick={() => { setSearchQuery(''); setSearchResults([]); }}
                      className="text-gray-400 hover:text-white text-xs px-1.5 py-0.5 rounded cursor-pointer ml-1"
                      title="Temizle"
                    >
                      ✕
                    </button>
                  )}
                </div>

                {/* Açılır Arama Sonuçları (Opak Arka Plan, Kapat Butonu & Kesintisiz Stacking) */}
                {searchResults.length > 0 && (
                  <div className="absolute top-full left-0 right-0 mt-2 bg-[#140b2a] border border-purple-500/40 rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.95)] overflow-hidden z-50 max-h-64 flex flex-col animate-fadeIn">
                    <div className="flex items-center justify-between px-3.5 py-2 bg-black/50 border-b border-white/10 text-[11px] text-gray-300 shrink-0">
                      <span className="font-semibold text-purple-300">🎵 Arama Sonuçları ({searchResults.length})</span>
                      <button
                        type="button"
                        onClick={() => setSearchResults([])}
                        className="text-gray-400 hover:text-white px-2 py-0.5 rounded cursor-pointer hover:bg-white/10 transition-colors"
                      >
                        Kapat ✕
                      </button>
                    </div>
                    <div className="overflow-y-auto divide-y divide-white/5 scrollbar-thin scrollbar-thumb-purple-500/30">
                      {searchResults.map((track) => (
                        <div
                          key={track.id}
                          onClick={() => handleSelectTrack(track)}
                          className="p-2.5 flex items-center gap-3 hover:bg-purple-600/25 cursor-pointer transition-colors"
                        >
                          <img
                            src={track.image || 'https://placehold.co/80x80?text=🎵'}
                            alt={track.name}
                            className="w-10 h-10 rounded-lg object-cover shadow shrink-0"
                          />
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-semibold text-white truncate">{track.name}</p>
                            <p className="text-xs text-gray-400 truncate">{track.artist} • {track.album}</p>
                          </div>
                          <span className="text-xs font-bold text-purple-300 bg-purple-500/20 px-2 py-1 rounded-lg shrink-0">
                            + Seç
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Seçilen Şarkılar */}
              {selectedTracks.length > 0 ? (
                <div className="space-y-2 pt-1">
                  <span className="text-xs text-purple-300 font-semibold flex items-center gap-1">
                    <span>✨</span> Referans Parçalar ({selectedTracks.length}/5):
                  </span>
                  <div className="grid grid-cols-1 gap-2">
                    {selectedTracks.map((track) => (
                      <div
                        key={track.id}
                        className="flex items-center justify-between p-2.5 bg-purple-950/40 border border-purple-400/30 rounded-xl"
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <img
                            src={track.image || 'https://placehold.co/60x60?text=🎵'}
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
                  💡 İpucu: Sevdiğin 1 veya daha fazla şarkı seç; yapay zeka müzikal benzerliklerine göre sana özel reçete yazsın.
                </p>
              )}
            </div>
          )}

          {/* Analiz & Keşfet Butonu */}
          <button
            onClick={() => handleAnalyzeAndDiscover()}
            disabled={loading || (!text.trim() && selectedTracks.length === 0)}
            className="w-full bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-bold py-3.5 px-6 rounded-2xl transition-all duration-300 disabled:opacity-50 flex justify-center items-center gap-2 cursor-pointer shadow-lg shadow-purple-600/25 transform hover:scale-[1.01]"
          >
            {loading ? (
              <span className="animate-spin text-lg">⏳ Analiz Ediliyor...</span>
            ) : (
              <>
                <span>🚀</span>
                <span>{selectedTracks.length > 0 ? "Reçeteyi & Benzer Şarkıları Bul" : "Ruh Halini Analiz Et"}</span>
              </>
            )}
          </button>
        </div>
      )}

      {/* ADIM 2: Teşhis & Terapi Yapılandırması */}
      {step === 2 && analysisResult && (
        <div className="space-y-5 animate-fadeIn">
          {/* Teşhis & Russell Modeli Kartı */}
          <div className="p-4 bg-purple-900/40 rounded-2xl border border-purple-500/30 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <div>
              <span className="text-purple-300 text-[11px] uppercase font-bold tracking-wider">
                Teşhis Edilen Ruh Hali
              </span>
              <p className="text-white text-lg font-bold capitalize flex items-center gap-2">
                <span>{currentMoodMeta.emoji || "🧠"}</span>
                <span>{currentMoodMeta.name || analysisResult.mood.replace(/_/g, ' ')}</span>
              </p>
            </div>

            <div className="flex items-center gap-2 text-xs">
              <span className="px-2.5 py-1 rounded-full bg-white/10 text-purple-200 border border-purple-400/30 font-medium">
                {analysisResult.engine?.includes('gemini') ? '✨ Gemini AI' : '⚡ Russell NLP'}
              </span>
              {typeof analysisResult.valence === 'number' && (
                <span className="px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-400/30 font-mono text-[11px]" title="Russell Koordinatları (Valence / Arousal)">
                  V: {analysisResult.valence > 0 ? `+${analysisResult.valence}` : analysisResult.valence} | A: {analysisResult.arousal}
                </span>
              )}
            </div>
          </div>

          {/* Terapi Modu Seçimi (ISO Prensibi) */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider">
                Terapi Modu (Müzikal Yolculuk)
              </label>
              <span className="text-[11px] text-purple-300 font-medium">ISO Prensibi</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {[
                { id: 'catharsis', emoji: '🌊', label: 'Katarsis', desc: 'Duygunla kal ve onu yaşa' },
                { id: 'uplift', emoji: '🌅', label: 'Moda Yükselt', desc: 'Kademeli neşe ve enerjiye geçiş' },
                { id: 'calm', emoji: '🍃', label: 'Sakinleştir', desc: 'Nabzı düşürüp huzura indir' },
              ].map((m) => {
                const isSelected = therapyMode === m.id;
                return (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setTherapyMode(m.id)}
                    className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-purple-600/30 border-purple-400 text-white shadow-md shadow-purple-500/20'
                        : 'bg-black/30 border-white/10 text-gray-300 hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-base">{m.emoji}</span>
                      <span className="text-xs font-bold">{m.label}</span>
                    </div>
                    <p className="text-[11px] text-gray-400 leading-tight">{m.desc}</p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Müzik Türleri */}
          {currentGenres.length > 0 && (
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="block text-gray-300 text-xs font-semibold uppercase tracking-wider">
                  Önerilen Müzik Türleri
                </label>
                <span className="text-xs text-purple-400 font-semibold">{selectedGenres.length} seçili</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {currentGenres.map(genre => {
                  const isSelected = selectedGenres.includes(genre);
                  return (
                    <button
                      key={genre}
                      type="button"
                      onClick={() => toggleGenre(genre)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 cursor-pointer border ${
                        isSelected
                          ? 'bg-gradient-to-r from-purple-500 to-indigo-600 border-purple-400 text-white shadow-md shadow-purple-500/30 scale-105'
                          : 'bg-white/5 border-white/10 text-gray-300 hover:bg-white/10'
                      }`}
                    >
                      {isSelected ? `✓ ${genre}` : `+ ${genre}`}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Dil & Enerji */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <label className="block text-gray-300 text-xs font-medium">Dil Tercihi</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
              >
                <option value="tr">🇹🇷 Türkçe (Sadece TR Sanatçılar)</option>
                <option value="en">🌍 Yabancı (Global Hitler)</option>
                <option value="mix">✨ Karışık (%50 TR / %50 Global)</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="block text-gray-300 text-xs font-medium">Enerji Seviyesi</label>
              <select
                value={energyLevel}
                onChange={(e) => setEnergyLevel(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-xl p-2.5 text-xs text-white focus:outline-none focus:ring-2 focus:ring-purple-500 cursor-pointer"
              >
                <option value="Düşük">Düşük (Akustik / Sakin)</option>
                <option value="Orta">Orta (Dengeli)</option>
                <option value="Yüksek">Yüksek (Dinamik / Yüksek BPM)</option>
              </select>
            </div>
          </div>

          {/* Şarkı Sayısı Slider */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-gray-300 text-xs font-medium">
              <span>Reçetedeki Şarkı Sayısı</span>
              <span className="font-bold text-purple-400">{count} Şarkı</span>
            </div>
            <input
              type="range"
              min="5"
              max="50"
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="w-full accent-purple-500 h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
            />
          </div>

          {/* Geri & Reçete Oluştur Butonları */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={() => setStep(1)}
              className="px-4 py-3 bg-white/5 hover:bg-white/10 text-white rounded-xl transition-all cursor-pointer text-sm font-semibold"
            >
              Geri
            </button>
            <button
              onClick={handleSearch}
              disabled={loading}
              className="flex-1 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-400 hover:to-emerald-500 text-white font-bold py-3 px-6 rounded-xl transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-[0_0_15px_rgba(16,185,129,0.4)] cursor-pointer"
            >
              {loading ? <span className="animate-spin text-lg">⏳ Reçete Hazırlanıyor...</span> : <span>Reçeteyi Oluştur 🎵</span>}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatBox;
