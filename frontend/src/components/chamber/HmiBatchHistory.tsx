"use client";

import { motion } from "framer-motion";
import { Clock, Thermometer, ChefHat, Weight, CheckCircle2, XCircle } from "lucide-react";

interface BatchItem {
  id: number;
  batch_number: string;
  product_name: string;
  weight_kg: number;
  started_at: string;
  finished_at: string | null;
  status: string;
  temperature_avg: number;
  yield_percent: number;
}

const MOCK_BATCHES: BatchItem[] = [
  {
    id: 1,
    batch_number: "B-2026-015",
    product_name: "Куриное филе г/к",
    weight_kg: 50,
    started_at: "2026-06-03 08:00",
    finished_at: "2026-06-03 11:30",
    status: "completed",
    temperature_avg: 74.2,
    yield_percent: 68,
  },
  {
    id: 2,
    batch_number: "B-2026-014",
    product_name: "Скумбрия х/к",
    weight_kg: 80,
    started_at: "2026-06-02 22:00",
    finished_at: "2026-06-03 06:00",
    status: "completed",
    temperature_avg: 22.5,
    yield_percent: 88,
  },
  {
    id: 3,
    batch_number: "B-2026-013",
    product_name: "Свиная шея",
    weight_kg: 40,
    started_at: "2026-06-02 14:00",
    finished_at: "2026-06-02 18:45",
    status: "completed",
    temperature_avg: 78.1,
    yield_percent: 64,
  },
  {
    id: 4,
    batch_number: "B-2026-012",
    product_name: "Сёмга х/к",
    weight_kg: 25,
    started_at: "2026-06-02 06:00",
    finished_at: "2026-06-02 12:00",
    status: "completed",
    temperature_avg: 24.0,
    yield_percent: 92,
  },
  {
    id: 5,
    batch_number: "B-2026-011",
    product_name: "Колбаски охотничьи",
    weight_kg: 30,
    started_at: "2026-06-01 16:00",
    finished_at: "2026-06-01 19:20",
    status: "completed",
    temperature_avg: 72.8,
    yield_percent: 72,
  },
];

const STATUS_COLORS: Record<string, string> = {
  completed: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  running: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  cancelled: "text-red-400 bg-red-500/10 border-red-500/20",
  planned: "text-slate-400 bg-slate-500/10 border-slate-500/20",
};

function formatTime(dateStr: string) {
  try {
    const d = new Date(dateStr);
    return d.toLocaleString("ru", {
      day: "numeric",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dateStr;
  }
}

export function HmiBatchHistory() {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-4"
    >
      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="text-2xl font-bold text-white">{MOCK_BATCHES.length}</div>
          <div className="text-xs text-muted-foreground mt-1">Всего партий</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="text-2xl font-bold text-white">
            {MOCK_BATCHES.reduce((s, b) => s + b.weight_kg, 0)}
          </div>
          <div className="text-xs text-muted-foreground mt-1">Всего кг</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="text-2xl font-bold text-blue-400">
            {(MOCK_BATCHES.reduce((s, b) => s + (b.yield_percent || 0), 0) / MOCK_BATCHES.length).toFixed(0)}%
          </div>
          <div className="text-xs text-muted-foreground mt-1">Средний выход</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="text-2xl font-bold text-orange-400">
            {MOCK_BATCHES.reduce((s, b) => s + b.temperature_avg, 0) / MOCK_BATCHES.length | 0}°C
          </div>
          <div className="text-xs text-muted-foreground mt-1">Средняя T</div>
        </div>
      </div>

      {/* Batch list */}
      <div className="space-y-2">
        {MOCK_BATCHES.map((batch, i) => (
          <motion.div
            key={batch.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-white/10 transition-colors cursor-pointer"
          >
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-feleti-gold/10">
                  <CheckCircle2 className="h-5 w-5 text-feleti-gold" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white">{batch.batch_number}</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] border ${STATUS_COLORS[batch.status] || STATUS_COLORS.planned}`}>
                      {batch.status === "completed" ? "Завершена" : batch.status}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1">
                      <ChefHat className="h-3 w-3" />
                      {batch.product_name}
                    </span>
                    <span className="flex items-center gap-1">
                      <Weight className="h-3 w-3" />
                      {batch.weight_kg} кг
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-6 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Thermometer className="h-3 w-3 text-orange-400" />
                  <span className="text-white/70">{batch.temperature_avg}°C</span>
                </span>
                <span>
                  Выход: <span className="text-feleti-gold">{batch.yield_percent}%</span>
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatTime(batch.started_at)}
                </span>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
