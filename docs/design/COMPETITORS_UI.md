# UI/UX Концепция: Экран "Анализ конкурентов" в FELETI-SMOK

> **Дата:** 2026-06-03  
> **Статус:** Концепция (дизайн-документ для frontend-реализации)  
> **Цель:** Современный, профессиональный, неперегруженный интерфейс для анализа конкурентов прямо в программе.

---

## 1. Философия дизайна

### Принципы (вдохновление: Linear, Apple, Figma, Notion)

| Принцип | Описание | Пример |
|---------|----------|--------|
| **Progressive Disclosure** | Показывать сначала самое важное, детали — по требованию | Карточка → раскрытие → полный анализ |
| **Information Density** | Много данных, но организовано | Сетка + фильтры + поиск |
| **Visual Hierarchy** | Размер, цвет, отступы ведут глаз | Заголовок → метрики → детали |
| **Contextual Actions** | Действия появляются в контексте | Hover → быстрые действия |
| **Minimal Chrome** | Минимум рамок, максимум контента | Карточки без теней, тонкие разделители |
| **Motion with Purpose** | Анимация только для ориентации | Раскрытие аккордеона, переключение табов |

---

## 2. Общая структура экрана

```
┌─────────────────────────────────────────────────────────────────────────┐
│  FELETI-SMOK                    [🔍 Поиск конкурентов...]    [👤 Admin] │
├─────────────────────────────────────────────────────────────────────────┤
│  📊 Анализ рынка                                                        │
│                                                                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │ 🏆 Лидеры  │ │ 🔥 Горячее │ │ 📈 Тренды  │ │ ⚠️ Риски   │           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  [Все] [Horeca] [Profi] [Industrial] [Дымогенераторы] [🔍]      │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────┐  ┌─────────────────────────────────────┐ │
│  │  🥇 Ижица / Varmen      │  │  📋 Быстрый обзор                   │ │
│  │  Россия · 1992 · 4000+  │  │  Загрузка: 20–1200 кг               │ │
│  │  клиентов               │  │  Цена: 350K–5M ₽                    │ │
│  │                         │  │  HMI: Сенсорная панель              │ │
│  │  [▸ Раскрыть]           │  │  Облако: ❌ Нет                     │ │
│  │                         │  │  Мобильное: ❌ Нет                  │ │
│  └─────────────────────────┘  │  Удаленный мониторинг: ❌           │ │
│                               └─────────────────────────────────────┘ │
│  ┌─────────────────────────┐                                          │
│  │  🥈 Mauting             │                                          │
│  │  Чехия · Премиум ·      │                                          │
│  │  Туннели 1–8 вагонеток  │                                          │
│  │                         │                                          │
│  │  [▸ Раскрыть]           │                                          │
│  └─────────────────────────┘                                          │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │  📊 Сравнительная матрица                                          │ │
│  │  [Таблица: модель | загрузка | цена | HMI | облако | мобильное]   │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Компоненты интерфейса (shadcn/ui + custom)

### 3.1. Карточка конкурента (CompetitorCard)

```tsx
// Компонент: app/components/competitors/CompetitorCard.tsx
// Использует: Card, Badge, Button, Collapsible

<Card className="group hover:border-primary/50 transition-colors">
  <CardHeader className="pb-3">
    <div className="flex items-start justify-between">
      <div className="flex items-center gap-3">
        <Avatar className="h-10 w-10 rounded-lg">
          <AvatarImage src="/competitors/ijiza-logo.png" />
          <AvatarFallback>ИЖ</AvatarFallback>
        </Avatar>
        <div>
          <CardTitle className="text-base">Ижица / Varmen</CardTitle>
          <CardDescription className="text-xs">
            Россия · Основана 1992 · 4000+ клиентов
          </CardDescription>
        </div>
      </div>
      <Badge variant="destructive">Главный конкурент</Badge>
    </div>
  </CardHeader>
  
  <CardContent className="pb-3">
    {/* Быстрые метрики — 4 колонки */}
    <div className="grid grid-cols-4 gap-2 text-center">
      <Metric label="Загрузка" value="20–1200 кг" />
      <Metric label="Цена от" value="350K ₽" />
      <Metric label="HMI" value="Сенсорная" />
      <Metric label="Рецептов" value="200+" />
    </div>
  </CardContent>
  
  <CardFooter className="pt-0">
    <Collapsible>
      <CollapsibleTrigger asChild>
        <Button variant="ghost" size="sm" className="w-full">
          <ChevronDown className="h-4 w-4 mr-2" />
          Подробный анализ
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        {/* Раскрывающийся контент */}
        <CompetitorDetails competitor="ijiza" />
      </CollapsibleContent>
    </Collapsible>
  </CardFooter>
