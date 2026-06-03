"use client";

import { motion } from "framer-motion";
import { Timer, Zap, DoorOpen } from "lucide-react";
import { PHASE_LABELS, PHASE_COLORS } from "@/lib/types/chamber";

interface PhaseProgressProps {
  phaseKey: string;
  progress: number;
  elapsedSeconds: number;
  smokeDensity: number;
  doorOpen: boolean;
  totalPhases?: number;
  currentPhaseIndex?: number;
}

export function PhaseProgress({
  phaseKey,
  progress,
  elapsedSeconds,
  smokeDensity,
  doorOpen,
  totalPhases = 4,
  currentPhaseIndex = 1,
}: PhaseProgressProps) {
  const phaseName = PHASE_LABELS[phaseKey] || phaseKey;
  const phaseColor = PHASE_COLORS[phaseKey] || "#c9a96e";

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span
              className="h-3 w-3 rounded-full"
              style={{ backgroundColor: phaseColor }}
            />
            <h3 className="text-sm font-medium text-white">
              Фаза {currentPhaseIndex}/{totalPhases}: {phaseName}
            </h3>
          </div>
          <span className="rounded-md bg-feleti-gold/10 px-2 py-0.5 text-xs font-medium text-feleti-gold">
            {Math.round(progress)}%
          </span>
        </div>
      </div>

      <div className="h-3 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{
            background: `linear-gradient(90deg, ${phaseColor}88, ${phaseColor})`,
          }}
          initial={{ width: 0 }}
          animate={{ width: `${Math.max(progress, 2)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <Timer className="h-3.5 w-3.5" />
          Прошло: <span className="text-white/70 font-mono">{formatTime(elapsedSeconds)}</span>
        </span>
        <span className="flex items-center gap-1.5">
          <Zap className="h-3.5 w-3.5" />
          Дым: <span className="text-white/70">{smokeDensity}%</span>
        </span>
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
