"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BookOpen,
  Search,
  CheckCircle2,
  Clock,
  Thermometer,
  Droplets,
  ArrowRight,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

interface RecipePhase {
  name: string;
  duration_min: number;
  t_chamber: number;
  humidity?: number;
}

interface RecipeVersion {
  id: number;
  version_number: number;
  program: RecipePhase[];
  yield_percent: number | null;
  losses_percent: number | null;
  notes: string | null;
  gost: string | null;
  verified: boolean;
}

interface Recipe {
  id: number;
  name: string;
  slug: string;
  description: string | null;
  status: string;
  tags: string[];
  current_version: RecipeVersion | null;
}

interface RecipePage {
  items: Recipe[];
  total: number;
}

async function fetchRecipes(): Promise<RecipePage> {
  const { data } = await apiClient.get("/recipes?size=50");
  return data;
}

export default function RecipesPage() {
  const [search, setSearch] = useState("");
  const { data, isLoading } = useQuery({
    queryKey: ["recipes"],
    queryFn: fetchRecipes,
  });

  const recipes = data?.items || [];
  const filtered = recipes.filter(
    (r) =>
      r.name.toLowerCase().includes(search.toLowerCase()) ||
      (r.description?.toLowerCase() || "").includes(search.toLowerCase()) ||
      r.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
  );

  if (isLoading) {
    return <RecipesSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Рецепты</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Библиотека программ копчения
          </p>
        </div>
        <span className="text-sm text-muted-foreground">
          Всего: {data?.total || 0}
        </span>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Поиск по названию, описанию, тегам..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
        />
      </div>

      {/* Recipe cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {filtered.map((recipe, i) => (
          <RecipeCard key={recipe.id} recipe={recipe} index={i} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
          <BookOpen className="h-12 w-12 text-muted-foreground/30" />
          <p className="mt-4 text-muted-foreground">Рецепты не найдены</p>
        </div>
      )}
    </div>
  );
}

function RecipeCard({ recipe, index }: { recipe: Recipe; index: number }) {
  const version = recipe.current_version;
  const phases = version?.program || [];
  const totalTime = phases.reduce((sum, p) => sum + (p.duration_min || 0), 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
      className="group rounded-2xl border border-white/5 bg-white/[0.02] p-5 hover:bg-white/[0.03] hover:border-white/10 transition-colors"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-500/10">
            <BookOpen className="h-4 w-4 text-emerald-400" />
          </div>
          <h3 className="font-medium text-white">{recipe.name}</h3>
        </div>
        {version?.verified && (
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
        )}
      </div>

      {/* Description */}
      {recipe.description && (
        <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
          {recipe.description}
        </p>
      )}

      {/* Tags */}
      <div className="flex flex-wrap gap-1.5 mb-4">
        {recipe.tags.map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground"
          >
            {tag}
          </span>
        ))}
      </div>

      {/* Phases preview */}
      {phases.length > 0 && (
        <div className="space-y-1.5 mb-4">
          {phases.slice(0, 3).map((phase, j) => (
            <div
              key={j}
              className="flex items-center gap-2 text-xs text-muted-foreground"
            >
              <span className="h-1.5 w-1.5 rounded-full bg-feleti-gold" />
              <span className="flex-1">{phase.name}</span>
              <span className="flex items-center gap-1">
                <Thermometer className="h-3 w-3" />
                {phase.t_chamber}°C
              </span>
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {phase.duration_min} мин
              </span>
            </div>
          ))}
          {phases.length > 3 && (
            <p className="text-xs text-muted-foreground/60 pl-3.5">
              +{phases.length - 3} фаз
            </p>
          )}
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {totalTime} мин
          </span>
          {version?.yield_percent != null && (
            <span className="flex items-center gap-1">
              <Droplets className="h-3 w-3" />
              {version.yield_percent}% выход
            </span>
          )}
        </div>
        <Link
          href={`/recipes/${recipe.slug}`}
          className="flex items-center gap-1 text-xs text-feleti-gold hover:text-feleti-gold/80 transition-colors"
        >
          Подробнее
          <ArrowRight className="h-3 w-3" />
        </Link>
      </div>
    </motion.div>
  );
}

function RecipesSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="h-10 animate-pulse rounded-xl bg-white/5" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="h-64 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
