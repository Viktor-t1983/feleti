"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Package,
  ArrowLeft,
  Play,
  Pause,
  Square,
  CheckCircle2,
  Clock,
  Thermometer,
  Droplets,
  User,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useParams } from "next/navigation";

type BatchStatus = "PLANNED" | "QUEUED" | "RUNNING" | "PAUSED" | "COMPLETED" | "CANCELLED" | "FAILED";

interface BatchPhase {
  id: number;
  phase_index: number;
  name: string;
  planned_duration_min: number | null;
  actual_duration_min: number | null;
  actual_start: string | null;
  actual_end: string | null;
  set_t_chamber: number | null;
  set_humidity: number | null;
  set_smoke: string | null;
  avg_t_chamber: number | null;
  avg_t_product: number | null;
  avg_humidity: number | null;
  notes: string | null;
}

interface BatchDetail {
  id: number;
  batch_number: string;
  status: BatchStatus;
  chamber_id: number;
  chamber_name: string | null;
  recipe_version_id: number;
  recipe_name: string | null;
  operator_name: string | null;
  product_weight_kg: number | null;
  yield_kg: number | null;
  losses_percent: number | null;
  planned_start: string | null;
  actual_start: string | null;
  actual_end: string | null;
  notes: string | null;
  errors: string[];
  phases: BatchPhase[];
  created_at: string;
  updated_at: string;
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

function formatDateTime(s: string | null): string {
  if (!s) return "—";
  return new Date(s).toLocaleString("ru-RU", {
    day: "numeric", month: "short", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function formatDuration(min: number | null): string {
  if (min == null) return "—";
  if (min < 60) return `${min} мин`;
  const h = Math.floor(min / 60);
  const m = min % 60;
  return `${h}ч ${m}м`;
}

export default function BatchDetailPage() {
  const params = useParams();
  const batchId = params.id as string;
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: batch, isLoading } = useQuery({
    queryKey: ["batch", batchId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/batches/${batchId}`);
      return data as BatchDetail;
    },
    refetchInterval: 15000,
  });

  const performAction = async (action: string) => {
    setActionLoading(action);
    try {
      await apiClient.post(`/batches/${batchId}/${action}`);
      await queryClient.invalidateQueries({ queryKey: ["batch", batchId] });
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
    } finally {
      setActionLoading(null);
    }
  };

  if (isLoading) return <BatchDetailSkeleton />;
  if (!batch) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Партия не найдена</p>
        <Link href="/batches" className="mt-4 text-sm text-feleti-gold hover:underline">Вернуться к списку</Link>
      </div>
    );
  }

  const cfg = STATUS_CONFIG[batch.status];

  const canStart = batch.status === "PLANNED" || batch.status === "PAUSED";
  const canPause = batch.status === "RUNNING";
  const canStop = batch.status === "RUNNING" || batch.status === "PAUSED";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/batches"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к партиям
        </Link>
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className={`flex h-12 w-12 items-center justify-center rounded-xl ${cfg.bg}`}>
              <Package className={`h-6 w-6 ${cfg.color}`} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">{batch.batch_number}</h1>
              <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium mt-1 ${cfg.color} ${cfg.bg} ${cfg.border}`}>
                {cfg.label}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Errors */}
      {batch.errors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-red-500/20 bg-red-500/10 p-4"
        >
          <h3 className="text-sm font-medium text-red-400 mb-2 flex items-center gap-2">
            <AlertTriangle className="h-4 w-4" /> Ошибки
          </h3>
          {batch.errors.map((e, i) => (
            <p key={i} className="text-sm text-red-400/80 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400 shrink-0" /> {e}
            </p>
          ))}
        </motion.div>
      )}

      {/* Info grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <InfoCard icon={FileText} label="Рецепт" value={batch.recipe_name || "—"} />
        <InfoCard icon={Thermometer} label="Камера" value={batch.chamber_name || "—"} href={`/chambers/${batch.chamber_id}`} />
        <InfoCard icon={User} label="Оператор" value={batch.operator_name || "—"} />
        <InfoCard icon={Clock} label="Создана" value={formatDateTime(batch.created_at)} />
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <InfoCard icon={Package} label="Вес продукта" value={batch.product_weight_kg ? `${batch.product_weight_kg} кг` : "—"} />
        {batch.yield_kg != null && <InfoCard icon={CheckCircle2} label="Выход" value={`${batch.yield_kg} кг`} />}
        {batch.losses_percent != null && <InfoCard icon={Droplets} label="Потери" value={`${batch.losses_percent}%`} />}
        <InfoCard icon={Clock} label="Старт" value={formatDateTime(batch.actual_start || batch.planned_start)} />
        {batch.actual_end && <InfoCard icon={CheckCircle2} label="Завершена" value={formatDateTime(batch.actual_end)} />}
      </div>

      {/* Control buttons */}
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
        <h3 className="text-sm font-medium text-white mb-4">Управление</h3>
        <div className="flex flex-wrap gap-3">
          {canStart && (
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => performAction("start")}
              disabled={actionLoading !== null}
              className="inline-flex items-center gap-2 rounded-xl border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
            >
              {actionLoading === "start" ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-400 border-t-transparent" /> : <Play className="h-4 w-4" />}
              Старт
            </motion.button>
          )}
          {canPause && (
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={() => performAction("pause")}
              disabled={actionLoading !== null}
              className="inline-flex items-center gap-2 rounded-xl border bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
            >
              <Pause className="h-4 w-4" /> Пауза
            </motion.button>
          )}
          {canStop && (
            <>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => performAction(batch.status === "PAUSED" ? "cancel" : "complete")}
                disabled={actionLoading !== null}
                className="inline-flex items-center gap-2 rounded-xl border bg-blue-500/10 text-blue-400 border-blue-500/20 hover:bg-blue-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
              >
                <CheckCircle2 className="h-4 w-4" /> Завершить
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => performAction("cancel")}
                disabled={actionLoading !== null}
                className="inline-flex items-center gap-2 rounded-xl border bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
              >
                <Square className="h-4 w-4" /> Отменить
              </motion.button>
            </>
          )}
        </div>
      </div>

      {/* Phases */}
      {batch.phases.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <h3 className="text-sm font-medium text-white mb-4">Фазы программы</h3>
          <div className="overflow-hidden rounded-xl border border-white/5">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">№</th>
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Фаза</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">T камеры</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Влажность</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Длит.</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Факт</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Ср. T</th>
                </tr>
              </thead>
              <tbody>
                {batch.phases.map((p, i) => (
                  <tr key={p.id} className="border-b border-white/5 hover:bg-white/[0.02]">
                    <td className="px-4 py-3 text-muted-foreground">{i + 1}</td>
                    <td className="px-4 py-3 text-white">{p.name}</td>
                    <td className="px-4 py-3 text-right text-white">{p.set_t_chamber != null ? `${p.set_t_chamber}°C` : "—"}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground">{p.set_humidity != null ? `${p.set_humidity}%` : "—"}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground">{formatDuration(p.planned_duration_min)}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground">{formatDuration(p.actual_duration_min)}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground">{p.avg_t_chamber != null ? `${p.avg_t_chamber.toFixed(1)}°C` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Notes */}
      {batch.notes && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-white/5 bg-white/[0.02] p-4"
        >
          <h3 className="text-sm font-medium text-white mb-2">Примечания</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">{batch.notes}</p>
        </motion.div>
      )}
    </div>
  );
}

function InfoCard({ icon: Icon, label, value, href }: {
  icon: React.ElementType; label: string; value: string; href?: string;
}) {
  const content = (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4 text-feleti-gold" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-sm font-medium text-white truncate">{value}</div>
    </div>
  );
  if (href) {
    return <Link href={href}>{content}</Link>;
  }
  return content;
}

function BatchDetailSkeleton() {
  return (
    <div className="space-y-8">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-white/5" />
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
