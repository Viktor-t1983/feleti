"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Flame,
  Snowflake,
  Zap,
  Droplets,
  ArrowRight,
  Thermometer,
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

interface Batch {
  id: number;
  chamber_id: number;
  status: string;
  batch_number: string;
}

async function fetchChambers(): Promise<ChamberPage> {
  const { data } = await apiClient.get("/chambers?size=50");
  return data;
}

async function fetchActiveBatches(): Promise<Batch[]> {
  const { data } = await apiClient.get("/batches?status=running&status=paused&size=50");
  return data.items || data || [];
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

function StatusBadge({ status }: { status: string }) {
  if (status === "running") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1">
        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
        <span className="text-[10px] font-medium text-emerald-400">В работе</span>
      </span>
    );
  }
  if (status === "paused") {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-500/10 border border-amber-500/20 px-2.5 py-1">
        <span className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
        <span className="text-[10px] font-medium text-amber-400">Пауза</span>
      </span>
    );
  }
  return null;
}

export default function ChambersPage() {
  const { data: chambersData, isLoading } = useQuery({
    queryKey: ["chambers"],
    queryFn: fetchChambers,
  });

  const { data: activeBatches } = useQuery({
    queryKey: ["batches", "active"],
    queryFn: fetchActiveBatches,
    refetchInterval: 15000,
  });

  const chambers = chambersData?.items || [];
  const batchMap = new Map<number, Batch>();
  (activeBatches || []).forEach((b) => {
    if (b.chamber_id) batchMap.set(b.chamber_id, b);
  });

  if (isLoading) {
    return <ChambersSkeleton />;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Камеры</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Управление коптильными камерами
            {activeBatches && activeBatches.length > 0 && (
              <span className="ml-2 text-emerald-400/60">
                · {activeBatches.filter((b) => b.status === "running").length} в работе
              </span>
            )}
          </p>
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {chambers.map((chamber, i) => {
          const active = batchMap.get(chamber.id);
          return (
            <ChamberCard
              key={chamber.id}
              chamber={chamber}
              index={i}
              activeBatch={active}
            />
          );
        })}
      </div>
    </div>
  );
}

function ChamberCard({
  chamber,
  index,
  activeBatch,
}: {
  chamber: Chamber;
  index: number;
  activeBatch?: Batch;
}) {
  const TypeIcon = typeIcons[chamber.type] || Flame;
  const isRunning = activeBatch?.status === "running";
  const isPaused = activeBatch?.status === "paused";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
    >
      <Link
        href={`/chambers/${chamber.id}`}
        className={`group relative block rounded-2xl border p-5 transition-all ${
          isRunning
            ? "border-emerald-500/20 bg-emerald-500/[0.02] hover:bg-emerald-500/[0.04]"
            : isPaused
            ? "border-amber-500/20 bg-amber-500/[0.02] hover:bg-amber-500/[0.04]"
            : "border-white/5 bg-white/[0.02] hover:bg-white/[0.03] hover:border-white/10"
        }`}
      >
        {isRunning && (
          <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-emerald-500/[0.03] to-transparent pointer-events-none" />
        )}

        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className={`flex h-10 w-10 items-center justify-center rounded-xl ${
              isRunning ? "bg-emerald-500/10" : "bg-feleti-gold/10"
            }`}>
              <TypeIcon className={`h-5 w-5 ${
                isRunning ? "text-emerald-400" : "text-feleti-gold"
              }`} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-medium text-white">{chamber.model}</h3>
                {activeBatch && <StatusBadge status={activeBatch.status} />}
              </div>
              <p className="text-xs text-muted-foreground">
                {chamber.manufacturer?.name || "—"}
              </p>
            </div>
          </div>
          <ArrowRight className={`h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity ${
            isRunning ? "text-emerald-400" : "text-muted-foreground"
          }`} />
        </div>

        {activeBatch && (
          <div className="mb-3 flex items-center gap-2 rounded-lg bg-white/[0.03] px-3 py-2">
            <Thermometer className="h-3.5 w-3.5 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              {activeBatch.batch_number}
            </span>
          </div>
        )}

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
          <div key={i} className="h-44 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
