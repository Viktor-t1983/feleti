"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  GitBranch,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Thermometer,
  Droplets,
  Clock,
  Beaker,
  FileText,
  RotateCcw,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { cn } from "@/lib/utils";

/* ---------- types ---------- */
interface Product {
  id: number; name: string; slug: string; category: string;
}

interface ChamberEntry {
  id: number; model: string; type: string;
  manufacturer: string | null;
  compatible: boolean;
  temp_range: [number, number] | null;
}

interface BrineEntry {
  id: number; name: string; method: string;
  salt_percent: number; duration_hours: number;
  recommended: boolean;
}

interface RefRecipe {
  recipe_id: number; recipe_name: string; product_id: number;
  phases_count: number; total_duration_min: number;
  brine_method: string | null;
  yield_percent: number | null; losses_percent: number | null;
}

interface AnalysisData {
  product_id: number;
  product_name: string | null;
  product_category: string | null;
  preferred_brine_methods: string[];
  chambers: ChamberEntry[];
  brines: BrineEntry[];
  reference_recipes: RefRecipe[];
}

const BRINE_METHOD_LABELS: Record<string, string> = {
  "сухой": "Сухой",
  "мокрый": "Мокрый",
  "шприцевание": "Шприцевание",
  "комбинированный": "Комбинированный",
  "смешанный": "Смешанный",
};

function formatDuration(min: number): string {
  if (min <= 0) return "—";
  if (min < 60) return `${min} мин`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return m > 0 ? `${h}ч ${m}м` : `${h}ч`;
}

