"use client";

import { motion } from "framer-motion";
import { Flame, Fan, Zap, Droplets, DoorOpen } from "lucide-react";

interface StatusIndicatorsProps {
  heatingOn: boolean;
  fanRpm: number;
  smokeActive: boolean;
  steamActive: boolean;
  doorOpen: boolean;
  damperPosition: number;
}

export function StatusIndicators({
  heatingOn,
  fanRpm,
  smokeActive,
  steamActive,
  doorOpen,
  damperPosition,
}: StatusIndicatorsProps) {
  const indicators = [
    {
      label: "ТЭН",
      icon: Flame,
      active: heatingOn,
      color: "text-orange-400",
      bg: "bg-orange-500/10",
      activeBg: "bg-orange-500/20",
      value: heatingOn ? "Нагрев" : "Ожидание",
    },
    {
      label: "Вентилятор",
      icon: Fan,
      active: fanRpm > 0,
      color: "text-cyan-400",
      bg: "bg-cyan-500/10",
      activeBg: "bg-cyan-500/20",
      value: `${fanRpm} об/мин`,
    },
    {
      label: "Дым",
      icon: Zap,
      active: smokeActive,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      activeBg: "bg-purple-500/20",
      value: smokeActive ? "Генерация" : "Выкл",
    },
    {
      label: "Пар",
      icon: Droplets,
      active: steamActive,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      activeBg: "bg-blue-500/20",
      value: steamActive ? "Увлажнение" : "Выкл",
    },
    {
      label: "Заслонка",
      icon: DoorOpen,
      active: damperPosition > 0,
      color: "text-amber-400",
      bg: "bg-amber-500/10",
      activeBg: "bg-amber-500/20",
      value: `${damperPosition}%`,
    },
  ];

  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
      <h3 className="text-sm font-medium text-white mb-4">Оборудование</h3>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {indicators.map((ind, i) => (
          <motion.div
            key={ind.label}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className={`flex flex-col items-center gap-2 rounded-xl border p-3 transition-colors ${
              ind.active
                ? `${ind.activeBg} border-white/10`
                : "bg-white/[0.02] border-white/5"
            }`}
          >
            <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${ind.active ? ind.activeBg : ind.bg}`}>
              <ind.icon className={`h-4 w-4 ${ind.active ? ind.color : "text-muted-foreground"}`} />
            </div>
            <span className={`text-[10px] font-medium ${ind.active ? "text-white" : "text-muted-foreground"}`}>
              {ind.label}
            </span>
            <span className={`text-[10px] ${ind.active ? ind.color : "text-muted-foreground/60"}`}>
              {ind.value}
            </span>
          </motion.div>
        ))}
      </div>

      {doorOpen && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="mt-3 flex items-center gap-2 rounded-lg bg-red-500/10 px-3 py-2"
        >
          <DoorOpen className="h-4 w-4 text-red-400" />
          <span className="text-xs text-red-400">Дверь камеры открыта!</span>
        </motion.div>
      )}
    </div>
  );
}
