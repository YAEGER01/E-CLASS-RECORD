// ngrokFetch.js
// Universal fetch wrapper to skip ngrok browser warning

export async function ngrokFetch(url, options = {}) {
  // Clone headers or create new
  let headers = options.headers ? { ...options.headers } : {};
  if (window.location.hostname.endsWith('.ngrok-free.dev')) {
    headers['ngrok-skip-browser-warning'] = 'true';
  }
  return fetch(url, { ...options, headers });
}
