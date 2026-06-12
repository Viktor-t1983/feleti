"use client";

import { Search, Star, List, LayoutGrid, Group, Ungroup } from "lucide-react";

export type ViewMode = "list" | "grid";
export type ColumnCount = 2 | 3 | 4 | 6;

interface GridControlsProps {
  viewMode: ViewMode;
  onChangeViewMode: (mode: ViewMode) => void;
  columns: ColumnCount;
  onChangeColumns: (n: ColumnCount) => void;
  groupByCountry: boolean;
  onChangeGroupBy: (v: boolean) => void;
  search: string;
  onChangeSearch: (v: string) => void;
  segment?: string;
  onChangeSegment?: (v: string) => void;
  mainOnly?: boolean;
  onChangeMainOnly?: (v: boolean) => void;
}

const COLUMNS: ColumnCount[] = [2, 3, 4, 6];

export function GridControls({
  viewMode,
  onChangeViewMode,
  columns,
  onChangeColumns,
  groupByCountry,
  onChangeGroupBy,
  search,
  onChangeSearch,
  segment,
  onChangeSegment,
  mainOnly,
  onChangeMainOnly,
}: GridControlsProps) {
  return (
    <div className="flex flex-wrap items-center gap-3">
      {/* View mode toggle */}
      <div className="flex rounded-xl border border-white/10 bg-white/5 p-0.5">
        <button
          onClick={() => onChangeViewMode("list")}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
            viewMode === "list"
              ? "bg-white/10 text-white"
              : "text-muted-foreground hover:text-white"
          }`}
        >
          <List className="h-3.5 w-3.5" />
          Список
        </button>
        <button
          onClick={() => onChangeViewMode("grid")}
          className={`flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
            viewMode === "grid"
              ? "bg-white/10 text-white"
              : "text-muted-foreground hover:text-white"
          }`}
        >
          <LayoutGrid className="h-3.5 w-3.5" />
          Сетка
        </button>
      </div>

      {/* Column count (grid only) */}
      {viewMode === "grid" && (
        <div className="flex items-center gap-1 rounded-xl border border-white/10 bg-white/5 px-2 py-1.5">
          <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider mr-1">
            Колонки
          </span>
          {COLUMNS.map((n) => (
            <button
              key={n}
              onClick={() => onChangeColumns(n)}
              className={`flex h-6 w-6 items-center justify-center rounded-md text-xs font-medium transition-colors ${
                columns === n
                  ? "bg-feleti-gold/20 text-feleti-gold"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
      )}

      {/* Divider */}
      <div className="hidden sm:block h-6 w-px bg-white/10" />

      {/* Group by country */}
      <button
        onClick={() => onChangeGroupBy(!groupByCountry)}
        className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition-colors ${
          groupByCountry
            ? "border-feleti-gold/30 bg-feleti-gold/10 text-feleti-gold"
            : "border-white/10 bg-white/5 text-muted-foreground hover:text-white"
        }`}
      >
        {groupByCountry ? (
          <Group className="h-3.5 w-3.5" />
        ) : (
          <Ungroup className="h-3.5 w-3.5" />
        )}
        По странам
      </button>

      {/* Search */}
      <div className="relative flex-1 min-w-[160px] max-w-xs">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
        <input
          type="text"
          placeholder="Поиск..."
          value={search}
          onChange={(e) => onChangeSearch(e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 py-2 pl-9 pr-3 text-xs text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none"
        />
      </div>

      {/* Segment filter */}
      {segment !== undefined && onChangeSegment && (
        <select
          value={segment}
          onChange={(e) => onChangeSegment(e.target.value)}
          className="rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-xs text-white focus:border-feleti-gold/50 focus:outline-none"
        >
          <option value="all">Все сегменты</option>
          <option value="horeca">Horeca</option>
          <option value="profi">Profi</option>
          <option value="industrial">Industrial</option>
          <option value="premium">Premium</option>
          <option value="middle">Middle</option>
          <option value="budget">Budget</option>
        </select>
      )}

      {/* Main only toggle */}
      {mainOnly !== undefined && onChangeMainOnly && (
        <button
          onClick={() => onChangeMainOnly(!mainOnly)}
          className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-medium transition-colors ${
            mainOnly
              ? "border-feleti-gold/40 bg-feleti-gold/10 text-feleti-gold"
              : "border-white/10 bg-white/5 text-muted-foreground hover:text-white"
          }`}
        >
          <Star className={`h-3.5 w-3.5 ${mainOnly ? "fill-feleti-gold" : ""}`} />
          Главные
        </button>
      )}
    </div>
  );
}
