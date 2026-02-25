# Pulse Mini App - Технічне завдання

## Огляд проекту

**Назва:** Pulse News Digest Mini App  
**Платформа:** Telegram Mini App (WebApp)  
**Мета:** Інтерактивний веб-інтерфейс для перегляду персоналізованих новинних дайджестів

**Інтеграція з основним ботом:**
- Mini App відкривається через кнопку в боті
- Отримує дані через API backend
- Синхронізується з налаштуваннями користувача
- Доступний тільки авторизованим користувачам бота

---

## Технічний стек

### Frontend
- **Framework:** React 18+ з TypeScript
- **Build tool:** Vite
- **Styling:** Tailwind CSS + CSS Modules
- **State management:** Zustand або React Context
- **HTTP client:** Axios
- **Routing:** React Router v6
- **UI components:** Headless UI або Radix UI
- **Icons:** Lucide React
- **Animations:** Framer Motion
- **Charts:** Recharts або Chart.js

### Integration
- **Telegram SDK:** @twa-dev/sdk
- **API:** REST API (з основного backend)
- **Auth:** Telegram WebApp initData validation

### Deployment
- **Hosting:** Vercel, Netlify або Cloudflare Pages
- **CDN:** Automatic через hosting platform
- **SSL:** Обов'язково (HTTPS)

### Development
- **Package manager:** pnpm або npm
- **Linting:** ESLint + Prettier
- **Type checking:** TypeScript strict mode
- **Testing:** Vitest + React Testing Library (опційно для MVP)

---

## Архітектура додатку

### Структура проекту

```
pulse-miniapp/
├── public/
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── api/
│   │   ├── client.ts           # Axios instance
│   │   ├── auth.ts             # Telegram auth
│   │   ├── digest.ts           # Digest endpoints
│   │   └── types.ts            # API types
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.tsx
│   │   │   ├── Tabs.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   └── ErrorBoundary.tsx
│   │   │
│   │   ├── digest/
│   │   │   ├── DigestHeader.tsx
│   │   │   ├── StoryCard.tsx
│   │   │   ├── StoryList.tsx
│   │   │   └── FilterBar.tsx
│   │   │
│   │   ├── story/
│   │   │   ├── StoryDetail.tsx
│   │   │   ├── StoryHeader.tsx
│   │   │   ├── StorySummary.tsx
│   │   │   ├── SourcesList.tsx
│   │   │   ├── Timeline.tsx
│   │   │   └── ShareButton.tsx
│   │   │
│   │   ├── stats/
│   │   │   ├── StatsOverview.tsx
│   │   │   ├── CategoryChart.tsx
│   │   │   └── TrendingTopics.tsx
│   │   │
│   │   └── settings/
│   │       ├── SettingsForm.tsx
│   │       ├── ThemeToggle.tsx
│   │       └── NotificationSettings.tsx
│   │
│   ├── pages/
│   │   ├── DigestPage.tsx      # Головна сторінка з дайджестом
│   │   ├── StoryPage.tsx       # Деталі новини
│   │   ├── StatsPage.tsx       # Статистика
│   │   ├── SavedPage.tsx       # Збережені новини
│   │   └── SettingsPage.tsx    # Налаштування
│   │
│   ├── hooks/
│   │   ├── useTelegram.ts      # Telegram WebApp SDK
│   │   ├── useDigest.ts        # Digest data fetching
│   │   ├── useStory.ts         # Story data fetching
│   │   └── useTheme.ts         # Theme management
│   │
│   ├── store/
│   │   ├── userStore.ts        # User state
│   │   ├── digestStore.ts      # Digest state
│   │   └── settingsStore.ts    # Settings state
│   │
│   ├── utils/
│   │   ├── formatters.ts       # Date, number formatters
│   │   ├── validators.ts       # Input validation
│   │   └── constants.ts        # App constants
│   │
│   ├── styles/
│   │   ├── globals.css         # Global styles
│   │   └── themes.css          # Theme variables
│   │
│   ├── types/
│   │   ├── digest.ts           # Digest types
│   │   ├── story.ts            # Story types
│   │   └── user.ts             # User types
│   │
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
│
├── .env.example
├── .eslintrc.js
├── .prettierrc
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

---

## Дизайн система

### Кольорова палітра

```css
/* Light Theme */
--color-primary: #FF6B6B;        /* Coral Red */
--color-secondary: #4ECDC4;      /* Electric Blue */
--color-background: #FFFFFF;     /* White */
--color-surface: #F8F9FA;        /* Light Gray */
--color-text-primary: #2D3436;   /* Dark Gray */
--color-text-secondary: #636E72; /* Medium Gray */
--color-border: #DFE6E9;         /* Light Border */

