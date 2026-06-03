"use client";

import { motion } from "framer-motion";
import { Thermometer } from "lucide-react";

interface TemperatureGaugeProps {
  label: string;
  value: number;
  setpoint: number;
  unit?: string;
  color?: string;
  bg?: string;
  icon?: React.ElementType;
  size?: "sm" | "lg";
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
}: TemperatureGaugeProps) {
  const percent = setpoint > 0 ? Math.min((value / setpoint) * 100, 120) : 0;
  const isOvershoot = value > setpoint * 1.05 && setpoint > 0;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="relative overflow-hidden rounded-2xl border border-white/5 bg-white/[0.02] p-5"
    >
      <div className="flex items-center justify-between mb-3">
        <div className={`flex items-center gap-2 rounded-lg ${bg} px-2.5 py-1.5`}>
          <Icon className={`h-4 w-4 ${color}`} />
          <span className="text-xs font-medium text-muted-foreground">{label}</span>
        </div>
        {setpoint > 0 && (
          <span className="text-xs text-muted-foreground/60">
            цель {setpoint}{unit}
          </span>
        )}
      </div>

      <div className={`font-bold tracking-tight ${size === "lg" ? "text-5xl" : "text-3xl"} text-white`}>
        {value.toFixed(1)}
        <span className={`${size === "lg" ? "text-2xl" : "text-lg"} text-muted-foreground ml-1`}>{unit}</span>
      </div>

      <div className="mt-3 h-1.5 rounded-full bg-white/5 overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${isOvershoot ? "bg-red-500" : "bg-feleti-gold"}`}
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(percent, 100)}%` }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        />
      </div>

      {isOvershoot && (
        <motion.p
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-1.5 text-xs text-red-400"
        >
          Превышение!
        </motion.p>
      )}
    </motion.div>
  );
}
