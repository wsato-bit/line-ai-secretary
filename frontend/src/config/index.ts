export const config = {
  API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8293',
  LINE_LOGIN_CHANNEL_ID: import.meta.env.VITE_LINE_LOGIN_CHANNEL_ID || '2009633523',
  LINE_LOGIN_REDIRECT_URI: import.meta.env.VITE_LINE_LOGIN_REDIRECT_URI || `${window.location.origin}/login`,
} as const;
