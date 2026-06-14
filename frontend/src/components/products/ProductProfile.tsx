"use client";

import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  FlaskConical,
  Drill,
  Flame,
  Gauge,
  FileText,
  Tags,
  Package,
  Beef,
  Clock,
  Snowflake,
  Cog,
  Link2,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { useState } from "react";

interface FactItem {
  object_name: string;
  object_type: string;
  predicate: string;
  article_id: number;
  source_text: string | null;
  confidence: number;
  params: Record<string, unknown>;
  inherited_from: string | null;
  chunk_id: number | null;
}

interface FactGroup {
  predicate: string;
  label: string;
  facts: FactItem[];
}

interface ProductProfileData {
  id: number;
  name: string;
  slug: string;
  category: string;
  gost: string | null;
  parent: { id: number; name: string; slug: string } | null;
  children: { id: number; name: string; slug: string }[];
  fact_groups: FactGroup[];
}

const PREDICATE_ICONS: Record<string, React.ElementType> = {
  uses_brine: FlaskConical,
  uses_equipment: Drill,
  uses_technology: Flame,
  has_parameter: Gauge,
  regulated_by: FileText,
  has_category: Tags,
  contains: Package,
  derived_from: Beef,
  shelf_life: Clock,
  storage_condition: Snowflake,
  process_step: Cog,
  mentions: Link2,
};

const PREDICATE_COLORS: Record<string, string> = {
  uses_brine: "border-cyan-500/20 bg-cyan-500/5",
  uses_equipment: "border-violet-500/20 bg-violet-500/5",
  uses_technology: "border-orange-500/20 bg-orange-500/5",
  has_parameter: "border-emerald-500/20 bg-emerald-500/5",
  regulated_by: "border-amber-500/20 bg-amber-500/5",
  has_category: "border-pink-500/20 bg-pink-500/5",
  contains: "border-sky-500/20 bg-sky-500/5",
  derived_from: "border-yellow-500/20 bg-yellow-500/5",
  shelf_life: "border-blue-500/20 bg-blue-500/5",
  storage_condition: "border-indigo-500/20 bg-indigo-500/5",
  process_step: "border-gray-500/20 bg-gray-500/5",
};

const PREDICATE_ACCENT: Record<string, string> = {
  uses_brine: "text-cyan-400",
  uses_equipment: "text-violet-400",
  uses_technology: "text-orange-400",
  has_parameter: "text-emerald-400",
  regulated_by: "text-amber-400",
  has_category: "text-pink-400",
  contains: "text-sky-400",
  derived_from: "text-yellow-400",
  shelf_life: "text-blue-400",
  storage_condition: "text-indigo-400",
  process_step: "text-gray-400",
};

function confidenceColor(c: number): string {
  if (c >= 0.8) return "text-green-400";
  if (c >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

function formatValue(val: unknown): string {
  if (val === null || val === undefined) return "";
  return String(val);
}

export function ProductProfile({ productId }: { productId: number }) {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());

  const { data, isLoading } = useQuery({
    queryKey: ["product-profile", productId],
    queryFn: async () => {
      const { data } = await apiClient.get(`/products/${productId}/profile`);
      return data as ProductProfileData;
    },
    enabled: !!productId,
  });

  if (isLoading) return <ProfileSkeleton />;
  if (!data) return null;

  const toggleGroup = (predicate: string) => {
    setExpandedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(predicate)) next.delete(predicate);
      else next.add(predicate);
      return next;
    });
  };

  return (
    <div className="space-y-4">
      {/* Parent reference */}
      {data.parent && (
        <a
          href={`/products/${data.parent.slug}`}
          className="inline-flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-1.5 text-xs text-muted-foreground hover:text-white transition-colors"
        >
          ← {data.parent.name}
        </a>
      )}

      {/* Children list */}
      {data.children.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {data.children.map((child) => (
            <a
              key={child.id}
              href={`/products/${child.slug}`}
              className="inline-flex items-center gap-1 rounded-lg border border-white/5 bg-white/[0.02] px-2.5 py-1 text-xs text-muted-foreground hover:text-feleti-gold transition-colors"
            >
              {child.name}
            </a>
          ))}
        </div>
      )}

      {/* Fact groups */}
      <AnimatePresence mode="popLayout">
        {data.fact_groups.map((group) => {
          const Icon = PREDICATE_ICONS[group.predicate] || Link2;
          const colorClass = PREDICATE_COLORS[group.predicate] || "border-white/5 bg-white/[0.02]";
          const accentClass = PREDICATE_ACCENT[group.predicate] || "text-muted-foreground";
          const isExpanded = expandedGroups.has(group.predicate) || group.facts.length <= 3;

          return (
            <motion.div
              key={group.predicate}
              layout
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-xl border ${colorClass} overflow-hidden`}
            >
              {/* Group header */}
              <button
                onClick={() => toggleGroup(group.predicate)}
                className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-white/[0.02]"
              >
                <div className="flex items-center gap-2">
                  <Icon className={`h-4 w-4 ${accentClass}`} />
                  <span className="text-sm font-medium text-white">{group.label}</span>
                  <span className="text-xs text-muted-foreground ml-1">({group.facts.length})</span>
                </div>
                {group.facts.length > 3 && (
                  isExpanded
                    ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                    : <ChevronRight className="h-4 w-4 text-muted-foreground" />
                )}
              </button>

              {/* Facts */}
              {isExpanded && (
                <div className="divide-y divide-white/5">
                  {group.facts.map((fact, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -8 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: i * 0.02 }}
                      className="px-4 py-3"
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-white">
                              {fact.object_name}
                            </span>
                            {fact.inherited_from && (
                              <span className="text-[10px] text-muted-foreground/60 border border-white/5 rounded px-1.5 py-0.5">
                                насл. от {fact.inherited_from}
                              </span>
                            )}
                            <span className={`text-[10px] font-medium uppercase ${confidenceColor(fact.confidence)}`}>
                              {Math.round(fact.confidence * 100)}%
                            </span>
                          </div>

                          {/* Params */}
                          {Object.keys(fact.params).length > 0 && (
                            <div className="flex flex-wrap gap-1.5 mt-1.5">
                              {Object.entries(fact.params).map(([k, v]) => (
                                <span
                                  key={k}
                                  className="inline-flex items-center rounded-md border border-white/5 bg-white/[0.03] px-1.5 py-0.5 text-[10px] text-muted-foreground"
                                >
                                  {k}: {formatValue(v)}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* Source text */}
                          {fact.source_text && (
                            <div className="mt-1.5">
                              <span className="text-[11px] italic text-muted-foreground/70 leading-relaxed">
                                «{fact.source_text.length > 200
                                  ? fact.source_text.slice(0, 200) + "…"
                                  : fact.source_text}»
                              </span>
                            </div>
                          )}
                        </div>

                        {/* Link to article */}
                        <a
                          href={`/knowledge/${fact.article_id}`}
                          className="shrink-0 mt-0.5 text-muted-foreground hover:text-feleti-gold transition-colors"
                          title="Открыть статью-источник"
                        >
                          <ExternalLink className="h-3.5 w-3.5" />
                        </a>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </motion.div>
          );
        })}
      </AnimatePresence>

      {data.fact_groups.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-xl border border-white/5 bg-white/[0.02] py-12">
          <FlaskConical className="h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">
            Знания по продукту ещё не загружены
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground/50">
            Дождитесь завершения AI-анализа статей
          </p>
        </div>
      )}
    </div>
  );
}

function ProfileSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-16 animate-pulse rounded-xl bg-white/5" />
      ))}
    </div>
  );
}
