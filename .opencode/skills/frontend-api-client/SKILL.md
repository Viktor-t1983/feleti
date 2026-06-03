# SKILL: frontend-api-client

> Связка frontend (Next.js) с backend (FastAPI). API-клиент, TanStack Query, аутентификация, обработка ошибок.

## 1. Архитектура

```
frontend/lib/
├── api/
│   ├── client.ts              # axios instance + interceptors
│   ├── auth.ts                # login, refresh, logout
│   ├── chambers.ts            # CRUD камер
│   ├── recipes.ts             # CRUD рецептов + calc
│   ├── batches.ts             # CRUD партий + lifecycle
│   ├── telemetry.ts           # REST telemetry
│   ├── knowledge.ts           # CRUD базы знаний
│   └── types.ts               # DTO из backend (или generated)
├── stores/
│   └── auth.store.ts          # Zustand: токены, пользователь
└── ws/
    └── chamber-telemetry.ts   # WebSocket менеджер
```

## 2. API-клиент

### 2.1. Базовый клиент
```typescript
// lib/api/client.ts
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — добавляем токен
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Response interceptor — refresh token при 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        const { data } = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        localStorage.setItem('access_token', data.access_token);
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        return api(originalRequest);
      }
    }
    return Promise.reject(error);
  }
);
```

### 2.2. TanStack Query hooks
```typescript
// lib/api/recipes.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';

export function useRecipes(params?: { page?: number; size?: number }) {
  return useQuery({
    queryKey: ['recipes', params],
    queryFn: async () => {
      const { data } = await api.get('/recipes', { params });
      return data;
    },
  });
}

export function useRecipe(id: number) {
  return useQuery({
    queryKey: ['recipe', id],
    queryFn: async () => {
      const { data } = await api.get(`/recipes/${id}`);
      return data;
    },
  });
}

export function useRecipeCalc(id: number) {
  return useQuery({
    queryKey: ['recipe-calc', id],
    queryFn: async () => {
      const { data } = await api.get(`/recipes/${id}/calc`);
      return data;
    },
  });
}

export function useCreateRecipe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: RecipeCreate) => api.post('/recipes', payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['recipes'] }),
  });
}
```

### 2.3. Auth store (Zustand)
```typescript
// lib/stores/auth.store.ts
import { create } from 'zustand';

interface AuthState {
  accessToken: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (access: string, refresh: string) => void;
  logout: () => void;
  setUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  login: (access, refresh) => {
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
    set({ accessToken: access, refreshToken: refresh });
  },
  logout: () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    set({ accessToken: null, refreshToken: null, user: null });
  },
  setUser: (user) => set({ user }),
}));
```

## 3. Типы

Генерация из OpenAPI (опционально):
```bash
# Установить openapi-typescript
npm install -D openapi-typescript

# Сгенерировать типы из running backend
npx openapi-typescript http://localhost:8000/api/v1/openapi.json -o lib/api/types.gen.ts
```

Или ручные типы:
```typescript
// lib/api/types.ts
export interface Recipe {
  id: number;
  name: string;
  slug: string;
  status: 'draft' | 'pending' | 'approved' | 'archived';
  current_version_id: number | null;
  // ...
}

export interface RecipeCalcResult {
  total_mass_kg: number;
  finished_mass_kg: number;
  losses_percent: number;
  cost_per_kg_raw: number;
  cost_per_kg_finished: number;
  bju_per_100g: {
    protein: number;
    fat: number;
    carbs: number;
    kcal: number;
  };
}
```

## 4. Обработка ошибок

```typescript
// components/ui/error-boundary.tsx
export function APIError({ error }: { error: Error }) {
  const message = axios.isAxiosError(error)
    ? error.response?.data?.error?.message || error.message
    : error.message;
  
  return (
    <div className="rounded-lg border border-error/20 bg-error/10 p-4 text-error">
      <p className="font-medium">Ошибка загрузки</p>
      <p className="text-sm">{message}</p>
    </div>
  );
}
```

## 5. Offline / кэширование

TanStack Query автоматически кэширует. Для offline-first добавить Dexie:
```typescript
// lib/offline/db.ts
import Dexie from 'dexie';

class OfflineDB extends Dexie {
  recipes!: Dexie.Table<Recipe, number>;
  
  constructor() {
    super('FELETI-SMOK');
    this.version(1).stores({
      recipes: '++id, slug, status',
    });
  }
}

export const offlineDB = new OfflineDB();
```

## 6. Чек-лист

- [ ] Axios instance с interceptors
- [ ] TanStack Query hooks для всех сущностей
- [ ] Zustand auth store
- [ ] Авто-refresh токена при 401
- [ ] Типы DTO (сгенерированы или ручные)
- [ ] Обработка ошибок (AxiosError)
- [ ] Offline кэш для критичных данных
- [ ] CORS настроен на backend

## 7. Связь с другими скиллами

- `frontend-init` — базовая настройка
- `design-system` — UI для ошибок, загрузки
- `telemetry-websocket` — WebSocket поверх REST
- `smoke-platform` — общие правила

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при создании связки frontend ↔ backend.
