  topTopics: Array<{
    topic: string;
    count: number;
    trend: 'up' | 'down' | 'stable';
  }>;
  activityByDay: Record<string, number>;
}
```

**Code example:**
```tsx
export function StatsOverview({ stats, period }: StatsOverviewProps) {
  return (
    <div className="stats-overview">
      <div className="stats-period-selector">
        <button className={cn({ active: period === 'week' })}>
          Тиждень
        </button>
        <button className={cn({ active: period === 'month' })}>
          Місяць
        </button>
        <button className={cn({ active: period === 'all' })}>
          Весь час
        </button>
      </div>
      
      <div className="stats-cards">
        <StatCard
          icon="📰"
          value={stats.storiesRead}
          label="новин прочитано"
        />
        <StatCard
          icon="⏱"
          value={`${Math.floor(stats.timeSaved / 60)} год`}
          label="заощаджено"
        />
        <StatCard
          icon="🔥"
          value={stats.trendingTopics}
          label="trending теми"
        />
      </div>
      
      <CategoryChart data={stats.categoriesBreakdown} />
      
      <TrendingTopics topics={stats.topTopics} />
      
      <ActivityChart data={stats.activityByDay} />
    </div>
  );
}
```

---

## 4. SavedPage (Збережені новини)

### Layout

```
┌─────────────────────────────────────┐
│ 💾 Збережені новини            [🔍] │ ← Header with search
├─────────────────────────────────────┤
│ [Всі] [Вчора] [Тиждень] [Місяць]   │ ← Filters
├─────────────────────────────────────┤
│                                     │
│ Вчора:                              │
│ ┌─────────────────────────────────┐ │
│ │ 🔴 Економічна реформа           │ │
│ │ 15 лютого, 20:30                │ │
│ │ [Відкрити] [Видалити]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Минулого тижня:                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔵 AI тренди 2026               │ │
│ │ 10 лютого, 19:15                │ │
│ │ [Відкрити] [Видалити]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔵 Інвестиції в стартапи        │ │
│ │ 08 лютого, 20:45                │ │
│ │ [Відкрити] [Видалити]           │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

**Функціонал:**
- Список збережених новин
- Пошук по збережених
- Фільтри по даті
- Swipe to delete
- Групування по датах

---

## 5. SettingsPage (Налаштування)

### Layout

```
┌─────────────────────────────────────┐
│ ⚙️ Налаштування                     │
├─────────────────────────────────────┤
│                                     │
│ 🎨 Зовнішній вигляд                 │
│ ┌─────────────────────────────────┐ │
│ │ Тема                            │ │
│ │ ◉ Світла ○ Темна ○ Авто         │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 📂 Категорії новин                  │
│ ┌─────────────────────────────────┐ │
│ │ ☑ Бізнес  ☑ Технології          │ │
│ │ ☑ Новини  ☐ Політика            │ │
│ │ ☐ Культура                       │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 🔔 Сповіщення                       │
│ ┌─────────────────────────────────┐ │
│ │ ☑ Щоденний дайджест              │ │
│ │   Час: 20:00         [Змінити]  │ │
│ │ ☑ Trending новини                │ │
│ │ ☐ Нові канали                    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 📊 Дайджест                         │
│ ┌─────────────────────────────────┐ │
│ │ Обсяг:                           │ │
│ │ ◉ Короткий (топ-10)              │ │
│ │ ○ Повний (всі новини)            │ │
│ │                                 │ │
│ │ Формат за замовчуванням:         │ │
│ │ ◉ Mini App ○ Текст              │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Зберегти зміни]                    │
│                                     │
└─────────────────────────────────────┘
```

---

## API Integration

### Backend API Endpoints

```typescript
// GET /api/v1/digest/:userId/:date
interface DigestResponse {
  date: string;
  stories: Story[];
  stats: {
    totalStories: number;
    trendingCount: number;
    channelsCount: number;
  };
}

// GET /api/v1/story/:storyId
interface StoryResponse {
  story: StoryDetail;
  publications: Publication[];
  analytics: StoryAnalytics;
}

// GET /api/v1/user/stats
interface StatsResponse {
  period: string;
  stats: UserStats;
}

// GET /api/v1/user/saved
interface SavedStoriesResponse {
  stories: SavedStory[];
  total: number;
}

// POST /api/v1/user/save
interface SaveStoryRequest {
  storyId: string;
}

// DELETE /api/v1/user/save/:storyId
interface DeleteSavedStoryRequest {
  storyId: string;
}

// PUT /api/v1/user/settings
interface UpdateSettingsRequest {
  theme?: 'light' | 'dark' | 'auto';
  categories?: string[];
  notifications?: {
    dailyDigest: boolean;
    trending: boolean;
    newChannels: boolean;
  };
  digestTime?: string;
}
```

