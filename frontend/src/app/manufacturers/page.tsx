"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Building2, Globe, ArrowRight, MapPin } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

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

  const { data, isLoading } = useQuery({
    queryKey: ["manufacturers"],
    queryFn: async () => {
      const { data } = await apiClient.get("/manufacturers?size=200");
      return data as ManufacturerPage;
    },
  });

  const manufacturers = data?.items || [];

  const filtered = manufacturers.filter((m) => {
    if (tab === "our_brands") return m.is_our_brand;
    if (tab === "competitors") return m.is_competitor;
    return true;
  });

  if (isLoading) return <ManufacturersSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Производители</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data?.total || 0} производителей
        </p>
      </div>

      {/* Tabs */}
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

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.map((m, i) => (
          <ManufacturerCard key={m.id} manufacturer={m} index={i} />
        ))}
        {filtered.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
            <Building2 className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-muted-foreground">Производители не найдены</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ManufacturerCard({
  manufacturer: m,
  index,
}: {
  manufacturer: ManufacturerRead;
  index: number;
}) {
  return (
    <Link href={`/manufacturers/${m.id}`}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.03 }}
        className="group rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:bg-white/[0.03] h-full"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
              <Building2 className="h-5 w-5 text-feleti-gold" />
            </div>
            <div>
              <h3 className="font-medium text-white">{m.name}</h3>
              {m.short_name && (
                <p className="text-xs text-muted-foreground mt-0.5">{m.short_name}</p>
              )}
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
        </div>

        {/* Badges */}
        <div className="flex flex-wrap gap-2 mb-3">
          {m.is_our_brand && (
            <span className="rounded-md bg-feleti-gold/10 px-2 py-0.5 text-xs text-feleti-gold">
              Наш бренд
            </span>
          )}
          {m.is_competitor && (
            <span className="rounded-md bg-red-500/10 px-2 py-0.5 text-xs text-red-400">
              Конкурент
            </span>
          )}
        </div>

        {/* Info */}
        <div className="space-y-1.5 text-sm">
          {m.country && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              <span>
                {m.country}
                {m.city ? `, ${m.city}` : ""}
              </span>
            </div>
          )}
          {m.website && (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Globe className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">{m.website}</span>
            </div>
          )}
        </div>

        {m.description && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {m.description}
          </p>
        )}
      </motion.div>
    </Link>
  );
}

function ManufacturersSkeleton() {
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
