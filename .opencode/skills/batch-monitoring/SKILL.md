# SKILL: batch-monitoring

> Мониторинг партий в реальном времени: KPI, отклонения от программы, алерты, дашборды. Используй при создании dashboard и страницы деталей партии.

## 1. KPI для партии

| KPI | Формула | Целевое значение |
|---|---|---|
| Прогресс | (фактическое время / плановое время) × 100% | ~100% |
| Отклонение t камеры | \|факт - план\| / план × 100% | < 5% |
| Отклонение t продукта | \|факт - план\| / план × 100% | < 10% |
| Выход | готовый вес / сырой вес × 100% | по рецепту ± 3% |
| Потери | (1 - выход/100) × 100% | по рецепту ± 2% |
| OEE | (полезное время / запланированное время) × 100% | > 85% |

## 2. Алерты (правила)

| Условие | Уровень | Действие |
|---|---|---|
| t камеры отклонилась > ±5°C от программы | WARNING | Уведомление оператору |
| t камеры отклонилась > ±10°C от программы | CRITICAL | Аварийная остановка |
| t продукта > target + 5°C | WARNING | Сократить время фазы |
| Дверь открыта > 30 сек | WARNING | Уведомление |
| Дверь открыта > 2 мин | CRITICAL | Пауза программы |
| Дымогенератор не работает в фазе копчения | CRITICAL | Остановка + алерт |
| Влажность отклонилась > ±10% от программы | WARNING | Корректировка |
| Время фазы превысило план на 20% | WARNING | Авто-переход или алерт |
| Ошибки Modbus (3+ подряд) | CRITICAL | Переключение на cloud |

## 3. UI компоненты

### 3.1. Дашборд активных партий
```tsx
// components/batch/dashboard.tsx
export function ActiveBatchesDashboard() {
  const { data: batches } = useActiveBatches();
  
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
      {batches?.map((batch) => (
        <BatchCard key={batch.id} batch={batch} />
      ))}
    </div>
  );
}

function BatchCard({ batch }: { batch: Batch }) {
  const deviation = calculateDeviation(batch);
  
  return (
    <Card className={cn(deviation > 10 && "border-warning")}>
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-sm">{batch.batch_number}</CardTitle>
          <p className="text-xs text-muted-foreground">{batch.recipe_version.recipe.name}</p>
        </div>
        <StatusBadge status={batch.status} />
      </CardHeader>
      <CardContent className="space-y-2">
        <Progress value={batch.progress_percent} className="h-2" />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Фаза {batch.current_phase + 1}/{batch.total_phases}</span>
          <span>{batch.phase_name}</span>
        </div>
        <div className="grid grid-cols-2 gap-2 pt-2">
          <MiniMetric label="Камера" value={`${batch.t_chamber}°C`} />
          <MiniMetric label="Продукт" value={`${batch.t_product}°C`} />
        </div>
        {deviation > 5 && (
          <Alert variant="warning" className="text-xs">
            <AlertTriangle className="h-4 w-4" />
            Отклонение от программы: {deviation.toFixed(1)}%
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
```

### 3.2. График отклонений
```tsx
// components/batch/deviation-chart.tsx
export function DeviationChart({ telemetry }: { telemetry: BatchTelemetry[] }) {
  const data = telemetry.map((t) => ({
    ts: t.ts,
    t_chamber_deviation: Math.abs(t.t_chamber - t.set_t_chamber),
    t_product_deviation: Math.abs(t.t_product - t.set_t_product),
  }));

  return (
    <ResponsiveContainer width="100%" height={200}>
      <AreaChart data={data}>
        <defs>
          <linearGradient id="deviation" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <XAxis dataKey="ts" tickFormatter={(v) => new Date(v).toLocaleTimeString()} />
        <YAxis />
        <Tooltip />
        <Area type="monotone" dataKey="t_chamber_deviation" stroke="#EF4444" fill="url(#deviation)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
```

## 4. Метрики для дашборда (сверху)

```tsx
// components/metrics/top-metrics.tsx
const metrics = [
  { label: 'Активные партии', value: 3, icon: Activity },
  { label: 'Завершено сегодня', value: 12, icon: CheckCircle },
  { label: 'Средний выход', value: '78%', icon: TrendingUp },
  { label: 'Алерты', value: 2, icon: AlertTriangle, alert: true },
];
```

## 5. Чек-лист

- [ ] Дашборд показывает все активные партии
- [ ] Прогресс обновляется в реальном времени (WebSocket)
- [ ] Отклонения > 5% подсвечиваются
- [ ] Алерты отправляются (UI notification + опц. email/TG)
- [ ] История алертов сохраняется
- [ ] Графики масштабируются по времени (1ч / 4ч / 8ч / 24ч)
- [ ] Мобильная версия: список карточек вместо сетки

## 6. Связь с другими скиллами

- `telemetry-websocket` — live-данные
- `program-visualizer` — графики программы
- `quality-control` — привязка КК к партии
- `pdf-report` — экспорт данных партии
- `smoke-platform` — общие правила

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при создании дашборда мониторинга.