/* ---------- component ---------- */
export default function MatrixPage() {
  const [productId, setProductId] = useState<number | "">("");

  /* ---- fetch products ---- */
  const { data: products } = useQuery({
    queryKey: ["products-all"],
    queryFn: async () => {
      const { data } = await apiClient.get("/products?size=200");
      return (data as { items: Product[] }).items;
    },
  });

  /* ---- fetch analysis ---- */
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["matrix", productId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/matrix/compatibility?product_id=${productId}&refs=10`);
      return data as AnalysisData;
    },
    enabled: !!productId,
  });

  const compatibleCount = data?.chambers.filter((c) => c.compatible).length ?? 0;
  const incompatibleCount = data?.chambers.filter((c) => !c.compatible).length ?? 0;
  const recommendedBrines = data?.brines.filter((b) => b.recommended) ?? [];
  const otherBrines = data?.brines.filter((b) => !b.recommended) ?? [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <GitBranch className="h-6 w-6 text-feleti-gold" />
          Матрица совместимости
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Продукт ↔ Камера ↔ Посол — rule-based анализ совместимости
        </p>
      </div>

      {/* Product selector */}
      <div className="flex items-center gap-4">
        <div className="w-80">
          <label className="block text-sm text-muted-foreground mb-1.5">Продукт</label>
          <select
            value={productId}
            onChange={(e) => setProductId(e.target.value ? Number(e.target.value) : "")}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
          >
            <option value="">— выберите продукт —</option>
            {products?.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.category})</option>
            ))}
          </select>
        </div>
        {data && (
          <div className="flex items-center gap-4 text-sm pt-5">
            <span className="inline-flex items-center gap-1.5 rounded-xl bg-green-500/10 px-3 py-1.5 text-green-400">
              <CheckCircle2 className="h-3.5 w-3.5" /> {compatibleCount} совместимых
            </span>
            <span className="inline-flex items-center gap-1.5 rounded-xl bg-red-500/10 px-3 py-1.5 text-red-400">
              <XCircle className="h-3.5 w-3.5" /> {incompatibleCount} несовместимых
            </span>
          </div>
        )}
      </div>

      {!productId && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-20">
          <GitBranch className="h-16 w-16 text-muted-foreground/20" />
          <p className="mt-4 text-sm text-muted-foreground">Выберите продукт для анализа совместимости</p>
        </div>
      )}

      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <RotateCcw className="h-6 w-6 text-muted-foreground animate-spin" />
          <span className="ml-3 text-sm text-muted-foreground">Загрузка...</span>
        </div>
      )}

      {error && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-red-500/10 bg-red-500/[0.02] py-12">
          <AlertCircle className="h-8 w-8 text-red-400" />
          <p className="mt-3 text-sm text-red-400">Ошибка загрузки</p>
          <button onClick={() => refetch()} className="mt-3 rounded-xl border border-white/10 px-4 py-2 text-sm text-white hover:bg-white/5">
            Повторить
          </button>
        </div>
      )}

      {data && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
          {/* Product info */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-semibold text-white">{data.product_name}</h2>
                <p className="text-sm text-muted-foreground mt-0.5">{data.product_category}</p>
              </div>
              {data.preferred_brine_methods.length > 0 && (
                <div className="text-right">
                  <span className="text-xs text-muted-foreground">Рекомендуемые посолы:</span>
                  <div className="flex gap-1.5 mt-1">
                    {data.preferred_brine_methods.map((m) => (
                      <span key={m} className="rounded-lg bg-feleti-gold/15 px-2 py-0.5 text-xs text-feleti-gold">
                        {BRINE_METHOD_LABELS[m] || m}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Chambers */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider flex items-center gap-2">
              <Thermometer className="h-4 w-4 text-feleti-gold" />
              Камеры ({data.chambers.length})
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Производитель</th>
                    <th className="pb-2 font-medium">Модель</th>
                    <th className="pb-2 font-medium">Тип</th>
                    <th className="pb-2 font-medium">Диапазон T</th>
                    <th className="pb-2 font-medium text-right">Совместимость</th>
                  </tr>
                </thead>
                <tbody>
                  {data.chambers.map((ch) => (
                    <tr key={ch.id} className="border-b border-white/[0.02] text-white/80">
                      <td className="py-2.5">{ch.manufacturer || "—"}</td>
                      <td className="py-2.5">{ch.model}</td>
                      <td className="py-2.5">
                        <span className={cn(
                          "rounded-md px-2 py-0.5 text-xs",
                          ch.type === "горячее" && "bg-red-500/10 text-red-300",
                          ch.type === "холодное" && "bg-blue-500/10 text-blue-300",
                          ch.type === "электро" && "bg-yellow-500/10 text-yellow-300",
                          ch.type === "универсальное" && "bg-purple-500/10 text-purple-300",
                          ch.type === "полугорячее" && "bg-orange-500/10 text-orange-300",
                          ch.type === "дымогенератор" && "bg-gray-500/10 text-gray-300",
                        )}>
                          {ch.type}
                        </span>
                      </td>
                      <td className="py-2.5 text-muted-foreground font-mono">
                        {ch.temp_range ? `${ch.temp_range[0]}…${ch.temp_range[1]}°C` : "—"}
                      </td>
                      <td className="py-2.5 text-right">
                        {ch.compatible ? (
                          <span className="inline-flex items-center gap-1 text-green-400">
                            <CheckCircle2 className="h-4 w-4" /> Совместима
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-red-400/70">
                            <XCircle className="h-4 w-4" /> Несовместима
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Brines */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
            <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider flex items-center gap-2">
              <Droplets className="h-4 w-4 text-feleti-gold" />
              Рассолы ({recommendedBrines.length} рекомендовано / {otherBrines.length} прочих)
              {data.preferred_brine_methods.length > 0 && (
                <span className="ml-2 text-xs font-normal text-muted-foreground">
                  (предпочтительные: {data.preferred_brine_methods.map(m => BRINE_METHOD_LABELS[m] || m).join(", ")})
                </span>
              )}
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-white/5 text-left text-muted-foreground">
                    <th className="pb-2 font-medium">Название</th>
                    <th className="pb-2 font-medium">Метод</th>
                    <th className="pb-2 font-medium">Соль %</th>
                    <th className="pb-2 font-medium">Длительность</th>
                    <th className="pb-2 font-medium text-right">Статус</th>
                  </tr>
                </thead>
                <tbody>
                  {recommendedBrines.map((b) => (
                    <tr key={b.id} className="border-b border-white/[0.02] text-white/80">
                      <td className="py-2 font-medium text-white">{b.name}</td>
                      <td className="py-2">{BRINE_METHOD_LABELS[b.method] || b.method}</td>
                      <td className="py-2 font-mono">{b.salt_percent}%</td>
                      <td className="py-2 text-muted-foreground">{b.duration_hours} ч</td>
                      <td className="py-2 text-right">
                        <span className="inline-flex items-center gap-1 text-green-400">
                          <CheckCircle2 className="h-4 w-4" /> Рекомендован
                        </span>
                      </td>
                    </tr>
                  ))}
                  {otherBrines.length > 0 && (
                    <tr className="border-b border-white/[0.02]">
                      <td colSpan={5} className="py-3 text-xs text-muted-foreground text-center">
                        {otherBrines.length} рассолов не подходят по методу посола
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Reference recipes */}
          {data.reference_recipes.length > 0 && (
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 space-y-4">
              <h3 className="text-sm font-semibold text-white/80 uppercase tracking-wider flex items-center gap-2">
                <FileText className="h-4 w-4 text-feleti-gold" />
                Референтные рецепты ({data.reference_recipes.length})
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {data.reference_recipes.map((r) => (
                  <div key={r.recipe_id} className="rounded-xl border border-white/5 bg-white/[0.03] p-4 space-y-2">
                    <div className="flex items-start justify-between">
                      <p className="font-medium text-white text-sm">{r.recipe_name}</p>
                      {r.yield_percent != null && (
                        <span className={cn(
                          "rounded-lg px-2 py-0.5 text-xs font-mono",
                          r.yield_percent >= 90 ? "bg-green-500/10 text-green-400" : "bg-yellow-500/10 text-yellow-400"
                        )}>
                          {r.yield_percent}%
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      {r.phases_count > 0 && (
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" /> {r.phases_count} фаз
                        </span>
                      )}
                      {r.total_duration_min > 0 && (
                        <span className="flex items-center gap-1">
                          <Thermometer className="h-3 w-3" /> {formatDuration(r.total_duration_min)}
                        </span>
                      )}
                      {r.brine_method && (
                        <span className="flex items-center gap-1">
                          <Beaker className="h-3 w-3" /> {BRINE_METHOD_LABELS[r.brine_method] || r.brine_method}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </motion.div>
      )}
    </div>
  );
}
