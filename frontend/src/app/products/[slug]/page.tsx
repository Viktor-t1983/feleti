"use client";

import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Tag,
  ArrowLeft,
  Clock,
  Thermometer,
  Droplets,
  BookOpen,
  FileText,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useParams } from "next/navigation";

interface ProductDetail {
  id: number;
  name: string;
  slug: string;
  category: string;
  description: string | null;
  images: string[];
  gost: string | null;
  shelf_life_days: number | null;
  storage_temp_min: number | null;
  storage_temp_max: number | null;
  storage_humidity_min: number | null;
  storage_humidity_max: number | null;
  base_recipe_id: number | null;
  created_at: string;
  updated_at: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  "колбаса вареная": "Варёные колбасы",
  "колбаса полукопченая": "Полукопчёные колбасы",
  "колбаса сырокопченая": "Сырокопчёные колбасы",
  "колбаса сыровяленая": "Сыровяленые колбасы",
  мясо: "Мясо",
  птица: "Птица",
  "рыба горячего копчения": "Рыба горячего копчения",
  "рыба холодного копчения": "Рыба холодного копчения",
  "рыба электростатического копчения": "Рыба э/к",
  сыр: "Сыр",
  сало: "Сало",
  масло: "Масло",
  снеки: "Снеки",
  прочее: "Прочее",
};

function formatDate(s: string | null): string {
  if (!s) return "—";
  return new Date(s).toLocaleString("ru-RU", {
    day: "numeric", month: "long", year: "numeric",
  });
}

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/products/by-slug/${slug}`);
      return data as ProductDetail;
    },
  });

  if (isLoading) return <ProductDetailSkeleton />;
  if (!product) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Продукт не найден</p>
        <Link href="/products" className="mt-4 text-sm text-feleti-gold hover:underline">Вернуться к списку</Link>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/products"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к продуктам
        </Link>
        <div className="flex items-start gap-4">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-feleti-gold/10 shrink-0">
            <Tag className="h-7 w-7 text-feleti-gold" />
          </div>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-white">{product.name}</h1>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <span className="inline-flex items-center rounded-full border border-feleti-gold/20 bg-feleti-gold/10 px-3 py-1 text-xs font-medium text-feleti-gold">
                {CATEGORY_LABELS[product.category] || product.category}
              </span>
              {product.gost && (
                <span className="inline-flex items-center rounded-full border border-white/10 bg-white/[0.04] px-3 py-1 text-xs font-medium text-muted-foreground">
                  {product.gost}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Storage info */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <InfoCard icon={Clock} label="Срок хранения" value={product.shelf_life_days ? `${product.shelf_life_days} дн.` : "—"} />
        <InfoCard icon={Thermometer} label="Температура" value={
          product.storage_temp_min != null || product.storage_temp_max != null
            ? `${product.storage_temp_min ?? "?"}…${product.storage_temp_max ?? "?"}°C`
            : "—"
        } />
        <InfoCard icon={Droplets} label="Влажность" value={
          product.storage_humidity_min != null || product.storage_humidity_max != null
            ? `${product.storage_humidity_min ?? "?"}…${product.storage_humidity_max ?? "?"}%`
            : "—"
        } />
        <InfoCard icon={FileText} label="Дата создания" value={formatDate(product.created_at)} />
      </div>

      {/* Description */}
      {product.description && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-white/5 bg-white/[0.02] p-5"
        >
          <h3 className="text-sm font-medium text-white mb-2">Описание</h3>
          <p className="text-sm text-muted-foreground whitespace-pre-wrap">{product.description}</p>
        </motion.div>
      )}

      {/* Images */}
      {product.images && product.images.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-2 sm:grid-cols-4 gap-4"
        >
          {product.images.map((url, i) => (
            <img
              key={i}
              src={url}
              alt={`${product.name} ${i + 1}`}
              className="rounded-xl border border-white/5 object-cover aspect-square"
            />
          ))}
        </motion.div>
      )}

      {/* Related recipes hint */}
      {product.base_recipe_id && (
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
        >
          <Link
            href={`/recipes?product_id=${product.base_recipe_id}`}
            className="inline-flex items-center gap-2 rounded-xl border border-feleti-gold/20 bg-feleti-gold/10 px-5 py-3 text-sm font-medium text-feleti-gold transition-all hover:bg-feleti-gold/20"
          >
            <BookOpen className="h-4 w-4" />
            Базовый рецепт
          </Link>
        </motion.div>
      )}
    </div>
  );
}

function InfoCard({ icon: Icon, label, value }: { icon: React.ElementType; label: string; value: string }) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-4 w-4 text-feleti-gold" />
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-sm font-medium text-white">{value}</div>
    </div>
  );
}

function ProductDetailSkeleton() {
  return (
    <div className="space-y-8">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-white/5" />
      <div className="grid grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
