"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { ArrowLeft, Pencil, Beef, Weight, DollarSign, AlertTriangle, Flame, Droplets } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { ErrorState } from "@/components/shared/ErrorState";
import { INGREDIENT_TYPES } from "@/lib/api/ingredients";

interface IngredientRead {
  id: number;
  name: string;
  slug: string;
  type: string;
  protein_per_100g: number | null;
  fat_per_100g: number | null;
  carbs_per_100g: number | null;
  kcal_per_100g: number | null;
  price_per_kg: number | null;
  unit: string;
  is_allergen: boolean;
  gmo_flag: boolean;
  allergens: string[];
  wood_species: string | null;
  wood_form: string | null;
  fraction_mm: number | null;
  description: string | null;
  created_at: string;
  updated_at: string | null;
}

const TYPE_COLORS: Record<string, string> = {
  "мясо": "text-red-400 bg-red-500/10 border-red-500/20",
  "жир": "text-amber-400 bg-amber-500/10 border-amber-500/20",
  "специя": "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  "соль": "text-blue-400 bg-blue-500/10 border-blue-500/20",
  "щепа": "text-yellow-600 bg-yellow-600/10 border-yellow-600/20",
  "жидкий дым": "text-orange-400 bg-orange-500/10 border-orange-500/20",
  "добавка": "text-purple-400 bg-purple-500/10 border-purple-500/20",
  "прочее": "text-muted-foreground bg-white/5 border-white/10",
};

export default function IngredientDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const { data: ingredient, isLoading, error, refetch } = useQuery({
    queryKey: ["ingredient", slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/ingredients/${slug}`);
      return data as IngredientRead;
    },
    enabled: !!slug,
  });

  if (error && !isLoading) return <ErrorState message="Не удалось загрузить ингредиент" onRetry={() => refetch()} />;
  if (isLoading || !ingredient) return <IngredientSkeleton />;

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href="/ingredients" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4">
        <ArrowLeft className="h-4 w-4" />
        Назад к ингредиентам
      </Link>
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-feleti-gold/10 shrink-0">
            <Beef className="h-7 w-7 text-feleti-gold" />
          </div>
          <div className="min-w-0">
            <h1 className="text-2xl font-bold text-white">{ingredient.name}</h1>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className={`inline-flex items-center rounded-full border px-3 py-1 text-xs font-medium ${TYPE_COLORS[ingredient.type] || ""}`}>
                {INGREDIENT_TYPES.find((t) => t.id === ingredient.type)?.label || ingredient.type}
              </span>
              {ingredient.is_allergen && (
                <span className="inline-flex items-center gap-1 rounded-full border border-red-500/20 bg-red-500/10 px-3 py-1 text-xs font-medium text-red-400">
                  <AlertTriangle className="h-3 w-3" /> Аллерген
                </span>
              )}
              {ingredient.gmo_flag && (
                  <span className="inline-flex items-center gap-1 rounded-full border border-yellow-500/20 bg-yellow-500/10 px-3 py-1 text-xs font-medium text-yellow-400">
                    ГМО
                  </span>
              )}
            </div>
          </div>
        </div>
        <Link href={`/ingredients/${ingredient.slug}/edit`}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition-colors hover:bg-white/5">
          <Pencil className="h-4 w-4" />
          Редактировать
        </Link>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-8">
        {ingredient.protein_per_100g != null && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <span className="text-xs text-muted-foreground flex items-center gap-1"><Beef className="h-3.5 w-3.5" /> Белки</span>
            <p className="text-lg font-semibold text-white mt-1">{ingredient.protein_per_100g} г</p>
          </div>
        )}
        {ingredient.fat_per_100g != null && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <span className="text-xs text-muted-foreground flex items-center gap-1"><Droplets className="h-3.5 w-3.5" /> Жиры</span>
            <p className="text-lg font-semibold text-white mt-1">{ingredient.fat_per_100g} г</p>
          </div>
        )}
        {ingredient.carbs_per_100g != null && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <span className="text-xs text-muted-foreground flex items-center gap-1"><Flame className="h-3.5 w-3.5" /> Углеводы</span>
            <p className="text-lg font-semibold text-white mt-1">{ingredient.carbs_per_100g} г</p>
          </div>
        )}
        {ingredient.kcal_per_100g != null && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <span className="text-xs text-muted-foreground">Калории</span>
            <p className="text-lg font-semibold text-white mt-1">{ingredient.kcal_per_100g} ккал</p>
          </div>
        )}
        {ingredient.price_per_kg != null && (
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <span className="text-xs text-muted-foreground flex items-center gap-1"><DollarSign className="h-3.5 w-3.5" /> Цена</span>
            <p className="text-lg font-semibold text-white mt-1">{ingredient.price_per_kg} ₽/{ingredient.unit}</p>
          </div>
        )}
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <span className="text-xs text-muted-foreground flex items-center gap-1"><Weight className="h-3.5 w-3.5" /> Ед. изм.</span>
          <p className="text-lg font-semibold text-white mt-1">{ingredient.unit}</p>
        </div>
      </div>

      {ingredient.allergens.length > 0 && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Аллергены</h2>
          <div className="flex flex-wrap gap-2">
            {ingredient.allergens.map((a) => (
              <span key={a} className="rounded-full bg-red-500/10 px-3 py-1 text-sm text-red-400">{a}</span>
            ))}
          </div>
        </div>
      )}

      {(ingredient.wood_species || ingredient.wood_form || ingredient.fraction_mm) && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Параметры щепы</h2>
          <div className="flex flex-wrap gap-3 text-sm text-white/80">
            {ingredient.wood_species && <span>Древесина: {ingredient.wood_species}</span>}
            {ingredient.wood_form && <span>Форма: {ingredient.wood_form}</span>}
            {ingredient.fraction_mm && <span>Фракция: {ingredient.fraction_mm} мм</span>}
          </div>
        </div>
      )}

      {ingredient.description && (
        <div className="mt-6">
          <h2 className="text-sm font-medium text-muted-foreground mb-2">Описание</h2>
          <p className="text-sm text-white/80 leading-relaxed">{ingredient.description}</p>
        </div>
      )}
    </div>
  );
}

function IngredientSkeleton() {
  return (
    <div className="mx-auto max-w-2xl py-8 space-y-4">
      <div className="h-4 w-32 animate-pulse rounded bg-white/5" />
      <div className="flex gap-3">
        <div className="h-14 w-14 animate-pulse rounded-xl bg-white/5" />
        <div className="h-8 w-48 animate-pulse rounded bg-white/5" />
      </div>
      <div className="grid grid-cols-3 gap-3 mt-8">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-20 animate-pulse rounded-xl bg-white/5" />
        ))}
      </div>
    </div>
  );
}
