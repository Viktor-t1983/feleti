"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Trash2,
  GripVertical,
  Clock,
  Thermometer,
  Droplets,
  Zap,
  Save,
  Copy,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import type { ProgramPhase } from "@/lib/types/chamber";
import { PHASE_LABELS } from "@/lib/types/chamber";

const PHASE_OPTIONS = Object.entries(PHASE_LABELS).filter(([k]) => k !== "idle");

const CONDITION_LABELS: Record<string, string> = {
  time: "По времени",
  core_temp: "По температуре продукта",
  combined: "Комбинированное",
};

function createPhase(name = "drying", index = 0): ProgramPhase {
  return {
    id: `phase-${Date.now()}-${index}`,
    name,
    temperature: 60,
    time_minutes: 30,
    humidity: 0,
    smoke_density: 0,
    condition: "time",
    condition_value: 30,
  };
}

const DEFAULT_PHASES = [
  { name: "preheat", temp: 50, time: 20 },
  { name: "drying", temp: 50, time: 30 },
  { name: "smoking", temp: 75, time: 60 },
  { name: "cooking", temp: 82, time: 45 },
];

export function HmiProgramEditor() {
  const [phases, setPhases] = useState<ProgramPhase[]>(
    DEFAULT_PHASES.map((p, i) => ({
      ...createPhase(p.name, i),
      temperature: p.temp,
      time_minutes: p.time,
    }))
  );
  const [programName, setProgramName] = useState("Новая программа");

  const addPhase = () => {
    setPhases((prev) => [...prev, createPhase("drying", prev.length)]);
  };

  const removePhase = (id: string) => {
    setPhases((prev) => prev.filter((p) => p.id !== id));
  };

  const updatePhase = (id: string, field: keyof ProgramPhase, value: string | number) => {
    setPhases((prev) =>
      prev.map((p) => (p.id === id ? { ...p, [field]: value } : p))
    );
  };

  const movePhase = (index: number, direction: -1 | 1) => {
    const newIndex = index + direction;
    if (newIndex < 0 || newIndex >= phases.length) return;
    setPhases((prev) => {
      const copy = [...prev];
      [copy[index], copy[newIndex]] = [copy[newIndex], copy[index]];
      return copy;
    });
  };

  const duplicatePhase = (id: string) => {
    const phase = phases.find((p) => p.id === id);
    if (!phase) return;
    setPhases((prev) => {
      const index = prev.findIndex((p) => p.id === id);
      const copy = [...prev];
      copy.splice(index + 1, 0, {
        ...phase,
        id: `phase-${Date.now()}`,
        name: phase.name,
      });
      return copy;
    });
  };

  const totalTime = phases.reduce((acc, p) => acc + p.time_minutes, 0);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-5"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center gap-4">
          <input
            value={programName}
            onChange={(e) => setProgramName(e.target.value)}
            className="bg-transparent text-lg font-bold text-white border-b border-white/10 pb-1 focus:outline-none focus:border-feleti-gold transition-colors w-64"
          />
          <span className="text-xs text-muted-foreground">
            {totalTime} мин · {phases.length} фаз
          </span>
        </div>
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold/10 border border-feleti-gold/20 px-4 py-2 text-sm font-medium text-feleti-gold hover:bg-feleti-gold/20 transition-colors"
        >
          <Save className="h-4 w-4" />
          Сохранить программу
        </motion.button>
      </div>

      {/* Timeline bar */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
        <div className="flex h-8 rounded-lg overflow-hidden">
          {phases.map((phase, i) => {
            const width = totalTime > 0 ? (phase.time_minutes / totalTime) * 100 : 0;
            return (
              <motion.div
                key={phase.id}
                initial={{ width: 0 }}
                animate={{ width: `${width}%` }}
                className="flex items-center justify-center text-[10px] font-medium text-white/70 first:rounded-l-lg last:rounded-r-lg"
                style={{
                  backgroundColor: `hsl(${i * 40 + 20}, 60%, 35%)`,
                }}
                title={`${PHASE_LABELS[phase.name] || phase.name}: ${phase.time_minutes} мин @ ${phase.temperature}°C`}
              >
                {width > 10 && `${PHASE_LABELS[phase.name]?.[0] || phase.name[0]}${i + 1}`}
              </motion.div>
            );
          })}
        </div>
        <div className="flex justify-between mt-2 text-[10px] text-muted-foreground">
          <span>0 мин</span>
          <span>{totalTime} мин</span>
        </div>
      </div>

      {/* Phase list */}
      <div className="space-y-2">
        <AnimatePresence>
          {phases.map((phase, index) => (
            <motion.div
              key={phase.id}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20, height: 0 }}
              className="group rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:border-white/10 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-center gap-4">
                <div className="flex items-center gap-3 sm:w-48 shrink-0">
                  <GripVertical className="h-4 w-4 text-muted-foreground/30 cursor-grab" />
                  <span className="text-xs text-muted-foreground/60 w-6">#{index + 1}</span>
                  <select
                    value={phase.name}
                    onChange={(e) => updatePhase(phase.id, "name", e.target.value)}
                    className="bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2.5 py-1.5 focus:outline-none focus:border-feleti-gold w-full"
                  >
                    {PHASE_OPTIONS.map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-1 flex-wrap items-center gap-3">
                  <div className="flex items-center gap-1.5">
                    <Thermometer className="h-3.5 w-3.5 text-orange-400" />
                    <input
                      type="number"
                      value={phase.temperature}
                      onChange={(e) => updatePhase(phase.id, "temperature", Number(e.target.value))}
                      className="w-16 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                    />
                    <span className="text-[10px] text-muted-foreground">°C</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Clock className="h-3.5 w-3.5 text-cyan-400" />
                    <input
                      type="number"
                      value={phase.time_minutes}
                      onChange={(e) => updatePhase(phase.id, "time_minutes", Number(e.target.value))}
                      className="w-16 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                    />
                    <span className="text-[10px] text-muted-foreground">мин</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Droplets className="h-3.5 w-3.5 text-blue-400" />
                    <input
                      type="number"
                      value={phase.humidity}
                      onChange={(e) => updatePhase(phase.id, "humidity", Number(e.target.value))}
                      className="w-14 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                    />
                    <span className="text-[10px] text-muted-foreground">%RH</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Zap className="h-3.5 w-3.5 text-purple-400" />
                    <input
                      type="number"
                      value={phase.smoke_density}
                      onChange={(e) => updatePhase(phase.id, "smoke_density", Number(e.target.value))}
                      className="w-14 bg-white/5 text-sm text-white rounded-lg border border-white/10 px-2 py-1.5 text-center focus:outline-none focus:border-feleti-gold"
                    />
                    <span className="text-[10px] text-muted-foreground">дым</span>
                  </div>
                  <select
                    value={phase.condition}
                    onChange={(e) => updatePhase(phase.id, "condition", e.target.value)}
                    className="bg-white/5 text-[10px] text-white/70 rounded-lg border border-white/10 px-2 py-1.5 focus:outline-none focus:border-feleti-gold"
                  >
                    {Object.entries(CONDITION_LABELS).map(([key, label]) => (
                      <option key={key} value={key}>{label}</option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => movePhase(index, -1)}
                    disabled={index === 0}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-white disabled:opacity-20"
                  >
                    <ArrowUp className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => movePhase(index, 1)}
                    disabled={index === phases.length - 1}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-white disabled:opacity-20"
                  >
                    <ArrowDown className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => duplicatePhase(phase.id)}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-feleti-gold"
                  >
                    <Copy className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => removePhase(phase.id)}
                    className="p-1.5 rounded-lg hover:bg-white/5 text-muted-foreground hover:text-red-400"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Add phase button */}
      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        onClick={addPhase}
        className="w-full rounded-xl border-2 border-dashed border-white/10 py-4 text-sm text-muted-foreground hover:border-feleti-gold/30 hover:text-feleti-gold transition-colors flex items-center justify-center gap-2"
      >
        <Plus className="h-4 w-4" />
        Добавить фазу
      </motion.button>
    </motion.div>
  );
}
