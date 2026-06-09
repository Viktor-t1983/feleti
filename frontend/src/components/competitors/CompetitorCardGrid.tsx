"use client";

import { Trophy, Store, ExternalLink, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";
import type { Competitor } from "./CompetitorCard";

const SEGMENT_STYLES: Record<string, { bg: string; text: string }> = {
  premium: { bg: "bg-amber-500/10", text: "text-amber-400" },
  industrial: { bg: "bg-blue-500/10", text: "text-blue-400" },
  middle: { bg: "bg-emerald-500/10", text: "text-emerald-400" },
  budget: { bg: "bg-gray-500/10", text: "text-gray-400" },
  horeca: { bg: "bg-purple-500/10", text: "text-purple-400" },
  profi: { bg: "bg-orange-500/10", text: "text-orange-400" },
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

interface CompetitorCardGridProps {
  competitor: Competitor;
  index: number;
  onSelect: (c: Competitor) => void;
}

export function CompetitorCardGrid({ competitor, index, onSelect }: CompetitorCardGridProps) {
  const segStyle = competitor.segment
    ? SEGMENT_STYLES[competitor.segment.toLowerCase().split("/")[0].trim()]
    : null;
  const flag = COUNTRY_FLAGS[competitor.country] || "";

  return (
    <motion.button
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
      onClick={() => onSelect(competitor)}
      className={`group relative w-full text-left rounded-2xl border p-4 transition-all duration-200 ${
        competitor.is_main_competitor
          ? "border-feleti-gold/20 bg-feleti-gold/[0.03] hover:border-feleti-gold/40"
          : "border-white/5 bg-white/[0.02] hover:border-white/20"
      } hover:bg-white/[0.04]`}
    >
      {/* Top row: icon + badges */}
      <div className="flex items-start justify-between mb-3">
        <div
          className={`flex h-10 w-10 items-center justify-center rounded-xl text-base font-bold shrink-0 ${
            competitor.is_main_competitor
              ? "bg-feleti-gold/20 text-feleti-gold"
              : "bg-white/5 text-white"
          }`}
        >
          {flag || competitor.name.charAt(0)}
        </div>
        <div className="flex items-center gap-1">
          {competitor.is_main_competitor && (
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-red-500/10">
              <Trophy className="h-3 w-3 text-red-400" />
            </span>
          )}
          <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 -translate-x-1 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-200" />
        </div>
      </div>

      {/* Name + country */}
      <h3 className="text-sm font-semibold text-white truncate mb-0.5">
        {competitor.name}
      </h3>
      <p className="text-xs text-muted-foreground truncate">
        {flag && <span className="mr-1">{flag}</span>}
        {competitor.country}
        {competitor.founded_year && <span> · с {competitor.founded_year}</span>}
      </p>

      {/* Segment badge */}
      {segStyle && (
        <span className={`inline-block mt-2 rounded-full px-2 py-0.5 text-[10px] font-medium ${segStyle.bg} ${segStyle.text}`}>
          {competitor.segment}
        </span>
      )}

      {/* Quick stats row */}
      <div className="mt-3 flex items-center gap-3 text-[10px] text-muted-foreground border-t border-white/5 pt-3">
        <span>
          до {competitor.models?.[0]?.max_load_kg || "—"} кг
        </span>
        {competitor.dealers && competitor.dealers.length > 0 && (
          <span className="inline-flex items-center gap-1">
            <Store className="h-3 w-3" />
            {competitor.dealers.length}
          </span>
        )}
        {competitor.base_url && (
          <span className="inline-flex items-center gap-1 ml-auto text-feleti-gold/60">
            <ExternalLink className="h-3 w-3" />
          </span>
        )}
      </div>
    </motion.button>
  );
}
