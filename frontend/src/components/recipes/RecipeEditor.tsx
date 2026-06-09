"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Trash2,
  Clock,
  Thermometer,
  Droplets,
  Zap,
  Save,
  Copy,
  ArrowUp,
  ArrowDown,
  Search,
  X,
  Flame,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface Product {
  id: number;
  name: string;
  slug: string;
  category: string;
}

interface Ingredient {
  id: number;
  name: string;
  slug: string;
  type: string;
}

interface Phase {
  name: string;
  t_chamber: number;
  duration_min: number;
  humidity: number;
  smoke: string;
  wood_species: string;
  t_product: number;
}

interface BrineData {
  method: string;
  salt_percent: number;
  sugar_percent: number;
  nitrite_ppm: number;
  duration_hours: number;
  temp_c: number;
  water_percent: number;
}

interface IngredientEntry {
  ingredient_id: number;
  name: string;
  mass_kg: number;
}

export interface FormData {
  name: string;
  slug: string;
  product_id: number;
  description: string;
  tags: string[];
  phases: Phase[];
  brine: BrineData | null;
  ingredients: IngredientEntry[];
  yield_percent: number;
  losses_percent: number;
  notes: string;
  gost: string;
  source: string;
}

function toSlug(s: string): string {
  const translit: Record<string, string> = {
    а: "a", б: "b", в: "v", г: "g", д: "d", е: "e", ё: "e",
    ж: "zh", з: "z", и: "i", й: "y", к: "k", л: "l", м: "m",
    н: "n", о: "o", п: "p", р: "r", с: "s", т: "t", у: "u",
    ф: "f", х: "kh", ц: "ts", ч: "ch", ш: "sh", щ: "shch",
    ъ: "", ы: "y", ь: "", э: "e", ю: "yu", я: "ya",
  };
  return s
    .toLowerCase()
    .trim()
    .split("")
    .map((c) => translit[c] || (/[a-z0-9-]/.test(c) ? c : "-"))
    .join("")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 300) || "recipe";
}

const SMOKE_OPTIONS = [
  { value: "без дыма", label: "Без дыма" },
  { value: "дым", label: "Дым" },
  { value: "электро", label: "Электро" },
];

const BRINE_METHODS = [
  { value: "сухой", label: "Сухой" },
  { value: "мокрый", label: "Мокрый" },
  { value: "шприцевание", label: "Шприцевание" },
  { value: "комбинированный", label: "Комбинированный" },
  { value: "смешанный", label: "Смешанный" },
];

const DEFAULT_PHASES: Phase[] = [
  { name: "Подсушка", t_chamber: 50, duration_min: 30, humidity: 0, smoke: "без дыма", wood_species: "", t_product: 0 },
  { name: "Копчение", t_chamber: 75, duration_min: 60, humidity: 0, smoke: "дым", wood_species: "ольха", t_product: 0 },
  { name: "Варка", t_chamber: 82, duration_min: 45, humidity: 80, smoke: "без дыма", wood_species: "", t_product: 72 },
];