### API Client Setup

```typescript
// src/api/client.ts
import axios from 'axios';
import { getTelegramWebApp } from './telegram';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add Telegram auth to every request
apiClient.interceptors.request.use(config => {
  const webApp = getTelegramWebApp();
  const initData = webApp?.initData;
  
  if (initData) {
    config.headers['X-Telegram-Init-Data'] = initData;
  }
  
  return config;
});

// Handle errors
apiClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      // Unauthorized - show error
      showError('Помилка авторизації');
    }
    return Promise.reject(error);
  }
);
```

### Telegram WebApp Integration

```typescript
// src/hooks/useTelegram.ts
import { useEffect, useState } from 'react';

interface TelegramWebApp {
  initData: string;
  initDataUnsafe: {
    user?: {
      id: number;
      first_name: string;
      last_name?: string;
      username?: string;
    };
  };
  colorScheme: 'light' | 'dark';
  themeParams: {
    bg_color: string;
    text_color: string;
    hint_color: string;
    link_color: string;
    button_color: string;
    button_text_color: string;
  };
  BackButton: {
    show: () => void;
    hide: () => void;
    onClick: (callback: () => void) => void;
  };
  MainButton: {
    text: string;
    color: string;
    textColor: string;
    isVisible: boolean;
    isActive: boolean;
    show: () => void;
    hide: () => void;
    enable: () => void;
    disable: () => void;
    onClick: (callback: () => void) => void;
  };
  expand: () => void;
  close: () => void;
  ready: () => void;
}

export function useTelegram() {
  const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
  
  useEffect(() => {
    const tg = (window as any).Telegram?.WebApp;
    
    if (tg) {
      tg.ready();
      tg.expand();
      setWebApp(tg);
    }
  }, []);
  
  return webApp;
}

// Usage in components
export function DigestPage() {
  const webApp = useTelegram();
  const navigate = useNavigate();
  
  useEffect(() => {
    if (!webApp) return;
    
    // Show back button
    webApp.BackButton.show();
    webApp.BackButton.onClick(() => {
      navigate(-1);
    });
    
    return () => {
      webApp.BackButton.hide();
    };
  }, [webApp, navigate]);
  
  // ...
}
```

---

## Performance Optimization

### 1. Code Splitting

```typescript
// Lazy load pages
const DigestPage = lazy(() => import('./pages/DigestPage'));
const StoryPage = lazy(() => import('./pages/StoryPage'));
const StatsPage = lazy(() => import('./pages/StatsPage'));
const SavedPage = lazy(() => import('./pages/SavedPage'));
const SettingsPage = lazy(() => import('./pages/SettingsPage'));

// In routes
<Suspense fallback={<LoadingSpinner />}>
  <Routes>
    <Route path="/" element={<DigestPage />} />
    <Route path="/story/:id" element={<StoryPage />} />
    <Route path="/stats" element={<StatsPage />} />
    <Route path="/saved" element={<SavedPage />} />
    <Route path="/settings" element={<SettingsPage />} />
  </Routes>
</Suspense>
```

### 2. Image Optimization

```typescript
// Use responsive images
function ChannelAvatar({ src, alt, size = 'md' }) {
  const sizes = {
    sm: 24,
    md: 32,
    lg: 48,
  };
  
  const dimension = sizes[size];
  
  return (
    <img
      src={src}
      alt={alt}
      width={dimension}
      height={dimension}
      loading="lazy"
      decoding="async"
    />
  );
}
```

### 3. Data Caching

```typescript
// Use React Query for caching
import { useQuery } from '@tanstack/react-query';

export function useDigest(userId: string, date: string) {
  return useQuery({
    queryKey: ['digest', userId, date],
    queryFn: () => fetchDigest(userId, date),
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 30 * 60 * 1000, // 30 minutes
  });
}
```

### 4. Virtual Scrolling

```typescript
// Use virtual scrolling for long lists
import { useVirtualizer } from '@tanstack/react-virtual';

export function StoryList({ stories }: { stories: Story[] }) {
  const parentRef = useRef<HTMLDivElement>(null);
  
  const virtualizer = useVirtualizer({
    count: stories.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 200, // Estimated height of story card
    overscan: 5,
  });
  
  return (
    <div ref={parentRef} className="story-list">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map(virtualItem => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            <StoryCard story={stories[virtualItem.index]} />
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## Animations & Transitions

### Page Transitions

```typescript
import { motion, AnimatePresence } from 'framer-motion';

