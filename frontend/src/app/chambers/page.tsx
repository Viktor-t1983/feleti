"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Flame,
  Snowflake,
  Zap,
  Droplets,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

interface Manufacturer {
  name: string;
}

interface Chamber {
  id: number;
  model: string;
  slug: string;
  type: string;
  max_load_kg: number | null;
  manufacturer: Manufacturer;
  supports_electro: boolean;
  supports_cold_smoke: boolean;
  supports_cooling: boolean;
  supports_freezing: boolean;
  supports_joint: boolean;
}

interface ChamberPage {
  items: Chamber[];
  total: number;
}

async function fetchChambers(): Promise<ChamberPage> {
  const { data } = await apiClient.get("/chambers?size=50");
  return data;
}

const typeIcons: Record<string, React.ElementType> = {
  hot: Flame,
  cold: Snowflake,
  universal: Zap,
  electro: Droplets,
};

const typeLabels: Record<string, string> = {
  hot: "Горячее копчение",
  cold: "Холодное копчение",
  universal: "Универсальная",
  electro: "Электростатика",
};

export default function ChambersPage() {
  const { data, isLoading } = useQuery({
    queryKey: ["chambers"],
    queryFn: fetchChambers,
  });

  const chambers = data?.items || [];

  if (isLoading) {
    return <ChambersSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Камеры</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Управление коптильными камерами
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {chambers.map((chamber, i) => (
          <ChamberCard key={chamber.id} chamber={chamber} index={i} />
        ))}
      </div>
    </div>
  );
}

function ChamberCard({ chamber, index }: { chamber: Chamber; index: number }) {
  const TypeIcon = typeIcons[chamber.type] || Flame;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
    >
      <Link
        href={`/chambers/${chamber.id}`}
        className="group block rounded-2xl border border-white/5 bg-white/[0.02] p-5 hover:bg-white/[0.03] hover:border-white/10 transition-colors"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
              <TypeIcon className="h-5 w-5 text-feleti-gold" />
            </div>
            <div>
              <h3 className="font-medium text-white">{chamber.model}</h3>
              <p className="text-xs text-muted-foreground">
                {chamber.manufacturer?.name || "—"}
              </p>
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        <div className="flex flex-wrap gap-1.5 mb-3">
          <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground">
            {typeLabels[chamber.type] || chamber.type}
          </span>
          {chamber.max_load_kg && (
            <span className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground">
              {chamber.max_load_kg} кг
            </span>
          )}
        </div>

        <div className="flex flex-wrap gap-1.5">
          {chamber.supports_electro && (
            <span className="rounded-full bg-feleti-gold/10 px-2 py-0.5 text-xs text-feleti-gold">
              Электро
            </span>
          )}
          {chamber.supports_cold_smoke && (
            <span className="rounded-full bg-blue-500/10 px-2 py-0.5 text-xs text-blue-400">
              Холодное
            </span>
          )}
          {chamber.supports_cooling && (
            <span className="rounded-full bg-cyan-500/10 px-2 py-0.5 text-xs text-cyan-400">
              Охлаждение
            </span>
          )}
          {chamber.supports_freezing && (
            <span className="rounded-full bg-indigo-500/10 px-2 py-0.5 text-xs text-indigo-400">
              Заморозка
            </span>
          )}
          {chamber.supports_joint && (
            <span className="rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
              Совместное
            </span>
          )}
        </div>
      </Link>
    </motion.div>
  );
}

function ChambersSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
