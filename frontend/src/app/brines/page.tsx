"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Droplets,
  Search,
  Thermometer,
  Clock,
  FlaskConical,
  Plus,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { ErrorState } from "@/components/shared/ErrorState";
import Link from "next/link";

interface BrineRead {
  id: number;
  name: string;
  slug: string;
  method: string;
  salt_percent: number;
  sugar_percent: number;
  nitrite_ppm: number;
  nitrate_ppm: number;
  spices: string[];
  duration_hours: number;
  temp_c: number;
  water_percent: number | null;
  description: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string | null;
}

interface BrinePage {
  items: BrineRead[];
  total: number;
}

const METHOD_TABS = [
  { id: "all", label: "Все" },
  { id: "сухой", label: "Сухой" },
  { id: "мокрый", label: "Мокрый" },
  { id: "шприцевание", label: "Шприцевание" },
  { id: "комбинированный", label: "Комбинированный" },
  { id: "смешанный", label: "Смешанный" },
];

const METHOD_COLORS: Record<string, string> = {
  "сухой": "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "мокрый": "text-blue-400 bg-blue-500/10 border-blue-500/20",
  "шприцевание": "text-purple-400 bg-purple-500/10 border-purple-500/20",
  "комбинированный": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  "смешанный": "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
};

export default function BrinesPage() {
  const [method, setMethod] = useState("all");
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["brines", method, search],
    queryFn: async () => {
      const params = new URLSearchParams({ size: "200" });
      if (method !== "all") params.set("method", method);
      if (search) params.set("q", search);
      const { data } = await apiClient.get(`/brines?${params}`);
      return data as BrinePage;
    },
  });

  const brines = data?.items || [];

  if (error && !isLoading) return <ErrorState message="Не удалось загрузить список рассолов" onRetry={() => refetch()} />;

  if (isLoading) return <BrinesSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Рассолы</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data?.total || 0} рецептур
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <Link
          href="/brines/new"
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90"
        >
          <Plus className="h-4 w-4" />
          Новый
        </Link>
        <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1 overflow-x-auto max-w-full">
          {METHOD_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setMethod(tab.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm transition-colors ${
                method === tab.id
                  ? "bg-white/10 text-white"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по названию..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {brines.map((brine, i) => (
          <BrineCard key={brine.id} brine={brine} index={i} />
        ))}
        {brines.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
            <Droplets className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-muted-foreground">Рассолы не найдены</p>
          </div>
        )}
      </div>
    </div>
  );
}

function BrineCard({ brine, index }: { brine: BrineRead; index: number }) {
  const methodColor = METHOD_COLORS[brine.method] || "text-muted-foreground bg-white/5 border-white/10";

  return (
    <Link href={`/brines/${brine.slug}`}>
      <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="group rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:bg-white/[0.03] h-full"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            <Droplets className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h3 className="font-medium text-white">{brine.name}</h3>
            <span className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium mt-1 ${methodColor}`}>
              {brine.method}
            </span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-3 text-xs mb-3">
        <div>
          <span className="text-muted-foreground">Соль</span>
          <p className="text-white font-medium mt-0.5">{brine.salt_percent}%</p>
        </div>
        <div>
          <span className="text-muted-foreground">Сахар</span>
          <p className="text-white font-medium mt-0.5">{brine.sugar_percent}%</p>
        </div>
        <div>
          <span className="text-muted-foreground">Нитрит</span>
          <p className="text-white font-medium mt-0.5">{brine.nitrite_ppm} ppm</p>
        </div>
        <div>
          <span className="text-muted-foreground flex items-center gap-1"><Clock className="h-3 w-3" /> Время</span>
          <p className="text-white font-medium mt-0.5">{brine.duration_hours} ч</p>
        </div>
        <div>
          <span className="text-muted-foreground flex items-center gap-1"><Thermometer className="h-3 w-3" /> T</span>
          <p className="text-white font-medium mt-0.5">{brine.temp_c}°C</p>
        </div>
        <div>
          <span className="text-muted-foreground flex items-center gap-1"><FlaskConical className="h-3 w-3" /> Вода</span>
          <p className="text-white font-medium mt-0.5">{brine.water_percent != null ? `${brine.water_percent}%` : "—"}</p>
        </div>
      </div>

      {/* Spices */}
      {brine.spices.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {brine.spices.map((spice) => (
            <span
              key={spice}
              className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground"
            >
              {spice}
            </span>
          ))}
        </div>
      )}
    </motion.div></Link>
  );
}

function BrinesSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="h-10 w-full animate-pulse rounded-xl bg-white/5" />
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
