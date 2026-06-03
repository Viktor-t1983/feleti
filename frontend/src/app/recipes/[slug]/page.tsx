"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BookOpen,
  ArrowLeft,
  Thermometer,
  Clock,
  Droplets,
  CheckCircle2,
  Tag,
  FileText,
  ChefHat,
  Beaker,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface RecipePhase {
  name: string;
  duration_min: number;
  t_chamber: number;
  humidity?: number;
  smoke?: string;
  wood_species?: string;
  t_product_target?: number;
  electro_voltage_kv?: number;
}

interface RecipeVersion {
  id: number;
  version_number: number;
  program: RecipePhase[];
  ingredients: { name: string; percent?: number; mass_kg?: number }[];
  brine: Record<string, unknown> | null;
  yield_percent: number | null;
  losses_percent: number | null;
  notes: string | null;
  gost: string | null;
  verified: boolean;
}

interface Recipe {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  tags: string[];
  current_version: RecipeVersion | null;
}

const PHASE_COLORS: Record<string, string> = {
  Подсушка: "#f59e0b",
  Копчение: "#c9a96e",
  "Копчение электро": "#a78bfa",
  Запекание: "#ef4444",
  Варка: "#3b82f6",
  Душирование: "#06b6d4",
  Посол: "#8b5cf6",
  Охлаждение: "#06b6d4",
  Заморозка: "#6366f1",
  Прогрев: "#10b981",
};

const SMOKE_LABELS: Record<string, string> = {
  none: "Нет",
  light: "Лёгкий",
  medium: "Средний",
  heavy: "Сильный",
};

