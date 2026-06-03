"use client";

import { motion } from "framer-motion";
import { Thermometer, AlertTriangle } from "lucide-react";

interface TemperatureGaugeProps {
  label: string;
  value: number;
  setpoint: number;
  unit?: string;
  color?: string;
  bg?: string;
  icon?: React.ElementType;
  size?: "sm" | "lg";
  alarmHigh?: number;
  alarmLow?: number;
}

export function TemperatureGauge({
  label,
  value,
  setpoint,
  unit = "°C",
  color = "text-orange-400",
  bg = "bg-orange-500/10",
  icon: Icon = Thermometer,
  size = "sm",
  alarmHigh,
  alarmLow,
}: TemperatureGaugeProps) {
  const percent = setpoint > 0 ? Math.min((value / setpoint) * 100, 120) : 0;
  const isOvershoot = value > setpoint * 1.05 && setpoint > 0;
  const isAlarmHigh = alarmHigh != null && value > alarmHigh;
  const isAlarmLow = alarmLow != null && value < alarmLow;
  const isAlarm = isAlarmHigh || isAlarmLow || isOvershoot;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className={`relative overflow-hidden rounded-2xl border p-5 transition-colors ${
        isAlarm
          ? "border-red-500/40 bg-red-500/[0.04]"
          : "border-white/5 bg-white/[0.02]"
      }`}
    >
      {/* Alarm glow */}
      {isAlarm && (
        <motion.div
          className="absolute inset-0 rounded-2xl pointer-events-none"
          animate={{
            boxShadow: [
              "inset 0 0 0px rgba(239,68,68,0)",
              "inset 0 0 40px rgba(239,68,68,0.15)",
              "inset 0 0 0px rgba(239,68,68,0)",
            ],
          }}
          transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
        />
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-3 relative z-10">
        <div className={`flex items-center gap-2 rounded-lg ${isAlarm ? "bg-red-500/10" : bg} px-2.5 py-1.5`}>
          <Icon className={`h-4 w-4 ${isAlarm ? "text-red-400" : color}`} />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        {setpoint > 0 && (
          <span className="text-xs text-muted-foreground/60">
            цель {setpoint}{unit}
          </span>
        )}
      </div>

      {/* Value */}
      <div className={`font-bold tracking-tight ${size === "lg" ? "text-5xl" : "text-3xl"} ${isAlarm ? "text-red-400" : "text-white"} relative z-10`}>
        {value.toFixed(1)}
        <span className={`${size === "lg" ? "text-2xl" : "text-lg"} text-muted-foreground ml-1`}>{unit}</span>
      </div>

      {/* Progress bar */}
      <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden relative z-10">
        <motion.div
          className={`h-full rounded-full ${isAlarm ? "bg-red-500" : "bg-feleti-gold"}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percent, 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>

      {/* Alarm text */}
      {isAlarm && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 flex items-center gap-1.5 relative z-10"
        >
          <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
          <span className="text-xs text-red-400">
            {isAlarmHigh
              ? `Превышение! Макс. ${alarmHigh}${unit}`
              : isAlarmLow
              ? `Ниже минимума! Мин. ${alarmLow}${unit}`
              : "Превышение!"}
          </span>
        </motion.div>
      )}
    </motion.div>
  );
}
