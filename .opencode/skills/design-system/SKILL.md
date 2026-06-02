# SKILL: design-system

> Брендирование UI в стиле FELETI. Используй при создании/изменении компонентов, страниц, тем.

## 1. Бренд-сводка

**FELETI** — бренд ООО «АгроПищеПром», г. Брест, Беларусь.  
**FELETI-SMOK** — направление коптильных камер + софт.  
**Слоган:** «Feel the progress».

**Ценности:** технологичность, открытость, надёжность, партнёрство, честность.  
**Тон:** деловой, но не сухой. Конкретный, без понтов. Технологичный.

**Детали:** `docs/FELETI_BRAND.md`.

## 2. Цветовая палитра (must-use)

### 2.1. Tailwind config

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: ["class"],
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // FELETI brand
        feleti: {
          black: "#0A0A0A",
          white: "#FFFFFF",
          red: {
            DEFAULT: "#E30613",
            dark: "#B3040F",
          },
        },
        // Surfaces (dark)
        "surface-1": "#1A1A1A",
        "surface-2": "#242424",
        "surface-3": "#2E2E2E",
        border: "#3A3A3A",
        // Semantic
        success: "#10B981",
        warning: "#F59E0B",
        error: "#EF4444",
        info: "#3B82F6",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      borderRadius: {
        sm: "4px",
        md: "8px",
        lg: "12px",
        xl: "16px",
      },
      boxShadow: {
        "fe-sm": "0 1px 2px rgba(0,0,0,0.05)",
        "fe-md": "0 2px 8px rgba(0,0,0,0.08)",
        "fe-lg": "0 8px 24px rgba(0,0,0,0.12)",
        "fe-xl": "0 16px 48px rgba(0,0,0,0.16)",
      },
      animation: {
        "fe-fade": "fadeIn 300ms cubic-bezier(0.16, 1, 0.3, 1)",
        "fe-slide-up": "slideUp 300ms cubic-bezier(0.16, 1, 0.3, 1)",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
```

### 2.2. CSS-переменные (для shadcn)

```css
/* frontend/app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;          /* white */
    --foreground: 0 0% 4%;            /* feleti-black */
    --card: 0 0% 100%;
    --card-foreground: 0 0% 4%;
    --primary: 357 95% 46%;           /* feleti-red #E30613 */
    --primary-foreground: 0 0% 100%;
    --secondary: 0 0% 96%;            /* surface-1 light */
    --secondary-foreground: 0 0% 4%;
    --muted: 0 0% 96%;
    --muted-foreground: 0 0% 45%;
    --accent: 357 95% 46%;
    --accent-foreground: 0 0% 100%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
    --info: 217 91% 60%;
    --border: 0 0% 90%;
    --input: 0 0% 90%;
    --ring: 357 95% 46%;
    --radius: 0.5rem;                 /* 8px */
  }
  
  .dark {
    --background: 0 0% 4%;            /* feleti-black */
    --foreground: 0 0% 100%;
    --card: 0 0% 10%;                 /* surface-1 */
    --card-foreground: 0 0% 100%;
    --primary: 357 95% 46%;           /* feleti-red */
    --primary-foreground: 0 0% 100%;
    --secondary: 0 0% 14%;            /* surface-2 */
    --secondary-foreground: 0 0% 100%;
    --muted: 0 0% 14%;
    --muted-foreground: 0 0% 65%;
    --accent: 357 95% 46%;
    --accent-foreground: 0 0% 100%;
    --destructive: 0 84% 60%;
    --destructive-foreground: 0 0% 100%;
    --success: 160 84% 39%;
    --warning: 38 92% 50%;
    --info: 217 91% 60%;
    --border: 0 0% 23%;
    --input: 0 0% 23%;
    --ring: 357 95% 46%;
  }
}