export function App() {
  const location = useLocation();
  
  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route
          path="/"
          element={
            <PageTransition>
              <DigestPage />
            </PageTransition>
          }
        />
        {/* Other routes */}
      </Routes>
    </AnimatePresence>
  );
}

function PageTransition({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      transition={{ duration: 0.2 }}
    >
      {children}
    </motion.div>
  );
}
```

### Card Animations

```typescript
function StoryCard({ story }: { story: Story }) {
  return (
    <motion.article
      className="story-card"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
    >
      {/* Card content */}
    </motion.article>
  );
}
```

---

## Testing Strategy

### Unit Tests (Optional for MVP)

```typescript
// src/components/__tests__/StoryCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { StoryCard } from '../StoryCard';

describe('StoryCard', () => {
  const mockStory = {
    id: '1',
    title: 'Test Story',
    summary: 'Test summary',
    status: 'verified',
    // ...
  };
  
  it('renders story title', () => {
    render(<StoryCard story={mockStory} onReadMore={() => {}} />);
    expect(screen.getByText('Test Story')).toBeInTheDocument();
  });
  
  it('calls onReadMore when clicked', () => {
    const onReadMore = jest.fn();
    render(<StoryCard story={mockStory} onReadMore={onReadMore} />);
    
    fireEvent.click(screen.getByRole('article'));
    expect(onReadMore).toHaveBeenCalledWith('1');
  });
});
```

---

## Deployment

### Environment Variables

```bash
# .env.example
VITE_API_BASE_URL=https://api.pulse.app
VITE_TELEGRAM_BOT_USERNAME=pulse_daily_bot
VITE_APP_VERSION=1.0.0
```

### Build Configuration

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['framer-motion', '@headlessui/react'],
        },
      },
    },
  },
});
```

### Deployment Steps

1. **Build:**
```bash
npm run build
```

2. **Deploy to Vercel:**
```bash
vercel --prod
```

3. **Update Bot:**
```python
# In backend: Update Mini App URL in bot menu button
menu_button = MenuButtonWebApp(
    text="📰 Дайджест",
    web_app=WebAppInfo(url="https://pulse-app.vercel.app")
)
await bot.set_chat_menu_button(menu_button=menu_button)
```

---

## Progressive Web App (PWA) Features

### manifest.json

```json
{
  "name": "Pulse News Digest",
  "short_name": "Pulse",
  "description": "Your personalized news digest",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#1A1D2E",
  "theme_color": "#FF6B6B",
  "icons": [
    {
      "src": "/icon-192.png",
      "sizes": "192x192",
      "type": "image/png"
    },
    {
      "src": "/icon-512.png",
      "sizes": "512x512",
      "type": "image/png"
    }
  ]
}
```

### Service Worker (Optional)

```typescript
// sw.ts - Basic caching strategy
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('pulse-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/index.html',
        '/assets/index.css',
        '/assets/index.js',
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
```

---

## Accessibility

### Requirements

- Semantic HTML
- ARIA labels where needed
- Keyboard navigation support
- Focus management
- Color contrast ratios (WCAG AA)

### Example

```tsx
function StoryCard({ story, onReadMore }: StoryCardProps) {
  return (
    <article
      className="story-card"
      onClick={() => onReadMore(story.id)}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          onReadMore(story.id);
        }
      }}
      tabIndex={0}
      role="button"
      aria-label={`Read more about: ${story.title}`}
    >
      {/* Card content */}
    </article>
  );
}
```

---

## Monitoring & Analytics

### Error Tracking

```typescript
// Optional: Sentry integration
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  integrations: [
    new Sentry.BrowserTracing(),
  ],
  tracesSampleRate: 0.1,
});
```

### Analytics Events

```typescript
// Track user interactions
export function trackEvent(
  eventName: string, 
  properties?: Record<string, any>
) {
  // Send to your analytics service
  console.log('Analytics:', eventName, properties);
  
  // Example: Telegram analytics
  window.Telegram?.WebApp?.sendData(
    JSON.stringify({ event: eventName, ...properties })
  );
}

// Usage
trackEvent('story_opened', { storyId: story.id, category: story.category });
trackEvent('digest_viewed', { storiesCount: stories.length });
```

---

## MVP Scope - What to Build First

### Phase 1: Core Functionality (2-3 weeks)

