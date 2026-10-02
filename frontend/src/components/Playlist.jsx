import React, { useState } from 'react';
import { replaceTrack, savePlaylist } from '../api/client';

const Playlist = ({ tracks, accessToken, mood, language, genres, onTrackReplace }) => {
  const [replacingIdx, setReplacingIdx] = useState(null);
  const [saving, setSaving] = useState(false);
  const [savedLink, setSavedLink] = useState(null);
  const [playingId, setPlayingId] = useState(null);
  const [audioInstance, setAudioInstance] = useState(null);

  const togglePlay = (track) => {
    if (!track.preview_url) {
      if (track.link) window.open(track.link, '_blank');
      return;
    }

    if (playingId === track.id) {
      audioInstance?.pause();
      setPlayingId(null);
    } else {
      audioInstance?.pause();
      const newAudio = new Audio(track.preview_url);
      newAudio.play();
      newAudio.onended = () => setPlayingId(null);
      setAudioInstance(newAudio);
      setPlayingId(track.id);
    }
  };

  const handleReplace = async (e, index) => {
    e.stopPropagation();
    setReplacingIdx(index);
    try {
      const exclude_ids = tracks.map(t => t.id);
      const result = await replaceTrack({
        access_token: accessToken,
        mood,
        exclude_ids,
        language,
        genres
      });
      onTrackReplace(index, result.track);
    } catch (error) {
      console.error(error);
      alert('Şarkı değiştirilemedi.');
    } finally {
      setReplacingIdx(null);
    }
  };

  const handleSave = async () => {
    if (!accessToken) {
      const wantLogin = window.confirm("Çalma listesini Spotify hesabınıza doğrudan kaydedebilmek için Spotify ile giriş yapmanız gerekiyor. Giriş yapmak ister misiniz?");
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
        mood_title: mood
      });
      setSavedLink(result.link);
    } catch (error) {
      console.error(error);
      alert('Çalma listesi kaydedilemedi: ' + (error.message || 'Lütfen tekrar deneyin.'));
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="bg-white/5 backdrop-blur-xl rounded-3xl p-6 shadow-2xl border border-white/10 flex flex-col h-full max-h-[800px]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center">
          <span className="mr-2">🎧</span> Senin İçin Seçilen Reçete
        </h2>
        <span className="bg-purple-600/30 text-purple-300 px-3 py-1 rounded-full text-xs font-bold tracking-wide border border-purple-500/30">
          {tracks.length} Şarkı
        </span>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2.5 pr-2 scrollbar-thin scrollbar-thumb-purple-500/30 scrollbar-track-transparent">
        {tracks.map((track, index) => {
          const isPlaying = playingId === track.id;
          return (
            <div 
              key={`${track.id}-${index}`} 
              onClick={() => togglePlay(track)}
              className={`flex items-center gap-4 p-3 rounded-2xl transition-all duration-300 cursor-pointer border ${isPlaying ? 'bg-purple-900/40 border-purple-500/50 shadow-lg shadow-purple-500/20' : 'bg-black/20 hover:bg-black/40 border-white/5 hover:border-white/10'}`}
            >
              <div className="relative w-12 h-12 rounded-xl overflow-hidden shadow-md shrink-0 group">
                <img src={track.image || "https://placehold.co/100x100?text=🎵"} alt={track.name} className="w-full h-full object-cover" />
                <div className={`absolute inset-0 bg-black/40 flex items-center justify-center transition-opacity ${isPlaying ? 'opacity-100' : 'opacity-0 hover:opacity-100'}`}>
                  <span className="text-white text-lg">{isPlaying ? "⏸️" : "▶️"}</span>
                </div>
              </div>
              
              <div className="flex-1 min-w-0">
                <h4 className={`text-sm font-semibold truncate ${isPlaying ? 'text-purple-300' : 'text-white'}`}>{track.name}</h4>
                <p className="text-gray-400 text-xs truncate">{track.artist} • {track.album}</p>
              </div>

              {/* Müzik Dalgası Animasyonu */}
              {isPlaying && (
                <div className="flex items-end gap-0.5 h-4 px-2">
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-full" style={{ animationDelay: '0ms' }} />
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-2/3" style={{ animationDelay: '150ms' }} />
                  <span className="w-1 bg-purple-400 animate-bounce rounded-full h-full" style={{ animationDelay: '300ms' }} />
                </div>
              )}
              
              <div className="flex items-center gap-2">
                {track.link && (
                  <a 
                    href={track.link} 
                    target="_blank" 
                    rel="noreferrer" 
                    onClick={(e) => e.stopPropagation()}
                    className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 hover:bg-green-500/20 text-gray-400 hover:text-green-400 transition-all text-xs"
                    title="Spotify'da Aç"
                  >
                    ↗️
                  </a>
                )}
                <button 
                  onClick={(e) => handleReplace(e, index)}
                  disabled={replacingIdx === index}
                  className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 hover:bg-purple-500/20 text-gray-300 hover:text-purple-300 transition-all disabled:opacity-50 text-xs"
                  title="Farklı bir şarkıyla değiştir"
                >
                  {replacingIdx === index ? <span className="animate-spin">⏳</span> : <span>🔄</span>}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      <div className="pt-4 mt-3 border-t border-white/10">
        {savedLink ? (
          <div className="bg-emerald-900/40 border border-emerald-500/40 rounded-2xl p-4 text-center animate-fadeIn">
            <div className="text-2xl mb-1">🎉</div>
            <p className="text-white font-bold text-sm mb-2">Reçeten Spotify Hesabına Kaydedildi!</p>
            <a 
              href={savedLink} 
              target="_blank" 
              rel="noreferrer"
              className="inline-block bg-[#1DB954] text-black font-bold text-xs py-2.5 px-6 rounded-full hover:bg-[#1ed760] transition-transform hover:scale-105 shadow-lg shadow-green-500/20"
            >
              Spotify'da Dinle 🎵
            </a>
          </div>
        ) : (
          <button
            onClick={handleSave}
            disabled={saving || tracks.length === 0}
            className="w-full bg-gradient-to-r from-[#1DB954] to-[#179c46] hover:from-[#1ed760] hover:to-[#1eb552] text-black font-extrabold py-3.5 px-6 rounded-2xl transition-all disabled:opacity-50 flex justify-center items-center gap-2 shadow-lg shadow-green-500/20 hover:scale-[1.01]"
          >
            {saving ? <span className="animate-spin text-lg">⏳</span> : <><span>✅</span> Spotify Çalma Listesi Olarak Kaydet</>}
          </button>
        )}
      </div>
    </div>
  );
};

export default Playlist;