</Card>
```

### 3.2. Раскрывающиеся детали (CompetitorDetails)

Структура внутри Collapsible:

```
┌─────────────────────────────────────────┐
│  📑 Вкладки: Обзор | Модели | Рецепты | │
│              Проблемы | Сравнение       │
├─────────────────────────────────────────┤
│                                         │
│  [Контент выбранной вкладки]            │
│                                         │
└─────────────────────────────────────────┘
```

**Вкладки (Tabs) с анимацией:**

```tsx
<Tabs defaultValue="overview" className="w-full">
  <TabsList className="grid w-full grid-cols-5">
    <TabsTrigger value="overview">Обзор</TabsTrigger>
    <TabsTrigger value="models">Модели</TabsTrigger>
    <TabsTrigger value="recipes">Рецепты</TabsTrigger>
    <TabsTrigger value="problems">Проблемы</TabsTrigger>
    <TabsTrigger value="compare">Сравнение</TabsTrigger>
  </TabsList>
  
  <TabsContent value="overview" className="mt-4 space-y-4">
    <CompetitorOverview />
  </TabsContent>
  
  <TabsContent value="models" className="mt-4">
    <CompetitorModels />
  </TabsContent>
  
  {/* ... */}
</Tabs>
```

### 3.3. Вкладка "Обзор" (CompetitorOverview)

```
┌─────────────────────────────────────────┐
│  📊 Ключевые метрики                    │
│  ┌────────┐┌────────┐┌────────┐┌──────┐│
│  │💰 Цены ││🏭 Завод││👥 Клиенты││⭐ Рейт││
│  │350K–5M ││ СПб   ││ 4000+  ││ 4.2/5││
│  └────────┘└────────┘└────────┘└──────┘│
│                                         │
│  📋 Описание                            │
│  [2-3 предложения о компании]           │
│                                         │
│  ✅ Сильные стороны          ❌ Слабые  │
│  · 25+ лет на рынке          · Нет     │
│  · 200+ рецептов              облака   │
│  · Собственное произ-        · Нет     │
│    водство                    мобилки  │
│  · Широкая линейка           · Плохие │
│                               инструкц.│
│                                         │
│  🏷️ Теги: horeca profi industrial      │
│     электростатика фрикционный          │
└─────────────────────────────────────────┘
```

### 3.4. Вкладка "Модели" (CompetitorModels)

Таблица с раскрывающимися строками (Accordion внутри Table):

```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Модель</TableHead>
      <TableHead>Загрузка</TableHead>
      <TableHead>Мощность</TableHead>
      <TableHead>Цена</TableHead>
      <TableHead className="w-[50px]"></TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {models.map(model => (
      <Accordion type="single" collapsible key={model.id}>
        <AccordionItem value={model.id} className="border-0">
          <AccordionTrigger className="hover:no-underline py-0">
            <TableRow className="border-0">
              <TableCell className="font-medium">{model.name}</TableCell>
              <TableCell>{model.load}</TableCell>
              <TableCell>{model.power}</TableCell>
              <TableCell>{model.price}</TableCell>
            </TableRow>
          </AccordionTrigger>
          <AccordionContent>
            <div className="pl-4 py-3 bg-muted/50 rounded-lg">
              {/* Детали модели */}
              <ModelDetails model={model} />
            </div>
          </AccordionContent>
        </AccordionItem>
      </Accordion>
    ))}
  </TableBody>
</Table>
```

### 3.5. Вкладка "Проблемы" (CompetitorProblems)

Визуальная шкала серьезности + аккордеон:

```tsx
<div className="space-y-3">
  {problems.map(problem => (
    <Card key={problem.id} className="border-l-4"
      style={{
        borderLeftColor: 
          problem.severity === 'high' ? '#ef4444' :
          problem.severity === 'medium' ? '#f59e0b' : '#22c55e'
      }}
    >
      <CardHeader className="py-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            {problem.title}
          </CardTitle>
          <Badge variant={problem.severity}>
            {problem.frequency}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="pt-0 pb-3">
        <p className="text-sm text-muted-foreground">
          {problem.description}
        </p>
        <div className="mt-2 flex items-center gap-2 text-xs text-muted-foreground">
          <MessageSquare className="h-3 w-3" />
          Источник: {problem.source}
        </div>
      </CardContent>
    </Card>
  ))}
</div>
```

### 3.6. Вкладка "Сравнение" (CompetitorCompare)

Интерактивная сравнительная таблица:

```tsx
<ComparisonTable 
  competitors={['feleti-smok', 'ijiza', 'mauting', 'fessmann']}
  features={[
    'max_load', 'price', 'hmi_type', 'cloud', 'mobile_app',
    'remote_monitoring', 'recipe_count', 'warranty', 'video_camera'
  ]}
