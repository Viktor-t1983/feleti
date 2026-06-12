"use client";

import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Building2,
  Globe,
  MapPin,
  Factory,
  X,
  ChevronDown,
  ChevronRight,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { GridControls } from "@/components/shared/GridControls";
import type { ViewMode, ColumnCount } from "@/components/shared/GridControls";
import { ErrorState } from "@/components/shared/ErrorState";
import { COUNTRY_FLAGS } from "@/lib/countries";

const TABS = [
  { id: "all", label: "Все" },
  { id: "our_brands", label: "Наши бренды" },
  { id: "competitors", label: "Конкуренты" },
];

interface ManufacturerRead {
  id: number;
  slug: string;
  name: string;
  short_name: string | null;
  country: string | null;
  city: string | null;
  founded_year: number | null;
  website: string | null;
  description: string | null;
  logo_url: string | null;
  is_our_brand: boolean;
  is_competitor: boolean;
  sort_order: number;
  created_at: string;
  updated_at: string | null;
}

interface ManufacturerPage {
  items: ManufacturerRead[];
  total: number;
}

export default function ManufacturersPage() {
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [columns, setColumns] = useState<ColumnCount>(3);
  const [groupByCountry, setGroupByCountry] = useState(false);
  const [selected, setSelected] = useState<ManufacturerRead | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["manufacturers"],
    queryFn: async () => {
      const { data } = await apiClient.get("/manufacturers?size=200");
      return data as ManufacturerPage;
    },
  });

  const manufacturers = data?.items || [];

  const filtered = useMemo(() => {
    return manufacturers.filter((m) => {
      const matchesTab =
        tab === "all" || (tab === "our_brands" && m.is_our_brand) || (tab === "competitors" && m.is_competitor);
      const q = search.toLowerCase();
      const matchesSearch =
        !q ||
        m.name.toLowerCase().includes(q) ||
        (m.country || "").toLowerCase().includes(q) ||
        (m.short_name || "").toLowerCase().includes(q);
      return matchesTab && matchesSearch;
    });
  }, [manufacturers, search, tab]);

  const grouped = useMemo(() => {
    if (!groupByCountry) return null;
    const groups = new Map<string, ManufacturerRead[]>();
    for (const m of filtered) {
      const country = m.country || "Другие";
      if (!groups.has(country)) groups.set(country, []);
      groups.get(country)!.push(m);
    }
    return Array.from(groups.entries())
      .map(([country, items]) => ({ country, items }))
      .sort((a, b) => {
        const ai = Object.keys(COUNTRY_FLAGS).indexOf(a.country);
        const bi = Object.keys(COUNTRY_FLAGS).indexOf(b.country);
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

  if (error && !isLoading) {
    return <ErrorState message="Не удалось загрузить список производителей" onRetry={() => refetch()} />;
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="h-32 animate-pulse rounded-2xl bg-white/5" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Производители</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {filtered.length} из {data?.total || 0} производителей
        </p>
      </div>

      {/* Tabs + toolbar */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1 overflow-x-auto max-w-full">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm transition-colors ${
                  tab === t.id
                    ? "bg-white/10 text-white"
                    : "text-muted-foreground hover:text-white"
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
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
        />
      </div>

      {/* Grouped view */}
      {grouped ? (
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
                    <div className="space-y-2">
                      {items.map((m) => (
                        <ManufacturerRow key={m.id} m={m} onSelect={setSelected} />
                      ))}
                    </div>
                  ) : (
                    <div
                      className="grid gap-4"
                      style={{
                        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                      }}
                    >
                      {items.map((m, i) => (
                        <ManufacturerCard key={m.id} m={m} index={i} onSelect={setSelected} />
                      ))}
                    </div>
                  )
                )}
              </motion.div>
            );
          })}
        </div>
      ) : viewMode === "list" ? (
        <div className="space-y-2">
          {filtered.map((m) => (
            <ManufacturerRow key={m.id} m={m} onSelect={setSelected} />
          ))}
        </div>
      ) : (
        <div
          className="grid gap-4"
          style={{
            gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
          }}
        >
          {filtered.map((m, i) => (
            <ManufacturerCard key={m.id} m={m} index={i} onSelect={setSelected} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
          <Building2 className="h-12 w-12 text-muted-foreground/30" />
          <p className="mt-4 text-muted-foreground">Производители не найдены</p>
        </div>
      )}

      {/* Detail modal */}
      <AnimatePresence>
        {selected && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
              onClick={() => setSelected(null)}
            />
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
              className="fixed inset-4 md:inset-x-auto md:inset-y-6 md:left-1/4 md:right-1/4 z-50 overflow-hidden rounded-2xl border border-white/10 bg-[#0f0f0f] shadow-2xl"
            >
              <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
                <div>
                  <h2 className="text-lg font-semibold text-white">{selected.name}</h2>
                  <p className="text-sm text-muted-foreground">
                    {selected.country}
                    {selected.city && <span> · {selected.city}</span>}
                  </p>
                </div>
                <button
                  onClick={() => setSelected(null)}
                  className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              <div className="overflow-y-auto p-6" style={{ maxHeight: "calc(100vh - 180px)" }}>
                {/* Badges */}
                <div className="flex gap-2 mb-4">
                  {selected.is_our_brand && (
                    <span className="rounded-md bg-feleti-gold/10 px-2.5 py-1 text-xs font-medium text-feleti-gold">
                      Наш бренд
                    </span>
                  )}
                  {selected.is_competitor && (
                    <span className="rounded-md bg-orange-500/10 px-2.5 py-1 text-xs font-medium text-orange-400">
                      Конкурент
                    </span>
                  )}
                </div>

                {/* Details grid */}
                <div className="grid grid-cols-2 gap-4 mb-4">
                  {selected.country && (
                    <div className="rounded-xl bg-white/5 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Страна</div>
                      <div className="text-sm text-white font-medium">
                        {COUNTRY_FLAGS[selected.country] && (
                          <span className="mr-1.5">{COUNTRY_FLAGS[selected.country]}</span>
                        )}
                        {selected.country}
                        {selected.city && <span>, {selected.city}</span>}
                      </div>
                    </div>
                  )}
                  {selected.founded_year && (
                    <div className="rounded-xl bg-white/5 p-4">
                      <div className="text-xs text-muted-foreground mb-1">Год основания</div>
                      <div className="text-sm text-white font-medium">{selected.founded_year}</div>
                    </div>
                  )}
                  {selected.website && (
                    <div className="rounded-xl bg-white/5 p-4 col-span-full">
                      <div className="text-xs text-muted-foreground mb-1">Веб-сайт</div>
                      <a
                        href={selected.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-feleti-gold/80 hover:text-feleti-gold inline-flex items-center gap-1.5"
                      >
                        <Globe className="h-4 w-4" />
                        {selected.website}
                      </a>
                    </div>
                  )}
                </div>

                {selected.description && (
                  <div>
                    <h4 className="text-sm font-medium text-white mb-2">Описание</h4>
                    <p className="text-sm text-muted-foreground leading-relaxed whitespace-pre-line">
                      {selected.description}
                    </p>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Grid Card ─── */
function ManufacturerCard({
  m,
  index,
  onSelect,
}: {
  m: ManufacturerRead;
  index: number;
  onSelect: (m: ManufacturerRead) => void;
}) {
  const flag = COUNTRY_FLAGS[m.country || ""] || "";
  return (
    <motion.button
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      onClick={() => onSelect(m)}
      className="group w-full text-left rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:bg-white/[0.03] hover:border-white/20"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            {flag ? (
              <span className="text-lg">{flag}</span>
            ) : (
              <Building2 className="h-5 w-5 text-feleti-gold" />
            )}
          </div>
          <div className="min-w-0">
            <h3 className="font-medium text-white truncate">{m.name}</h3>
            {m.short_name && (
              <p className="text-xs text-muted-foreground truncate">{m.short_name}</p>
            )}
          </div>
        </div>
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5 mb-3">
        {m.is_our_brand && (
          <span className="rounded-md bg-feleti-gold/10 px-2 py-0.5 text-[10px] font-medium text-feleti-gold">
            Наш бренд
          </span>
        )}
        {m.is_competitor && (
          <span className="rounded-md bg-orange-500/10 px-2 py-0.5 text-[10px] font-medium text-orange-400">
            Конкурент
          </span>
        )}
      </div>

      {/* Info */}
      <div className="space-y-1 text-xs text-muted-foreground">
        {m.country && (
          <div className="flex items-center gap-1.5">
            <MapPin className="h-3 w-3 shrink-0" />
            <span className="truncate">
              {flag && <span className="mr-1">{flag}</span>}
              {m.country}
              {m.city ? `, ${m.city}` : ""}
            </span>
          </div>
        )}
        {m.website && (
          <div className="flex items-center gap-1.5">
            <Globe className="h-3 w-3 shrink-0" />
            <span className="truncate">{m.website}</span>
          </div>
        )}
      </div>

      {m.description && (
        <p className="mt-2 text-xs text-muted-foreground line-clamp-2">{m.description}</p>
      )}
    </motion.button>
  );
}

/* ─── List Row ─── */
function ManufacturerRow({
  m,
  onSelect,
}: {
  m: ManufacturerRead;
  onSelect: (m: ManufacturerRead) => void;
}) {
  const flag = COUNTRY_FLAGS[m.country || ""] || "";
  return (
    <motion.button
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      onClick={() => onSelect(m)}
      className="group flex w-full items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 text-left transition-all hover:bg-white/[0.03] hover:border-white/20"
    >
      <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-feleti-gold/10 shrink-0">
        {flag ? (
          <span className="text-sm">{flag}</span>
        ) : (
          <Factory className="h-4 w-4 text-feleti-gold" />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-medium text-white truncate">{m.name}</span>
          {m.is_our_brand && (
            <span className="shrink-0 rounded bg-feleti-gold/10 px-1.5 py-0.5 text-[10px] text-feleti-gold">
              Бренд
            </span>
          )}
          {m.is_competitor && (
            <span className="shrink-0 rounded bg-orange-500/10 px-1.5 py-0.5 text-[10px] text-orange-400">
              Конкурент
            </span>
          )}
        </div>
        <p className="text-xs text-muted-foreground truncate">
          {m.country || "—"}
          {m.city && <span>, {m.city}</span>}
          {m.founded_year && <span> · с {m.founded_year}</span>}
        </p>
      </div>
      {m.website && (
        <Globe className="h-3.5 w-3.5 text-muted-foreground shrink-0" />
      )}
    </motion.button>
  );
}
