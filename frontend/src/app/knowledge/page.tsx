"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  Search,
  Tag,
  Folder,
  FolderOpen,
  ChevronRight,
  ChevronDown,
  Wrench,
  Scale,
  GraduationCap,
  SortAsc,
  SortDesc,
  Calendar,
  Type,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { ErrorState } from "@/components/shared/ErrorState";
import Link from "next/link";

/* ─── Types ─── */

interface TreeItem {
  path: string;
  label: string;
  count: number;
  children: TreeItem[];
}

interface KnowledgeArticle {
  id: number;
  title: string;
  slug: string;
  excerpt: string | null;
  category: string;
  tags: string[];
  topic_path: string | null;
  ai_category: string | null;
  competitor_id: number | null;
  created_at: string;
}

interface KnowledgePage {
  items: KnowledgeArticle[];
  total: number;
  page: number;
}

type SortField = "created_at" | "title";
type SortDir = "asc" | "desc";

/* ─── Config ─── */

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ElementType; color: string; bg: string }> = {
  theory: { label: "Теория", icon: GraduationCap, color: "text-blue-400", bg: "bg-blue-500/10" },
  recipe: { label: "Рецепт", icon: BookOpen, color: "text-emerald-400", bg: "bg-emerald-500/10" },
  troubleshooting: { label: "Решение проблем", icon: Wrench, color: "text-amber-400", bg: "bg-amber-500/10" },
  regulation: { label: "Нормативы", icon: Scale, color: "text-purple-400", bg: "bg-purple-500/10" },
};

/* ─── Tree component ─── */