/>
```

Визуально:
```
┌─────────────────┬─────────────┬─────────┬─────────┬──────────┐
│ Параметр        │ FELETI-SMOK │  Ижица  │ Mauting │ Fessmann │
├─────────────────┼─────────────┼─────────┼─────────┼──────────┤
│ Загрузка        │ 50–500 кг   │20–1200кг│500+ кг  │ 100–2000+│
│ Цена (от)       │ 450K ₽      │ 350K ₽  │ 5M ₽    │ 8M ₽     │
│ HMI             │ ✅ Цветной  │ Сенсорн.│ Сенсорн.│ Сенсорн. │
│ Web-интерфейс   │ ✅ Есть     │ ❌ Нет  │ ❌ Нет  │ ✅ FES   │
│ Облако          │ ✅ Есть     │ ❌ Нет  │ ❌ Нет  │ ✅ Есть  │
│ Мобильное       │ ✅ Есть     │ ❌ Нет  │ ❌ Нет  │ ✅ Есть  │
│ Видеокамера     │ ✅ Есть     │ ❌ Нет  │ ❌ Нет  │ ❌ Нет   │
│ Telegram бот    │ ✅ Есть     │ ❌ Нет  │ ❌ Нет  │ ❌ Нет   │
│ ERP интеграция  │ ✅ API      │ ❌ Нет  │ ❌ Нет  │ ✅ OPC   │
│ Рецептов        │ 200+        │ 200+    │ 1000+   │ 1000+    │
│ Гарантия        │ 2 года      │ 1 год   │ 2–3 года│ 2–3 года │
│ Производство РФ │ ✅ Да       │ ✅ Да   │ ❌ Нет  │ ❌ Нет   │
└─────────────────┴─────────────┴─────────┴─────────┴──────────┘
```

**Цветовая индикация:**
- ✅ Зеленый — FELETI-SMOK лучше
- ⚠️ Желтый — паритет
- ❌ Красный — конкурент лучше

---

## 4. Мировой опыт (reference)

### 4.1. Linear — таблицы и фильтры
- Чистые таблицы без границ
- Hover-эффекты вместо выделения
- Inline-фильтры
- Быстрые действия на hover

### 4.2. Apple — карточки продуктов
- Большие карточки с фото
- Акцент на 1-2 ключевых параметрах
- "Узнать больше" → раскрытие
- Минимум текста, максимум визуала

### 4.3. Figma — сравнение планов
- Таблица с переключением тарифов
- Чекбоксы/крестики для функций
- Липкий заголовок
- Акцент на "Рекомендуемом"

### 4.4. Notion — базы данных
- Гибкие виды: таблица, галерея, список
- Фильтры и сортировка
- Свойства (теги, даты, числа)
- Раскрывающиеся страницы

### 4.5. Tesla — конфигуратор
- Пошаговый выбор
- Визуальная обратная связь
- Минимум текстовых описаний
- Сравнение конфигураций

---

## 5. Адаптивность

### Десктоп (> 1280px)
- Сетка 3 колонки карточек
- Полная таблица сравнения
- Боковая панель деталей

### Планшет (768–1280px)
- Сетка 2 колонки
- Таблица с горизонтальным скроллом
- Аккордеон вместо боковой панели

### Мобиль (< 768px)
- Список карточек (1 колонка)
- Фильтры в Drawer/Sheet
- Табы в вертикальном списке
- Полноэкранный просмотр деталей

---

## 6. Анимации и микровзаимодействия

| Элемент | Анимация | Библиотека |
|---------|----------|------------|
| Раскрытие аккордеона | height 0 → auto, 200ms ease | Framer Motion / CSS |
| Переключение табов | fade + slideX, 150ms | Framer Motion |
| Hover карточки | border-color + translateY(-2px), 150ms | CSS transition |
| Появление контента | stagger children, 50ms delay | Framer Motion |
| Загрузка данных | skeleton pulse | shadcn/ui Skeleton |
| Фильтрация | layout animation | Framer Motion layout |

---

## 7. Цветовая схема (FELETI бренд)

```css
:root {
  /* Основные */
  --feleti-primary: #1a1a1a;      /* Графит — основной */
  --feleti-accent: #c9a96e;       /* Золотой/дым — акцент */
  --feleti-success: #22c55e;      /* Зеленый — наше преимущество */
  --feleti-warning: #f59e0b;      /* Желтый — паритет */
  --feleti-danger: #ef4444;       /* Красный — слабость */
  
  /* Фоны */
  --feleti-bg: #fafafa;           /* Светлый фон */
  --feleti-card: #ffffff;         /* Карточка */
  --feleti-muted: #f4f4f5;        /* Muted фон */
  
  /* Текст */
  --feleti-text: #18181b;         /* Основной */
  --feleti-text-muted: #71717a;   /* Вторичный */
}
```

---

## 8. Поиск и фильтрация

```tsx
<div className="flex items-center gap-3 mb-6">
  <div className="relative flex-1">
    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
    <Input 
      placeholder="Поиск по названию, модели, технологии..."
      className="pl-9"
    />
  </div>
  
  <Select defaultValue="all">
    <SelectTrigger className="w-[160px]">
      <SelectValue placeholder="Сегмент" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="all">Все сегменты</SelectItem>
      <SelectItem value="horeca">Horeca</SelectItem>
      <SelectItem value="profi">Profi</SelectItem>
      <SelectItem value="industrial">Industrial</SelectItem>
    </SelectContent>
  </Select>
  
  <Select defaultValue="all">
    <SelectTrigger className="w-[160px]">
      <SelectValue placeholder="Страна" />
    </SelectTrigger>
    <SelectContent>
      <SelectItem value="all">Все страны</SelectItem>
      <SelectItem value="russia">Россия</SelectItem>
      <SelectItem value="germany">Германия</SelectItem>
      <SelectItem value="czech">Чехия</SelectItem>
    </SelectContent>
  </Select>
