"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Tag,
  Search,
  ArrowRight,
  Thermometer,
  Droplets,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";

const CATEGORIES = [
  { id: "all", label: "Все" },
  { id: "колбаса вареная", label: "Варёные колбасы" },
  { id: "колбаса полукопченая", label: "Полукопчёные" },
  { id: "колбаса сырокопченая", label: "Сырокопчёные" },
  { id: "колбаса сыровяленая", label: "Сыровяленые" },
  { id: "мясо", label: "Мясо" },
  { id: "птица", label: "Птица" },
  { id: "рыба горячего копчения", label: "Рыба г/к" },
  { id: "рыба холодного копчения", label: "Рыба х/к" },
  { id: "рыба электростатического копчения", label: "Рыба э/к" },
  { id: "сыр", label: "Сыр" },
  { id: "сало", label: "Сало" },
  { id: "масло", label: "Масло" },
  { id: "снеки", label: "Снеки" },
  { id: "прочее", label: "Прочее" },
];

interface Product {
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
}

interface ProductPage {
  items: Product[];
  total: number;
}

function formatTemp(min: number | null, max: number | null): string {
  if (min == null && max == null) return "—";
  if (min != null && max != null) return `${min}…${max}°C`;
  return `${min ?? max}°C`;
}

function formatHumidity(min: number | null, max: number | null): string {
  if (min == null && max == null) return "—";
  if (min != null && max != null) return `${min}…${max}%`;
  return `${min ?? max}%`;
}

export default function ProductsPage() {
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["products", category, search],
    queryFn: async () => {
      const params = new URLSearchParams({ size: "200" });
      if (category !== "all") params.set("category", category);
      if (search) params.set("q", search);
      const { data } = await apiClient.get(`/products?${params}`);
      return data as ProductPage;
    },
  });

  const products = data?.items || [];
  const categorySet = products.reduce<Record<string, boolean>>((acc, p) => { acc[p.category] = true; return acc; }, {});
  const categories = Object.keys(categorySet);

  if (isLoading) return <ProductsSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Продукты</h1>
        <p className="text-sm text-muted-foreground mt-1">
          {data?.total || 0} продуктов в {categories.length} категориях
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1 overflow-x-auto max-w-full">
          {CATEGORIES.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setCategory(tab.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm transition-colors ${
                category === tab.id
                  ? "bg-white/10 text-white"
                  : "text-muted-foreground hover:text-white"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <div className="relative flex-1 max-w-xs">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск по названию..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>
      </div>

      {/* Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map((product, i) => (
          <ProductCard key={product.id} product={product} index={i} />
        ))}
        {products.length === 0 && (
          <div className="col-span-full flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
            <Tag className="h-12 w-12 text-muted-foreground/30" />
            <p className="mt-4 text-muted-foreground">Продукты не найдены</p>
          </div>
        )}
      </div>
    </div>
  );
}

function ProductCard({ product, index }: { product: Product; index: number }) {
  return (
    <Link href={`/products/${product.slug}`}>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.03 }}
        className="group rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition-all hover:bg-white/[0.03] h-full"
      >
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
              <Tag className="h-5 w-5 text-feleti-gold" />
            </div>
            <div>
              <h3 className="font-medium text-white">{product.name}</h3>
              {product.gost && (
                <p className="text-xs text-muted-foreground mt-0.5">{product.gost}</p>
              )}
            </div>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
        </div>

        {/* Storage info */}
        <div className="grid grid-cols-3 gap-3 text-xs">
          {product.shelf_life_days != null && (
            <div>
              <span className="text-muted-foreground">Хранение</span>
              <p className="text-white font-medium mt-0.5">{product.shelf_life_days} дн.</p>
            </div>
          )}
          {(product.storage_temp_min != null || product.storage_temp_max != null) && (
            <div>
              <span className="text-muted-foreground flex items-center gap-1">
                <Thermometer className="h-3 w-3" /> T
              </span>
              <p className="text-white font-medium mt-0.5">
                {formatTemp(product.storage_temp_min, product.storage_temp_max)}
              </p>
            </div>
          )}
          {(product.storage_humidity_min != null || product.storage_humidity_max != null) && (
            <div>
              <span className="text-muted-foreground flex items-center gap-1">
                <Droplets className="h-3 w-3" /> Влаж.
              </span>
              <p className="text-white font-medium mt-0.5">
                {formatHumidity(product.storage_humidity_min, product.storage_humidity_max)}
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </Link>
  );
}

function ProductsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="grid grid-cols-3 gap-4">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-32 animate-pulse rounded-2xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
