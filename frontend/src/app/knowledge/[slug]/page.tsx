"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Tag, Calendar, User } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useParams } from "next/navigation";

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
}

async function fetchArticle(slug: string): Promise<KnowledgeArticle> {
  const { data } = await apiClient.get("/knowledge?size=50&is_published=true");
  const article = data.items.find((a: KnowledgeArticle) => a.slug === slug);
  if (!article) throw new Error("Статья не найдена");
  return article;
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

  const { data: article, isLoading } = useQuery({
    queryKey: ["knowledge", slug],
    queryFn: () => fetchArticle(slug),
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
    <div className="max-w-3xl mx-auto space-y-6">
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
