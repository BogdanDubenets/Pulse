---
name: miniapp-development
description: Розробка Telegram Mini App та веб-додатків на React + Vite + Tailwind. Використовуйте для створення компонентів, сторінок, API-інтеграції та деплою.
---

# Навичка: Mini App / Web App Development

Фронтенд-розробка Telegram Mini App та веб-ресурсів Pulse.

## Технічний стек

| Технологія | Версія | Призначення |
|-----------|--------|-------------|
| React | 18+ | UI framework |
| TypeScript | 5+ | Типізація |
| Vite | 6+ | Build tool + dev server |
| Tailwind CSS | 4+ | Стилізація |
| Lucide React | latest | Іконки |
| Axios | latest | HTTP-клієнт |

## Структура проекту

```
pulse-miniapp/
├── public/
│   └── pulse-logo.svg         # Лого бренду
├── src/
│   ├── api/                    # API-клієнт
│   │   └── digest.ts           # Запити до бекенду
│   ├── components/             # UI-компоненти
│   │   ├── Layout.tsx          # Базовий layout з ambient glow
│   │   ├── DigestListItem.tsx  # Елемент списку новин
│   │   └── CategorySectionUnified.tsx  # Секція категорії
│   ├── pages/                  # Сторінки
│   │   └── DigestPage.tsx      # Головна сторінка дайджесту
│   ├── types/                  # TypeScript типи
│   │   └── index.ts
│   ├── index.css               # Палітра (@theme) + base стилі
│   └── main.tsx                # Entry point
├── index.html                  # HTML з favicon та title
├── tailwind.config.js          # Tailwind конфіг з палітрою
├── vite.config.ts              # Vite конфіг (proxy для API)
└── package.json
```

## Конвенції

### Компоненти

1. **Functional components only** — `React.FC<Props>`
2. **Іменування:** PascalCase, один компонент = один файл
3. **Стилізація:** Tailwind classes, жодних inline styles
4. **Кольори:** Тільки з дизайн-системи (`pulse-design-system`)

### API-інтеграція

```typescript
// api/digest.ts — приклад
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function fetchDigest(userId: string, hours: number = 24) {
  const response = await fetch(`${API_BASE}/api/v1/digest/${userId}?hours=${hours}`, {
    headers: {
      'X-Telegram-Init-Data': window.Telegram?.WebApp?.initData || ''
    }
  });
  return response.json();
}
```

### Telegram WebApp SDK

```typescript
// Доступ до Telegram контексту
const tg = window.Telegram?.WebApp;
const userId = tg?.initDataUnsafe?.user?.id;
const colorScheme = tg?.colorScheme; // 'light' | 'dark'

// Haptic feedback
tg?.HapticFeedback?.impactOccurred('medium');

// Закрити Mini App
tg?.close();

// Expand Mini App
tg?.expand();
```

### Vite Proxy (локальна розробка)

```typescript
// vite.config.ts
export default defineConfig({
  server: {
    proxy: {
      '/api': 'http://localhost:8000'
    }
  }
});
```

## Dev-команди

```bash
npm run dev      # Dev server (:5174)
npm run build    # Production build → dist/
npm run preview  # Preview production build
```

## Деплой

### Vercel
```bash
npx vercel --prod
```

### Telegram Bot Menu Button
```python
# bot/main.py — встановлення кнопки Mini App
await bot.set_chat_menu_button(
    menu_button=MenuButtonWebApp(
        text="📰 Дайджест",
        web_app=WebAppInfo(url=WEBAPP_URL)
    )
)
```

## Чекліст нового компонента

- [ ] Створити файл у `src/components/` або `src/pages/`
- [ ] Використовувати типи з `src/types/`
- [ ] Кольори тільки з палітри (навичка `pulse-design-system`)
- [ ] Responsive: `max-w-md mx-auto` в Layout
- [ ] Тестувати на мобільному viewport (375px ширина)
