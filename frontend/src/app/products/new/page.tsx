"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, PlusCircle } from "lucide-react";
import Link from "next/link";
import { apiClient } from "@/lib/api/client";
import { ProductForm, type ProductFormData } from "@/components/products/ProductForm";

export default function NewProductPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (data: ProductFormData) => {
    setSaving(true);
    setError(null);
    try {
      const payload: Record<string, unknown> = {
        name: data.name,
        slug: data.slug,
        category: data.category,
      };
      if (data.description) payload.description = data.description;
      if (data.gost) payload.gost = data.gost;
      if (data.shelf_life_days) payload.shelf_life_days = parseInt(data.shelf_life_days);
      if (data.storage_temp_min) payload.storage_temp_min = parseFloat(data.storage_temp_min);
      if (data.storage_temp_max) payload.storage_temp_max = parseFloat(data.storage_temp_max);
      if (data.storage_humidity_min) payload.storage_humidity_min = parseFloat(data.storage_humidity_min);
      if (data.storage_humidity_max) payload.storage_humidity_max = parseFloat(data.storage_humidity_max);

      const response = await apiClient.post("/products", payload);
      router.push(`/products/${response.data.slug}`);
    } catch {
      setError("Ошибка создания продукта");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/products"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к продуктам
        </Link>
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
            <PlusCircle className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Новый продукт</h1>
            <p className="text-sm text-muted-foreground mt-0.5">Добавьте новый вид продукции</p>
          </div>
        </div>
      </div>

      {error && (
        <div className="rounded-xl border border-red-400/20 bg-red-400/5 px-4 py-3 text-sm text-red-400">{error}</div>
      )}

      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
        <ProductForm onSave={handleSave} saving={saving} />
      </div>
    </div>
  );
}
