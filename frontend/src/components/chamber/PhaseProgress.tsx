"use client";

import { motion } from "framer-motion";
import { Timer, Zap, DoorOpen } from "lucide-react";

interface PhaseInfo {
  name: string;
  duration_min: number;
  key?: string;
}

interface PhaseProgressProps {
  phaseKey: string;
  progress: number;
  elapsedSeconds: number;
  smokeDensity: number;
  doorOpen: boolean;
  totalPhases?: number;
  currentPhaseIndex?: number;
  phases?: PhaseInfo[];
  phaseElapsed?: number;
}

export function PhaseProgress({
  phaseKey,
  progress,
  elapsedSeconds,
  smokeDensity,
  doorOpen,
  currentPhaseIndex = 0,
  phases,
  phaseElapsed,
}: PhaseProgressProps) {
  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const totalPhases = phases?.length || 0;
  const isIdle = phaseKey === "idle" || phaseKey === "completed";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
    >
      {/* Phase sequence timeline */}
      {phases && phases.length > 0 && (
        <div className="mb-5">
          <div className="flex items-center gap-1 mb-2">
            {phases.map((p, i) => {
              const isDone = i < currentPhaseIndex;
              const isCurrent = i === currentPhaseIndex;
              const isNext = i > currentPhaseIndex;
              return (
                <div key={i} className="flex-1 flex flex-col items-center gap-1">
                  <div className="flex items-center w-full">
                    <div
                      className={`h-1.5 flex-1 rounded-full transition-colors ${
                        i === 0 ? "" : "ml-0.5"
                      } ${
                        isDone
                          ? "bg-emerald-500/60"
                          : isCurrent
                          ? "bg-feleti-gold"
                          : "bg-white/10"
                      }`}
                    />
                    {i === currentPhaseIndex && (
                      <motion.div
                        layoutId="phase-dot"
                        className="h-3 w-3 rounded-full bg-feleti-gold border-2 border-black shrink-0 mx-0.5"
                      />
                    )}
                    {i !== currentPhaseIndex && (
                      <div
                        className={`h-2.5 w-2.5 rounded-full shrink-0 mx-0.5 ${
                          isDone ? "bg-emerald-500/60" : "bg-white/10"
                        }`}
                      />
                    )}
                    <div
                      className={`h-1.5 flex-1 rounded-full transition-colors ${
                        i === phases.length - 1 ? "" : "mr-0.5"
                      } ${
                        isDone
                          ? "bg-emerald-500/60"
                          : isNext
                          ? "bg-white/10"
                          : ""
                      }`}
                    />
                  </div>
                  <span
                    className={`text-[10px] ${
                      isCurrent
                        ? "text-feleti-gold font-medium"
                        : isDone
                        ? "text-emerald-400/60"
                        : "text-muted-foreground/40"
                    } truncate max-w-[80px] text-center`}
                  >
                    {p.name}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Current phase info */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-medium text-white">
              {isIdle
                ? phaseKey === "completed"
                  ? "Партия завершена"
                  : "Ожидание"
                : `Фаза ${currentPhaseIndex + 1}/${totalPhases || "—"}: ${phases?.[currentPhaseIndex]?.name || phaseKey}`}
            </h3>
          </div>
          {!isIdle && (
            <span className="rounded-md bg-feleti-gold/10 px-2 py-0.5 text-xs font-medium text-feleti-gold">
              {Math.round(progress)}%
            </span>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {!isIdle && (
        <div className="h-3 rounded-full bg-white/5 overflow-hidden">
          <motion.div
            className="h-full rounded-full"
            style={{
              background: `linear-gradient(90deg, #c9a96e88, #c9a96e)`,
            }}
            initial={{ width: 0 }}
            animate={{ width: `${Math.max(progress, 2)}%` }}
            transition={{ duration: 0.8, ease: "easeOut" }}
          />
        </div>
      )}

      {/* Stats row */}
      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <Timer className="h-3.5 w-3.5" />
          Прошло: <span className="text-white/70 font-mono">{formatTime(elapsedSeconds)}</span>
        </span>
        {phaseElapsed != null && phases?.[currentPhaseIndex]?.duration_min && !isIdle && (
          <span className="flex items-center gap-1.5">
            <Timer className="h-3.5 w-3.5" />
            Осталось:{" "}
            <span className="text-white/70 font-mono">
              {formatTime(
                Math.max(0, phases[currentPhaseIndex].duration_min * 60 - phaseElapsed)
              )}
            </span>
          </span>
        )}
        {!isIdle && (
          <span className="flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5" />
            Дым: <span className="text-white/70">{smokeDensity}%</span>
          </span>
        )}
        {doorOpen && (
          <motion.span
            initial={{ opacity: 0, x: -5 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-1.5 text-amber-400"
          >
            <DoorOpen className="h-3.5 w-3.5 animate-pulse" />
            Дверь открыта
          </motion.span>
        )}
      </div>
    </motion.div>
  );
}
