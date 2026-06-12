"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { Search, Package, AlertTriangle, Plus } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import { ErrorState } from "@/components/shared/ErrorState";
import Link from "next/link";

const TYPE_TABS = [
  { id: "all", label: "Все" },
  { id: "мясо", label: "Мясо" },
  { id: "жир", label: "Жир" },
  { id: "специя", label: "Специя" },
  { id: "соль", label: "Соль" },
  { id: "щепа", label: "Щепа" },
  { id: "жидкий дым", label: "Жидкий дым" },
  { id: "добавка", label: "Добавка" },
  { id: "прочее", label: "Прочее" },
];

interface IngredientRead {
  id: number;
  name: string;
  slug: string;
  type: string;
  protein_per_100g: number;
  fat_per_100g: number;
  carbs_per_100g: number;
  kcal_per_100g: number;
  price_per_kg: number;
  unit: string;
  is_allergen: boolean;
  allergens: string[];
  gmo_flag: boolean;
  wood_species: string | null;
  wood_form: string | null;
  fraction_mm: string | null;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

interface IngredientPage {
  items: IngredientRead[];
  total: number;
}

function formatBJU(value: number): string {
  if (value === 0) return "0";
  return value % 1 === 0 ? value.toString() : value.toFixed(1);
}

export default function IngredientsPage() {
  const [typeFilter, setTypeFilter] = useState("all");
  const [search, setSearch] = useState("");

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["ingredients", typeFilter, search],
    queryFn: async () => {
      const params = new URLSearchParams({ size: "200" });
      if (typeFilter !== "all") params.set("type", typeFilter);
      if (search) params.set("q", search);
      const { data } = await apiClient.get(`/ingredients?${params}`);
      return data as IngredientPage;
    },
  });

  const ingredients = data?.items || [];

  if (error && !isLoading) return <ErrorState message="Не удалось загрузить список ингредиентов" onRetry={() => refetch()} />;

  if (isLoading) return <IngredientsSkeleton />;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Ингредиенты</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Всего: {data?.total || 0}
        </p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <Link
          href="/ingredients/new"
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-4 py-2 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90"
        >
          <Plus className="h-4 w-4" />
          Новый
        </Link>
        <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1 overflow-x-auto max-w-full">
          {TYPE_TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setTypeFilter(tab.id)}
              className={`whitespace-nowrap rounded-lg px-3 py-1.5 text-sm transition-colors ${
                typeFilter === tab.id
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

      <div className="rounded-xl border border-white/5 bg-white/[0.02] overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/5 text-muted-foreground">
              <th className="text-left font-medium py-3 px-4">Название</th>
              <th className="text-left font-medium py-3 px-4">Тип</th>
              <th className="text-left font-medium py-3 px-4">Б/Ж/У</th>
              <th className="text-left font-medium py-3 px-4">Ккал</th>
              <th className="text-left font-medium py-3 px-4">Цена/кг</th>
              <th className="text-left font-medium py-3 px-4">Аллерген</th>
            </tr>
          </thead>
          <tbody>
            {ingredients.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="flex flex-col items-center justify-center py-16">
                    <Package className="h-12 w-12 text-muted-foreground/30" />
                    <p className="mt-4 text-muted-foreground">Ингредиенты не найдены</p>
                  </div>
                </td>
              </tr>
            ) : (
              ingredients.map((ingredient, i) => (
                <IngredientRow key={ingredient.id} ingredient={ingredient} index={i} />
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function IngredientRow({ ingredient, index }: { ingredient: IngredientRead; index: number }) {
  const router = useRouter();
  return (
    <motion.tr
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.03 }}
      className="border-b border-white/5 last:border-b-0 hover:bg-white/[0.03] transition-colors cursor-pointer"
      onClick={() => router.push(`/ingredients/${ingredient.slug}`)}
    >
      <td className="py-3 px-4 text-white font-medium">{ingredient.name}</td>
      <td className="py-3 px-4 text-muted-foreground capitalize">{ingredient.type}</td>
      <td className="py-3 px-4 text-muted-foreground">
        {formatBJU(ingredient.protein_per_100g)} / {formatBJU(ingredient.fat_per_100g)} / {formatBJU(ingredient.carbs_per_100g)}
      </td>
      <td className="py-3 px-4 text-muted-foreground">{ingredient.kcal_per_100g}</td>
      <td className="py-3 px-4 text-muted-foreground">{ingredient.price_per_kg.toFixed(2)} ₽</td>
      <td className="py-3 px-4">
        {ingredient.is_allergen ? (
          <span className="inline-flex items-center gap-1 text-amber-400" title={ingredient.allergens.join(", ")}>
            <AlertTriangle className="h-4 w-4" />
            <span className="text-xs">{ingredient.allergens.length > 0 ? ingredient.allergens.join(", ") : "Да"}</span>
          </span>
        ) : (
          <span className="text-muted-foreground/50">—</span>
        )}
      </td>
    </motion.tr>
  );
}

function IngredientsSkeleton() {
  return (
    <div className="space-y-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
      <div className="rounded-xl border border-white/5 overflow-hidden">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="h-12 animate-pulse bg-white/5 border-b border-white/5 last:border-b-0" />
        ))}
      </div>
    </div>
  );
}
