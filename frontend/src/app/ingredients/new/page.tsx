"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { IngredientForm, type IngredientFormData } from "@/components/ingredients/IngredientForm";
import { apiClient } from "@/lib/api/client";

export default function NewIngredientPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);

  const handleSave = async (data: IngredientFormData) => {
    setSaving(true);
    try {
      await apiClient.post("/ingredients", {
        name: data.name,
        slug: data.slug,
        type: data.type,
        protein_per_100g: parseFloat(data.protein_per_100g) || null,
        fat_per_100g: parseFloat(data.fat_per_100g) || null,
        carbs_per_100g: parseFloat(data.carbs_per_100g) || null,
        kcal_per_100g: parseInt(data.kcal_per_100g) || null,
        price_per_kg: parseFloat(data.price_per_kg) || null,
        unit: data.unit || "кг",
        is_allergen: data.is_allergen,
        gmo_flag: data.gmo_flag,
        allergens: data.allergens ? data.allergens.split(",").map((s: string) => s.trim()).filter(Boolean) : [],
        wood_species: data.wood_species || null,
        wood_form: data.wood_form || null,
        fraction_mm: data.fraction_mm ? parseFloat(data.fraction_mm) : null,
        description: data.description || null,
      });
      toast.success("Ингредиент создан");
      router.push("/ingredients");
    } catch (e) {
      toast.error((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка при создании");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href="/ingredients" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад к ингредиентам
      </Link>
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
          <Plus className="h-5 w-5 text-feleti-gold" />
        </div>
        <h1 className="text-xl font-bold text-white">Новый ингредиент</h1>
      </div>
      <IngredientForm onSave={handleSave} saving={saving} />
    </div>
  );
}
