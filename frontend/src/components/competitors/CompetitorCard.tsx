"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, Trophy, AlertTriangle, ExternalLink, Store } from "lucide-react";
import { CompetitorDetails } from "./CompetitorDetails";

const SEGMENT_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  premium: { bg: "bg-amber-500/10", text: "text-amber-400", label: "Premium" },
  industrial: { bg: "bg-blue-500/10", text: "text-blue-400", label: "Industrial" },
  "middle": { bg: "bg-emerald-500/10", text: "text-emerald-400", label: "Middle" },
  "budget": { bg: "bg-gray-500/10", text: "text-gray-400", label: "Budget" },
  horeca: { bg: "bg-purple-500/10", text: "text-purple-400", label: "Horeca" },
  profi: { bg: "bg-orange-500/10", text: "text-orange-400", label: "Profi" },
};

const COUNTRY_FLAGS: Record<string, string> = {
  "Германия": "🇩🇪",
  "США": "🇺🇸",
  "Чехия": "🇨🇿",
  "Австрия": "🇦🇹",
  "Россия": "🇷🇺",
  "Китай": "🇨🇳",
  "Словения": "🇸🇮",
};

function getSegmentStyle(segment: string | null | undefined) {
  if (!segment) return { bg: "bg-white/5", text: "text-muted-foreground", label: "—" };
  const key = segment.toLowerCase().split("/")[0].trim();
  return SEGMENT_STYLES[key] || { bg: "bg-white/5", text: "text-muted-foreground", label: segment };
}

export interface Competitor {
  id: number;
  name: string;
  slug: string;
  country: string;
  founded_year?: number;
  segment: string;
  is_main_competitor: boolean;
  client_count?: number;
  recipe_count?: number;
  warranty_years?: number;
  has_cloud: boolean | null;
  has_mobile_app: boolean | null;
  has_remote_monitoring: boolean | null;
  has_video_camera: boolean | null;
  description: string;
  base_url?: string;
  dealers?: DealerEntry[];
  strengths: string[];
  weaknesses: string[];
  models: CompetitorModel[];
  problems: CompetitorProblem[];
}

export interface DealerEntry {
  country: string;
  company: string;
  contact?: string;
  website?: string;
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
  const segStyle = getSegmentStyle(competitor.segment);
  const flag = COUNTRY_FLAGS[competitor.country] || "";
  const dealerCount = competitor.dealers?.length || 0;

  return (
    <motion.div
      layout
      className={`relative overflow-hidden rounded-2xl border transition-all duration-300 ${
        competitor.is_main_competitor
          ? "border-feleti-gold/30 bg-feleti-gold/[0.03]"
          : "border-white/5 bg-white/[0.02]"
      } hover:border-white/10`}
    >
      {/* Header */}
      <div
        className="cursor-pointer p-6"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-4">
            <div
              className={`flex h-12 w-12 items-center justify-center rounded-xl text-lg font-bold shrink-0 ${
                competitor.is_main_competitor
                  ? "bg-feleti-gold/20 text-feleti-gold"
                  : "bg-white/5 text-white"
              }`}
            >
              {flag || competitor.name.charAt(0)}
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-lg font-semibold text-white truncate">
                  {competitor.name}
                </h3>
                {competitor.is_main_competitor && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs font-medium text-red-400 border border-red-500/20 shrink-0">
                    <Trophy className="h-3 w-3" />
                    Главный
                  </span>
                )}
                <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${segStyle.bg} ${segStyle.text} shrink-0`}>
                  {segStyle.label}
                </span>
              </div>
              <p className="text-sm text-muted-foreground mt-0.5">
                {flag && <span className="mr-1">{flag}</span>}
                {competitor.country}
                {competitor.founded_year && <span> · осн. {competitor.founded_year}</span>}
              </p>
              {competitor.base_url && (
                <a
                  href={competitor.base_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="mt-0.5 inline-flex items-center gap-1 text-xs text-feleti-gold/70 hover:text-feleti-gold transition-colors"
                >
                  <ExternalLink className="h-3 w-3" />
                  {new URL(competitor.base_url).hostname}
                </a>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {dealerCount > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400 border border-blue-500/20">
                <Store className="h-3 w-3" />
                {dealerCount}
              </span>
            )}
            {(competitor.problems?.length || 0) > 0 && (
              <span className="inline-flex items-center gap-1 rounded-full bg-red-500/10 px-2 py-0.5 text-xs text-red-400">
                <AlertTriangle className="h-3 w-3" />
                {competitor.problems?.length || 0}
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
          <Metric label="Рецептов" value={competitor.recipe_count?.toString() || "?"} />
          <Metric label="HMI" value={competitor.has_cloud ? "Облако" : "Локальная"} />
          <Metric label="Гарантия" value={`${competitor.warranty_years || "?"} г.`} />
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
