# SKILL: quality-control

> Контроль качества копчёной продукции: органолептика, лабораторные показатели, дефекты, соответствие ГОСТ. Используй при создании UI КК и отчётности.

## 1. Параметры контроля качества

### 1.1. Органолептика (визуальная оценка)
| Параметр | Хорошо | Плохо |
|---|---|---|
| Цвет | Золотисто-коричневый, равномерный | Блёклый, пятна, подтёки |
| Консистенция | Упругая, восстанавливается | Рыхлая, водянистая, сухая |
| Запах | Приятный копчёный | Горький, затхлый, кислый |
| Вкус | Яркий, сбалансированный | Пересол, недосол, горечь |
| Общий вид | Чистый, без слизи | Слизь, плесень, подтёки бульона |

### 1.2. Лабораторные показатели
| Показатель | Норма (рыба г/к) | Норма (колбасы в/к) | Норма (х/к) |
|---|---|---|---|
| Соль, % | 2–4 | 2,5–4 | 3–5 |
| Жир, % | по сорту | по сорту | по сорту |
| Влага, % | ≤ 70 | ≤ 70 | ≤ 55 |
| aw (активность воды) | ≤ 0,96 | ≤ 0,96 | ≤ 0,92 |
| Бензпирен, мг/кг | ≤ 0,001 | ≤ 0,001 | ≤ 0,001 |
| КМАФАнМ, КОЕ/г | ≤ 1×10⁵ | ≤ 1×10⁵ | ≤ 1×10⁴ |
| БГКП | Не допускаются в 1 г | Не допускаются в 1 г | Не допускаются в 0,1 г |

### 1.3. Дефекты и причины
| Дефект | Причина | Исправление |
|---|---|---|
| Горький вкус | Много дыма, высокая t, хвойная щепа | Уменьшить дым, снизить t, ольха |
| Кислый запах | Недостаточная свежесть сырья | Строгий входной контроль |
| Затхлый запах | Плохая сушка, плесень | Улучшить сушку, проветривание |
| Солёный | Нарушен посол (пересол) | Соблюдать % соли, время |
| Несолёный | Нарушен посол (недосол) | Проверить плотность тузлука |
| Сухой/жёсткий | Пересушили, перегрев | Снизить t сушки, время |
| Блёклый цвет | Мало нитрита, мало дыма | Проверить нитрит, интенсивность дыма |
| Горький налёт | Коптильная жидкость вместо дыма | Не использовать жидкий дым как замену |

## 2. Модель данных (предлагаемая)

```typescript
interface QualityControlRecord {
  id: number;
  batch_id: number;
  checked_at: string;          // ISO datetime
  checked_by: string;          // имя технолога
  
  // Органолептика (1-5 баллов или pass/fail)
  color_score: number;         // 1-5
  consistency_score: number;   // 1-5
  smell_score: number;         // 1-5
  taste_score: number;         // 1-5
  overall_score: number;       // среднее
  
  // Лаборатория (числовые значения)
  salt_percent?: number;
  fat_percent?: number;
  moisture_percent?: number;
  aw?: number;
  benzopyrene_mg_kg?: number;
  
  // Фото
  photos: string[];            // URLs в MinIO
  
  // Дефекты
  defects: QualityDefect[];
  
  // Решение
  decision: 'accept' | 'reject' | 'rework';
  notes: string;
}

interface QualityDefect {
  type: string;                // ключ из таблицы дефектов
  severity: 'minor' | 'major' | 'critical';
  description: string;
}
```

## 3. UI компоненты

### 3.1. Карточка оценки органолептики
```tsx
// components/quality/organoleptic-card.tsx
export function OrganolepticCard({ record }: { record: QualityControlRecord }) {
  const items = [
    { label: 'Цвет', score: record.color_score },
    { label: 'Консистенция', score: record.consistency_score },
    { label: 'Запах', score: record.smell_score },
    { label: 'Вкус', score: record.taste_score },
  ];
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Органолептика</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.map((item) => (
          <div key={item.label} className="flex items-center justify-between">
            <span>{item.label}</span>
            <StarRating score={item.score} />
          </div>
        ))}
        <div className="border-t pt-2">
          <div className="flex justify-between font-bold">
            <span>Итого</span>
            <span className={record.overall_score >= 4 ? 'text-success' : 'text-warning'}>
              {record.overall_score.toFixed(1)} / 5
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
```

### 3.2. Индикатор лабораторных показателей
```tsx
// components/quality/lab-indicators.tsx
export function LabIndicator({ label, value, min, max, unit }: {
  label: string; value: number; min: number; max: number; unit: string;
}) {
  const isOk = value >= min && value <= max;
  const percent = ((value - min) / (max - min)) * 100;
  
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-sm">
        <span>{label}</span>
        <span className={isOk ? 'text-success' : 'text-error'}>
          {value} {unit} ({isOk ? 'OK' : 'FAIL'})
        </span>
      </div>
      <div className="h-2 rounded-full bg-surface-3">
        <div
          className={cn("h-full rounded-full", isOk ? "bg-success" : "bg-error")}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}
```

## 4. Чек-лист контроля качества

- [ ] Проверена органолептика (цвет, консистенция, запах, вкус)
- [ ] Сделаны фото (общий вид, срез, упаковка)
- [ ] Замерены лабораторные показатели (соль, влага, aw)
- [ ] Проверено соответствие ГОСТ/ТУ
- [ ] Выставлено решение: accept / reject / rework
- [ ] Результаты привязаны к batch_id
- [ ] Алерты при критических отклонениях

## 5. Связь с другими скиллами

- `batches-lifecycle` — привязка к партии
- `batch-monitoring` — KPI на дашборде
- `pdf-report` — печать акта КК
- `smoke-platform` — общие правила

---

**Версия:** 0.1.0 (2026-06-03)
**Загружай:** при создании UI контроля качества.
