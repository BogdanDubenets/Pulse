export const FALLBACK_USER_ID = 461874849;

export const getUserId = (): number => {
    const webApp = (window as any).Telegram?.WebApp;

    // Пріоритет - реальний ID з Telegram
    const tgId = webApp?.initDataUnsafe?.user?.id;
    if (tgId) {
        return tgId;
    }

    // Якщо ми в браузері (тести), використовуємо захардкоджений ID
    return FALLBACK_USER_ID;
};

export const isTelegramApp = (): boolean => {
    return !!(window as any).Telegram?.WebApp?.initDataUnsafe?.user?.id;
};

// Ініціалізація WebApp
export const initWebApp = () => {
    const webApp = (window as any).Telegram?.WebApp;
    if (webApp) {
        webApp.ready();
        webApp.expand();
    }
};