/* Dark Theme */
--color-primary-dark: #FF6B6B;
--color-secondary-dark: #4ECDC4;
--color-background-dark: #1A1D2E;    /* Navy */
--color-surface-dark: #252A3F;       /* Dark Navy */
--color-text-primary-dark: #FFFFFF;
--color-text-secondary-dark: #B2B9C4;
--color-border-dark: #3A4059;

/* Status Colors */
--color-trending: #FF6B6B;       /* Red */
--color-verified: #4ECDC4;       /* Blue */
--color-pending: #95A5A6;        /* Gray */
--color-success: #00B894;        /* Green */
--color-warning: #FDCB6E;        /* Yellow */
--color-error: #D63031;          /* Red */
```

### Typography

```css
/* Font Family */
--font-primary: -apple-system, BlinkMacSystemFont, 'Segoe UI', 
                Roboto, 'Helvetica Neue', Arial, sans-serif;

/* Font Sizes */
--text-xs: 12px;     /* Small labels */
--text-sm: 14px;     /* Body text, secondary */
--text-base: 16px;   /* Body text */
--text-lg: 18px;     /* Large body */
--text-xl: 20px;     /* Subtitle */
--text-2xl: 24px;    /* Title */
--text-3xl: 30px;    /* Large title */

/* Font Weights */
--font-normal: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;

/* Line Heights */
--leading-tight: 1.25;
--leading-normal: 1.5;
--leading-relaxed: 1.75;
```

### Spacing

```css
/* Spacing Scale */
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

### Border Radius

```css
--radius-sm: 4px;    /* Buttons, small elements */
--radius-md: 8px;    /* Cards, inputs */
--radius-lg: 12px;   /* Large cards */
--radius-xl: 16px;   /* Hero elements */
--radius-full: 9999px; /* Pills, avatars */
```

### Shadows

```css
/* Light Theme */
--shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
--shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
--shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
--shadow-xl: 0 20px 25px rgba(0, 0, 0, 0.15);

/* Dark Theme */
--shadow-sm-dark: 0 1px 2px rgba(0, 0, 0, 0.3);
--shadow-md-dark: 0 4px 6px rgba(0, 0, 0, 0.4);
--shadow-lg-dark: 0 10px 15px rgba(0, 0, 0, 0.5);
```

---

## Сторінки та компоненти

## 1. DigestPage (Головна сторінка)

### Layout

```
┌─────────────────────────────────────┐
│ 💓 Pulse          15 лютого    [≡] │ ← Header (fixed)
├─────────────────────────────────────┤
│ [Trending] [Всі] [Бізнес] [Tech] → │ ← Tabs (sticky)
├─────────────────────────────────────┤
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔥 TRENDING                     │ │
│ │ 🔴 Нова економічна реформа      │ │
│ │                                 │ │
│ │ Уряд оголосив пакет реформ... │ │ ← Story Card
│ │                                 │ │
│ │ 📌 3 з 7 джерел                 │ │
│ │ [Читати більше →]               │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔴 MonoAI залучив $5M           │ │
│ │ ...                             │ │ ← Scroll area
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ 🔵 Нові правила для IT-ФОПів    │ │
│ │ ...                             │ │
│ └─────────────────────────────────┘ │
│                                     │
├─────────────────────────────────────┤
│ [📰] [📊] [💾] [⚙️]                 │ ← Bottom Nav (fixed)
└─────────────────────────────────────┘
```

### DigestHeader Component

**Props:**
```typescript
interface DigestHeaderProps {
  date: Date;
  storiesCount: number;
  onMenuClick: () => void;
}
```

**Функціонал:**
- Показує дату дайджесту
- Кількість новин
- Кнопка меню (burger)
- Gradient background з brand кольорами

**Code example:**
```tsx
export function DigestHeader({ date, storiesCount, onMenuClick }: DigestHeaderProps) {
  const formattedDate = formatDate(date, 'dd MMMM yyyy');
  
  return (
    <header className="digest-header">
      <div className="header-content">
        <div className="header-left">
          <div className="logo">💓 Pulse</div>
          <div className="date">{formattedDate}</div>
        </div>
        
        <button 
          className="menu-button"
          onClick={onMenuClick}
          aria-label="Menu"
        >
          <MenuIcon />
        </button>
      </div>
      
      <div className="header-stats">
        <span className="stories-count">
          {storiesCount} {pluralize(storiesCount, 'новина', 'новини', 'новин')}
        </span>
      </div>
    </header>
  );
}
```

