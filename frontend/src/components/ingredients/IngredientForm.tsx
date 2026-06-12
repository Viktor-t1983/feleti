"use client";

import { useState, useEffect } from "react";
import type { IngredientType } from "@/lib/api/ingredients";
import { INGREDIENT_TYPES } from "@/lib/api/ingredients";

export interface IngredientFormData {
  name: string;
  slug: string;
  type: IngredientType;
  protein_per_100g: string;
  fat_per_100g: string;
  carbs_per_100g: string;
  kcal_per_100g: string;
  price_per_kg: string;
  unit: string;
  is_allergen: boolean;
  gmo_flag: boolean;
  allergens: string;
  wood_species: string;
  wood_form: string;
  fraction_mm: string;
  description: string;
}

interface IngredientFormProps {
  initialData?: IngredientFormData;
  onSave: (data: IngredientFormData) => Promise<void>;
  saving: boolean;
}

export function IngredientForm({ initialData, onSave, saving }: IngredientFormProps) {
  const [form, setForm] = useState<IngredientFormData>(
    initialData || {
      name: "", slug: "", type: "мясо",
      protein_per_100g: "", fat_per_100g: "", carbs_per_100g: "",
      kcal_per_100g: "", price_per_kg: "", unit: "кг",
      is_allergen: false, gmo_flag: false,
      allergens: "", wood_species: "", wood_form: "", fraction_mm: "",
      description: "",
    }
  );

  useEffect(() => {
    if (initialData) setForm(initialData);
  }, [initialData]);

  const update = <K extends keyof IngredientFormData>(key: K, value: IngredientFormData[K]) =>
    setForm((prev) => ({
      ...prev,
      [key]: value,
      ...(key === "name" && !initialData
        ? { slug: String(value).toLowerCase().replace(/[^a-zа-яё0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") }
        : {}),
    }));

  const num = (key: keyof IngredientFormData) => (value: string) => update(key, value.trim() === "" ? "" : value);

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form); }} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Название *</label>
          <input value={form.name} onChange={(e) => update("name", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" required />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Slug</label>
          <input value={form.slug} onChange={(e) => update("slug", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white/70 outline-none focus:border-feleti-gold/50 font-mono" required />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Тип *</label>
          <select value={form.type} onChange={(e) => update("type", e.target.value as IngredientType)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50">
            {INGREDIENT_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Единица измерения</label>
          <input value={form.unit} onChange={(e) => update("unit", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Белки (г/100г)</label>
          <input type="number" step="0.1" value={form.protein_per_100g} onChange={(e) => num("protein_per_100g")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Жиры (г/100г)</label>
          <input type="number" step="0.1" value={form.fat_per_100g} onChange={(e) => num("fat_per_100g")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Углеводы (г/100г)</label>
          <input type="number" step="0.1" value={form.carbs_per_100g} onChange={(e) => num("carbs_per_100g")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Ккал/100г</label>
          <input type="number" value={form.kcal_per_100g} onChange={(e) => num("kcal_per_100g")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Цена за кг (₽)</label>
          <input type="number" step="0.01" value={form.price_per_kg} onChange={(e) => num("price_per_kg")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="flex items-center gap-3">
          <input type="checkbox" id="is_allergen" checked={form.is_allergen}
            onChange={(e) => update("is_allergen", e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-white/5 text-feleti-gold focus:ring-feleti-gold" />
          <label htmlFor="is_allergen" className="text-sm text-muted-foreground">Аллерген</label>
        </div>
        <div className="flex items-center gap-3">
          <input type="checkbox" id="gmo_flag" checked={form.gmo_flag}
            onChange={(e) => update("gmo_flag", e.target.checked)}
            className="h-4 w-4 rounded border-white/20 bg-white/5 text-feleti-gold focus:ring-feleti-gold" />
          <label htmlFor="gmo_flag" className="text-sm text-muted-foreground">ГМО</label>
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Аллергены (через запятую)</label>
        <input value={form.allergens} onChange={(e) => update("allergens", e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Порода дерева</label>
          <input value={form.wood_species} onChange={(e) => update("wood_species", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Форма щепы</label>
          <input value={form.wood_form} onChange={(e) => update("wood_form", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Фракция (мм)</label>
          <input type="number" step="0.1" value={form.fraction_mm} onChange={(e) => num("fraction_mm")(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Описание</label>
        <textarea value={form.description} onChange={(e) => update("description", e.target.value)} rows={3}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y" />
      </div>

      <div className="flex justify-end">
        <button type="submit" disabled={saving || !form.name || !form.slug}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90 disabled:opacity-50">
          {initialData ? "Сохранить" : "Создать"}
        </button>
      </div>
    </form>
  );
}
