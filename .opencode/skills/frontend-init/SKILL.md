# SKILL: frontend-init

> Инициализация Next.js 14 frontend с FELETI-брендом. Используй при первой настройке или сбросе frontend.

## 1. Предусловия

- Node.js 18+ установлен
- `frontend/` директория пустая или не существует
- Backend запущен и доступен по `http://localhost:8000`

## 2. Инициализация Next.js 14

```bash
cd D:/Коптильные камеры/koptilnya-platform
npx create-next-app@14 frontend --typescript --tailwind --eslint --app --src-dir --no-turbopack
```

**Выборы:**
- TypeScript: **Yes**
- ESLint: **Yes**
- Tailwind CSS: **Yes**
- `src/` directory: **Yes**
- App Router: **Yes**
- Turbopack: **No** (пока стабильнее webpack)

## 3. Установка shadcn/ui

```bash
cd frontend
npx shadcn-ui@latest init
```

**Выборы:**
- Style: **New York**
- Base color: **Slate** (переопределим на FELETI)
- CSS variables: **Yes**

## 4. Установка зависимостей

```bash
cd frontend

# State management
npm install zustand

# Forms + validation
npm install react-hook-form zod @hookform/resolvers

# API + caching
npm install @tanstack/react-query axios

# Charts
npm install recharts

# Icons
npm install lucide-react

# Animations
npm install framer-motion

# Internationalization
npm install next-intl

# PWA
npm install next-pwa

# Offline storage
npm install dexie

# Fonts (Google)
npm install @fontsource/inter @fontsource/jetbrains-mono
```

## 5. Настройка PWA

### 5.1. next.config.js
```js
const withPWA = require('next-pwa')({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
});

/** @type {import('next').NextConfig} */
const nextConfig = withPWA({
  output: 'standalone',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
});

module.exports = nextConfig;
```

### 5.2. public/manifest.json
```json
{
  "name": "FELETI-SMOK",
  "short_name": "FELETI",
  "description": "Платформа управления коптильным производством",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0A0A0A",
  "theme_color": "#E30613",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ]
}
```

## 6. Настройка темы (FELETI)

См. полный `design-system` SKILL. Кратко:

1. Заменить `tailwind.config.ts` на конфиг из `design-system`
2. Заменить `globals.css` на CSS-переменные FELETI
3. Создать `components/theme-provider.tsx` (тёмная тема по умолчанию)
4. Обновить `app/layout.tsx` с шрифтами Inter + JetBrains Mono

## 7. Настройка API-клиента

```typescript
// lib/api/client.ts
import axios from 'axios';

export const apiClient = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
```

## 8. Проверка запуска

```bash
cd frontend
npm run dev
# Открыть http://localhost:3000
```

## 9. Чек-лист

- [ ] Next.js 14 установлен с App Router
- [ ] shadcn/ui инициализирован
- [ ] Все зависимости установлены
- [ ] PWA настроен (manifest, next-pwa)
- [ ] FELETI тема применена (tailwind.config, globals.css)
- [ ] Шрифты подключены (Inter, JetBrains Mono)
- [ ] API-клиент создан
- [ ] `npm run dev` запускается без ошибок
- [ ] `npm run build` собирается без ошибок

## 10. Связь с другими скиллами

- `design-system` — брендирование UI
- `frontend-api-client` — связка с backend
- `smoke-platform` — общие правила

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при инициализации или сбросе frontend.
