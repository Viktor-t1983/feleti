"use client";

import { useState, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { BarChart3, Loader2, Plus, ChevronDown, ChevronRight } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { apiClient } from "@/lib/api/client";
import { CompetitorCard } from "@/components/competitors/CompetitorCard";
import { CompetitorCardGrid } from "@/components/competitors/CompetitorCardGrid";
import { CompetitorModal } from "@/components/competitors/CompetitorModal";
import { GridControls } from "@/components/shared/GridControls";
import type { ViewMode, ColumnCount } from "@/components/shared/GridControls";
import type { Competitor } from "@/components/competitors/CompetitorCard";
import { ErrorState } from "@/components/shared/ErrorState";
import { COUNTRY_FLAGS, COUNTRY_ORDER } from "@/lib/countries";

interface CompetitorsResponse {
  items: Competitor[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

async function fetchCompetitors(): Promise<CompetitorsResponse> {
  const response = await apiClient.get<CompetitorsResponse>("/competitors?page=1&size=100");
  return response.data;
}

export default function CompetitorsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);

  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("all");
  const [mainOnly, setMainOnly] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("list");
  const [columns, setColumns] = useState<ColumnCount>(3);
  const [groupByCountry, setGroupByCountry] = useState(false);
  const [selectedCompetitor, setSelectedCompetitor] = useState<Competitor | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["competitors"],
    queryFn: fetchCompetitors,
    enabled: isAuthenticated,
  });

  const competitors = data?.items || [];

  const filtered = useMemo(() => {
    return competitors.filter((c) => {
      const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) ||
        (c.country || "").toLowerCase().includes(search.toLowerCase());
      const matchesSegment = segment === "all" || (c.segment || "").toLowerCase().includes(segment);
      const matchesMain = !mainOnly || c.is_main_competitor;
      return matchesSearch && matchesSegment && matchesMain;
    });
  }, [competitors, search, segment, mainOnly]);

  const grouped = useMemo(() => {
    if (!groupByCountry) return null;
    const groups = new Map<string, Competitor[]>();
    for (const c of filtered) {
      const country = c.country || "Другие";
      if (!groups.has(country)) groups.set(country, []);
      groups.get(country)!.push(c);
    }
    return Array.from(groups.entries())
      .map(([country, items]) => ({ country, items }))
      .sort((a, b) => {
        const ai = COUNTRY_ORDER.indexOf(a.country);
        const bi = COUNTRY_ORDER.indexOf(b.country);
        if (ai !== -1 && bi !== -1) return ai - bi;
        if (ai !== -1) return -1;
        if (bi !== -1) return 1;
        return b.items.length - a.items.length;
      });
  }, [filtered, groupByCountry]);

  const toggleGroup = (country: string) => {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(country)) next.delete(country);
      else next.add(country);
      return next;
    });
  };

  if (isLoadingAuth || !isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      {/* Header */}
      <section className="px-6 py-10">
        <div className="mx-auto max-w-7xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <BarChart3 className="h-6 w-6 text-feleti-gold" />
                <div>
                  <h1 className="text-2xl font-bold text-white">Анализ конкурентов</h1>
                  <p className="text-sm text-muted-foreground">
                    {filtered.length} из {competitors.length} конкурентов
                  </p>
                </div>
              </div>
              <button
                onClick={() => router.push("/competitors/new")}
                className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-4 py-2.5 text-sm font-medium text-black hover:bg-feleti-gold/90 transition-colors shrink-0"
              >
                <Plus className="h-4 w-4" />
                Добавить
              </button>
            </div>

            <GridControls
              viewMode={viewMode}
              onChangeViewMode={setViewMode}
              columns={columns}
              onChangeColumns={setColumns}
              groupByCountry={groupByCountry}
              onChangeGroupBy={setGroupByCountry}
              search={search}
              onChangeSearch={setSearch}
              segment={segment}
              onChangeSegment={setSegment}
              mainOnly={mainOnly}
              onChangeMainOnly={setMainOnly}
            />
          </motion.div>
        </div>
      </section>

      {/* Content */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-7xl">
          {error && !isLoading ? (
            <ErrorState message="Не удалось загрузить список конкурентов" onRetry={() => refetch()} />
          ) : isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
            </div>
          ) : filtered.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center py-16"
            >
              <BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground text-sm">Конкуренты не найдены</p>
            </motion.div>
          ) : grouped ? (
            /* Grouped by country */
            <div className="space-y-6">
              {grouped.map(({ country, items }) => {
                const isCollapsed = collapsedGroups.has(country);
                const flag = COUNTRY_FLAGS[country] || "";
                return (
                  <motion.div
                    key={country}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                  >
                    {/* Sticky group header */}
                    <button
                      onClick={() => toggleGroup(country)}
                      className="sticky top-0 z-10 flex items-center gap-3 w-full py-3 mb-4 bg-[#0a0a0a] border-b border-white/5"
                    >
                      {isCollapsed ? (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      )}
                      <span className="text-lg font-semibold text-white">
                        {flag && <span className="mr-2">{flag}</span>}
                        {country}
                      </span>
                      <span className="text-xs text-muted-foreground bg-white/5 rounded-full px-2 py-0.5">
                        {items.length}
                      </span>
                    </button>

                    {!isCollapsed && (
                      viewMode === "list" ? (
                        <div className="space-y-3">
                          {items.map((competitor) => (
                            <CompetitorCard key={competitor.id} competitor={competitor} />
                          ))}
                        </div>
                      ) : (
                        <div
                          className="grid gap-4"
                          style={{
                            gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                          }}
                        >
                          {items.map((competitor, i) => (
                            <CompetitorCardGrid
                              key={competitor.id}
                              competitor={competitor}
                              index={i}
                              onSelect={setSelectedCompetitor}
                            />
                          ))}
                        </div>
                      )
                    )}
                  </motion.div>
                );
              })}
            </div>
          ) : viewMode === "list" ? (
            /* Flat list */
            <div className="space-y-3">
              {filtered.map((competitor, index) => (
                <motion.div
                  key={competitor.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                >
                  <CompetitorCard competitor={competitor} />
                </motion.div>
              ))}
            </div>
          ) : (
            /* Flat grid */
            <div
              className="grid gap-4"
              style={{
                gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
              }}
            >
              {filtered.map((competitor, i) => (
                <CompetitorCardGrid
                  key={competitor.id}
                  competitor={competitor}
                  index={i}
                  onSelect={setSelectedCompetitor}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Modal for grid view detail */}
      <CompetitorModal
        competitor={selectedCompetitor}
        onClose={() => setSelectedCompetitor(null)}
      />
    </main>
  );
}
