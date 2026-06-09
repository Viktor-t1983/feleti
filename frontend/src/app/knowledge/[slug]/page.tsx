"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  ArrowLeft, Tag, Calendar, User,
  Sparkles, Loader2, AlertTriangle, CheckCircle, XCircle,
  Wrench, Lightbulb, Target, Globe, FileText, Package,
  FlaskConical, Bug, ChevronDown, ChevronUp
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState, type ReactNode } from "react";

interface KnowledgeArticle {
  id: number;
  title: string;
  slug: string;
  body_md: string;
  excerpt: string | null;
  category: string;
  tags: string[];
  author: { full_name: string | null; username: string } | null;
  created_at: string;
  updated_at: string;
  competitor_id: number | null;
}

interface ArticleAnalysis {
  id: number;
  article_id: number;
  products: string[];
  technologies: string[];
  problems: { title: string; description: string; severity: string }[];
  equipment: { name: string; specs: Record<string, string> }[];
  key_insights: string[];
  competitor_mentions: { name: string; products: string[]; pricing: string | null }[];
  target_markets: string[];
  ai_category: string | null;
  model_used: string | null;
  status: "pending" | "running" | "done" | "error";
  error: string | null;
  analyzed_at: string | null;
}

async function fetchArticle(slug: string): Promise<KnowledgeArticle> {
  const { data } = await apiClient.get(`/knowledge/by-slug/${slug}`);
  return data;
}

async function fetchAnalysis(articleId: number): Promise<ArticleAnalysis | null> {
  try {
    const { data } = await apiClient.get(`/knowledge/${articleId}/analysis`);
    return data;
  } catch {
    return null;
  }
}

async function triggerAnalysis(articleId: number): Promise<void> {
  await apiClient.post(`/knowledge/${articleId}/analyze`);
}