function TreeNode({ node, depth, selected, onSelect }: {
  node: TreeItem;
  depth: number;
  selected: string | null;
  onSelect: (path: string) => void;
}) {
  const [open, setOpen] = useState(depth < 1);
  const hasChildren = node.children.length > 0;
  const isSelected = selected === node.path;
  const isDescendantSelected = selected && selected.startsWith(node.path + "/");

  return (
    <div>
      <button
        onClick={() => {
          onSelect(node.path);
          if (hasChildren) setOpen(!open);
        }}
        className={`flex w-full items-center gap-1.5 rounded-lg px-2 py-1.5 text-left text-sm transition-colors ${
          isSelected
            ? "bg-feleti-gold/15 text-feleti-gold"
            : isDescendantSelected
              ? "text-feleti-gold/70"
              : "text-muted-foreground hover:text-white hover:bg-white/5"
        }`}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {hasChildren ? (
          open ? <ChevronDown className="h-3.5 w-3.5 shrink-0" /> : <ChevronRight className="h-3.5 w-3.5 shrink-0" />
        ) : (
          <span className="w-3.5 shrink-0" />
        )}
        {open ? <FolderOpen className="h-3.5 w-3.5 shrink-0" /> : <Folder className="h-3.5 w-3.5 shrink-0" />}
        <span className="truncate flex-1">{node.label}</span>
        <span className="text-xs text-muted-foreground/50">{node.count}</span>
      </button>
      <AnimatePresence initial={false}>
        {open && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            {node.children.map((child) => (
              <TreeNode key={child.path} node={child} depth={depth + 1} selected={selected} onSelect={onSelect} />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Main page ─── */

export default function KnowledgeLibrary() {
  const [search, setSearch] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>("created_at");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  const treeQuery = useQuery({
    queryKey: ["knowledge-tree"],
    queryFn: () => apiClient.get("/knowledge/tree").then((r) => r.data as TreeItem[]),
    staleTime: 60000,
  });

  const articlesQuery = useQuery({
    queryKey: ["knowledge", selectedPath, sortField, sortDir],
    queryFn: () => {
      const params = new URLSearchParams({ size: "200", sort_by: sortField, sort_order: sortDir });
      if (selectedPath) params.set("topic_path", selectedPath);
      return apiClient.get(`/knowledge?${params}`).then((r) => r.data as KnowledgePage);
    },
    staleTime: 10000,
  });

  const articles = articlesQuery.data?.items || [];
  const filtered = search
    ? articles.filter((a) =>
        a.title.toLowerCase().includes(search.toLowerCase()) ||
        (a.excerpt?.toLowerCase() || "").includes(search.toLowerCase()) ||
        a.tags.some((t) => t.toLowerCase().includes(search.toLowerCase()))
      )
    : articles;

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else { setSortField(field); setSortDir("desc"); }
  };

  return (
    <div className="flex gap-5 h-[calc(100vh-7rem)]">
      {/* Sidebar */}
      <aside className="w-64 shrink-0 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-white">Папки</h2>
          <span className="text-xs text-muted-foreground/50">{articlesQuery.data?.total ?? 0} ст.</span>
        </div>
        <div className="flex-1 overflow-y-auto space-y-0.5 pr-2 scrollbar-thin">
          {/* All articles */}
          <button
            onClick={() => setSelectedPath(null)}
            className={`flex w-full items-center gap-2 rounded-lg px-3 py-1.5 text-sm transition-colors ${
              selectedPath === null ? "bg-feleti-gold/15 text-feleti-gold" : "text-muted-foreground hover:text-white hover:bg-white/5"
            }`}
          >
            <BookOpen className="h-3.5 w-3.5" />
            <span>Все статьи</span>
          </button>
          <div className="h-px bg-white/5 my-1" />
          {treeQuery.error ? (
            <p className="text-xs text-red-400 px-2">Ошибка загрузки дерева</p>
          ) : treeQuery.isLoading ? (
            Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="h-7 animate-pulse rounded-lg bg-white/5 ml-3" style={{ width: `${60 + Math.random() * 30}%` }} />
            ))
          ) : (
            (treeQuery.data || []).map((node) => (
              <TreeNode key={node.path} node={node} depth={0} selected={selectedPath} onSelect={setSelectedPath} />
            ))
          )}
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Поиск..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
            />
          </div>
          <button
            onClick={() => toggleSort("created_at")}
            className={`inline-flex items-center gap-1 rounded-xl border px-3 py-2 text-xs transition-colors ${
              sortField === "created_at" ? "border-feleti-gold/30 text-feleti-gold" : "border-white/5 text-muted-foreground hover:text-white"
            }`}
          >
            <Calendar className="h-3 w-3" />
            {sortDir === "asc" ? <SortAsc className="h-3 w-3" /> : <SortDesc className="h-3 w-3" />}
          </button>
          <button
            onClick={() => toggleSort("title")}
            className={`inline-flex items-center gap-1 rounded-xl border px-3 py-2 text-xs transition-colors ${
              sortField === "title" ? "border-feleti-gold/30 text-feleti-gold" : "border-white/5 text-muted-foreground hover:text-white"
            }`}
          >
            <Type className="h-3 w-3" />
            {sortDir === "asc" ? "А-Я" : "Я-А"}
          </button>
        </div>

        {/* Articles grid */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          {articlesQuery.error ? (
            <ErrorState message="Ошибка загрузки статей" onRetry={() => articlesQuery.refetch()} />
          ) : articlesQuery.isLoading ? (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-36 animate-pulse rounded-2xl bg-white/5" />
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
              <BookOpen className="h-12 w-12 text-muted-foreground/30" />
              <p className="mt-4 text-muted-foreground">Ничего не найдено</p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
              {filtered.map((article, i) => (
                <ArticleCard key={article.id} article={article} index={i} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Article card ─── */

function ArticleCard({ article, index }: { article: KnowledgeArticle; index: number }) {
  const config = CATEGORY_CONFIG[article.category] || {
    label: article.ai_category || article.category,
    icon: BookOpen,
    color: "text-muted-foreground",
    bg: "bg-white/5",
  };
  const Icon = config.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
    >
      <Link
        href={`/knowledge/${article.slug}`}
        className="group block rounded-2xl border border-white/5 bg-white/[0.02] p-4 hover:bg-white/[0.03] hover:border-white/10 transition-colors h-full"
      >
        <div className="flex items-start justify-between mb-2">
          <span className={`inline-flex items-center gap-1 rounded-full ${config.bg} px-2 py-0.5 text-xs ${config.color}`}>
            <Icon className="h-3 w-3" />
            {config.label}
          </span>
          {article.topic_path && (
            <span className="text-[10px] text-muted-foreground/40 truncate max-w-[120px] text-right">
              {article.topic_path.split("/").pop()}
            </span>
          )}
        </div>
        <h3 className="font-medium text-sm text-white mb-1.5 line-clamp-2">{article.title}</h3>
        {article.excerpt && (
          <p className="text-xs text-muted-foreground line-clamp-2 mb-3">{article.excerpt}</p>
        )}
        <div className="flex flex-wrap items-center gap-1.5">
          {article.tags.slice(0, 2).map((tag) => (
            <span key={tag} className="inline-flex items-center gap-1 rounded-full bg-white/5 px-1.5 py-0.5 text-[10px] text-muted-foreground">
              <Tag className="h-2 w-2" />
              {tag}
            </span>
          ))}
          <span className="text-[10px] text-muted-foreground/50 ml-auto">
            {new Date(article.created_at).toLocaleDateString("ru-RU")}
          </span>
        </div>
      </Link>
    </motion.div>
  );
}