@layer base {
  * { @apply border-border; }
  body {
    @apply bg-background text-foreground;
    font-feature-settings: "rlig" 1, "calt" 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## 3. Типографика

```tsx
// frontend/app/layout.tsx
import { Inter, JetBrains_Mono } from "next/font/google";

const inter = Inter({
  subsets: ["latin", "cyrillic"],
  variable: "--font-inter",
  display: "swap",
});

const jetbrains = JetBrains_Mono({
  subsets: ["latin", "cyrillic"],
  variable: "--font-jetbrains",
  display: "swap",
});

export default function RootLayout({ children }) {
  return (
    <html lang="ru" className={`${inter.variable} ${jetbrains.variable}`}>
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
```

## 4. Компоненты shadcn/ui — кастомизация

### 4.1. Установка

```bash
cd frontend
npx shadcn-ui@latest init
# выбираем: New York style, slate base, CSS variables YES
```

### 4.2. Кастомизация после init

В `tailwind.config.ts` — заменяем `slate` → `feleti`:

```ts
colors: {
  border: "hsl(var(--border))",
  input: "hsl(var(--input))",
  ring: "hsl(var(--ring))",
  background: "hsl(var(--background))",
  foreground: "hsl(var(--foreground))",
  primary: {
    DEFAULT: "hsl(var(--primary))",
    foreground: "hsl(var(--primary-foreground))",
  },
  // ...
}
```

В `globals.css` — заменяем дефолтные shadcn-переменные на FELETI (см. секцию 2.2).

### 4.3. Кнопка с FELETI Red

```tsx
// components/ui/button.tsx (shadcn)
import { cva, type VariantProps } from "class-variance-authority";
import { Slot } from "@radix-ui/react-slot";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90",
        outline: "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary: "bg-secondary text-secondary-foreground hover:bg-secondary/80",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3",
        lg: "h-11 rounded-md px-8",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);
```

**Использование:**
```tsx
<Button>Primary CTA (красный)</Button>
<Button variant="outline">Вторичная</Button>
<Button variant="ghost">Третичная</Button>
<Button variant="destructive">Удалить</Button>
```

## 5. Тёмная тема — дефолт

```tsx
// components/theme-provider.tsx
"use client";
import { createContext, useContext, useEffect, useState } from "react";

type Theme = "dark" | "light" | "system";

const ThemeContext = createContext<{
  theme: Theme;
  setTheme: (t: Theme) => void;
}>({ theme: "dark", setTheme: () => {} });

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>("dark");  // ← дефолт dark
  
  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark");
    if (theme === "system") {
      const systemTheme = window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }
  }, [theme]);
  
  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => useContext(ThemeContext);
```

## 6. Иконки (Lucide React)

```tsx
import { Thermometer, Droplets, Wind, AlertTriangle, ChevronRight } from "lucide-react";

<Thermometer className="h-5 w-5" />
<Droplets className="h-5 w-5 text-info" />
<Wind className="h-5 w-5 text-muted-foreground" />
```

**Правила:**
- Размер: 16 (sm), 20 (md), 24 (default), 32 (lg).
- Цвет: `currentColor` (наследует).
- Stroke: 1.5 px (дефолт).
- Без обводки (заливка — только если нужно).

## 7. Телеметрия — карточка

```tsx
// components/telemetry/chamber-card.tsx
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Thermometer, Droplets, Wind, Zap } from "lucide-react";

export function ChamberCard({ chamber, telemetry }: { chamber: Chamber; telemetry: ChamberTelemetry }) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-medium">
          {chamber.manufacturer.name} {chamber.model}
        </CardTitle>
        <Badge variant={telemetry.errors.length > 0 ? "destructive" : "default"}>
          {telemetry.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-4">
          <Metric icon={<Thermometer />} label="Камера" value={`${telemetry.t_chamber}°C`} />
          <Metric icon={<Thermometer />} label="Продукт" value={`${telemetry.t_product}°C`} />
          <Metric icon={<Droplets />} label="Влажность" value={`${telemetry.humidity}%`} />
          <Metric icon={<Wind />} label="Дым" value={`${telemetry.smoke_density}%`} />
          {chamber.capabilities.supports_electro && (
            <Metric icon={<Zap />} label="Электро" value={`${telemetry.electro_voltage} кВ`} />
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="text-muted-foreground">{icon}</div>
      <div>
        <div className="text-xs text-muted-foreground">{label}</div>
        <div className="text-lg font-semibold font-mono">{value}</div>
      </div>
    </div>
  );
}
```

## 8. Анимации (Framer Motion)

```tsx
import { motion } from "framer-motion";

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
  transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
>
  {children}
</motion.div>
```

**Правила:**
- 200 ms — быстрые (hover, focus).
- 300 ms — стандарт (модалки, drawer'ы).
- 500 ms — медленные (page transitions).
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out-back).
- `prefers-reduced-motion` — обязательно.

## 9. PWA иконки

- `public/icon-192.png` — 192×192
- `public/icon-512.png` — 512×512
- `public/icon-maskable-192.png` — 192×192, safe zone 60%
- `public/icon-maskable-512.png` — 512×512, safe zone 60%
- `public/apple-touch-icon.png` — 180×180
- `public/favicon.ico` — 32×32

**Генерация:** через `real-favicon-generator.net` или `@vite-pwa/assets-generator`.

**Стиль:** чёрный фон + белый/красный логотип F.

## 10. A11y чек-лист

- [ ] Контраст текст/фон ≥ 4.5:1 (WCAG AA).
- [ ] Все интерактивные элементы фокусируемы.
- [ ] `:focus-visible` стиль (ring).
- [ ] `<label>` для всех `<input>`.
- [ ] ARIA для кастомных компонентов (модалки, дропдауны).
- [ ] Навигация с клавиатуры (Tab, Enter, Esc, стрелки).
- [ ] Семантический HTML (`<main>`, `<nav>`, `<article>`).
- [ ] `alt` для изображений.
- [ ] `prefers-reduced-motion` уважается.

## 11. Чек-лист брендирования

- [ ] Используется FELETI Red `#E30613` (не другой оттенок).
- [ ] Тёмная тема — дефолт.
- [ ] Шрифт Inter загружен.
- [ ] Скругления по шкале (4/8/12/full).
- [ ] Тени минималистичные.
- [ ] Анимации ≤ 300 ms.
- [ ] Красный — ≤ 5% площади экрана.
- [ ] Иконки — Lucide (не emoji).
- [ ] A11y — пройден.
- [ ] Логотип в правильной версии (для фона).

## 12. Связь с другими скиллами

- `smoke-platform` — общие правила.

---

**Версия:** 0.1.0
**Загружай:** при создании/изменении UI-компонентов.
