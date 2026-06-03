"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Trophy, AlertTriangle } from "lucide-react";
import { CompetitorDetails } from "./CompetitorDetails";

export interface Competitor {
  id: string;
  name: string;
  slug: string;
  country: string;
  foundedYear?: number;
  segment: string;
  isMainCompetitor: boolean;
  clientCount?: number;
  recipeCount?: number;
  warrantyYears?: number;
  hasCloud: boolean | null;
  hasMobileApp: boolean | null;
  hasRemoteMonitoring: boolean | null;
  hasVideoCamera: boolean | null;
  description: string;
  strengths: string[];
  weaknesses: string[];
  models: CompetitorModel[];
  problems: CompetitorProblem[];
}

export interface CompetitorModel {
  id?: number;
  name: string;
  max_load_kg?: number;
  power_kw?: number;
  voltage_v?: number;
  weight_kg?: number;
  dimensions?: string;
  modes?: string[];
  automation_level?: string;
  price_rub?: number;
}

export interface CompetitorProblem {
  title: string;
  description: string;
  severity: "low" | "medium" | "high";
  frequency: string;
  source: string;
}

interface CompetitorCardProps {
  competitor: Competitor;
}

export function CompetitorCard({ competitor }: CompetitorCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <motion.div
      layout
      className={`relative overflow-hidden rounded-2xl border transition-colors duration-300 ${
        competitor.isMainCompetitor
          ? "border-feleti-gold/30 bg-feleti-gold/[0.03]"
          : "border-white/5 bg-white/[0.02]"
      }`}
    >
      {/* Header */}
      <div
        className="cursor-pointer p-6"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-xl text-lg font-bold ${
                competitor.isMainCompetitor
                  ? "bg-feleti-gold/20 text-feleti-gold"
                  : "bg-white/5 text-white"
              }`}
            >
              {competitor.name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-lg font-semibold text-white">
                  {competitor.name}
                </h3>
                {competitor.isMainCompetitor && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400 border border-red-500/20">
                    <Trophy className="h-3 w-3" />
                    Главный конкурент
                  </span>
                )}
              </div>
              <p className="text-sm text-muted-foreground">
                {competitor.country} · {competitor.foundedYear} ·{" "}
                {competitor.segment}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {competitor.problems.length > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-400">
                <AlertTriangle className="h-3 w-3" />
                {competitor.problems.length} проблем
              </span>
            )}
            <motion.div
              animate={{ rotate: isOpen ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="h-5 w-5 text-muted-foreground" />
            </motion.div>
          </div>
        </div>

        {/* Quick metrics */}
        <div className="mt-4 grid grid-cols-4 gap-4">
          <Metric label="Загрузка" value={`до ${competitor.models[0]?.max_load_kg || "?"} кг`} />
          <Metric label="Рецептов" value={competitor.recipeCount?.toString() || "?"} />
          <Metric label="HMI" value="Сенсорная" />
          <Metric label="Гарантия" value={`${competitor.warrantyYears || "?"} год`} />
        </div>
      </div>

      {/* Expandable content */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="border-t border-white/5 px-6 pb-6">
              <CompetitorDetails competitor={competitor} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="text-center">
      <div className="text-sm font-medium text-white">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}
