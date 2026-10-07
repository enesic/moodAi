import React, { useState } from 'react';
import { replaceTrack, savePlaylist } from '../api/client';

const STAGE_BADGES = [
  { label: 'Eşlik (Match)', color: 'bg-purple-500/20 text-purple-300 border-purple-400/30' },
  { label: 'Geçiş (Bridge)', color: 'bg-amber-500/20 text-amber-300 border-amber-400/30' },
  { label: 'Hedef (Target)', color: 'bg-emerald-500/20 text-emerald-300 border-emerald-400/30' },
];

const Playlist = ({ tracks, accessToken, mood, language, genres, onTrackReplace, showToast }) => {
  const [replacingIdx, setReplacingIdx] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedLink, setSavedLink] = useState(null);

  // Seçilen şarkı için Spotify Embed Mini Oynatıcı
  const [activeEmbedTrack, setActiveEmbedTrack] = useState(() => tracks[0] || null);
  const [playingPreviewId, setPlayingPreviewId] = useState(null);
  const [audioInstance, setAudioInstance] = useState(null);

  const handleSelectTrackForPlayer = (track) => {
    setActiveEmbedTrack(track);

    // Varsa ses önizlemesini çal/durdur
    if (track.preview_url) {
      if (playingPreviewId === track.id) {
        audioInstance?.pause();
        setPlayingPreviewId(null);
      } else {
        audioInstance?.pause();
        const newAudio = new Audio(track.preview_url);
        newAudio.play().catch(() => {});
        newAudio.onended = () => setPlayingPreviewId(null);
        setAudioInstance(newAudio);
        setPlayingPreviewId(track.id);
      }
    }
  };

  const handleReplace = async (e, index) => {
    e.stopPropagation();
    setReplacingIdx(index);
    try {
      const exclude_ids = tracks.map(t => t.id);
      const exclude_artists = tracks.map(t => t.artist);
      const result = await replaceTrack({
        access_token: accessToken,
        mood,
        exclude_ids,
        exclude_artists,
        language,
        genres,
      });
      if (result.track) {
        onTrackReplace(index, result.track);
        if (activeEmbedTrack?.id === tracks[index]?.id) {
          setActiveEmbedTrack(result.track);
        }
        showToast?.('Şarkı alternatif bir parça ile değiştirildi 🔄', 'info');
      }
    } catch (error) {
      console.error(error);
      showToast?.(error.message || 'Şarkı değiştirilemedi.', 'error');
    } finally {
      setReplacingIdx(null);
    }
  };

  const handleSave = async () => {
    if (!accessToken) {
      const wantLogin = window.confirm(
        "Çalma listesini Spotify hesabınıza doğrudan kaydedebilmek için Spotify ile giriş yapmanız gerekiyor. Şimdi giriş yapmak ister misiniz?"
      );
      if (wantLogin) {
        window.location.href = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/login`;
      }
      return;
    }

    setSaving(true);
    try {
      const track_uris = tracks.map(t => t.uri);
      const result = await savePlaylist({
        access_token: accessToken,
        track_uris,
        mood_title: mood,
      });
      setSavedLink(result.link);
      showToast?.('Reçete Spotify hesabınıza başarıyla kaydedildi! 🎉', 'success');
    } catch (error) {
      console.error(error);
      showToast?.(error.message || 'Çalma listesi kaydedilemedi.', 'error');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="glass-panel rounded-3xl p-5 sm:p-7 flex flex-col h-full max-h-[850px] shadow-2xl transition-all relative overflow-hidden">
      {/* Üst Glow Işığı */}
      <div className="absolute -top-16 -right-16 w-44 h-44 bg-green-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Başlık & İstatistik */}
      <div className="flex justify-between items-center mb-4 pb-3 border-b border-white/5 relative z-10">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-emerald-500/15 border border-emerald-400/25 flex items-center justify-center text-xl shadow-inner">
            🎵
          </div>
          <div>
            <h2 className="text-lg sm:text-xl font-black text-white tracking-tight flex items-center gap-2">
              <span>Müzikal Terapi Reçeten</span>
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            </h2>
            <p className="text-[11px] text-gray-400 mt-0.5">
              ISO prensibiyle sıralanmış iyileştirici parça akışı
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className="bg-purple-500/20 text-purple-300 px-3 py-1 rounded-full text-xs font-black tracking-wide border border-purple-400/30 shrink-0 shadow-sm">
            {tracks.length} Parça
          </span>
        </div>
      </div>

      {/* Spotify Embed Mini Oynatıcı Paneli */}
      {activeEmbedTrack && (
        <div className="mb-4 bg-black/60 rounded-2xl p-2 border border-white/10 shadow-xl overflow-hidden animate-fadeIn relative z-10">
          <iframe
            title={`Spotify Player: ${activeEmbedTrack.name}`}
            src={`https://open.spotify.com/embed/track/${activeEmbedTrack.id}?utm_source=generator&theme=0`}
            width="100%"
            height="80"
            frameBorder="0"
            allow="autoplay; clipboard-write; encrypted-media; fullscreen; picture-in-picture"
            loading="lazy"
            className="rounded-xl"
          />
        </div>
      )}

      {/* Şarkı Listesi */}
      <div className="flex-1 overflow-y-auto space-y-2 pr-1.5 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent relative z-10">
        {tracks.map((track, index) => {
          const isSelected = activeEmbedTrack?.id === track.id;
          const isPlayingPreview = playingPreviewId === track.id;
          const stageBadge = track.stage !== null && track.stage !== undefined ? STAGE_BADGES[track.stage] : null;

          return (
            <div
              key={`${track.id}-${index}`}
              onClick={() => handleSelectTrackForPlayer(track)}
              className={`group flex items-center gap-3.5 p-3 rounded-2xl transition-all duration-200 cursor-pointer border ${
                isSelected
                  ? 'bg-purple-900/40 border-purple-400/60 shadow-lg shadow-purple-600/20 ring-1 ring-purple-400/30'
                  : 'bg-black/30 hover:bg-white/[0.06] border-white/5 hover:border-white/15'
              }`}
            >
              {/* Sıra Numarası / Play İkonu */}
              <div className="w-6 text-center shrink-0">
                <span className={`text-xs font-bold font-mono transition-opacity ${isSelected ? 'text-purple-300' : 'text-gray-400 group-hover:hidden'}`}>
                  {index + 1}
                </span>
                <span className={`text-xs hidden group-hover:inline-block ${isSelected ? 'text-purple-300' : 'text-white'}`}>
                  ▶
                </span>
              </div>

              {/* Albüm Görseli */}
              <div className="relative w-12 h-12 rounded-xl overflow-hidden shadow-md shrink-0">
                <img
                  src={track.image || 'https://placehold.co/100x100?text=🎵'}
                  alt={track.name}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                />
                {isSelected && (
                  <div className="absolute inset-0 bg-purple-900/40 flex items-center justify-center">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                  </div>
                )}
              </div>

              {/* Şarkı Bilgileri */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h4 className={`text-xs sm:text-sm font-bold truncate transition-colors ${isSelected ? 'text-purple-300' : 'text-white group-hover:text-purple-200'}`}>
                    {track.name}
                  </h4>
                  {stageBadge && (
                    <span className={`text-[9px] px-2 py-0.5 rounded-full border font-bold uppercase tracking-wider shrink-0 hidden sm:inline-block ${stageBadge.color}`}>
                      {stageBadge.label}
                    </span>
                  )}
                </div>
                <p className="text-gray-400 text-[11px] truncate mt-0.5">
                  <span className="font-medium text-gray-300">{track.artists || track.artist}</span> • {track.album}
                </p>
              </div>

              {/* Önizleme Dalgası (Varsa) */}
              {isPlayingPreview && (
                <div className="flex items-end gap-0.5 h-3.5 px-1.5 shrink-0">
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-full" style={{ animationDelay: '0ms' }} />
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-2/3" style={{ animationDelay: '150ms' }} />
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-full" style={{ animationDelay: '300ms' }} />
                </div>
              )}

              {/* Butonlar */}
              <div className="flex items-center gap-1.5 shrink-0">
                {track.link && (
                  <a
                    href={track.link}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="w-8 h-8 flex items-center justify-center rounded-xl bg-white/5 hover:bg-green-500/20 text-gray-400 hover:text-green-400 transition-all text-xs border border-transparent hover:border-green-500/30"
                    title="Spotify'da Aç"
                  >
                    ↗️
                  </a>
                )}
                <button
                  onClick={(e) => handleReplace(e, index)}
                  disabled={replacingIdx === index}
                  className="w-8 h-8 flex items-center justify-center rounded-xl bg-white/5 hover:bg-purple-500/20 text-gray-300 hover:text-purple-300 transition-all disabled:opacity-50 text-xs cursor-pointer border border-transparent hover:border-purple-400/30"
                  title="Farklı bir şarkıyla değiştir"
                >
                  {replacingIdx === index ? <span className="animate-spin text-xs">⏳</span> : <span>🔄</span>}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Kaydetme Butonu & Bağlantı */}
      <div className="pt-4 mt-3 border-t border-white/10 relative z-10">
        {savedLink ? (
          <div className="bg-emerald-950/40 border border-emerald-500/40 rounded-2xl p-4 text-center animate-fadeIn flex flex-col sm:flex-row items-center justify-between gap-3 shadow-lg">
            <div className="text-left">
              <p className="text-emerald-300 font-bold text-xs sm:text-sm">🎉 Spotify Hesabına Eklendi!</p>
              <p className="text-gray-300 text-[11px]">Çalma listen doğrudan Spotify kütüphanende hazır.</p>
            </div>
            <a
              href={savedLink}
              target="_blank"
              rel="noreferrer"
              className="bg-[#1DB954] text-black font-black text-xs py-2.5 px-5 rounded-full hover:bg-[#1ed760] transition-transform hover:scale-105 shadow-md shadow-green-500/30 shrink-0"
            >
              Spotify'da Aç 🎵
            </a>
          </div>
        ) : (
          <button
            onClick={handleSave}
            disabled={saving || tracks.length === 0}
            className="w-full bg-[#1DB954] hover:bg-[#1ed760] text-black font-black py-3.5 px-6 rounded-2xl transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-xl shadow-green-500/25 hover:scale-[1.01] active:scale-[0.99] cursor-pointer text-sm"
          >
            {saving ? (
              <span className="animate-spin text-base">⏳ Spotify Kütüphanesine Ekleniyor...</span>
            ) : (
              <>
                <span className="text-base">🎧</span>
                <span>Spotify Çalma Listesi Olarak Kaydet</span>
              </>
            )}
          </button>
        )}
      </div>
    </div>
  );
};

export default Playlist;
