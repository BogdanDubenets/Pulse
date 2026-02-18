import axios from 'axios';

// In development, we might proxy requests or use direct URL
// In production, this should be the deployed backend URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

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