export function RecipeEditor({
  initialData,
  onSave,
  saving,
  mode,
}: {
  initialData?: FormData;
  onSave: (data: FormData) => void;
  saving: boolean;
  mode: "create" | "edit";
}) {
  const [form, setForm] = useState<FormData>(
    initialData || {
      name: "",
      slug: "",
      product_id: 0,
      description: "",
      tags: [],
      phases: [...DEFAULT_PHASES],
      brine: null,
      ingredients: [],
      yield_percent: 0,
      losses_percent: 0,
      notes: "",
      gost: "",
      source: "",
    }
  );
  const [tagInput, setTagInput] = useState("");
  const [ingSearch, setIngSearch] = useState("");
  const [autoSlug, setAutoSlug] = useState(true);

  const { data: productsData } = useQuery({
    queryKey: ["products-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/products?size=200");
      return data as { items: Product[]; total: number };
    },
  });

  const { data: ingredientsData } = useQuery({
    queryKey: ["ingredients-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/ingredients?size=200");
      return data as { items: Ingredient[]; total: number };
    },
  });

  const products = productsData?.items || [];
  const ingredients = ingredientsData?.items || [];

  const updateForm = <K extends keyof FormData>(key: K, value: FormData[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleNameChange = (name: string) => {
    setForm((prev) => ({
      ...prev,
      name,
      slug: autoSlug ? toSlug(name) : prev.slug,
    }));
  };

  const addTag = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && tagInput.trim()) {
      e.preventDefault();
      if (!form.tags.includes(tagInput.trim())) {
        updateForm("tags", [...form.tags, tagInput.trim()]);
      }
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    updateForm("tags", form.tags.filter((t) => t !== tag));
  };

  const addPhase = () => {
    updateForm("phases", [
      ...form.phases,
      { name: "Подсушка", t_chamber: 60, duration_min: 30, humidity: 0, smoke: "без дыма", wood_species: "", t_product: 0 },
    ]);
  };

  const updatePhase = (index: number, field: keyof Phase, value: string | number) => {
    const phases = [...form.phases];
    phases[index] = { ...phases[index], [field]: value };
    updateForm("phases", phases);
  };

  const removePhase = (index: number) => {
    updateForm("phases", form.phases.filter((_, i) => i !== index));
  };

  const movePhase = (index: number, dir: -1 | 1) => {
    const newIndex = index + dir;
    if (newIndex < 0 || newIndex >= form.phases.length) return;
    const phases = [...form.phases];
    [phases[index], phases[newIndex]] = [phases[newIndex], phases[index]];
    updateForm("phases", phases);
  };

  const duplicatePhase = (index: number) => {
    const phases = [...form.phases];
    phases.splice(index + 1, 0, { ...phases[index] });
    updateForm("phases", phases);
  };

  const addIngredient = (ing: Ingredient) => {
    if (form.ingredients.some((i) => i.ingredient_id === ing.id)) return;
    updateForm("ingredients", [
      ...form.ingredients,
      { ingredient_id: ing.id, name: ing.name, mass_kg: 1 },
    ]);
    setIngSearch("");
  };

  const updateIngredient = (index: number, mass_kg: number) => {
    const ingredients = [...form.ingredients];
    ingredients[index] = { ...ingredients[index], mass_kg };
    updateForm("ingredients", ingredients);
  };

  const removeIngredient = (index: number) => {
    updateForm("ingredients", form.ingredients.filter((_, i) => i !== index));
  };

  const filteredIngredients = ingredients.filter(
    (i) =>
      i.name.toLowerCase().includes(ingSearch.toLowerCase()) &&
      !form.ingredients.some((fi) => fi.ingredient_id === i.id)
  );

  const totalPhasesTime = form.phases.reduce((acc, p) => acc + p.duration_min, 0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave(form);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Metadata */}
      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <h2 className="text-sm font-medium text-white mb-5">Основное</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">Название *</label>
            <input
              value={form.name}
              onChange={(e) => handleNameChange(e.target.value)}
              required
              placeholder="Докторская колбаса"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">
              Slug
              <button
                type="button"
                onClick={() => setAutoSlug(!autoSlug)}
                className={`ml-2 text-[10px] ${autoSlug ? "text-feleti-gold" : "text-muted-foreground"} underline`}
              >
                {autoSlug ? "авто" : "вручную"}
              </button>
            </label>
            <input
              value={form.slug}
              onChange={(e) => {
                setAutoSlug(false);
                updateForm("slug", e.target.value);
              }}
              required
              pattern="^[a-z0-9-]+$"
              placeholder="doktorskaya"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30 font-mono"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">Продукт *</label>
            <select
              value={form.product_id}
              onChange={(e) => updateForm("product_id", Number(e.target.value))}
              required
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
            >
              <option value={0} disabled>Выберите продукт</option>
              {products.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1.5">ГОСТ</label>
            <input
              value={form.gost}
              onChange={(e) => updateForm("gost", e.target.value)}
              placeholder="ГОСТ Р 52196-2011"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs text-muted-foreground mb-1.5">Описание</label>
            <textarea
              value={form.description}
              onChange={(e) => updateForm("description", e.target.value)}
              rows={3}
              placeholder="Описание рецепта..."
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30 resize-none"
            />
          </div>
          <div className="sm:col-span-2">
            <label className="block text-xs text-muted-foreground mb-1.5">Теги</label>
            <div className="flex flex-wrap gap-1.5 mb-2">
              {form.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center gap-1 rounded-lg bg-feleti-gold/10 px-2.5 py-1 text-xs text-feleti-gold"
                >
                  {tag}
                  <button type="button" onClick={() => removeTag(tag)} className="hover:text-white">
                    <X className="h-3 w-3" />
                  </button>
                </span>
              ))}
            </div>
            <input
              value={tagInput}
              onChange={(e) => setTagInput(e.target.value)}
              onKeyDown={addTag}
              placeholder="Введите тег и нажмите Enter"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30"
            />
          </div>
        </div>
      </section>

      {/* Phases */}
      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-medium text-white">Программа копчения</h2>
          <span className="text-xs text-muted-foreground">
            {totalPhasesTime} мин · {form.phases.length} фаз
          </span>
        </div>

        {/* Timeline */}
        {form.phases.length > 0 && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-3 mb-4">
            <div className="flex h-6 rounded-lg overflow-hidden">
              {form.phases.map((phase, i) => {
                const w = totalPhasesTime > 0 ? (phase.duration_min / totalPhasesTime) * 100 : 0;
                return (
                  <div
                    key={i}
                    className="flex items-center justify-center text-[9px] font-medium text-white/60 first:rounded-l-lg last:rounded-r-lg"
                    style={{ width: `${w}%`, backgroundColor: `hsl(${i * 40 + 20}, 60%, 30%)` }}
                  >
                    {w > 8 && `${phase.name.slice(0, 4)}`}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <div className="space-y-2">
          <AnimatePresence>
            {form.phases.map((phase, i) => (
              <motion.div
                key={`phase-${i}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20, height: 0 }}
                className="group rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-white/10 transition-colors"
              >
                <div className="flex flex-col sm:flex-row sm:items-start gap-4">
                  <div className="flex items-center gap-2 sm:w-40 shrink-0">
                    <span className="text-xs text-muted-foreground/60 w-5">#{i + 1}</span>
                    <input
                      value={phase.name}
                      onChange={(e) => updatePhase(i, "name", e.target.value)}
                      placeholder="Название фазы"
                      className="flex-1 bg-transparent text-sm text-white border-b border-white/10 pb-0.5 focus:outline-none focus:border-feleti-gold transition-colors"
                    />
                  </div>

                  <div className="flex flex-1 flex-wrap items-center gap-2">
                    <div className="flex items-center gap-1">
                      <Thermometer className="h-3.5 w-3.5 text-orange-400 shrink-0" />
                      <input
                        type="number"
                        value={phase.t_chamber}
                        onChange={(e) => updatePhase(i, "t_chamber", Number(e.target.value))}
                        className="w-14 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                      />
                      <span className="text-[10px] text-muted-foreground">°C</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Clock className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
                      <input
                        type="number"
                        value={phase.duration_min}
                        onChange={(e) => updatePhase(i, "duration_min", Number(e.target.value))}
                        className="w-14 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                      />
                      <span className="text-[10px] text-muted-foreground">мин</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Droplets className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                      <input
                        type="number"
                        value={phase.humidity}
                        onChange={(e) => updatePhase(i, "humidity", Number(e.target.value))}
                        className="w-12 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                      />
                      <span className="text-[10px] text-muted-foreground">%</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <Zap className="h-3.5 w-3.5 text-purple-400 shrink-0" />
                      <select
                        value={phase.smoke}
                        onChange={(e) => updatePhase(i, "smoke", e.target.value)}
                        className="bg-white/5 text-[10px] text-white rounded-lg border border-white/10 px-2 py-1.5 focus:outline-none focus:border-feleti-gold"
                      >
                        {SMOKE_OPTIONS.map((o) => (
                          <option key={o.value} value={o.value}>{o.label}</option>
                        ))}
                      </select>
                    </div>
                    {phase.smoke !== "без дыма" && (
                      <div className="flex items-center gap-1">
                        <Flame className="h-3.5 w-3.5 text-amber-400 shrink-0" />
                        <input
                          value={phase.wood_species}
                          onChange={(e) => updatePhase(i, "wood_species", e.target.value)}
                          placeholder="щепа"
                          className="w-16 bg-white/5 text-[10px] text-white rounded-lg border border-white/10 px-2 py-1.5 focus:outline-none focus:border-feleti-gold"
                        />
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0">
                    <button type="button" onClick={() => movePhase(i, -1)} disabled={i === 0}
                      className="p-1 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-white disabled:opacity-20">
                      <ArrowUp className="h-3.5 w-3.5" />
                    </button>
                    <button type="button" onClick={() => movePhase(i, 1)} disabled={i === form.phases.length - 1}
                      className="p-1 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-white disabled:opacity-20">
                      <ArrowDown className="h-3.5 w-3.5" />
                    </button>
                    <button type="button" onClick={() => duplicatePhase(i)}
                      className="p-1 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-feleti-gold">
                      <Copy className="h-3.5 w-3.5" />
                    </button>
                    <button type="button" onClick={() => removePhase(i)}
                      className="p-1 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-red-400">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        <button
          type="button"
          onClick={addPhase}
          className="mt-3 w-full rounded-xl border-2 border-dashed border-white/10 py-3 text-sm text-muted-foreground hover:border-feleti-gold/30 hover:text-feleti-gold transition-colors flex items-center justify-center gap-2"
        >
          <Plus className="h-4 w-4" /> Добавить фазу
        </button>
      </section>

      {/* Brine */}
      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-medium text-white">Посол</h2>
          {form.brine === null ? (
            <button
              type="button"
              onClick={() =>
                updateForm("brine", {
                  method: "мокрый", salt_percent: 2.5, sugar_percent: 0.5,
                  nitrite_ppm: 100, duration_hours: 12, temp_c: 4, water_percent: 100,
                })
              }
              className="text-xs text-feleti-gold hover:underline"
            >
              + Добавить посол
            </button>
          ) : (
            <button
              type="button"
              onClick={() => updateForm("brine", null)}
              className="text-xs text-red-400 hover:underline"
            >
              Убрать
            </button>
          )}
        </div>
        {form.brine && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Метод</label>
              <select
                value={form.brine.method}
                onChange={(e) => updateForm("brine", { ...form.brine!, method: e.target.value })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50"
              >
                {BRINE_METHODS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Соль, %</label>
              <input type="number" step="0.1" value={form.brine.salt_percent}
                onChange={(e) => updateForm("brine", { ...form.brine!, salt_percent: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Сахар, %</label>
              <input type="number" step="0.1" value={form.brine.sugar_percent}
                onChange={(e) => updateForm("brine", { ...form.brine!, sugar_percent: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Нитрит, ppm</label>
              <input type="number" value={form.brine.nitrite_ppm}
                onChange={(e) => updateForm("brine", { ...form.brine!, nitrite_ppm: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Длительность, ч</label>
              <input type="number" step="0.5" value={form.brine.duration_hours}
                onChange={(e) => updateForm("brine", { ...form.brine!, duration_hours: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">T, °C</label>
              <input type="number" step="0.5" value={form.brine.temp_c}
                onChange={(e) => updateForm("brine", { ...form.brine!, temp_c: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
            <div>
              <label className="block text-xs text-muted-foreground mb-1">Вода, %</label>
              <input type="number" value={form.brine.water_percent}
                onChange={(e) => updateForm("brine", { ...form.brine!, water_percent: Number(e.target.value) })}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
            </div>
          </div>
        )}
      </section>

      {/* Ingredients */}
      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <h2 className="text-sm font-medium text-white mb-5">Ингредиенты</h2>

        {/* Search & add */}
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            value={ingSearch}
            onChange={(e) => setIngSearch(e.target.value)}
            placeholder="Поиск ингредиентов..."
            className="w-full rounded-xl border border-white/10 bg-white/5 py-2 pl-10 pr-4 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30"
          />
          {ingSearch && (
            <div className="absolute top-full left-0 right-0 z-10 mt-1 max-h-48 overflow-y-auto rounded-xl border border-white/10 bg-[#1a1a1a] shadow-xl">
              {filteredIngredients.slice(0, 10).map((ing) => (
                <button
                  key={ing.id}
                  type="button"
                  onClick={() => addIngredient(ing)}
                  className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-white hover:bg-white/5 transition-colors text-left"
                >
                  <span className="text-xs text-muted-foreground">{ing.type}</span>
                  <span>{ing.name}</span>
                </button>
              ))}
              {filteredIngredients.length === 0 && (
                <p className="px-4 py-3 text-xs text-muted-foreground">Ничего не найдено</p>
              )}
            </div>
          )}
        </div>

        <div className="space-y-2">
          {form.ingredients.map((entry, i) => (
            <div
              key={entry.ingredient_id}
              className="flex items-center gap-3 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5"
            >
              <span className="flex-1 text-sm text-white">{entry.name}</span>
              <div className="flex items-center gap-1.5">
                <input
                  type="number"
                  step="0.1"
                  min="0"
                  value={entry.mass_kg}
                  onChange={(e) => updateIngredient(i, Number(e.target.value))}
                  className="w-20 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2.5 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                />
                <span className="text-xs text-muted-foreground w-6">кг</span>
              </div>
              <button
                type="button"
                onClick={() => removeIngredient(i)}
                className="p-1 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-red-400"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          ))}
          {form.ingredients.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-4">Начните вводить название ингредиента для поиска</p>
          )}
        </div>
      </section>

      {/* Notes & Stats */}
      <section className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <h2 className="text-sm font-medium text-white mb-5">Характеристики</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-5">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Выход, %</label>
            <input type="number" step="0.1" value={form.yield_percent}
              onChange={(e) => updateForm("yield_percent", Number(e.target.value))}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Потери, %</label>
            <input type="number" step="0.1" value={form.losses_percent}
              onChange={(e) => updateForm("losses_percent", Number(e.target.value))}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50" />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Источник</label>
            <input value={form.source}
              onChange={(e) => updateForm("source", e.target.value)}
              placeholder="Ссылка или название источника"
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30" />
          </div>
        </div>
        <div>
          <label className="block text-xs text-muted-foreground mb-1">Примечания</label>
          <textarea
            value={form.notes}
            onChange={(e) => updateForm("notes", e.target.value)}
            rows={3}
            placeholder="Технологические заметки..."
            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 placeholder:text-muted-foreground/30 resize-none"
          />
        </div>
      </section>

      {/* Submit */}
      <div className="flex justify-end gap-3">
        <button
          type="submit"
          disabled={saving || !form.name || !form.slug || !form.product_id}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-6 py-3 text-sm font-medium text-black hover:bg-feleti-gold/90 transition-colors disabled:opacity-50 cursor-pointer"
        >
          {saving ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-black border-t-transparent" />
          ) : (
            <Save className="h-4 w-4" />
          )}
          {mode === "create" ? "Создать рецепт" : "Сохранить изменения"}
        </button>
      </div>
    </form>
  );
}
