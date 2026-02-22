import axios from 'axios';

// In development, we might proxy requests or use direct URL
// In production, this should be the deployed backend URL
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://pulse-production-6dd0.up.railway.app/api/v1';
export const API_ORIGIN = new URL(API_BASE_URL).origin;

console.log('Pulse API URL:', API_BASE_URL);

export const apiClient = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add interceptor to include Telegram initData mostly for auth
apiClient.interceptors.request.use((config) => {
    if (window.Telegram?.WebApp?.initData) {
        config.headers['X-Telegram-Init-Data'] = window.Telegram.WebApp.initData;
    }
    return config;
});
