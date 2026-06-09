"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Flame,
  BookOpen,
  Package,
  TrendingUp,
  Factory,
  Snowflake,
  Droplets,
  Zap,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface DashboardStats {
  counts: {
    chambers: number;
    recipes: number;
    batches: number;
    batches_active: number;
    products: number;
    ingredients: number;
    users: number;
    competitors: number;
  };
  chambers: {
    id: number;
    model: string;
    manufacturer: string;
    status: string;
    max_load_kg: number;
    type: string;
  }[];
  batch_statuses: Record<string, number>;
}

async function fetchDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get("/dashboard/stats");
  return data;
}

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.08 },
  },
};

const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.4 } },
};

const BATCH_STATUS_COLORS: Record<string, string> = {
  planned: "#94a3b8",
  queued: "#3b82f6",
  running: "#10b981",
  paused: "#f59e0b",
  completed: "#10b981",
  cancelled: "#ef4444",
  failed: "#dc2626",
};

const BATCH_STATUS_LABELS: Record<string, string> = {
  planned: "Запланированы",
  queued: "В очереди",
  running: "В работе",
  paused: "Пауза",
  completed: "Завершены",
  cancelled: "Отменены",
  failed: "Ошибки",
};

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard", "stats"],
    queryFn: fetchDashboardStats,
    refetchInterval: 30000,
  });

  if (isLoading || !data) {
    return <DashboardSkeleton />;
  }

  const { counts, chambers, batch_statuses } = data;

  const batchChartData = Object.entries(batch_statuses)
    .filter(([, value]) => value > 0)
    .map(([key, value]) => ({
      name: BATCH_STATUS_LABELS[key] || key,
      value,
      color: BATCH_STATUS_COLORS[key] || "#94a3b8",
    }));

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Панель управления</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Обзор производства в реальном времени
        </p>
      </div>

      {/* KPI Cards */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <StatCard
          icon={Factory}
          label="Камеры"
          value={counts.chambers}
          href="/chambers"
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          icon={BookOpen}
          label="Рецепты"
          value={counts.recipes}
          href="/recipes"
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          icon={Package}
          label="Партии"
          value={counts.batches}
          href="/batches"
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          icon={TrendingUp}
          label="Конкуренты"
          value={counts.competitors}
          href="/competitors"
          color="text-feleti-gold"
          bg="bg-feleti-gold/10"
        />
      </motion.div>

      {/* Charts row */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid gap-4 lg:grid-cols-2"
      >
        {/* Batch status chart */}
        <motion.div
          variants={item}
          className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-4">
            Распределение партий по статусам
          </h3>
          {batchChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={batchChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                <XAxis
                  dataKey="name"
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                />
                <YAxis
                  tick={{ fill: "#888", fontSize: 12 }}
                  axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
                  allowDecimals={false}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "#fff",
                  }}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {batchChartData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[220px] items-center justify-center text-muted-foreground text-sm">
              Нет данных о партиях
            </div>
          )}
        </motion.div>

        {/* Batch status pie */}
        <motion.div
          variants={item}
          className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-4">
            Статусы партий
          </h3>
          {batchChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={batchChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={80}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {batchChartData.map((entry, index) => (
                    <Cell key={index} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1a1a1a",
                    border: "1px solid rgba(255,255,255,0.1)",
                    borderRadius: "8px",
                    color: "#fff",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="flex h-[220px] items-center justify-center text-muted-foreground text-sm">
              Нет данных о партиях
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* Secondary stats */}
      <motion.div
        variants={container}
        initial="hidden"
        animate="show"
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <MiniStat label="Продуктов" value={counts.products} />
        <MiniStat label="Ингредиентов" value={counts.ingredients} />
        <MiniStat label="Пользователей" value={counts.users} />
        <MiniStat
          label="Активных партий"
          value={counts.batches_active}
          alert={counts.batches_active > 0}
        />
      </motion.div>

      {/* Chambers status */}
      <motion.div variants={item} initial="hidden" animate="show">
        <h2 className="text-lg font-semibold text-white mb-4">Статус камер</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {chambers.map((chamber) => (
            <ChamberCard key={chamber.id} chamber={chamber} />
          ))}
        </div>
      </motion.div>

      {/* Quick actions */}
      <motion.div variants={item} initial="hidden" animate="show">
        <h2 className="text-lg font-semibold text-white mb-4">Быстрые действия</h2>
        <div className="flex flex-wrap gap-3">
          <QuickAction href="/recipes/new" icon={BookOpen} label="Новый рецепт" />
          <QuickAction href="/batches" icon={Package} label="Запустить партию" />
          <QuickAction href="/competitors" icon={TrendingUp} label="Анализ конкурентов" />
        </div>
      </motion.div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  href,
  color,
  bg,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  href: string;
  color: string;
  bg: string;
}) {
  return (
    <motion.div variants={item}>
      <Link
        href={href}
        className="flex items-center gap-4 rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-colors hover:bg-white/[0.04] hover:border-white/10"
      >
        <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${bg}`}>
          <Icon className={`h-6 w-6 ${color}`} />
        </div>
        <div>
          <div className="text-2xl font-bold text-white">{value}</div>
          <div className="text-sm text-muted-foreground">{label}</div>
        </div>
      </Link>
    </motion.div>
  );
}

function MiniStat({
  label,
  value,
  alert,
}: {
  label: string;
  value: number;
  alert?: boolean;
}) {
  return (
    <motion.div
      variants={item}
      className={`rounded-xl border p-4 text-center transition-colors ${
        alert
          ? "border-feleti-gold/20 bg-feleti-gold/[0.03]"
          : "border-white/5 bg-white/[0.02]"
      }`}
    >
      <div className={`text-xl font-bold ${alert ? "text-feleti-gold" : "text-white"}`}>
        {value}
      </div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </motion.div>
  );
}

function ChamberCard({
  chamber,
}: {
  chamber: DashboardStats["chambers"][0];
}) {
  const typeIcons: Record<string, React.ElementType> = {
    hot: Flame,
    cold: Snowflake,
    universal: Zap,
    electro: Droplets,
  };
  const TypeIcon = typeIcons[chamber.type] || Factory;

  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="font-medium text-white">{chamber.model}</h3>
          <p className="text-xs text-muted-foreground">{chamber.manufacturer}</p>
        </div>
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-white/5">
          <TypeIcon className="h-4 w-4 text-feleti-gold" />
        </div>
      </div>
      <div className="mt-3 flex items-center gap-3">
        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          {chamber.status}
        </span>
        <span className="text-xs text-muted-foreground">до {chamber.max_load_kg} кг</span>
      </div>
    </div>
  );
}

function QuickAction({
  href,
  icon: Icon,
  label,
}: {
  href: string;
  icon: React.ElementType;
  label: string;
}) {
  return (
    <Link
      href={href}
      className="inline-flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white transition-colors hover:bg-white/[0.04] hover:border-feleti-gold/30"
    >
      <Icon className="h-4 w-4 text-feleti-gold" />
      {label}
    </Link>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-8">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-white/5" />
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
      <div className="grid grid-cols-2 gap-4">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="h-64 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