export default function RecipeDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const { data: recipe, isLoading } = useQuery({
    queryKey: ["recipe", slug],
    queryFn: () => fetchRecipe(slug),
  });

  if (isLoading) {
    return <RecipeDetailSkeleton />;
  }

  if (!recipe) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Рецепт не найден</p>
        <Link
          href="/recipes"
          className="mt-4 text-sm text-feleti-gold hover:underline"
        >
          Вернуться к списку
        </Link>
      </div>
    );
  }

  const version = recipe.current_version;
  const phases = version?.program || [];
  const totalTime = phases.reduce((sum, p) => sum + (p.duration_min || 0), 0);

  const chartData = phases.map((p, i) => ({
    name: `${p.name} (${i + 1})`,
    temp: p.t_chamber,
    time: p.duration_min,
    color: PHASE_COLORS[p.name] || "#94a3b8",
  }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/recipes"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к рецептам
        </Link>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{recipe.name}</h1>
            {recipe.description && (
              <p className="text-sm text-muted-foreground mt-2 max-w-2xl">
                {recipe.description}
              </p>
            )}
          </div>
          {version?.verified && (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4" />
              Утверждён
            </span>
          )}
        </div>
      </div>

      {/* Tags & GOST */}
      <div className="flex flex-wrap items-center gap-3">
        {recipe.tags.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center gap-1 rounded-full bg-white/5 px-3 py-1 text-sm text-muted-foreground"
          >
            <Tag className="h-3 w-3" />
            {tag}
          </span>
        ))}
        {version?.gost && (
          <span className="inline-flex items-center gap-1 rounded-full bg-feleti-gold/10 px-3 py-1 text-sm text-feleti-gold">
            <FileText className="h-3 w-3" />
            {version.gost}
          </span>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard label="Общее время" value={`${totalTime} мин`} icon={Clock} />
        <StatCard label="Фаз" value={`${phases.length}`} icon={BookOpen} />
        {version?.yield_percent != null && (
          <StatCard label="Выход" value={`${version.yield_percent}%`} icon={Droplets} />
        )}
        {version?.losses_percent != null && (
          <StatCard label="Потери" value={`${version.losses_percent}%`} icon={Thermometer} />
        )}
      </div>

      {/* Temperature chart */}
      {chartData.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-4">
            Температурный профиль
          </h3>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
              <XAxis
                dataKey="name"
                tick={{ fill: "#888", fontSize: 11 }}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              />
              <YAxis
                tick={{ fill: "#888", fontSize: 12 }}
                axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                label={{ value: "°C", angle: -90, position: "insideLeft", fill: "#888" }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#1a1a1a",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: "8px",
                  color: "#fff",
                }}
              />
              <Bar dataKey="temp" radius={[4, 4, 0, 0]}>
                {chartData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>
      )}

      {/* Phases table */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
      >
        <h3 className="text-sm font-medium text-white mb-4">
          Программа копчения
        </h3>
        <div className="overflow-hidden rounded-xl border border-white/5">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">№</th>
                <th className="px-4 py-3 text-left font-medium text-muted-foreground">Фаза</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">T камеры</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Время</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Влажность</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Дым</th>
                <th className="px-4 py-3 text-right font-medium text-muted-foreground">Щепа</th>
              </tr>
            </thead>
            <tbody>
              {phases.map((phase, i) => (
                <tr
                  key={i}
                  className="border-b border-white/5 hover:bg-white/[0.02]"
                >
                  <td className="px-4 py-3 text-muted-foreground">{i + 1}</td>
                  <td className="px-4 py-3">
                    <span className="inline-flex items-center gap-2">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: PHASE_COLORS[phase.name] || "#94a3b8" }}
                      />
                      <span className="text-white">{phase.name}</span>
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right text-white">
                    {phase.t_chamber}°C
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {phase.duration_min} мин
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {phase.humidity != null ? `${phase.humidity}%` : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {phase.smoke ? (SMOKE_LABELS[phase.smoke] || phase.smoke) : "—"}
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground">
                    {phase.wood_species || "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Ingredients */}
      {version?.ingredients && version.ingredients.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <ChefHat className="h-4 w-4 text-feleti-gold" />
            Ингредиенты
          </h3>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {version.ingredients.map((ing, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg bg-white/[0.03] px-3 py-2 text-sm"
              >
                <span className="text-white">{ing.name}</span>
                <span className="text-muted-foreground">
                  {ing.percent != null ? `${ing.percent}%` : ing.mass_kg ? `${ing.mass_kg} кг` : ""}
                </span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Brine */}
      {version?.brine && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.18 }}
          className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
            <Beaker className="h-4 w-4 text-feleti-gold" />
            Посол
          </h3>
          <div className="grid gap-2 sm:grid-cols-3">
            {version.brine.method != null && (
              <div className="text-sm">
                <span className="text-muted-foreground">Метод: </span>
                <span className="text-white">{String(version.brine.method)}</span>
              </div>
            )}
            {version.brine.salt_percent != null && (
              <div className="text-sm">
                <span className="text-muted-foreground">Соли: </span>
                <span className="text-white">{String(version.brine.salt_percent)}%</span>
              </div>
            )}
            {version.brine.duration_hours != null && (
              <div className="text-sm">
                <span className="text-muted-foreground">Длительность: </span>
                <span className="text-white">{String(version.brine.duration_hours)} ч</span>
              </div>
            )}
          </div>
        </motion.div>
      )}

      {/* Notes */}
      {version?.notes && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="rounded-xl border border-white/5 bg-white/[0.02] p-4"
        >
          <h3 className="text-sm font-medium text-white mb-2">Примечания</h3>
          <p className="text-sm text-muted-foreground">{version.notes}</p>
        </motion.div>
      )}
    </div>
  );
}

function StatCard({ label, value, icon: Icon }: { label: string; value: string; icon: React.ElementType }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4 text-feleti-gold" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-lg font-bold text-white">{value}</div>
    </div>
  );
}

function RecipeDetailSkeleton() {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="h-4 w-32 animate-pulse rounded bg-white/5" />
        <div className="h-8 w-64 animate-pulse rounded-lg bg-white/5" />
      </div>
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
      <div className="h-72 animate-pulse rounded-2xl bg-white/5" />
    </div>
  );
}

async function fetchRecipe(slug: string): Promise<Recipe> {
  const { data } = await apiClient.get(`/recipes/by-slug/${slug}`);
  return data;
}
