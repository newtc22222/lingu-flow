export const apiFetch = async (url: string, options: RequestInit = {}) => {
  const token = localStorage.getItem('token');
  const headers = new Headers(options.headers || {});

  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }

  const response = await fetch(url, {
    ...options,
    headers
  });

  if (response.status === 401) {
    // Expired/invalid token. Drop it and hard-navigate to the auth screen — a
    // full document load (rather than a router push) guarantees every store,
    // including any in-flight exam session state, is discarded with it.
    localStorage.removeItem('token');
    if (window.location.pathname !== '/auth') {
      window.location.assign('/auth');
    }
  }

  return response;
};
