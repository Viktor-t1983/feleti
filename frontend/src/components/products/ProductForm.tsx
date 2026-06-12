"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import type { ProductCategory } from "@/lib/api/products";

const CATEGORIES: { id: ProductCategory; label: string }[] = [
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

export interface ProductFormData {
  name: string;
  slug: string;
  category: ProductCategory;
  description: string;
  gost: string;
  shelf_life_days: string;
  storage_temp_min: string;
  storage_temp_max: string;
  storage_humidity_min: string;
  storage_humidity_max: string;
}

interface ProductFormProps {
  initialData?: ProductFormData;
  onSave: (data: ProductFormData) => Promise<void>;
  saving: boolean;
}

export function ProductForm({ initialData, onSave, saving }: ProductFormProps) {
  const [form, setForm] = useState<ProductFormData>(
    initialData || {
      name: "",
      slug: "",
      category: "прочее",
      description: "",
      gost: "",
      shelf_life_days: "",
      storage_temp_min: "",
      storage_temp_max: "",
      storage_humidity_min: "",
      storage_humidity_max: "",
    }
  );

  useEffect(() => {
    if (initialData) setForm(initialData);
  }, [initialData]);

  const update = (key: keyof ProductFormData, value: string) =>
    setForm((prev) => ({
      ...prev,
      [key]: value,
      ...(key === "name" && !initialData
        ? { slug: value.toLowerCase().replace(/[^a-zа-яё0-9]+/g, "-").replace(/^-|-$/g, "").replace(/-+/g, "-") }
        : {}),
    }));

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSave(form);
      }}
      className="space-y-6"
    >
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Название *</label>
          <input
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
            placeholder="Докторская варёная"
            required
          />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Slug</label>
          <input
            value={form.slug}
            onChange={(e) => update("slug", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white/70 outline-none focus:border-feleti-gold/50 font-mono"
            placeholder="doktorskaya-varyonaya"
            required
          />
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Категория *</label>
        <select
          value={form.category}
          onChange={(e) => update("category", e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
        >
          {CATEGORIES.map((c) => (
            <option key={c.id} value={c.id}>{c.label}</option>
          ))}
        </select>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Описание</label>
        <textarea
          value={form.description}
          onChange={(e) => update("description", e.target.value)}
          rows={3}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">ГОСТ</label>
          <input
            value={form.gost}
            onChange={(e) => update("gost", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
            placeholder="ГОСТ Р 52196-2011"
          />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Срок хранения (дней)</label>
          <input
            type="number"
            value={form.shelf_life_days}
            onChange={(e) => update("shelf_life_days", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
            min={0}
          />
        </div>
      </div>

      <div className="border-t border-white/5 pt-4">
        <p className="text-sm text-muted-foreground mb-3">Условия хранения</p>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5">T мин (°C)</label>
            <input
              type="number"
              value={form.storage_temp_min}
              onChange={(e) => update("storage_temp_min", e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5">T макс (°C)</label>
            <input
              type="number"
              value={form.storage_temp_max}
              onChange={(e) => update("storage_temp_max", e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
              step="0.1"
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5">Влажность мин (%)</label>
            <input
              type="number"
              value={form.storage_humidity_min}
              onChange={(e) => update("storage_humidity_min", e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
              min={0} max={100}
            />
          </div>
          <div>
            <label className="block text-sm text-muted-foreground mb-1.5">Влажность макс (%)</label>
            <input
              type="number"
              value={form.storage_humidity_max}
              onChange={(e) => update("storage_humidity_max", e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
              min={0} max={100}
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={saving || !form.name || !form.slug}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90 disabled:opacity-50"
        >
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {initialData ? "Сохранить" : "Создать"}
        </button>
      </div>
    </form>
  );
}
