"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { ArrowLeft, Droplets, Clock, Thermometer, FlaskConical, Pencil } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { ErrorState } from "@/components/shared/ErrorState";

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

const METHOD_COLORS: Record<string, string> = {
  "сухой": "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "мокрый": "text-blue-400 bg-blue-500/10 border-blue-500/20",
  "шприцевание": "text-purple-400 bg-purple-500/10 border-purple-500/20",
  "комбинированный": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  "смешанный": "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
};

export default function BrineDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const { data: brine, isLoading, error, refetch } = useQuery({
    queryKey: ["brine", slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/brines/${slug}`);
      return data as BrineRead;
    },
    enabled: !!slug,
  });

  if (error && !isLoading) return <ErrorState message="Не удалось загрузить рассол" onRetry={() => refetch()} />;

  if (isLoading || !brine) return <BrineDetailSkeleton />;

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href="/brines" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4">
        <ArrowLeft className="h-4 w-4" />
        Назад к рассолам
      </Link>
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-feleti-gold/10 shrink-0">
            <Droplets className="h-7 w-7 text-feleti-gold" />
          </div>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-white">{brine.name}</h1>
            <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium mt-2 ${METHOD_COLORS[brine.method] || ""}`}>
              {brine.method}
            </span>
          </div>
        </div>
        <Link
          href={`/brines/${brine.slug}/edit`}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition-colors hover:bg-white/5"
        >
          <Pencil className="h-4 w-4" />
          Редактировать
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-8">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground">Соль</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.salt_percent}%</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground">Сахар</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.sugar_percent}%</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground">Нитрит</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.nitrite_ppm} ppm</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground flex items-center gap-1"><Clock className="h-3.5 w-3.5" /> Время</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.duration_hours} ч</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground flex items-center gap-1"><Thermometer className="h-3.5 w-3.5" /> T</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.temp_c}°C</p>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground flex items-center gap-1"><FlaskConical className="h-3.5 w-3.5" /> Вода</span>
          <p className="text-lg font-semibold text-white mt-1">{brine.water_percent != null ? `${brine.water_percent}%` : "—"}</p>
        </div>
      </div>

      {brine.spices.length > 0 && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Специи</h2>
          <div className="flex flex-wrap gap-2">
            {brine.spices.map((spice) => (
              <span key={spice} className="rounded-full bg-white/5 px-3 py-1 text-sm text-white">{spice}</span>
            ))}
          </div>
        </div>
      )}

      {brine.description && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Описание</h2>
          <p className="text-sm text-white/80 leading-relaxed">{brine.description}</p>
        </div>
      )}

      {brine.notes && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Примечания</h2>
          <p className="text-sm text-white/60 leading-relaxed">{brine.notes}</p>
        </div>
      )}
    </div>
  );
}

function BrineDetailSkeleton() {
  return (
    <div className="mx-auto max-w-2xl py-8 space-y-4">
      <div className="h-4 w-32 animate-pulse rounded bg-white/5" />
      <div className="flex gap-3">
        <div className="h-14 w-14 animate-pulse rounded-xl bg-white/5" />
        <div className="h-8 w-48 animate-pulse rounded bg-white/5" />
      </div>
      <div className="grid grid-cols-3 gap-3 mt-8">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
