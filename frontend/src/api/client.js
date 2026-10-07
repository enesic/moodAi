const BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/+$/, '');

// ==============================================================================
// TOKEN & AUTH DEPOLAMA YARDIMCILARI
// ==============================================================================

export const getStoredAuth = () => {
  try {
    const raw = localStorage.getItem('moodai_auth');
    if (raw) return JSON.parse(raw);
  } catch (e) {
    // legacy fallback
  }
  const token = localStorage.getItem('moodai_token');
  if (token) return { access_token: token, refresh_token: null, expires_at: null };
  return null;
};

export const setStoredAuth = (auth) => {
  if (!auth) {
    localStorage.removeItem('moodai_auth');
    localStorage.removeItem('moodai_token');
    return;
  }
  localStorage.setItem('moodai_auth', JSON.stringify(auth));
  if (auth.access_token) {
    localStorage.setItem('moodai_token', auth.access_token);
  }
};

export const clearStoredAuth = () => {
  localStorage.removeItem('moodai_auth');
  localStorage.removeItem('moodai_token');
  localStorage.removeItem('moodai_guest');
};

// ==============================================================================
// OTOMATİK TOKEN YENİLEME & FETCH SARMALAYICI
// ==============================================================================

export const refreshAccessToken = async () => {
  const current = getStoredAuth();
  if (!current?.refresh_token) return null;

  try {
    const res = await fetch(`${BASE_URL}/api/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: current.refresh_token }),
    });
    if (!res.ok) throw new Error('Refresh failed');
    const newTokens = await res.json();
    const updated = {
      ...current,
      access_token: newTokens.access_token,
      refresh_token: newTokens.refresh_token || current.refresh_token,
      expires_at: newTokens.expires_at,
    };
    setStoredAuth(updated);
    return updated.access_token;
  } catch (err) {
    clearStoredAuth();
    return null;
  }
};

const handleResponse = async (res) => {
  if (res.ok) return res;
  let errorDetail = 'İstek başarısız oldu';
  try {
    const body = await res.json();
    if (typeof body.detail === 'string') {
      errorDetail = body.detail;
    } else if (body.detail?.message) {
      errorDetail = body.detail.message;
    } else if (Array.isArray(body.detail)) {
      errorDetail = body.detail.map(d => d.msg || JSON.stringify(d)).join(', ');
    }
  } catch (_) {
    errorDetail = res.statusText || errorDetail;
  }
  const err = new Error(errorDetail);
  err.status = res.status;
  throw err;
};

// ==============================================================================
// API ÇAĞRILARI
// ==============================================================================

export const getMeta = async () => {
  const res = await fetch(`${BASE_URL}/api/meta`);
  await handleResponse(res);
  return res.json();
};

export const login = async () => {
  const res = await fetch(`${BASE_URL}/api/login`);
  await handleResponse(res);
  const data = await res.json();
  window.location.href = data.auth_url;
};

export const analyze = async (text, seedArtists = [], seedTracks = []) => {
  const res = await fetch(`${BASE_URL}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      seed_artists: seedArtists || [],
      seed_tracks: seedTracks || [],
    }),
  });
  await handleResponse(res);
  return res.json();
};

export const searchAutocomplete = async (query, accessToken = null) => {
  if (!query || !query.trim()) return { tracks: [] };
  const tokenParam = accessToken ? `&access_token=${encodeURIComponent(accessToken)}` : '';
  try {
    const res = await fetch(`${BASE_URL}/api/search-autocomplete?q=${encodeURIComponent(query.trim())}${tokenParam}`);
    if (!res.ok) return { tracks: [] };
    return res.json();
  } catch (_) {
    return { tracks: [] };
  }
};

export const searchTracks = async (params) => {
  const res = await fetch(`${BASE_URL}/api/search-tracks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  await handleResponse(res);
  return res.json();
};

export const replaceTrack = async (params) => {
  const res = await fetch(`${BASE_URL}/api/replace-track`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  await handleResponse(res);
  return res.json();
};

export const savePlaylist = async (params) => {
  const res = await fetch(`${BASE_URL}/api/save-playlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  await handleResponse(res);
  return res.json();
};

export const getMoodCard = async (params) => {
  const res = await fetch(`${BASE_URL}/api/mood-card`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  await handleResponse(res);
  return res.blob();
};

export const getVibeCard = async (params) => {
  const res = await fetch(`${BASE_URL}/api/vibe-card`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  await handleResponse(res);
  return res.blob();
};

// ==============================================================================
// PRO & FREEMIUM MONETİZASYON YARDIMCILARI
// ==============================================================================

const DAILY_FREE_LIMIT = 3;

export const getProStatus = () => {
  try {
    return localStorage.getItem('moodai_pro') === 'true';
  } catch (_) {
    return false;
  }
};

export const setProStatus = (status) => {
  try {
    if (status) {
      localStorage.setItem('moodai_pro', 'true');
    } else {
      localStorage.removeItem('moodai_pro');
    }
  } catch (_) {}
};

export const getDailyUsage = () => {
  try {
    const today = new Date().toISOString().slice(0, 10);
    const raw = localStorage.getItem('moodai_daily_usage');
    if (!raw) return { count: 0, date: today, remaining: DAILY_FREE_LIMIT };
    const parsed = JSON.parse(raw);
    if (parsed.date !== today) {
      return { count: 0, date: today, remaining: DAILY_FREE_LIMIT };
    }
    const count = parsed.count || 0;
    return {
      count,
      date: today,
      remaining: Math.max(0, DAILY_FREE_LIMIT - count),
    };
  } catch (_) {
    return { count: 0, date: new Date().toISOString().slice(0, 10), remaining: DAILY_FREE_LIMIT };
  }
};

export const incrementDailyUsage = () => {
  const current = getDailyUsage();
  const nextCount = current.count + 1;
  try {
    localStorage.setItem(
      'moodai_daily_usage',
      JSON.stringify({ date: current.date, count: nextCount })
    );
  } catch (_) {}
  return {
    count: nextCount,
    date: current.date,
    remaining: Math.max(0, DAILY_FREE_LIMIT - nextCount),
  };
};

