"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Package,
  Play,
  Pause,
  CheckCircle2,
  Clock,
  AlertCircle,
  XCircle,
  Search,
  Filter,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";

interface Batch {
  id: number;
  batch_number: string;
  status: string;
  chamber_name: string | null;
  recipe_name: string | null;
  operator_name: string | null;
  product_weight_kg: number | null;
  yield_kg: number | null;
  losses_percent: number | null;
  planned_start: string | null;
  actual_start: string | null;
  actual_end: string | null;
  created_at: string;
}

interface BatchPage {
  items: Batch[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

const statusConfig: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  planned: { label: "Запланирована", icon: Clock, color: "text-slate-400", bg: "bg-slate-500/10" },
  queued: { label: "В очереди", icon: Clock, color: "text-blue-400", bg: "bg-blue-500/10" },
  running: { label: "В работе", icon: Play, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  paused: { label: "Пауза", icon: Pause, color: "text-amber-400", bg: "bg-amber-500/10" },
  completed: { label: "Завершена", icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  cancelled: { label: "Отменена", icon: XCircle, color: "text-red-400", bg: "bg-red-500/10" },
  failed: { label: "Ошибка", icon: AlertCircle, color: "text-red-400", bg: "bg-red-500/10" },
};

async function fetchBatches(status?: string): Promise<BatchPage> {
  const url = status ? `/batches?status=${status}&size=50` : "/batches?size=50";
  const { data } = await apiClient.get(url);
  return data;
}

export default function BatchesPage() {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");

  const { data, isLoading } = useQuery({
    queryKey: ["batches", statusFilter],
    queryFn: () => fetchBatches(statusFilter === "all" ? undefined : statusFilter),
  });

  const batches = data?.items || [];
  const filtered = batches.filter(
    (b) =>
      b.batch_number.toLowerCase().includes(search.toLowerCase()) ||
      (b.recipe_name?.toLowerCase() || "").includes(search.toLowerCase()) ||
      (b.chamber_name?.toLowerCase() || "").includes(search.toLowerCase())
  );

  if (isLoading) {
    return <BatchesSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Партии</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Управление производственными партиями
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">
            Всего: {data?.total || 0}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по номеру, рецепту, камере..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
          >
            <option value="all">Все статусы</option>
            <option value="planned">Запланированы</option>
            <option value="running">В работе</option>
            <option value="completed">Завершены</option>
            <option value="cancelled">Отменены</option>
          </select>
        </div>
      </div>

      {/* Batch list */}
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <EmptyState />
        ) : (
          filtered.map((batch, i) => (
            <BatchCard key={batch.id} batch={batch} index={i} />
          ))
        )}
      </div>
    </div>
  );
}

function BatchCard({ batch, index }: { batch: Batch; index: number }) {
  const config = statusConfig[batch.status] || statusConfig.planned;
  const StatusIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/[0.03] transition-colors"
    >
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="flex items-center gap-4">
          <div className={`flex h-10 w-10 items-center justify-center rounded-lg ${config.bg}`}>
            <StatusIcon className={`h-5 w-5 ${config.color}`} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-medium text-white">{batch.batch_number}</h3>
              <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs ${config.bg} ${config.color}`}>
                {config.label}
              </span>
            </div>
            <p className="text-sm text-muted-foreground">
              {batch.recipe_name || "—"} · {batch.chamber_name || "—"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 text-sm">
          <div className="text-right">
            <div className="text-white">{batch.product_weight_kg ? `${batch.product_weight_kg} кг` : "—"}</div>
            <div className="text-xs text-muted-foreground">Загрузка</div>
          </div>
          {batch.yield_kg && (
            <div className="text-right">
              <div className="text-white">{batch.yield_kg} кг</div>
              <div className="text-xs text-muted-foreground">Выход</div>
            </div>
          )}
          {batch.losses_percent && (
            <div className="text-right">
              <div className="text-white">{batch.losses_percent}%</div>
              <div className="text-xs text-muted-foreground">Потери</div>
            </div>
          )}
          <div className="text-right hidden sm:block">
            <div className="text-white">{batch.operator_name || "—"}</div>
            <div className="text-xs text-muted-foreground">Оператор</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
      <Package className="h-12 w-12 text-muted-foreground/30" />
      <p className="mt-4 text-muted-foreground">Партии не найдены</p>
      <p className="text-sm text-muted-foreground/60">Измените фильтры или создайте новую партию</p>
    </div>
  );
}

function BatchesSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="h-10 animate-pulse rounded-xl bg-white/5" />
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
