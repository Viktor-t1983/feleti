"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Globe,
  Play,
  Loader2,
  FileText,
  Package,
  Database,
  ExternalLink,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

interface SyncResult {
  competitor: string;
  status: string;
  articles: number;
  models: number;
  errors: number;
  pages_crawled: number;
}

interface PipelineResults {
  competitors: Array<{
    id: number;
    name: string;
    slug: string;
    model_count: number;
    problem_count: number;
  }>;
  articles: Array<{
    id: number;
    title: string;
    slug: string;
    category: string;
    created_at: string;
  }>;
  models: Array<{
    id: number;
    name: string;
    competitor_id: number;
    max_load_kg: number | null;
    power_kw: number | null;
  }>;
  totals: {
    competitors: number;
    articles: number;
    models: number;
  };
}

const COMPETITORS = [
  {
    id: "ijiza",
    name: "Ижица",
    country: "Россия",
    url: "https://ijiza.ru",
    description: "Ведущий российский производитель коптильных камер",
  },
  {
    id: "mauting",
    name: "Mauting",
    country: "Чехия",
    url: "https://www.mauting.com",
    description: "Чешское оборудование для копчения и термообработки",
  },
  {
    id: "fessmann",
    name: "Fessmann",
    country: "Германия",
    url: "https://www.fessmann.com",
    description: "Немецкие коптильно-варочные камеры премиум-класса",
  },
  {
    id: "kerres",
    name: "Kerres",
    country: "Германия",
    url: "https://www.kerres.de",
    description: "Немецкие камеры для копчения и созревания",
  },
  {
    id: "agros",
    name: "Агрос",
    country: "Россия",
    url: "https://agros.su",
    description: "Российский производитель пищевого оборудования",
  },
];

export default function PipelinePage() {
  const [crawlingId, setCrawlingId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: results, isLoading } = useQuery({
    queryKey: ["pipeline-results"],
    queryFn: async () => {
      const { data } = await apiClient.get("/pipeline/results");
      return data as PipelineResults;
    },
    refetchInterval: 10000,
  });

  const crawlMutation = useMutation({
    mutationFn: async (name: string) => {
      setCrawlingId(name);
      const { data } = await apiClient.post(`/pipeline/crawl/competitor/${name}/sync`);
      return data as SyncResult;
    },
    onSuccess: () => {
      setCrawlingId(null);
      queryClient.invalidateQueries({ queryKey: ["pipeline-results"] });
    },
    onError: () => {
      setCrawlingId(null);
    },
  });

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-white">Knowledge Pipeline</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Парсинг сайтов конкурентов и каталогов коптильного оборудования
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 mb-1">
            <Globe className="h-4 w-4 text-feleti-gold" />
            <span className="text-xs text-muted-foreground">Конкуренты</span>
          </div>
          <div className="text-lg font-bold text-white">{results?.totals.competitors ?? 0}</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 mb-1">
            <FileText className="h-4 w-4 text-blue-400" />
            <span className="text-xs text-muted-foreground">Статьи</span>
          </div>
          <div className="text-lg font-bold text-white">{results?.totals.articles ?? 0}</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 mb-1">
            <Package className="h-4 w-4 text-emerald-400" />
            <span className="text-xs text-muted-foreground">Модели</span>
          </div>
          <div className="text-lg font-bold text-white">{results?.totals.models ?? 0}</div>
        </div>
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="flex items-center gap-2 mb-1">
            <Database className="h-4 w-4 text-purple-400" />
            <span className="text-xs text-muted-foreground">Источников</span>
          </div>
          <div className="text-lg font-bold text-white">{COMPETITORS.length}</div>
        </div>
      </div>

      {/* Competitor cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {COMPETITORS.map((comp, i) => (
          <motion.div
            key={comp.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
            className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="font-medium text-white">{comp.name}</h3>
                <p className="text-xs text-muted-foreground mt-0.5">{comp.country}</p>
              </div>
            </div>
            <p className="text-xs text-muted-foreground mb-4">{comp.description}</p>

            {/* Stats for this competitor */}
            {results?.competitors.find((c) => c.slug === comp.id) && (
              <div className="flex gap-3 mb-4 text-xs">
                <span className="text-muted-foreground">
                  Моделей:{" "}
                  <span className="text-white font-medium">
                    {results.competitors.find((c) => c.slug === comp.id)?.model_count ?? 0}
                  </span>
                </span>
                <span className="text-muted-foreground">
                  Проблем:{" "}
                  <span className="text-white font-medium">
                    {results.competitors.find((c) => c.slug === comp.id)?.problem_count ?? 0}
                  </span>
                </span>
              </div>
            )}

            <div className="flex items-center gap-2">
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => crawlMutation.mutate(comp.id)}
                disabled={crawlingId === comp.id}
                className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold/10 text-feleti-gold border border-feleti-gold/20 hover:bg-feleti-gold/20 px-4 py-2 text-sm font-medium transition-all cursor-pointer disabled:opacity-50"
              >
                {crawlingId === comp.id ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Парсинг...
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Запустить
                  </>
                )}
              </motion.button>
              <a
                href={comp.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-white transition-colors p-2"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Recent articles */}
      {results?.articles && results.articles.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="text-sm font-medium text-white mb-4">Последние статьи</h3>
          <div className="space-y-2">
            {results.articles.slice(0, 10).map((article) => (
              <Link
                key={article.id}
                href={`/knowledge/${article.slug}`}
                className="block rounded-xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/[0.03] transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="h-4 w-4 text-blue-400 shrink-0" />
                  <div className="min-w-0 flex-1">
                    <p className="text-sm text-white truncate">{article.title}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      {new Date(article.created_at).toLocaleDateString("ru-RU")}
                    </p>
                  </div>
                  <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                </div>
              </Link>
            ))}
          </div>
        </motion.div>
      )}

      {/* Recent models */}
      {results?.models && results.models.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
          <h3 className="text-sm font-medium text-white mb-4">Последние модели</h3>
          <div className="overflow-hidden rounded-xl border border-white/5">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="px-4 py-3 text-left font-medium text-muted-foreground">Название</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Загрузка</th>
                  <th className="px-4 py-3 text-right font-medium text-muted-foreground">Мощность</th>
                </tr>
              </thead>
              <tbody>
                {results.models.slice(0, 10).map((model) => (
                  <tr key={model.id} className="border-b border-white/5">
                    <td className="px-4 py-3 text-white">{model.name}</td>
                    <td className="px-4 py-3 text-right text-muted-foreground">
                      {model.max_load_kg ? `${model.max_load_kg} кг` : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground">
                      {model.power_kw ? `${model.power_kw} кВт` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}

      {/* Empty state */}
      {!isLoading && (!results || results.totals.articles === 0) && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
          <Globe className="h-12 w-12 text-muted-foreground/30" />
          <p className="mt-4 text-muted-foreground">Данные ещё не собраны</p>
          <p className="text-xs text-muted-foreground mt-1">
            Запустите парсинг одного из конкурентов
          </p>
        </div>
      )}
    </div>
  );
}

function ArrowRight({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
    </svg>
  );
}