### Tabs Component

**Props:**
```typescript
interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
}

interface Tab {
  id: string;
  label: string;
  count?: number;
  icon?: React.ReactNode;
}
```

**Функціонал:**
- Горизонтальний scroll для багатьох табів
- Активний таб підсвічується
- Показує кількість новин в табі
- Smooth scroll animation

**Code example:**
```tsx
export function Tabs({ tabs, activeTab, onTabChange }: TabsProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  
  return (
    <div className="tabs-container">
      <div ref={scrollRef} className="tabs-scroll">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={cn('tab', { active: tab.id === activeTab })}
            onClick={() => onTabChange(tab.id)}
          >
            {tab.icon && <span className="tab-icon">{tab.icon}</span>}
            <span className="tab-label">{tab.label}</span>
            {tab.count !== undefined && (
              <span className="tab-count">{tab.count}</span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
}
```

### StoryCard Component

**Props:**
```typescript
interface StoryCardProps {
  story: Story;
  onReadMore: (storyId: string) => void;
}

interface Story {
  id: string;
  title: string;
  summary: string;
  status: 'trending' | 'verified' | 'pending';
  category: string;
  userSourcesCount: number;
  totalSourcesCount: number;
  firstSource: {
    channelTitle: string;
    channelAvatar: string;
    publishedAt: Date;
  };
  sources: Source[];
}
```

**Функціонал:**
- Компактне відображення новини
- Badge зі статусом (trending/verified)
- Короткий саммарі (перші 150 символів)
- Кількість джерел
- Аватарки каналів (перші 3)
- Click для деталей

**Code example:**
```tsx
export function StoryCard({ story, onReadMore }: StoryCardProps) {
  const statusConfig = {
    trending: { icon: '🔥', label: 'TRENDING', color: 'red' },
    verified: { icon: '🔵', label: 'VERIFIED', color: 'blue' },
    pending: { icon: '⚪', label: 'PENDING', color: 'gray' }
  };
  
  const config = statusConfig[story.status];
  const shortSummary = truncate(story.summary, 150);
  
  return (
    <article className="story-card" onClick={() => onReadMore(story.id)}>
      {/* Header */}
      <div className="story-card-header">
        <Badge 
          icon={config.icon}
          label={config.label}
          color={config.color}
        />
        <div className="sources-badge">
          📌 {story.userSourcesCount} з {story.totalSourcesCount}
        </div>
      </div>
      
      {/* Content */}
      <h3 className="story-title">{story.title}</h3>
      <p className="story-summary">{shortSummary}</p>
      
      {/* Footer */}
      <div className="story-card-footer">
        <div className="channel-avatars">
          {story.sources.slice(0, 3).map(source => (
            <img
              key={source.id}
              src={source.channelAvatar}
              alt={source.channelTitle}
              className="channel-avatar"
            />
          ))}
          {story.sources.length > 3 && (
            <span className="more-channels">
              +{story.sources.length - 3}
            </span>
          )}
        </div>
        
        <button className="read-more-btn">
          Детальніше →
        </button>
      </div>
    </article>
  );
}
```

**Styling:**
```css
.story-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  box-shadow: var(--shadow-sm);
  cursor: pointer;
  transition: all 0.2s ease;
}

.story-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.story-card:active {
  transform: translateY(0);
}

.story-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-3);
}

.story-title {
  font-size: var(--text-lg);
  font-weight: var(--font-semibold);
  color: var(--color-text-primary);
  margin-bottom: var(--space-2);
  line-height: var(--leading-tight);
}

.story-summary {
  font-size: var(--text-sm);
  color: var(--color-text-secondary);
  line-height: var(--leading-normal);
  margin-bottom: var(--space-4);
}

.story-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.channel-avatars {
  display: flex;
  align-items: center;
  gap: var(--space-1);
}

.channel-avatar {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-full);
  border: 2px solid var(--color-surface);
  margin-left: -8px;
}

.channel-avatar:first-child {
  margin-left: 0;
}

.read-more-btn {
  color: var(--color-primary);
  font-weight: var(--font-medium);
  font-size: var(--text-sm);
}
```

---

## 2. StoryPage (Деталі новини)

### Layout

