---
name: pulse-design-system
description: Дизайн-система Pulse. Використовуйте при створенні або зміні UI-компонентів, стилів, кольорів та брендингу Mini App та майбутніх веб-ресурсів.
---

# Навичка: Дизайн-система Pulse

Єдина система візуального дизайну для всіх фронтенд-проектів Pulse — Mini App, веб-сайт, лендінги.

## Кольорова палітра

### Темна тема (основна)

| Токен | HEX | Tailwind | Використання |
|-------|-----|----------|-------------|
| `background` | `#1A1D2E` | `bg-background` | Основний фон |
| `surface` | `#252A3F` | `bg-surface` | Картки, секції, модалки |
| `primary` | `#FF6B6B` | `text-primary` | Акцент, CTA, активні елементи |
| `secondary` | `#4ECDC4` | `text-secondary` | Вторинний акцент, верифіковані |
| `accent` | `#FDCB6E` | `text-accent` | Жовтий, попередження |
| `border` | `#3A4059` | `border-border` | Бордери, розділювачі |

### Текст

| Токен | HEX | Tailwind | Використання |
|-------|-----|----------|-------------|
| `text-primary` | `#FFFFFF` | `text-text-primary` | Заголовки, основний текст |
| `text-secondary` | `#B2B9C4` | `text-text-secondary` | Вторинний текст, мета-інфо |
| `text-muted` | `#636E72` | `text-text-muted` | Неактивні, placeholder |

### Статусні кольори

| Токен | HEX | Tailwind | Використання |
|-------|-----|----------|-------------|
| `success` | `#00B894` | `text-success` | Успіх, підтверджено |
| `warning` | `#FDCB6E` | `text-warning` | Попередження |
| `error` | `#D63031` | `text-error` | Помилки |
| `trending` | `#FF6B6B` | `text-trending` | Трендові новини |
| `verified` | `#4ECDC4` | `text-verified` | Верифіковане джерело |
| `pending` | `#95A5A6` | `text-pending` | Очікування |

## Правила стилізації

### ✅ Правильно
```tsx
// Використовуй змінні палітри
<div className="bg-surface border border-border text-text-primary">
<span className="text-text-secondary">мета-інфо</span>
<button className="bg-primary text-white">CTA</button>
```

### ❌ Неправильно
```tsx
// НЕ використовуй хардкоджені кольори
<div className="bg-white/5 border border-white/10 text-white">
<span className="text-slate-400">мета-інфо</span>
<button className="bg-red-500 text-white">CTA</button>
```

## CSS-змінні

Палітра визначена у `src/index.css` через `@theme`:
```css
@theme {
  --color-background: #1A1D2E;
  --color-surface: #252A3F;
  --color-primary: #FF6B6B;
  /* ... повний список вище */
}
```

Tailwind автоматично підхоплює через `tailwind.config.js`.

## Типографіка

- **Шрифт:** Inter (Google Fonts)
- **Заголовки:** `font-black`, `text-3xl`
- **Підзаголовки:** `font-bold`, `text-lg`
- **Основний текст:** `font-medium`, `text-sm`
- **Мета-інфо:** `font-normal`, `text-[10px]`–`text-xs`

## Компоненти

### Картки
- Фон: `bg-surface`
- Бордер: `border border-border`
- Скруглення: `rounded-2xl`
- Ефект: `backdrop-blur-md shadow-xl`

### Кнопки (CTA)
- Primary: `bg-primary text-white hover:bg-primary/90`
- Ghost: `bg-primary/5 text-primary border border-primary/10`
- Перехід: `transition-all active:scale-[0.98]`

### Ambient Glow (фон Layout)
```tsx
<div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-primary/20 blur-[100px] rounded-full mix-blend-screen" />
<div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-accent/10 blur-[100px] rounded-full mix-blend-screen" />
```

## Брендинг

- **Лого:** `public/pulse-logo.svg` — серце з пульсом, градієнт coral→teal
- **Favicon:** той самий SVG
- **Назва:** Pulse (без emoji у коді, тільки лого)

## Майбутнє: Light Theme

При додаванні light теми використовувати `Telegram.WebApp.colorScheme`:
```tsx
const colorScheme = window.Telegram?.WebApp?.colorScheme; // 'light' | 'dark'
```

Альтернативні значення для light:
| Токен | Dark | Light |
|-------|------|-------|
| `background` | `#1A1D2E` | `#F8F9FA` |
| `surface` | `#252A3F` | `#FFFFFF` |
| `text-primary` | `#FFFFFF` | `#1A1D2E` |
| `text-secondary` | `#B2B9C4` | `#636E72` |
| `border` | `#3A4059` | `#E2E8F0` |
