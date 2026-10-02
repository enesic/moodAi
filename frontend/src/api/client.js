const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const login = async () => {
  const res = await fetch(`${BASE_URL}/api/login`);
  if (!res.ok) throw new Error('Spotify giriş bağlantısı alınamadı');
  const data = await res.json();
  window.location.href = data.auth_url;
};

export const analyze = async (text) => {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) throw new Error('Analysis failed');
  return res.json();
};

export const searchAutocomplete = async (query, accessToken = null) => {
  if (!query || !query.trim()) return { tracks: [] };
  const tokenParam = accessToken ? `&access_token=${encodeURIComponent(accessToken)}` : '';
  const res = await fetch(`${BASE_URL}/api/search-autocomplete?q=${encodeURIComponent(query)}${tokenParam}`);
  if (!res.ok) return { tracks: [] };
  return res.json();
};

export const searchTracks = async (params) => {
  const res = await fetch(`${BASE_URL}/api/search-tracks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Search failed');
  return res.json();
};

export const replaceTrack = async (params) => {
  const res = await fetch(`${BASE_URL}/api/replace-track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Replace failed');
  return res.json();
};

export const savePlaylist = async (params) => {
  const res = await fetch(`${BASE_URL}/api/save-playlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Save failed');
  return res.json();
};

export const getMoodCard = async (params) => {
  const res = await fetch(`${BASE_URL}/api/mood-card`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error('Mood card failed');
  return res.blob();
};