```
┌─────────────────────────────────────┐
│ [←] Нова економічна реформа    [⋮] │ ← Header
├─────────────────────────────────────┤
│ [Саммарі] [Джерела] [Timeline]     │ ← Tabs
├─────────────────────────────────────┤
│                                     │
│ 📝 ПОВНИЙ ЗМІСТ                     │
│                                     │
│ Уряд оголосив пакет реформ який    │
│ вплине на малий бізнес. Основні    │
│ зміни:                              │
│                                     │
│ • Спрощення реєстрації              │ ← Scroll area
│ • Зниження податків до 5%           │
│ • Цифровізація через Дія            │
│                                     │
│ [Повний текст резюме]               │
│                                     │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                     │
│ 📊 ДЖЕРЕЛА (7)                      │
│                                     │
│ ⚡ Першоджерело:                    │
│ ┌─────────────────────────────────┐ │
│ │ 📢 Мінфін                       │ │
│ │ 11:23  •  127K переглядів       │ │
│ │ [Відкрити в каналі →]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ 📰 Детальний аналіз:                │
│ ┌─────────────────────────────────┐ │
│ │ 📢 Forbes Ukraine               │ │
│ │ 12:10  •  487 слів              │ │
│ │ [Відкрити →]                    │ │
│ └─────────────────────────────────┘ │
│                                     │
│ [Показати ще 5 джерел →]            │
│                                     │
├─────────────────────────────────────┤
│ [Поділитися] [Зберегти] [Закрити]  │ ← Actions
└─────────────────────────────────────┘
```

### StoryDetail Component

**Props:**
```typescript
interface StoryDetailProps {
  storyId: string;
  onBack: () => void;
}
```

**Tabs:**
1. **Саммарі** - повний текст резюме
2. **Джерела** - список всіх джерел з деталями
3. **Timeline** - візуалізація поширення

**Code example:**
```tsx
export function StoryDetail({ storyId, onBack }: StoryDetailProps) {
  const { data: story, isLoading } = useStory(storyId);
  const [activeTab, setActiveTab] = useState('summary');
  
  if (isLoading) return <LoadingSpinner />;
  if (!story) return <ErrorMessage />;
  
  return (
    <div className="story-detail">
      <StoryHeader 
        title={story.title}
        status={story.status}
        onBack={onBack}
      />
      
      <Tabs
        tabs={[
          { id: 'summary', label: 'Саммарі' },
          { id: 'sources', label: 'Джерела', count: story.sources.length },
          { id: 'timeline', label: 'Timeline' }
        ]}
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />
      
      <div className="story-content">
        {activeTab === 'summary' && <StorySummary summary={story.summary} />}
        {activeTab === 'sources' && <SourcesList sources={story.sources} />}
        {activeTab === 'timeline' && <Timeline publications={story.publications} />}
      </div>
      
      <StoryActions 
        storyId={storyId}
        onShare={() => shareStory(story)}
        onSave={() => saveStory(story)}
      />
    </div>
  );
}
```

### SourcesList Component

**Props:**
```typescript
interface SourcesListProps {
  sources: Source[];
}

interface Source {
  id: string;
  channelId: string;
  channelTitle: string;
  channelAvatar: string;
  channelUsername?: string;
  publishedAt: Date;
  postUrl: string;
  wordCount: number;
  viewsCount: number;
  reactionsCount: number;
  isPrimarySource: boolean;
  isMostDetailed: boolean;
}
```

**Функціонал:**
- Показує всі джерела новини
- Виділяє першоджерело (⚡)
- Показує найдетальніше покриття (📰)
- Метрики кожного джерела
- Кнопка "Відкрити в каналі"

