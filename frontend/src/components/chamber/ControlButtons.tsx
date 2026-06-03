"use client";

import { motion } from "framer-motion";
import { Play, Pause, Square, Loader2 } from "lucide-react";

interface ControlButtonsProps {
  status: "idle" | "running" | "paused" | "completed" | "error";
  onStart?: () => void;
  onPause?: () => void;
  onResume?: () => void;
  onStop?: () => void;
  loading?: boolean;
}

export function ControlButtons({
  status,
  onStart,
  onPause,
  onResume,
  onStop,
  loading = false,
}: ControlButtonsProps) {
  const isRunning = status === "running";
  const isPaused = status === "paused";
  const isIdle = status === "idle";
  const isFinished = status === "completed" || status === "error";

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
      <h3 className="text-sm font-medium text-white mb-4">Управление</h3>
      <div className="flex flex-wrap gap-3">
        {isIdle && (
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onStart}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-xl border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            Старт
          </motion.button>
        )}

        {isRunning && (
          <>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onPause}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer"
            >
              <Pause className="h-4 w-4" />
              Пауза
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onStop}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Square className="h-4 w-4" />
              )}
              Стоп
            </motion.button>
          </>
        )}

        {isPaused && (
          <>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onResume}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer"
            >
              <Play className="h-4 w-4" />
              Продолжить
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              onClick={onStop}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-xl border bg-red-500/10 text-red-400 border-red-500/20 hover:bg-red-500/20 px-6 py-3 text-sm font-medium transition-all cursor-pointer"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Square className="h-4 w-4" />
              )}
              Стоп
            </motion.button>
          </>
        )}

        {isFinished && (
          <span className="inline-flex items-center gap-1.5 rounded-xl bg-blue-500/10 px-4 py-3 text-xs text-blue-400 border border-blue-500/20">
            {status === "completed" ? "Партия завершена" : "Завершено с ошибкой"}
          </span>
        )}

        {isIdle && !loading && (
          <span className="inline-flex items-center text-xs text-muted-foreground/60 ml-2">
            Ожидание команды
          </span>
        )}
      </div>
    </div>
  );
}
