"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  BookOpen,
  Search,
  Tag,
  ArrowRight,
  Lightbulb,
  Wrench,
  Scale,
  GraduationCap,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

interface KnowledgeArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  category: string;
  tags: string[];
  author: { full_name: string | null; username: string } | null;
  created_at: string;
}

interface KnowledgePage {
  items: KnowledgeArticle[];
  total: number;
}

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  theory: { label: "Теория", icon: GraduationCap, color: "text-blue-400", bg: "bg-blue-500/10" },
  recipe: { label: "Рецепт", icon: BookOpen, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  troubleshooting: { label: "Решение проблем", icon: Wrench, color: "text-amber-400", bg: "bg-amber-500/10" },
  regulation: { label: "Нормативы", icon: Scale, color: "text-purple-400", bg: "bg-purple-500/10" },
  comparison: { label: "Сравнение", icon: Scale, color: "text-cyan-400", bg: "bg-cyan-500/10" },
  review: { label: "Обзор", icon: Lightbulb, color: "text-pink-400", bg: "bg-pink-500/10" },
  news: { label: "Новости", icon: Lightbulb, color: "text-orange-400", bg: "bg-orange-500/10" },
  guide: { label: "Руководство", icon: BookOpen, color: "text-feleti-gold", bg: "bg-feleti-gold/10" },
};

async function fetchKnowledge(): Promise<KnowledgePage> {
  const { data } = await apiClient.get("/knowledge?size=50&is_published=true");
  return data;
}

export default function KnowledgePage() {
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");

  const { data, isLoading } = useQuery({
    queryKey: ["knowledge"],
    queryFn: fetchKnowledge,
  });

  const articles = data?.items || [];
  const filtered = articles.filter((a) => {
    const matchesSearch =
      a.title.toLowerCase().includes(search.toLowerCase()) ||
      (a.excerpt?.toLowerCase() || "").includes(search.toLowerCase()) ||
      a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()));
    const matchesCategory =
      categoryFilter === "all" || a.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  const categories = Array.from(
    new Set(articles.map((a) => a.category))
  ).sort();

  if (isLoading) {
    return <KnowledgeSkeleton />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">База знаний</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Теория, руководства и лучшие практики копчения
        </p>
      </div>

      {/* Search & filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по статьям..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2.5 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
        >
          <option value="all" className="bg-[#1a1a1a]">Все категории</option>
          {categories.map((c) => (
            <option key={c} value={c} className="bg-[#1a1a1a]">
              {CATEGORY_CONFIG[c]?.label || c}
            </option>
          ))}
        </select>
      </div>

      {/* Articles */}
      <div className="grid gap-4 sm:grid-cols-2">
        {filtered.map((article, i) => (
          <ArticleCard key={article.id} article={article} index={i} />
        ))}
      </div>

      {filtered.length === 0 && (
        <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
          <BookOpen className="h-12 w-12 text-muted-foreground/30" />
          <p className="mt-4 text-muted-foreground">Статьи не найдены</p>
        </div>
      )}
    </div>
  );
}

function ArticleCard({
  article,
  index,
}: {
  article: KnowledgeArticle;
  index: number;
}) {
  const config = CATEGORY_CONFIG[article.category] || {
    label: article.category,
    icon: BookOpen,
    color: "text-muted-foreground",
    bg: "bg-white/5",
  };
  const CategoryIcon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.08, duration: 0.3 }}
    >
      <Link
        href={`/knowledge/${article.slug}`}
        className="group block rounded-2xl border border-white/5 bg-white/[0.02] p-5 hover:bg-white/[0.03] hover:border-white/10 transition-colors h-full"
      >
        <div className="flex items-start justify-between mb-3">
          <span
            className={`inline-flex items-center gap-1 rounded-full ${config.bg} px-2 py-0.5 text-xs ${config.color}`}
          >
            <CategoryIcon className="h-3 w-3" />
            {config.label}
          </span>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
        </div>

        <h3 className="font-medium text-white mb-2">{article.title}</h3>
        {article.excerpt && (
          <p className="text-sm text-muted-foreground line-clamp-2 mb-3">
            {article.excerpt}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-2 mt-auto">
          {article.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5 text-xs text-muted-foreground"
            >
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
          <span className="text-xs text-muted-foreground/60 ml-auto">
            {new Date(article.created_at).toLocaleDateString("ru-RU")}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}

function KnowledgeSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="h-10 animate-pulse rounded-xl bg-white/5" />
      <div className="grid gap-4 sm:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-40 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
