"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Edit3 } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { RecipeEditor } from "@/components/recipes/RecipeEditor";
import type { FormData } from "@/components/recipes/RecipeEditor";

interface RecipeVersion {
  id: number;
  version_number: number;
  program: Record<string, unknown>[];
  ingredients: Record<string, unknown>[];
  brine: Record<string, unknown> | null;
  yield_percent: number | null;
  losses_percent: number | null;
  notes: string | null;
  gost: string | null;
  source: string | null;
  verified: boolean;
  status: string;
}

interface Recipe {
  id: number;
  name: string;
  slug: string;
  product_id: number;
  description: string | null;
  status: string;
  tags: string[];
  current_version: RecipeVersion | null;
}

function recipeToFormData(recipe: Recipe, version?: RecipeVersion | null): FormData {
  const v = version || recipe.current_version;
  const phases = v?.program?.map((p: Record<string, unknown>) => ({
    name: String(p.name || ""),
    t_chamber: Number(p.t_chamber || 0),
    duration_min: Number(p.duration_min || 0),
    humidity: Number(p.humidity || 0),
    smoke: p.smoke === "none" ? "без дыма" : p.smoke === "medium" ? "дым" : "электро",
    wood_species: String(p.wood_species || ""),
    t_product: Number(p.t_product_target || 0),
  })) || [];

  const brineData = v?.brine;
  const brine = brineData
    ? {
        method: String(brineData.method || "мокрый"),
        salt_percent: Number(brineData.salt_percent || 0),
        sugar_percent: Number(brineData.sugar_percent || 0),
        nitrite_ppm: Number(brineData.nitrite_ppm || 0),
        duration_hours: Number(brineData.duration_hours || 0),
        temp_c: Number(brineData.temp_c || 0),
        water_percent: Number(brineData.water_percent || 0),
      }
    : null;

  const ingredients = v?.ingredients?.map((i: Record<string, unknown>) => ({
    ingredient_id: Number(i.ingredient_id || i.id || 0),
    name: String(i.name || ""),
    mass_kg: Number(i.mass_kg || i.percent || 0) || 1,
  })) || [];

  return {
    name: recipe.name,
    slug: recipe.slug,
    product_id: recipe.product_id,
    description: recipe.description || "",
    tags: recipe.tags || [],
    phases,
    brine,
    ingredients,
    yield_percent: v?.yield_percent ?? 0,
    losses_percent: v?.losses_percent ?? 0,
    notes: v?.notes || "",
    gost: v?.gost || "",
    source: v?.source || "",
  };
}

export default function EditRecipePage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: recipe, isLoading } = useQuery({
    queryKey: ["recipe-edit", slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/recipes/by-slug/${slug}`);
      return data as Recipe;
    },
  });

  const handleSave = async (data: FormData) => {
    if (!recipe) return;
    setSaving(true);
    setError(null);
    try {
      await apiClient.patch(`/recipes/${recipe.id}`, {
        name: data.name,
        description: data.description || null,
        tags: data.tags,
      });

      const versionPayload = {
        program: data.phases.map((p) => ({
          name: p.name,
          t_chamber: p.t_chamber,
          duration_min: p.duration_min,
          humidity: p.humidity || 0,
          smoke: p.smoke === "без дыма" ? "none" : p.smoke === "дым" ? "medium" : "heavy",
          ...(p.wood_species ? { wood_species: p.wood_species } : {}),
          ...(p.t_product > 0 ? { t_product_target: p.t_product } : {}),
        })),
        brine: data.brine
          ? {
              method: data.brine.method,
              salt_percent: data.brine.salt_percent,
              ...(data.brine.sugar_percent ? { sugar_percent: data.brine.sugar_percent } : {}),
              ...(data.brine.nitrite_ppm ? { nitrite_ppm: data.brine.nitrite_ppm } : {}),
              duration_hours: data.brine.duration_hours,
              temp_c: data.brine.temp_c,
              ...(data.brine.water_percent ? { water_percent: data.brine.water_percent } : {}),
            }
          : null,
        ingredients: data.ingredients.map((i) => ({
          ingredient_id: i.ingredient_id,
          name: i.name,
          mass_kg: i.mass_kg,
        })),
        yield_percent: data.yield_percent || null,
        losses_percent: data.losses_percent || null,
        notes: data.notes || null,
        gost: data.gost || null,
        source: data.source || null,
      };

      await apiClient.post(`/recipes/${recipe.id}/versions`, versionPayload);
      router.push(`/recipes/${data.slug}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка сохранения рецепта";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-6 w-32 animate-pulse rounded bg-white/5" />
        <div className="h-8 w-48 animate-pulse rounded-lg bg-white/5" />
        <div className="h-[600px] animate-pulse rounded-2xl bg-white/5" />
      </div>
    );
  }

  if (!recipe) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Рецепт не найден</p>
        <Link
          href="/recipes"
          className="mt-4 text-sm text-feleti-gold hover:underline"
        >
          Вернуться к списку
        </Link>
      </div>
    );
  }

  const initialData = recipeToFormData(recipe, recipe.current_version);

  return (
    <div className="space-y-6">
      <div>
        <Link
          href={`/recipes/${slug}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к рецепту
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            <Edit3 className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Редактировать</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{recipe.name}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <RecipeEditor
        mode="edit"
        initialData={initialData}
        onSave={handleSave}
        saving={saving}
      />
    </div>
  );
}