</div>
```

---

## 9. Интеграция с backend

### API Endpoints (предлагаемые)

```
GET /api/v1/competitors                    # Список конкурентов
GET /api/v1/competitors/{id}               # Детали конкурента
GET /api/v1/competitors/{id}/models        # Модели
GET /api/v1/competitors/{id}/recipes       # Рецепты
GET /api/v1/competitors/{id}/problems      # Проблемы
GET /api/v1/competitors/compare            # Сравнительная матрица
```

### Модели БД (добавить)

```python
class Competitor(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    slug: Mapped[str] = mapped_column(unique=True)
    country: Mapped[str]
    founded_year: Mapped[int | None]
    segment: Mapped[str]  # horeca / profi / industrial
    website: Mapped[str | None]
    logo_url: Mapped[str | None]
    is_main_competitor: Mapped[bool] = mapped_column(default=False)
    
    # Метрики
    client_count: Mapped[int | None]
    recipe_count: Mapped[int | None]
    warranty_years: Mapped[int | None]
    
    # Флаги
    has_cloud: Mapped[bool] = mapped_column(default=False)
    has_mobile_app: Mapped[bool] = mapped_column(default=False)
    has_remote_monitoring: Mapped[bool] = mapped_column(default=False)
    has_erp_integration: Mapped[bool] = mapped_column(default=False)
    has_video_camera: Mapped[bool] = mapped_column(default=False)
    
    # Связи
    models: Mapped[list["CompetitorModel"]] = relationship(back_populates="competitor")
    problems: Mapped[list["CompetitorProblem"]] = relationship(back_populates="competitor")

class CompetitorModel(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"))
    name: Mapped[str]
    slug: Mapped[str]
    max_load_kg: Mapped[float | None]
    volume_m3: Mapped[float | None]
    power_kw: Mapped[float | None]
    voltage_v: Mapped[int | None]
    price_rrp_rub: Mapped[int | None]
    
    competitor: Mapped["Competitor"] = relationship(back_populates="models")

class CompetitorProblem(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"))
    title: Mapped[str]
    description: Mapped[str]
    severity: Mapped[str]  # low / medium / high
    frequency: Mapped[str]  # rare / sometimes / often / always
    source: Mapped[str]  # forum / review / expert / own_research
    source_url: Mapped[str | None]
    
    competitor: Mapped["Competitor"] = relationship(back_populates="problems")
```

---

## 10. Roadmap реализации

| Этап | Что делать | Статус |
|------|-----------|--------|
| **1** | Добавить модели Competitor + CompetitorModel + CompetitorProblem в БД | ⏳ |
| **2** | Создать API endpoints для конкурентов | ⏳ |
| **3** | Сидировать данные Ижицы из DEEP_DIVE.md | ⏳ |
| **4** | Реализовать CompetitorCard + CompetitorDetails (React) | ⏳ |
| **5** | Реализовать ComparisonTable | ⏳ |
| **6** | Реализовать фильтры и поиск | ⏳ |
| **7** | Добавить Mauting, Fessmann, Kerres (данные + UI) | ⏳ |
| **8** | Адаптивность (mobile/tablet) | ⏳ |
| **9** | Анимации (Framer Motion) | ⏳ |

---

**Связанные документы:**
- `docs/COMPETITORS.md` — данные о конкурентах
- `docs/research/ijiza/DEEP_DIVE.md` — глубокий анализ Ижицы
- `docs/research/ijiza/HMI_ANALYSIS.md` — HMI Ижицы
- `.opencode/skills/frontend-init/SKILL.md` — инициализация frontend
- `.opencode/skills/program-visualizer/SKILL.md` — визуализация программ