function renderMarkdown(md: string): string {
  // Simple markdown to HTML conversion
  return md
    .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-white mb-4">$1</h1>')
    .replace(/^## (.*$)/gim, '<h2 class="text-xl font-semibold text-white mt-6 mb-3">$1</h2>')
    .replace(/^### (.*$)/gim, '<h3 class="text-lg font-medium text-white mt-4 mb-2">$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong class="text-white">$1</strong>')
    .replace(/\*(.*?)\*/g, '<em class="text-muted-foreground">$1</em>')
    .replace(/^\d+\.\s+(.*$)/gim, '<li class="text-muted-foreground ml-4">$1</li>')
    .replace(/^- (.*$)/gim, '<li class="text-muted-foreground ml-4">$1</li>')
    .replace(/\n\n/g, '</p><p class="text-muted-foreground mb-3">')
    .replace(/\|(.+)\|/g, (match) => {
      if (match.includes('---')) return '';
      const cells = match.split('|').filter(c => c.trim());
      if (cells.length === 0) return '';
      return `<tr class="border-b border-white/5">${cells.map(c => `<td class="px-3 py-2 text-sm text-muted-foreground">${c.trim()}</td>`).join('')}</tr>`;
    })
    .replace(/<tr/g, '<table class="w-full text-sm mb-4"><thead class="bg-white/5"><tr')
    .replace(/<\/tr>/g, '</tr></thead></table>');
}

export default function KnowledgeDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const queryClient = useQueryClient();
  const [analysisOpen, setAnalysisOpen] = useState(false);

  const { data: article, isLoading } = useQuery({
    queryKey: ["knowledge", slug],
    queryFn: () => fetchArticle(slug),
  });

  const { data: analysis, isLoading: analysisLoading } = useQuery({
    queryKey: ["knowledge", slug, "analysis"],
    queryFn: () => article ? fetchAnalysis(article.id) : null,
    enabled: !!article,
  });

  const analyzeMutation = useMutation({
    mutationFn: () => article ? triggerAnalysis(article.id) : Promise.reject(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge", slug, "analysis"] });
      setAnalysisOpen(true);
    },
  });

  if (isLoading) {
    return <ArticleSkeleton />;
  }

  if (!article) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Статья не найдена</p>
        <Link
          href="/knowledge"
          className="mt-4 text-sm text-feleti-gold hover:underline"
        >
          Вернуться к базе знаний
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/knowledge"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к базе знаний
        </Link>
        <h1 className="text-3xl font-bold text-white">{article.title}</h1>
        {article.excerpt && (
          <p className="text-lg text-muted-foreground mt-3">{article.excerpt}</p>
        )}
      </div>

      {/* Meta */}
      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground border-y border-white/5 py-3">
        <span className="flex items-center gap-1">
          <Calendar className="h-3.5 w-3.5" />
          {new Date(article.created_at).toLocaleDateString("ru-RU")}
        </span>
        {article.author && (
          <span className="flex items-center gap-1">
            <User className="h-3.5 w-3.5" />
            {article.author.full_name || article.author.username}
          </span>
        )}
        <div className="flex gap-1.5">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full bg-white/5 px-2 py-0.5 text-xs"
            >
              <Tag className="h-2.5 w-2.5" />
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Content */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="prose prose-invert max-w-none"
        dangerouslySetInnerHTML={{
          __html: renderMarkdown(article.body_md),
        }}
      />

      {/* AI Analysis Section */}
      <div className="border border-white/10 rounded-lg overflow-hidden">
        <button
          onClick={() => setAnalysisOpen(!analysisOpen)}
          className="w-full flex items-center justify-between px-4 py-3 bg-white/5 hover:bg-white/10 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-feleti-gold" />
            <span className="text-sm font-medium text-white">AI-анализ статьи</span>
            {analysis?.status === "done" && (
              <CheckCircle className="h-3.5 w-3.5 text-green-400" />
            )}
            {analysis?.status === "running" && (
              <Loader2 className="h-3.5 w-3.5 text-yellow-400 animate-spin" />
            )}
            {analysis?.status === "error" && (
              <XCircle className="h-3.5 w-3.5 text-red-400" />
            )}
          </div>
          {analysisOpen ? <ChevronUp className="h-4 w-4 text-muted-foreground" /> : <ChevronDown className="h-4 w-4 text-muted-foreground" />}
        </button>

        {analysisOpen && (
          <div className="p-4 space-y-4">
            {analysisLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 text-feleti-gold animate-spin" />
              </div>
            ) : !analysis ? (
              <div className="text-center py-6 space-y-3">
                <Sparkles className="h-8 w-8 text-muted-foreground mx-auto" />
                <p className="text-sm text-muted-foreground">
                  AI-анализ ещё не выполнен. Запустите анализ, чтобы извлечь продукты, технологии и инсайты из статьи.
                </p>
                <button
                  onClick={() => analyzeMutation.mutate()}
                  disabled={analyzeMutation.isPending}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-feleti-gold/20 text-feleti-gold border border-feleti-gold/30 rounded-lg hover:bg-feleti-gold/30 transition-colors text-sm disabled:opacity-50"
                >
                  {analyzeMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  {analyzeMutation.isPending ? "Анализирую..." : "Запустить AI-анализ"}
                </button>
              </div>
            ) : analysis.status === "running" ? (
              <div className="flex items-center justify-center gap-3 py-8">
                <Loader2 className="h-5 w-5 text-feleti-gold animate-spin" />
                <span className="text-sm text-muted-foreground">Анализ выполняется...</span>
              </div>
            ) : analysis.status === "error" ? (
              <div className="flex items-start gap-3 p-3 bg-red-500/10 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-400 shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-red-400">Ошибка анализа</p>
                  <p className="text-xs text-red-300/70 mt-1">{analysis.error}</p>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                {analysis.ai_category && (
                  <div className="flex items-center gap-2">
                    <FileText className="h-4 w-4 text-feleti-gold" />
                    <span className="text-xs text-muted-foreground">Категория AI:</span>
                    <span className="text-xs text-white bg-white/10 px-2 py-0.5 rounded">{analysis.ai_category}</span>
                  </div>
                )}

                {analysis.products.length > 0 && (
                  <AnalysisSection icon={<Package className="h-4 w-4" />} title="Продукты" items={analysis.products} />
                )}

                {analysis.technologies.length > 0 && (
                  <AnalysisSection icon={<FlaskConical className="h-4 w-4" />} title="Технологии" items={analysis.technologies} />
                )}

                {analysis.equipment.length > 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-2">
                      <Wrench className="h-4 w-4 text-feleti-gold" />
                      Оборудование
                    </h4>
                    <div className="space-y-2">
                      {analysis.equipment.map((eq, i) => (
                        <div key={i} className="p-2 bg-white/5 rounded text-sm">
                          <span className="text-white font-medium">{eq.name}</span>
                          {Object.keys(eq.specs).length > 0 && (
                            <div className="mt-1 text-xs text-muted-foreground grid grid-cols-2 gap-1">
                              {Object.entries(eq.specs).map(([k, v]) => (
                                <span key={k}>{k}: {v}</span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.problems.length > 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-2">
                      <Bug className="h-4 w-4 text-feleti-gold" />
                      Проблемы
                    </h4>
                    <div className="space-y-2">
                      {analysis.problems.map((p, i) => (
                        <div key={i} className="p-2 bg-white/5 rounded text-sm">
                          <div className="flex items-center gap-2">
                            <span className="text-white font-medium">{p.title}</span>
                            <span className={`text-xs px-1.5 py-0.5 rounded ${
                              p.severity === "high" ? "bg-red-500/20 text-red-400" :
                              p.severity === "medium" ? "bg-yellow-500/20 text-yellow-400" :
                              "bg-green-500/20 text-green-400"
                            }`}>{p.severity}</span>
                          </div>
                          {p.description && (
                            <p className="text-xs text-muted-foreground mt-1">{p.description}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.competitor_mentions.length > 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-2">
                      <Target className="h-4 w-4 text-feleti-gold" />
                      Упоминания конкурентов
                    </h4>
                    <div className="space-y-2">
                      {analysis.competitor_mentions.map((m, i) => (
                        <div key={i} className="p-2 bg-white/5 rounded text-sm">
                          <span className="text-white font-medium">{m.name}</span>
                          {m.products.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-1">
                              {m.products.map((p) => (
                                <span key={p} className="text-xs bg-white/5 px-1.5 py-0.5 rounded">{p}</span>
                              ))}
                            </div>
                          )}
                          {m.pricing && <p className="text-xs text-muted-foreground mt-0.5">Цены: {m.pricing}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {analysis.target_markets.length > 0 && (
                  <AnalysisSection icon={<Globe className="h-4 w-4" />} title="Целевые рынки" items={analysis.target_markets} />
                )}

                {analysis.key_insights.length > 0 && (
                  <div>
                    <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-2">
                      <Lightbulb className="h-4 w-4 text-feleti-gold" />
                      Ключевые инсайты
                    </h4>
                    <ul className="space-y-1">
                      {analysis.key_insights.map((insight, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span className="text-feleti-gold mt-1">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {analysis.analyzed_at && (
                  <p className="text-xs text-muted-foreground text-right">
                    Анализ выполнен: {new Date(analysis.analyzed_at).toLocaleString("ru-RU")}
                    {analysis.model_used && ` • Модель: ${analysis.model_used}`}
                  </p>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function AnalysisSection({ icon, title, items }: { icon: ReactNode; title: string; items: string[] }) {
  return (
    <div>
      <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-2">
        {icon}
        {title}
      </h4>
      <div className="flex flex-wrap gap-1.5">
        {items.map((item, i) => (
          <span key={i} className="text-xs bg-white/5 text-muted-foreground px-2 py-1 rounded">
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

function ArticleSkeleton() {
  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="h-8 w-32 animate-pulse rounded bg-white/5" />
      <div className="h-12 w-3/4 animate-pulse rounded-lg bg-white/5" />
      <div className="h-4 w-full animate-pulse rounded bg-white/5" />
      <div className="h-4 w-2/3 animate-pulse rounded bg-white/5" />
      <div className="space-y-3">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="h-4 animate-pulse rounded bg-white/5" />
        ))}
      </div>
    </div>
  );
}
