"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Search, BarChart3, Loader2 } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { apiClient } from "@/lib/api/client";
import { CompetitorCard } from "@/components/competitors/CompetitorCard";
import type { Competitor } from "@/components/competitors/CompetitorCard";

interface CompetitorsResponse {
  items: Competitor[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

async function fetchCompetitors(): Promise<CompetitorsResponse> {
  const response = await apiClient.get<CompetitorsResponse>("/competitors?page=1&size=20");
  return response.data;
}

export default function CompetitorsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);

  const [search, setSearch] = useState("");
  const [segment, setSegment] = useState("all");

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  const { data, isLoading } = useQuery({
    queryKey: ["competitors"],
    queryFn: fetchCompetitors,
    enabled: isAuthenticated,
  });

  const competitors = data?.items || [];

  const filtered = competitors.filter((c) => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase());
    const matchesSegment = segment === "all" || (c.segment || "").toLowerCase().includes(segment);
    return matchesSearch && matchesSegment;
  });

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
      <section className="px-6 py-12">
        <div className="mx-auto max-w-5xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <div className="flex items-center gap-3 mb-4">
              <BarChart3 className="h-6 w-6 text-feleti-gold" />
              <h1 className="text-3xl font-bold text-white">Анализ конкурентов</h1>
            </div>
            <p className="text-muted-foreground max-w-2xl">
              Полный разбор рынка коптильного оборудования. Данные из БД.
            </p>
          </motion.div>

          {/* Filters */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="mt-8 flex flex-col sm:flex-row gap-4"
          >
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Поиск по названию..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none focus:ring-1 focus:ring-feleti-gold/50"
              />
            </div>
            <select
              value={segment}
              onChange={(e) => setSegment(e.target.value)}
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white focus:border-feleti-gold/50 focus:outline-none"
            >
              <option value="all">Все сегменты</option>
              <option value="horeca">Horeca</option>
              <option value="profi">Profi</option>
              <option value="industrial">Industrial</option>
            </select>
          </motion.div>
        </div>
      </section>

      {/* Cards */}
      <section className="px-6 pb-24">
        <div className="mx-auto max-w-5xl space-y-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
            </div>
          ) : (
            filtered.map((competitor, index) => (
              <motion.div
                key={competitor.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.15 + index * 0.1 }}
              >
                <CompetitorCard competitor={competitor} />
              </motion.div>
            ))
          )}
        </div>
      </section>
    </main>
  );
}
