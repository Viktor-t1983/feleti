"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, PlusCircle } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { RecipeEditor } from "@/components/recipes/RecipeEditor";
import type { FormData } from "@/components/recipes/RecipeEditor";

export default function NewRecipePage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (data: FormData) => {
    setSaving(true);
    setError(null);
    try {
      const payload = {
        name: data.name,
        slug: data.slug,
        product_id: data.product_id,
        description: data.description || null,
        tags: data.tags,
        initial_version: {
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
        },
      };
      const response = await apiClient.post("/recipes", payload);
      router.push(`/recipes/${response.data.slug}`);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка создания рецепта";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/recipes"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к рецептам
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            <PlusCircle className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Новый рецепт</h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              Создайте программу копчения с нуля
            </p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      <RecipeEditor mode="create" onSave={handleSave} saving={saving} />
    </div>
  );
}
