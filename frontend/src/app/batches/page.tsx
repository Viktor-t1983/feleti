"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Package,
  Play,
  Pause,
  Square,
  CheckCircle2,
  Clock,
  ArrowRight,
  AlertCircle,
  Search,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

type BatchStatus = "PLANNED" | "QUEUED" | "RUNNING" | "PAUSED" | "COMPLETED" | "CANCELLED" | "FAILED";

interface Batch {
  id: number;
  batch_number: string;
  status: BatchStatus;
  chamber_id: number;
  chamber_name: string | null;
  recipe_name: string | null;
  operator_name: string | null;
  product_weight_kg: number | null;
  yield_kg: number | null;
  planned_start: string | null;
  actual_start: string | null;
  actual_end: string | null;
  notes: string | null;
  created_at: string;
}

interface BatchPage {
  items: Batch[];
  total: number;
}

const STATUS_CONFIG: Record<BatchStatus, { label: string; color: string; bg: string; border: string }> = {
  PLANNED: { label: "Запланирована", color: "text-slate-400", bg: "bg-slate-500/10", border: "border-slate-500/20" },
  QUEUED: { label: "В очереди", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  RUNNING: { label: "В работе", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  PAUSED: { label: "Пауза", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  COMPLETED: { label: "Завершена", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
  CANCELLED: { label: "Отменена", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
  FAILED: { label: "Ошибка", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
};

const STATUS_ORDER: BatchStatus[] = ["RUNNING", "PAUSED", "PLANNED", "QUEUED", "COMPLETED", "CANCELLED", "FAILED"];
const FILTER_TABS = [
  { id: "all", label: "Все" },
  { id: "active", label: "Активные" },
  { id: "PLANNED", label: "Запланированные" },
  { id: "COMPLETED", label: "Завершённые" },
] as const;

async function fetchBatches(status?: string): Promise<BatchPage> {
  const params = status && status !== "all"
    ? status === "active"
      ? "?status=RUNNING&status=PAUSED&size=50"
      : `?status=${status}&size=50`
    : "?size=50";
  const { data } = await apiClient.get(`/batches${params}`);
  return data;
}

const STATUS_ICONS: Record<string, React.ElementType> = {
  RUNNING: Play,
  PAUSED: Pause,
  COMPLETED: CheckCircle2,
  CANCELLED: Square,
  FAILED: AlertCircle,
};

function StatusBadge({ status }: { status: BatchStatus }) {
  const cfg = STATUS_CONFIG[status];
  const Icon = STATUS_ICONS[status] || Package;
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${cfg.color} ${cfg.bg} ${cfg.border}`}>
      <Icon className="h-3 w-3" />
      {cfg.label}
    </span>
  );
}

function formatDateTime(s: string | null): string {
  if (!s) return "—";
  const d = new Date(s);
  return d.toLocaleDateString("ru-RU", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

export default function BatchesPage() {
  const [filter, setFilter] = useState<string>("all");
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["batches", filter],
    queryFn: () => fetchBatches(filter),
    refetchInterval: filter === "active" ? 10000 : 30000,
  });

  const batches = (data?.items || []).filter((b) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      b.batch_number.toLowerCase().includes(q) ||
      (b.chamber_name || "").toLowerCase().includes(q) ||
      (b.recipe_name || "").toLowerCase().includes(q)
    );
  });

  const sorted = [...batches].sort(
    (a, b) => STATUS_ORDER.indexOf(a.status) - STATUS_ORDER.indexOf(b.status)
  );

  if (isLoading) return <BatchesSkeleton />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Партии</h1>
          <p className="text-sm text-muted-foreground mt-1">Всего: {data?.total || 0}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1">
          {FILTER_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setFilter(tab.id)}
              className={`rounded-lg px-3 py-1.5 text-sm transition-colors ${
                filter === tab.id ? "bg-white/10 text-white" : "text-muted-foreground hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по номеру, камере, рецепту..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>
      </div>

      {/* Batches list */}
      <div className="space-y-3">
        {sorted.map((batch, i) => (
          <BatchRow key={batch.id} batch={batch} index={i} />
        ))}
        {sorted.length === 0 && (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
            <Package className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-muted-foreground">Партии не найдены</p>
          </div>
        )}
      </div>
    </div>
  );
}

function BatchRow({ batch, index }: { batch: Batch; index: number }) {
  const cfg = STATUS_CONFIG[batch.status];
  return (
    <Link href={`/batches/${batch.id}`}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.04 }}
        className={`group rounded-2xl border p-5 transition-all hover:bg-white/[0.03] ${
          batch.status === "RUNNING"
            ? "border-emerald-500/20 bg-emerald-500/[0.02]"
            : batch.status === "PAUSED"
            ? "border-amber-500/20 bg-amber-500/[0.02]"
            : "border-white/5 bg-white/[0.02]"
        }`}
      >
        {batch.status === "RUNNING" && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/[0.03] to-transparent pointer-events-none" />
        )}
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Left: number + status */}
          <div className="flex items-center gap-3 min-w-[200px]">
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${cfg.bg}`}>
              <Package className={`h-5 w-5 ${cfg.color}`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-medium text-white">{batch.batch_number}</span>
                <StatusBadge status={batch.status} />
              </div>
            </div>
          </div>

          {/* Center: chamber + recipe + operator */}
          <div className="flex-1 grid grid-cols-1 sm:grid-cols-3 gap-2 text-sm">
            <div>
              <span className="text-muted-foreground text-xs">Камера</span>
              <p className="text-white">{batch.chamber_name || "—"}</p>
            </div>
            <div>
              <span className="text-muted-foreground text-xs">Рецепт</span>
              <p className="text-white truncate">{batch.recipe_name || "—"}</p>
            </div>
            <div>
              <span className="text-muted-foreground text-xs">Вес / Выход</span>
              <p className="text-white">
                {batch.product_weight_kg ? `${batch.product_weight_kg} кг` : "—"}
                {batch.yield_kg ? ` → ${batch.yield_kg} кг` : ""}
              </p>
            </div>
          </div>

          {/* Right: time + arrow */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground shrink-0">
            <span className="flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {batch.actual_start
                ? formatDateTime(batch.actual_start)
                : batch.planned_start
                ? formatDateTime(batch.planned_start)
                : "—"}
            </span>
            <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </motion.div>
    </Link>
  );
}

function BatchesSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
