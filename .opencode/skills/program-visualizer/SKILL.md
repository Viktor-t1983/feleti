# SKILL: program-visualizer

> Мега-крутая визуализация программ копчения: timeline фаз, графики температуры/времени, индикаторы прогресса. Используй при создании UI рецептов и мониторинга партий.

## 1. Что визуализируем

Программа копчения — это список фаз (ProgramPhase):
```typescript
interface ProgramPhase {
  index: number;
  name: string;           // "Подсушка", "Копчение", "Варка", "Охлаждение"
  duration_min: number;
  t_chamber: number;      // °C
  t_product?: number;     // °C (target)
  humidity_percent?: number;
  smoke: 'none' | 'light' | 'medium' | 'heavy';
  wood_species?: string;  // "ольха", "бук", "дуб"...
  electro_voltage_kv?: number;  // 0 = выкл
  fan_speed_percent?: number;
  transition: 'time' | 'product_temp' | 'delta_t';
}
```

## 2. Компоненты визуализации

### 2.1. Timeline фаз (основной)
```tsx
// components/recipe/phase-timeline.tsx
import { motion } from 'framer-motion';

export function PhaseTimeline({ phases, currentPhase }: { phases: ProgramPhase[]; currentPhase?: number }) {
  const totalDuration = phases.reduce((sum, p) => sum + p.duration_min, 0);
  
  return (
    <div className="flex w-full gap-1 rounded-lg bg-surface-2 p-2">
      {phases.map((phase, i) => {
        const widthPercent = (phase.duration_min / totalDuration) * 100;
        const isActive = i === currentPhase;
        const isCompleted = currentPhase !== undefined && i < currentPhase;
        
        return (
          <motion.div
            key={phase.index}
            className={cn(
              "relative flex flex-col items-center justify-center rounded px-2 py-3 text-xs",
              isActive && "bg-feleti-red text-white",
              isCompleted && "bg-success/20 text-success",
              !isActive && !isCompleted && "bg-surface-3 text-muted-foreground"
            )}
            style={{ width: `${widthPercent}%` }}
            layout
          >
            <span className="font-medium">{phase.name}</span>
            <span>{phase.duration_min} мин</span>
            <span className="mt-1 font-mono">{phase.t_chamber}°C</span>
            {phase.smoke !== 'none' && (
              <span className="mt-0.5 text-[10px] opacity-70">дым: {phase.smoke}</span>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
```

### 2.2. График температуры по времени
```tsx
// components/recipe/temperature-chart.tsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function TemperatureChart({ phases }: { phases: ProgramPhase[] }) {
  const data = phases.map((p, i) => ({
    name: p.name,
    time: phases.slice(0, i + 1).reduce((s, x) => s + x.duration_min, 0),
    t_chamber: p.t_chamber,
    t_product: p.t_product || null,
  }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#3A3A3A" />
        <XAxis dataKey="name" stroke="#888" />
        <YAxis stroke="#888" label={{ value: '°C', angle: -90 }} />
        <Tooltip 
          contentStyle={{ background: '#1A1A1A', border: '1px solid #3A3A3A' }}
          labelStyle={{ color: '#fff' }}
        />
        <Line type="stepAfter" dataKey="t_chamber" stroke="#E30613" strokeWidth={2} dot />
        <Line type="stepAfter" dataKey="t_product" stroke="#3B82F6" strokeWidth={2} strokeDasharray="5 5" dot />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 2.3. Круговой прогресс (для active batch)
```tsx
// components/batch/circular-progress.tsx
export function CircularProgress({ progress, phase, totalPhases }: { progress: number; phase: number; totalPhases: number }) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (progress / 100) * circumference;

  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <svg className="h-full w-full -rotate-90">
        <circle cx="64" cy="64" r={radius} stroke="#3A3A3A" strokeWidth="8" fill="none" />
        <circle
          cx="64" cy="64" r={radius}
          stroke="#E30613"
          strokeWidth="8"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className="transition-all duration-500"
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-bold">{Math.round(progress)}%</div>
        <div className="text-xs text-muted-foreground">{phase + 1}/{totalPhases}</div>
      </div>
    </div>
  );
}
```

### 2.4. Карточка фазы (детали)
```tsx
// components/recipe/phase-card.tsx
export function PhaseCard({ phase, isActive }: { phase: ProgramPhase; isActive?: boolean }) {
  return (
    <Card className={cn(isActive && "border-feleti-red")}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">{phase.index + 1}. {phase.name}</CardTitle>
          {phase.smoke !== 'none' && <SmokeBadge level={phase.smoke} />}
        </div>
      </CardHeader>
      <CardContent className="grid grid-cols-3 gap-2 text-sm">
        <Metric label="Время" value={`${phase.duration_min} мин`} />
        <Metric label="Камера" value={`${phase.t_chamber}°C`} />
        {phase.humidity_percent && <Metric label="Влажность" value={`${phase.humidity_percent}%`} />}
        {phase.electro_voltage_kv ? <Metric label="Электро" value={`${phase.electro_voltage_kv} кВ`} /> : null}
        {phase.wood_species ? <Metric label="Щепа" value={phase.wood_species} /> : null}
      </CardContent>
    </Card>
  );
}
```

## 3. Цветовая кодировка фаз

| Фаза | Цвет | Иконка |
|---|---|---|
| Подсушка | `#F59E0B` (жёлтый) | `Wind` |
| Копчение | `#6B7280` (дымный) | `Cloud` |
| Варка | `#EF4444` (красный) | `Flame` |
| Охлаждение | `#3B82F6` (синий) | `Snowflake` |
| Запекание | `#F97316` (оранжевый) | `FlameKindling` |
| Подвяливание | `#10B981` (зелёный) | `Timer` |

## 4. Анимации

```tsx
// Framer Motion для переходов между фазами
const phaseVariants = {
  hidden: { opacity: 0, x: -20 },
  visible: (i: number) => ({
    opacity: 1,
    x: 0,
    transition: { delay: i * 0.1, duration: 0.3 },
  }),
};
```

## 5. Чек-лист

- [ ] Timeline показывает все фазы с пропорциональной шириной
- [ ] График температуры — step-линия (не плавная)
- [ ] Цвета фаз соответствуют типу операции
- [ ] Прогресс обновляется в реальном времени (для active batch)
- [ ] Hover/клик на фазу показывает детали
- [ ] Анимации ≤ 300ms
- [ ] Адаптивно на мобильных (вертикальный timeline)

## 6. Связь с другими скиллами

- `design-system` — цвета, карточки, типографика
- `frontend-api-client` — данные программы из API
- `telemetry-websocket` — live-обновление прогресса
- `add-recipe` — структура ProgramPhase
- `batches-lifecycle` — active batch + текущая фаза

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при создании UI программ копчения.
