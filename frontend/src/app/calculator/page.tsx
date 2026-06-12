"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Calculator,
  Plus,
  Trash2,
  RotateCcw,
  Flame,
  Droplets,
  Clock,
  Scale,
  DollarSign,
  Beef,
  Wheat,
  Zap,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { cn } from "@/lib/utils";

/* ---------- types ---------- */
interface Product {
  id: number; name: string; slug: string; category: string;
}
interface Chamber {
  id: number; model: string; type: string;
  manufacturer: { name: string };
}
interface Ingredient {
  id: number; name: string; type: string;
  protein_per_100g: number; fat_per_100g: number;
  carbs_per_100g: number; kcal_per_100g: number;
  price_per_kg: number;
}

interface CalcPhase {
  key: string;
  index: number;
  name: string;
  t_chamber: string;
  t_product: string;
  duration_min: string;
  smoke: string;
  electro_voltage_kv: string;
}

interface CalcIngredient {
  ingredient_id: number;
  mass_kg: string;
}

interface CalcResult {
  recipe_id: number;
  total_mass_kg: number;
  finished_mass_kg: number;
  losses_percent: number;
  cost_per_kg_raw: number;
  cost_per_kg_finished: number;
  total_cost: number;
  bju_per_100g: { protein: number; fat: number; carbs: number; kcal: number };
  program: {
    total_duration_min: number;
    phases_count: number;
    phases_summary: {
      index: number; name: string; duration_min: number;
      t_chamber: number | null; t_product: number | null;
      smoke: string; electro_voltage_kv: number;
    }[];
  };
  breakdown: { ingredient_id: number; name: string; mass_kg: number; cost: number; protein: number; fat: number; carbs: number; kcal: number }[];
}

