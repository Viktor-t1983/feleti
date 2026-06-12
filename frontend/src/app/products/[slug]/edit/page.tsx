"use client";

import { useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Pencil, Loader2 } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { ProductForm, type ProductFormData } from "@/components/products/ProductForm";

export default function EditProductPage() {
  const params = useParams();
  const slug = params.slug as string;
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: product, isLoading } = useQuery({
    queryKey: ["product", slug],
    queryFn: async () => {
      const { data } = await apiClient.get(`/products/by-slug/${slug}`);
      return data as Record<string, unknown>;
    },
  });

  const handleSave = async (formData: ProductFormData) => {
    if (!product) return;
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {};
      if (formData.name !== product.name) payload.name = formData.name;
      if (formData.category !== product.category) payload.category = formData.category;
      if (formData.description !== (product.description || "")) payload.description = formData.description || null;
      if (formData.gost !== (product.gost || "")) payload.gost = formData.gost || null;
      if (formData.shelf_life_days !== (product.shelf_life_days?.toString() || "")) payload.shelf_life_days = formData.shelf_life_days ? parseInt(formData.shelf_life_days) : null;
      if (formData.storage_temp_min !== (product.storage_temp_min?.toString() || "")) payload.storage_temp_min = formData.storage_temp_min ? parseFloat(formData.storage_temp_min) : null;
      if (formData.storage_temp_max !== (product.storage_temp_max?.toString() || "")) payload.storage_temp_max = formData.storage_temp_max ? parseFloat(formData.storage_temp_max) : null;
      if (formData.storage_humidity_min !== (product.storage_humidity_min?.toString() || "")) payload.storage_humidity_min = formData.storage_humidity_min ? parseFloat(formData.storage_humidity_min) : null;
      if (formData.storage_humidity_max !== (product.storage_humidity_max?.toString() || "")) payload.storage_humidity_max = formData.storage_humidity_max ? parseFloat(formData.storage_humidity_max) : null;

      await apiClient.patch(`/products/${product.id}`, payload);
      router.push(`/products/${slug}`);
    } catch {
      setError("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  if (!product) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <p className="text-muted-foreground">Продукт не найден</p>
        <Link href="/products" className="mt-4 text-sm text-feleti-gold hover:underline">Вернуться к списку</Link>
      </div>
    );
  }

  const initialData: ProductFormData = {
    name: product.name as string,
    slug: product.slug as string,
    category: product.category as ProductFormData["category"],
    description: (product.description as string) || "",
    gost: (product.gost as string) || "",
    shelf_life_days: (product.shelf_life_days as number)?.toString() || "",
    storage_temp_min: (product.storage_temp_min as number)?.toString() || "",
    storage_temp_max: (product.storage_temp_max as number)?.toString() || "",
    storage_humidity_min: (product.storage_humidity_min as number)?.toString() || "",
    storage_humidity_max: (product.storage_humidity_max as number)?.toString() || "",
  };

  return (
    <div className="space-y-6">
      <div>
        <Link
          href={`/products/${slug}`}
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к продукту
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            <Pencil className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Редактировать продукт</h1>
            <p className="text-sm text-muted-foreground mt-0.5">{product.name as string}</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-400">{error}</div>
      )}

      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <ProductForm initialData={initialData} onSave={handleSave} saving={saving} />
      </div>
    </div>
  );
}
