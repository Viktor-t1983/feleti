"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { IngredientForm, type IngredientFormData } from "@/components/ingredients/IngredientForm";
import { apiClient } from "@/lib/api/client";

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
}

export default function EditIngredientPage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;
  const [saving, setSaving] = useState(false);
  const [initialData, setInitialData] = useState<IngredientFormData | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    apiClient.get(`/ingredients/${slug}`).then(({ data }: { data: IngredientRead }) => {
      setInitialData({
        name: data.name,
        slug: data.slug,
        type: data.type as IngredientFormData["type"],
        protein_per_100g: data.protein_per_100g != null ? String(data.protein_per_100g) : "",
        fat_per_100g: data.fat_per_100g != null ? String(data.fat_per_100g) : "",
        carbs_per_100g: data.carbs_per_100g != null ? String(data.carbs_per_100g) : "",
        kcal_per_100g: data.kcal_per_100g != null ? String(data.kcal_per_100g) : "",
        price_per_kg: data.price_per_kg != null ? String(data.price_per_kg) : "",
        unit: data.unit || "кг",
        is_allergen: data.is_allergen,
        gmo_flag: data.gmo_flag,
        allergens: data.allergens.join(", "),
        wood_species: data.wood_species || "",
        wood_form: data.wood_form || "",
        fraction_mm: data.fraction_mm != null ? String(data.fraction_mm) : "",
        description: data.description || "",
      });
    }).catch(() => {
      toast.error("Не удалось загрузить ингредиент");
      router.push("/ingredients");
    }).finally(() => setLoading(false));
  }, [slug, router]);

  const handleSave = async (formData: IngredientFormData) => {
    setSaving(true);
    try {
      await apiClient.patch(`/ingredients/${slug}`, {
        name: formData.name,
        slug: formData.slug,
        type: formData.type,
        protein_per_100g: parseFloat(formData.protein_per_100g) || null,
        fat_per_100g: parseFloat(formData.fat_per_100g) || null,
        carbs_per_100g: parseFloat(formData.carbs_per_100g) || null,
        kcal_per_100g: parseInt(formData.kcal_per_100g) || null,
        price_per_kg: parseFloat(formData.price_per_kg) || null,
        unit: formData.unit,
        is_allergen: formData.is_allergen,
        gmo_flag: formData.gmo_flag,
        allergens: formData.allergens ? formData.allergens.split(",").map((s: string) => s.trim()).filter(Boolean) : [],
        wood_species: formData.wood_species || null,
        wood_form: formData.wood_form || null,
        fraction_mm: formData.fraction_mm ? parseFloat(formData.fraction_mm) : null,
        description: formData.description || null,
      });
      toast.success("Ингредиент сохранён");
      router.push(`/ingredients/${formData.slug}`);
    } catch (e) {
      toast.error((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка при сохранении");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return (
    <div className="mx-auto max-w-2xl py-8 space-y-4">
      <div className="h-4 w-32 animate-pulse rounded bg-white/5" />
      <div className="h-8 w-48 animate-pulse rounded bg-white/5" />
      <div className="h-96 animate-pulse rounded-2xl bg-white/5" />
    </div>
  );

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href={`/ingredients/${slug}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад
      </Link>
      <h1 className="text-xl font-bold text-white mb-6">Редактировать ингредиент</h1>
      <IngredientForm initialData={initialData} onSave={handleSave} saving={saving} />
    </div>
  );
}
