import { create } from 'zustand';

interface ThemeState {
    theme: 'light' | 'dark';
    toggleTheme: () => void;
    setTheme: (theme: 'light' | 'dark') => void;
    initTheme: () => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
    theme: 'dark', // Default
    toggleTheme: () => set((state) => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        localStorage.setItem('pulse_theme', newTheme);
        document.documentElement.classList.toggle('dark', newTheme === 'dark');
        return { theme: newTheme };
    }),
    setTheme: (theme) => {
        localStorage.setItem('pulse_theme', theme);
        document.documentElement.classList.toggle('dark', theme === 'dark');
        set({ theme });
    },
    initTheme: () => {
        // 1. Пріоритет користувача (localStorage)
        const savedTheme = localStorage.getItem('pulse_theme') as 'light' | 'dark';

        // 2. Тема Telegram WebApp
        // @ts-ignore
        const tgTheme = window.Telegram?.WebApp?.colorScheme;

        // 3. Системна тема
        const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';

        const finalTheme = savedTheme || tgTheme || systemTheme || 'dark';

        document.documentElement.classList.toggle('dark', finalTheme === 'dark');
        set({ theme: finalTheme });

        // Слухаємо зміни в Telegram (якщо користувач змінює тему в налаштуваннях)
        // @ts-ignore
        if (window.Telegram?.WebApp) {
            // @ts-ignore
            window.Telegram.WebApp.onEvent('themeChanged', () => {
                // @ts-ignore
                const newTgTheme = window.Telegram.WebApp.colorScheme;
                if (!localStorage.getItem('pulse_theme')) {
                    document.documentElement.classList.toggle('dark', newTgTheme === 'dark');
                    set({ theme: newTgTheme });
                }
            });
        }
    }
}));