**Must Have:**
- ✅ DigestPage with story list
- ✅ StoryPage with full details
- ✅ Tabs navigation (Trending/All/Categories)
- ✅ Telegram WebApp integration
- ✅ API integration
- ✅ Responsive design
- ✅ Dark/Light theme
- ✅ Basic animations

**Can Skip:**
- ❌ Stats page (Phase 2)
- ❌ Saved stories (Phase 2)
- ❌ Settings page (Phase 2)
- ❌ Charts/graphs (Phase 2)
- ❌ Search (Phase 2)
- ❌ PWA features (Phase 2)

### Phase 2: Enhanced Features (1-2 weeks)

- ✅ Stats page with charts
- ✅ Saved stories functionality
- ✅ Settings page
- ✅ Search
- ✅ Filters
- ✅ Share functionality

---

## Integration with Main Bot

### Opening Mini App from Bot

```python
# In bot handlers
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

@router.message(Command("summary"))
async def cmd_summary(message: Message):
    """Open digest in Mini App"""
    
    user = await get_user(message.from_user.id)
    today = datetime.now().date()
    
    # Create WebApp button
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="📰 Відкрити дайджест",
            web_app=WebAppInfo(
                url=f"https://pulse-app.vercel.app/?userId={user.id}&date={today}"
            )
        )],
        [InlineKeyboardButton(
            text="📄 Текстова версія",
            callback_data=f"digest_text:{today}"
        )]
    ])
    
    digest_stats = await get_digest_stats(user.id, today)
    
    await message.answer(
        f"💓 Твій дайджест за {today.strftime('%d %B')} готовий!\n\n"
        f"📊 {digest_stats['total']} новин з {digest_stats['channels']} каналів\n"
        f"🔥 {digest_stats['trending']} trending тем",
        reply_markup=keyboard
    )
```

### Menu Button

```python
# Set persistent menu button
from aiogram.types import MenuButtonWebApp

async def setup_menu_button(bot: Bot):
    """Set Mini App as menu button"""
    
    menu_button = MenuButtonWebApp(
        text="📰 Дайджест",
        web_app=WebAppInfo(url="https://pulse-app.vercel.app")
    )
    
    await bot.set_chat_menu_button(menu_button=menu_button)
```

---

## Success Metrics

### User Engagement

- **Session Duration:** Avg time in Mini App
- **Page Views:** Pages per session
- **Interaction Rate:** % users who open story details
- **Return Rate:** % users who open Mini App again

### Technical Performance

- **Load Time:** <2 seconds initial load
- **Time to Interactive:** <3 seconds
- **Bundle Size:** <500KB gzipped
- **Lighthouse Score:** >90 Performance, >95 Accessibility

### Business Metrics

- **Adoption Rate:** % users who prefer Mini App vs text
- **Retention Impact:** Retention difference Mini App vs text users
- **Feature Usage:** Most used features in Mini App

---

## Next Steps After MVP

### Phase 3 Features:
- 🎧 Audio player for podcasts (inline)
- 📊 Advanced analytics dashboard
- 🔍 Full-text search across all digests
- 📤 Share to social media
- 💬 Comments/reactions (if community features)
- 🎨 Customizable themes
- 📱 Native app feel (swipe gestures, pull-to-refresh)
- 🌐 Multi-language support

---

## Support & Maintenance

### Browser Compatibility

**Target browsers:**
- Chrome/Edge 90+
- Safari 14+
- Firefox 88+
- Telegram WebView (Android/iOS)

### Known Issues & Solutions

**Issue:** Telegram WebView sometimes doesn't support latest CSS features
**Solution:** Use PostCSS with autoprefixer, test in actual Telegram

**Issue:** Back button behavior in nested routes
**Solution:** Properly manage Telegram BackButton state

---

## Final Checklist Before Launch

- [ ] All core pages implemented
- [ ] API integration working
- [ ] Telegram WebApp auth working
- [ ] Responsive on all screen sizes
- [ ] Dark/Light themes working
- [ ] Animations smooth (60fps)
- [ ] Images optimized
- [ ] Error handling in place
- [ ] Loading states for all async operations
- [ ] Tested in real Telegram (Android + iOS)
- [ ] Menu button configured in bot
- [ ] Production API URL configured
- [ ] Analytics tracking setup
- [ ] Build optimized (<500KB)
- [ ] Deployed to production
- [ ] SSL certificate valid
- [ ] Backup/rollback plan ready

---

**Успіхів з розробкою Mini App! 🚀**

Це технічне завдання покриває всі аспекти розробки від архітектури до deployment. Розробник має всю необхідну інформацію для створення high-quality Mini App для Pulse.