**Code example:**
```tsx
export function SourcesList({ sources }: SourcesListProps) {
  const primarySource = sources.find(s => s.isPrimarySource);
  const detailedSource = sources.find(s => s.isMostDetailed);
  const otherSources = sources.filter(
    s => !s.isPrimarySource && !s.isMostDetailed
  );
  
  return (
    <div className="sources-list">
      {primarySource && (
        <div className="source-section">
          <h4 className="source-section-title">
            ⚡ Першоджерело:
          </h4>
          <SourceCard source={primarySource} isPrimary />
        </div>
      )}
      
      {detailedSource && detailedSource !== primarySource && (
        <div className="source-section">
          <h4 className="source-section-title">
            📰 Найдетальніше покриття:
          </h4>
          <SourceCard source={detailedSource} />
        </div>
      )}
      
      {otherSources.length > 0 && (
        <div className="source-section">
          <h4 className="source-section-title">
            Інші джерела ({otherSources.length}):
          </h4>
          {otherSources.map(source => (
            <SourceCard key={source.id} source={source} />
          ))}
        </div>
      )}
    </div>
  );
}

function SourceCard({ source, isPrimary = false }: { source: Source; isPrimary?: boolean }) {
  const formattedTime = formatTime(source.publishedAt);
  const formattedViews = formatNumber(source.viewsCount);
  
  return (
    <div className={cn('source-card', { primary: isPrimary })}>
      <div className="source-header">
        <img 
          src={source.channelAvatar} 
          alt={source.channelTitle}
          className="source-avatar"
        />
        <div className="source-info">
          <div className="source-name">{source.channelTitle}</div>
          <div className="source-meta">
            {formattedTime} • {formattedViews} переглядів
          </div>
        </div>
      </div>
      
      <div className="source-stats">
        <span className="stat">
          📝 {source.wordCount} слів
        </span>
        <span className="stat">
          ❤️ {source.reactionsCount} реакцій
        </span>
      </div>
      
      <button 
        className="open-channel-btn"
        onClick={() => window.open(source.postUrl, '_blank')}
      >
        Відкрити в каналі →
      </button>
    </div>
  );
}
```

### Timeline Component

**Props:**
```typescript
interface TimelineProps {
  publications: Publication[];
}

interface Publication {
  id: string;
  channelTitle: string;
  publishedAt: Date;
}
```

**Функціонал:**
- Візуальна timeline поширення новини
- Показує хронологію публікацій
- Різниця в часі між публікаціями
- Scroll horizontal якщо багато джерел

**Code example:**
```tsx
export function Timeline({ publications }: TimelineProps) {
  const sorted = [...publications].sort(
    (a, b) => a.publishedAt.getTime() - b.publishedAt.getTime()
  );
  
  const firstTime = sorted[0].publishedAt;
  const lastTime = sorted[sorted.length - 1].publishedAt;
  
  return (
    <div className="timeline">
      <div className="timeline-header">
        <h4>⏱ Поширення новини</h4>
        <div className="timeline-range">
          {formatTime(firstTime)} → {formatTime(lastTime)}
        </div>
      </div>
      
      <div className="timeline-track">
        {sorted.map((pub, index) => {
          const prevPub = sorted[index - 1];
          const timeDiff = prevPub 
            ? getTimeDiff(prevPub.publishedAt, pub.publishedAt)
            : null;
          
          return (
            <div key={pub.id} className="timeline-item">
              <div className="timeline-point" />
              <div className="timeline-content">
                <div className="timeline-time">
                  {formatTime(pub.publishedAt)}
                  {timeDiff && (
                    <span className="time-diff">+{timeDiff}</span>
                  )}
                </div>
                <div className="timeline-channel">
                  {pub.channelTitle}
                  {index === 0 && <span className="badge">⚡ першим</span>}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
```

---

## 3. StatsPage (Статистика)

### Layout

```
┌─────────────────────────────────────┐
│ 📊 Твоя статистика                  │ ← Header
├─────────────────────────────────────┤
│                                     │
│ За тиждень:                         │
│ ┌─────────────────────────────────┐ │
│ │ 📰 124 новини прочитано         │ │
│ │ ⏱ 10 год заощаджено             │ │
│ │ 🔥 3 trending теми               │ │ ← Stats Cards
│ └─────────────────────────────────┘ │
│                                     │
│ Топ категорії:                      │
│ ┌─────────────────────────────────┐ │
│ │     [Pie Chart]                 │ │
│ │                                 │ │ ← Category Chart
│ │ 💼 Бізнес - 45%                 │ │
│ │ 💻 Tech - 30%                   │ │
│ │ 📰 Новини - 25%                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Trending topics:                    │
│ ┌─────────────────────────────────┐ │
│ │ 1. AI/ML - 23 згадки ↑          │ │
│ │ 2. Стартапи - 18 згадок         │ │ ← Trending List
│ │ 3. Податки - 15 згадок ↓        │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Активність по днях:                 │
│ ┌─────────────────────────────────┐ │
│ │     [Bar Chart]                 │ │
│ │                                 │ │ ← Activity Chart
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘
```

### StatsOverview Component

**Props:**
```typescript
interface StatsOverviewProps {
  stats: UserStats;
  period: 'week' | 'month' | 'all';
}

interface UserStats {
  storiesRead: number;
  timeSaved: number; // minutes
  trendingTopics: number;
  categoriesBreakdown: Record<string, number>;