/* ---------- helpers ---------- */
function formatDuration(min: number): string {
  if (min < 60) return `${min} мин`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}ч ${m}м` : `${h}ч`;
}

function phaseKey(): string {
  return Math.random().toString(36).slice(2, 8);
}

function defaultPhases(): CalcPhase[] {
  return [
    { key: phaseKey(), index: 1, name: "Подсушка", t_chamber: "40", t_product: "25", duration_min: "30", smoke: "none", electro_voltage_kv: "0" },
    { key: phaseKey(), index: 2, name: "Копчение", t_chamber: "80", t_product: "60", duration_min: "60", smoke: "дым", electro_voltage_kv: "0" },
  ];
}

const SMOKE_OPTIONS = [
  { value: "none", label: "Нет" },
  { value: "дым", label: "Дым" },
  { value: "жидкий дым", label: "Жидкий дым" },
];

/* ---------- component ---------- */
export default function CalculatorPage() {
  const [productId, setProductId] = useState<number | "">("");
  const [chamberId, setChamberId] = useState<number | "">("");
  const [brineMethod, setBrineMethod] = useState("");
  const [ingredients, setIngredients] = useState<CalcIngredient[]>([]);
  const [phases, setPhases] = useState<CalcPhase[]>(defaultPhases());
  const [result, setResult] = useState<CalcResult | null>(null);
  const [calcError, setCalcError] = useState<string | null>(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [showResults, setShowResults] = useState(false);

  /* ---- data fetching ---- */
  const { data: products } = useQuery({
    queryKey: ["products-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/products?size=200");
      return (data as { items: Product[] }).items;
    },
  });

  const { data: chambers } = useQuery({
    queryKey: ["chambers-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/chambers?size=200");
      return (data as { items: Chamber[] }).items;
    },
  });

  const { data: allIngredients } = useQuery({
    queryKey: ["ingredients-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/ingredients?size=200");
      return (data as { items: Ingredient[] }).items;
    },
  });

  const selectedProduct = products?.find((p) => p.id === productId);

  /* ---- presets ---- */
  const applyPresets = useCallback(async () => {
    if (!productId) return;
    setCalcLoading(true);
    try {
      const params = new URLSearchParams({ product_id: String(productId) });
      if (chamberId) params.set("chamber_id", String(chamberId));
      const { data } = await apiClient.get(`/calc/presets?${params}`);
      if (data?.recommended_program) {
        const newPhases: CalcPhase[] = data.recommended_program.map(
          (p: Record<string, unknown>, i: number) => ({
            key: phaseKey(),
            index: i + 1,
            name: (p.name as string) || "",
            t_chamber: p.t_chamber != null ? String(p.t_chamber) : "",
            t_product: p.t_product != null ? String(p.t_product) : "",
            duration_min: p.duration_min != null ? String(p.duration_min) : "60",
            smoke: (p.smoke as string) || "none",
            electro_voltage_kv: p.electro_voltage_kv != null ? String(p.electro_voltage_kv) : "0",
          })
        );
        setPhases(newPhases);
      }
    } catch {
      /* ignore — do nothing */
    } finally {
      setCalcLoading(false);
    }
  }, [productId, chamberId]);

  /* auto-preset on product change */
  const prevProductRef = useRef<number | "">("");
  useEffect(() => {
    if (productId && productId !== prevProductRef.current) {
      prevProductRef.current = productId;
      applyPresets();
    }
  }, [productId, applyPresets]);

  /* ---- ingredients add/remove ---- */
  const addIngredient = () => {
    if (!allIngredients?.length) return;
    const first = allIngredients[0];
    setIngredients((prev) => [...prev, { ingredient_id: first.id, mass_kg: "1.0" }]);
  };

  const removeIngredient = (index: number) => {
    setIngredients((prev) => prev.filter((_, i) => i !== index));
  };

  const updateIngredient = (index: number, field: "ingredient_id" | "mass_kg", value: string) => {
    setIngredients((prev) =>
      prev.map((ing, i) => (i === index ? { ...ing, [field]: field === "mass_kg" ? value : Number(value) } : ing))
    );
  };

  /* ---- phases ---- */
  const addPhase = () => {
    const idx = phases.length + 1;
    setPhases((prev) => [
      ...prev,
      { key: phaseKey(), index: idx, name: "", t_chamber: "", t_product: "", duration_min: "60", smoke: "none", electro_voltage_kv: "0" },
    ]);
  };

  const removePhase = (key: string) => {
    setPhases((prev) => {
      const filtered = prev.filter((p) => p.key !== key);
      return filtered.map((p, i) => ({ ...p, index: i + 1 }));
    });
  };

  const updatePhase = (key: string, field: keyof CalcPhase, value: string) => {
    setPhases((prev) =>
      prev.map((p) => (p.key === key ? { ...p, [field]: value } : p))
    );
  };

  const movePhase = (key: string, dir: -1 | 1) => {
    setPhases((prev) => {
      const idx = prev.findIndex((p) => p.key === key);
      if (idx === -1) return prev;
      const nextIdx = idx + dir;
      if (nextIdx < 0 || nextIdx >= prev.length) return prev;
      const arr = [...prev];
      [arr[idx], arr[nextIdx]] = [arr[nextIdx], arr[idx]];
      return arr.map((p, i) => ({ ...p, index: i + 1 }));
    });
  };

  /* ---- calculation ---- */
  const runCalc = useCallback(async () => {
    setCalcError(null);
    setCalcLoading(true);
    setShowResults(false);
    try {
      const payload = {
        product_id: productId || 1,
        chamber_id: chamberId || null,
        brine_method: brineMethod || null,
        ingredients: ingredients.filter((i) => i.mass_kg && Number(i.mass_kg) > 0).map((i) => ({
          ingredient_id: i.ingredient_id,
          mass_kg: Number(i.mass_kg),
        })),
        program: phases.map((p) => ({
          index: p.index,
          name: p.name,
          t_chamber: p.t_chamber ? Number(p.t_chamber) : null,
          t_product: p.t_product ? Number(p.t_product) : null,
          duration_min: Number(p.duration_min) || 60,
          smoke: p.smoke,
          electro_voltage_kv: Number(p.electro_voltage_kv) || 0,
        })),
      };
      const { data } = await apiClient.post("/calc/preview", payload);
      setResult(data as CalcResult);
      setShowResults(true);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setCalcError(detail || "Ошибка расчёта");
    } finally {
      setCalcLoading(false);
    }
  }, [productId, chamberId, brineMethod, ingredients, phases]);

  /* ---- save as recipe ---- */
  const [saving, setSaving] = useState(false);
  const saveAsRecipe = useCallback(async () => {
    if (!result || !productId) return;
    setSaving(true);
    try {
      const baseName = selectedProduct?.name ? `Калькуляция: ${selectedProduct.name}` : "Новый рецепт";
      const baseSlug = baseName.toLowerCase().replace(/[^a-zа-яё0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "").slice(0, 100);
      const slug = `${baseSlug}-${Date.now().toString(36)}`;
      const payload = {
        product_id: productId,
        name: baseName,
        slug,
        description: `Создано из технологического калькулятора ${new Date().toLocaleString("ru-RU")}`,
        initial_version: {
          program: phases.map((p) => ({
            index: p.index, name: p.name,
            t_chamber: p.t_chamber ? Number(p.t_chamber) : null,
            t_product: p.t_product ? Number(p.t_product) : null,
            duration_min: Number(p.duration_min) || 60,
            smoke: p.smoke, electro_voltage_kv: Number(p.electro_voltage_kv) || 0,
          })),
          brine: brineMethod ? { method: brineMethod } : null,
          ingredients: ingredients
            .filter((i) => Number(i.mass_kg) > 0)
            .map((i) => ({ ingredient_id: i.ingredient_id, mass_kg: Number(i.mass_kg) })),
          yield_percent: result.total_mass_kg > 0 ? +((result.finished_mass_kg / result.total_mass_kg) * 100).toFixed(1) : null,
          losses_percent: result.losses_percent,
          bju_per_100g: result.bju_per_100g,
          cost_per_kg: result.cost_per_kg_finished,
        },
      };
      const { data } = await apiClient.post("/recipes", payload);
      window.location.href = `/recipes/${(data as { slug: string }).slug}`;
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setCalcError(detail || "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }, [result, productId, selectedProduct, ingredients, phases, brineMethod]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Calculator className="h-6 w-6 text-feleti-gold" />
          Технологический калькулятор
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Подбор режима копчения: продукт → камера → ингредиенты → программа → расчёт
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ─────── Inputs (left) ─────── */}
        <div className="lg:col-span-3 space-y-5">
          {/* Product & Chamber */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
            <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider">1. Продукт и камера</h2>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-muted-foreground mb-1.5">Продукт *</label>
                <select
                  value={productId}
                  onChange={(e) => setProductId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                >
                  <option value="">— выберите продукт —</option>
                  {products?.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm text-muted-foreground mb-1.5">Камера</label>
                <select
                  value={chamberId}
                  onChange={(e) => setChamberId(e.target.value ? Number(e.target.value) : "")}
                  className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                >
                  <option value="">— не выбрана —</option>
                  {chambers?.map((c) => (
                    <option key={c.id} value={c.id}>{c.manufacturer?.name} {c.model}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm text-muted-foreground mb-1.5">Посол (метод)</label>
              <select
                value={brineMethod}
                onChange={(e) => setBrineMethod(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
              >
                <option value="">— без посола —</option>
                <option value="сухой">Сухой посол</option>
                <option value="мокрый">Мокрый посол (тузлук)</option>
                <option value="шприцевание">Шприцевание</option>
                <option value="смешанный">Смешанный</option>
              </select>
            </div>
          </div>

          {/* Ingredients */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider">2. Ингредиенты</h2>
              <button onClick={addIngredient} className="inline-flex items-center gap-1.5 rounded-xl bg-feleti-gold/20 px-3 py-1.5 text-xs font-medium text-feleti-gold transition-colors hover:bg-feleti-gold/30">
                <Plus className="h-3.5 w-3.5" /> Добавить
              </button>
            </div>
            {ingredients.length === 0 && (
              <p className="text-sm text-muted-foreground py-2">Нет ингредиентов — расчёт покажет нули</p>
            )}
            <AnimatePresence mode="popLayout">
              {ingredients.map((ing, i) => (
                <motion.div
                  key={`ing-${i}`}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="flex items-center gap-3"
                >
                  <select
                    value={ing.ingredient_id}
                    onChange={(e) => updateIngredient(i, "ingredient_id", e.target.value)}
                    className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50"
                  >
                    {allIngredients?.map((ai) => (
                      <option key={ai.id} value={ai.id}>{ai.name}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    step="0.1"
                    min="0"
                    value={ing.mass_kg}
                    onChange={(e) => updateIngredient(i, "mass_kg", e.target.value)}
                    className="w-24 rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-feleti-gold/50 text-right"
                    placeholder="кг"
                  />
                  <span className="text-xs text-muted-foreground w-4">кг</span>
                  <button onClick={() => removeIngredient(i)} className="text-red-400/60 hover:text-red-400 transition-colors">
                    <Trash2 className="h-4 w-4" />
                  </button>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Program */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider">3. Программа копчения</h2>
              <div className="flex items-center gap-2">
                <button onClick={applyPresets} disabled={!productId || calcLoading}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 px-3 py-1.5 text-xs text-muted-foreground transition-colors hover:text-white disabled:opacity-50">
                  <RotateCcw className="h-3.5 w-3.5" /> По presets
                </button>
                <button onClick={addPhase} className="inline-flex items-center gap-1.5 rounded-xl bg-feleti-gold/20 px-3 py-1.5 text-xs font-medium text-feleti-gold transition-colors hover:bg-feleti-gold/30">
                  <Plus className="h-3.5 w-3.5" /> Фаза
                </button>
              </div>
            </div>
            <AnimatePresence mode="popLayout">
              {phases.map((phase) => (
                <motion.div
                  key={phase.key}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="rounded-xl border border-white/5 bg-white/[0.03] p-3 space-y-2"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-md bg-white/5 text-xs text-muted-foreground font-mono">{phase.index}</span>
                    <input
                      value={phase.name}
                      onChange={(e) => updatePhase(phase.key, "name", e.target.value)}
                      className="flex-1 rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                      placeholder="Название фазы"
                    />
                    <button onClick={() => movePhase(phase.key, -1)} className="text-muted-foreground/50 hover:text-white transition-colors" title="Вверх">
                      <ChevronUp className="h-4 w-4" />
                    </button>
                    <button onClick={() => movePhase(phase.key, 1)} className="text-muted-foreground/50 hover:text-white transition-colors" title="Вниз">
                      <ChevronDown className="h-4 w-4" />
                    </button>
                    <button onClick={() => removePhase(phase.key)} className="text-red-400/60 hover:text-red-400 transition-colors">
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                  <div className="grid grid-cols-5 gap-2">
                    <div>
                      <label className="block text-[10px] text-muted-foreground mb-0.5">T камеры</label>
                      <input type="number" value={phase.t_chamber} onChange={(e) => updatePhase(phase.key, "t_chamber", e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white outline-none focus:border-feleti-gold/50" placeholder="°C" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-muted-foreground mb-0.5">T продукта</label>
                      <input type="number" value={phase.t_product} onChange={(e) => updatePhase(phase.key, "t_product", e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white outline-none focus:border-feleti-gold/50" placeholder="°C" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-muted-foreground mb-0.5">Длит-ть</label>
                      <input type="number" value={phase.duration_min} onChange={(e) => updatePhase(phase.key, "duration_min", e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white outline-none focus:border-feleti-gold/50" placeholder="мин" />
                    </div>
                    <div>
                      <label className="block text-[10px] text-muted-foreground mb-0.5">Дым</label>
                      <select value={phase.smoke} onChange={(e) => updatePhase(phase.key, "smoke", e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white outline-none focus:border-feleti-gold/50">
                        {SMOKE_OPTIONS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-[10px] text-muted-foreground mb-0.5">Электро</label>
                      <input type="number" step="1" value={phase.electro_voltage_kv} onChange={(e) => updatePhase(phase.key, "electro_voltage_kv", e.target.value)}
                        className="w-full rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-white outline-none focus:border-feleti-gold/50" placeholder="кВ" />
                    </div>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>

          {/* Calc button */}
          <div className="flex items-center gap-3">
            <button onClick={runCalc} disabled={calcLoading || !productId}
              className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-6 py-3 text-sm font-bold text-black transition-colors hover:bg-feleti-gold/90 disabled:opacity-50">
              {calcLoading ? (
                <><RotateCcw className="h-4 w-4 animate-spin" /> Расчёт...</>
              ) : (
                <><Calculator className="h-4 w-4" /> Рассчитать</>
              )}
            </button>
            {result && (
              <button onClick={saveAsRecipe} disabled={saving}
                className="inline-flex items-center gap-2 rounded-xl border border-feleti-gold/30 px-6 py-3 text-sm font-medium text-feleti-gold transition-colors hover:bg-feleti-gold/10 disabled:opacity-50">
                {saving ? "Сохранение..." : "Сохранить как рецепт"}
              </button>
            )}
          </div>
          {calcError && (
            <p className="text-sm text-red-400">{calcError}</p>
          )}
        </div>

        {/* ─────── Results (right) ─────── */}
        <div className="lg:col-span-2 space-y-4">
          <div className="sticky top-6">
            <h2 className="text-sm font-semibold text-white/80 uppercase tracking-wider mb-4">4. Результаты</h2>
            {!showResults || !result ? (
              <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
                <Calculator className="h-12 w-12 text-muted-foreground/30" />
                <p className="mt-4 text-sm text-muted-foreground">Заполните параметры и нажмите «Рассчитать»</p>
              </div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="space-y-4"
              >
                {/* Yield */}
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
                  <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">Выход и потери</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <ResultCard icon={<Scale className="h-4 w-4 text-feleti-gold" />} label="Сырьё" value={`${result.total_mass_kg.toFixed(2)} кг`} />
                    <ResultCard icon={<Beef className="h-4 w-4 text-green-400" />} label="Готовый продукт" value={`${result.finished_mass_kg.toFixed(2)} кг`} />
                    <ResultCard icon={<Flame className="h-4 w-4 text-red-400" />} label="Потери" value={`${result.losses_percent.toFixed(1)}%`} />
                    <ResultCard icon={<Clock className="h-4 w-4 text-blue-400" />} label="Полный цикл" value={formatDuration(result.program.total_duration_min)} />
                  </div>
                </div>

                {/* Cost */}
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
                  <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">Себестоимость</h3>
                  <div className="grid grid-cols-2 gap-3">
                    <ResultCard icon={<DollarSign className="h-4 w-4 text-feleti-gold" />} label="За кг сырья" value={`${result.cost_per_kg_raw.toFixed(2)} ₽`} />
                    <ResultCard icon={<DollarSign className="h-4 w-4 text-green-400" />} label="За кг готового" value={`${result.cost_per_kg_finished.toFixed(2)} ₽`} />
                    <div className="col-span-2">
                      <ResultCard icon={<DollarSign className="h-4 w-4 text-white" />} label="Общая стоимость партии" value={`${result.total_cost.toFixed(2)} ₽`} size="lg" />
                    </div>
                  </div>
                </div>

                {/* BJU */}
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
                  <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">БЖУ на 100 г</h3>
                  <div className="grid grid-cols-4 gap-2">
                    <BJUCard icon={<Beef className="h-3.5 w-3.5 text-red-400" />} label="Белки" value={`${result.bju_per_100g.protein.toFixed(1)} г`} />
                    <BJUCard icon={<Droplets className="h-3.5 w-3.5 text-yellow-400" />} label="Жиры" value={`${result.bju_per_100g.fat.toFixed(1)} г`} />
                    <BJUCard icon={<Wheat className="h-3.5 w-3.5 text-blue-400" />} label="Углеводы" value={`${result.bju_per_100g.carbs.toFixed(1)} г`} />
                    <BJUCard icon={<Zap className="h-3.5 w-3.5 text-orange-400" />} label="Ккал" value={`${result.bju_per_100g.kcal.toFixed(0)}`} />
                  </div>
                </div>

                {/* Phases summary */}
                <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-3">
                  <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">Программа ({result.program.phases_count} фаз)</h3>
                  {result.program.phases_summary.map((ph) => (
                    <div key={ph.index} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0">
                      <div className="flex items-center gap-2">
                        <span className="w-5 h-5 flex items-center justify-center rounded bg-white/5 font-mono text-[10px] text-muted-foreground">{ph.index}</span>
                        <span className="text-white/80">{ph.name || `Фаза ${ph.index}`}</span>
                      </div>
                      <div className="flex items-center gap-3 text-muted-foreground">
                        {ph.t_chamber != null && <span>{ph.t_chamber}°C</span>}
                        <span>{ph.duration_min} мин</span>
                        {ph.smoke !== "none" && <span className="text-feleti-gold">🔥</span>}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Ingredient breakdown */}
                {result.breakdown.length > 0 && (
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-3">
                    <h3 className="text-xs font-semibold text-white/60 uppercase tracking-wider">Разбор ингредиентов</h3>
                    <div className="space-y-1">
                      {result.breakdown.map((b) => (
                        <div key={b.ingredient_id} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0">
                          <span className="text-white/80">{b.name}</span>
                          <div className="flex items-center gap-3 text-muted-foreground">
                            <span>{b.mass_kg.toFixed(2)} кг</span>
                            <span>{b.cost.toFixed(2)} ₽</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ── sub-components ── */
function ResultCard({ icon, label, value, size }: { icon: React.ReactNode; label: string; value: string; size?: "default" | "lg" }) {
  return (
    <div className={cn("rounded-xl border border-white/5 bg-white/[0.03] p-3 flex items-center gap-3", size === "lg" && "p-4")}>
      <div className={cn("flex h-8 w-8 items-center justify-center rounded-lg bg-white/5 shrink-0", size === "lg" && "h-10 w-10")}>
        {icon}
      </div>
      <div className="min-w-0">
        <p className="text-[11px] text-muted-foreground">{label}</p>
        <p className={cn("font-semibold text-white truncate", size === "lg" ? "text-base" : "text-sm")}>{value}</p>
      </div>
    </div>
  );
}

function BJUCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.03] p-2.5 text-center">
      <div className="flex justify-center mb-1">{icon}</div>
      <p className="text-[10px] text-muted-foreground">{label}</p>
      <p className="text-xs font-semibold text-white mt-0.5">{value}</p>
    </div>
  );
}
