"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import type { BrineMethod } from "@/lib/api/brines";

const METHODS: { id: BrineMethod; label: string }[] = [
  { id: "сухой", label: "Сухой" },
  { id: "мокрый", label: "Мокрый" },
  { id: "шприцевание", label: "Шприцевание" },
  { id: "комбинированный", label: "Комбинированный" },
  { id: "смешанный", label: "Смешанный" },
];

export interface BrineFormData {
  name: string;
  slug: string;
  method: BrineMethod;
  salt_percent: string;
  sugar_percent: string;
  nitrite_ppm: string;
  nitrate_ppm: string;
  duration_hours: string;
  temp_c: string;
  water_percent: string;
  description: string;
  notes: string;
  spices: string;
}

interface BrineFormProps {
  initialData?: BrineFormData;
  onSave: (data: BrineFormData) => Promise<void>;
  saving: boolean;
}

export function BrineForm({ initialData, onSave, saving }: BrineFormProps) {
  const [form, setForm] = useState<BrineFormData>(
    initialData || {
      name: "", slug: "", method: "сухой",
      salt_percent: "3", sugar_percent: "1", nitrite_ppm: "80", nitrate_ppm: "0",
      duration_hours: "24", temp_c: "4", water_percent: "",
      description: "", notes: "", spices: "",
    }
  );

  useEffect(() => {
    if (initialData) setForm(initialData);
  }, [initialData]);

  const update = (key: keyof BrineFormData, value: string) =>
    setForm((prev) => ({
      ...prev,
      [key]: value,
      ...(key === "name" && !initialData
        ? { slug: value.toLowerCase().replace(/[^a-zа-яё0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") }
        : {}),
    }));

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

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Метод *</label>
        <select value={form.method} onChange={(e) => update("method", e.target.value)}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50">
          {METHODS.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Соль (%)</label>
          <input type="number" step="0.1" value={form.salt_percent} onChange={(e) => update("salt_percent", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Сахар (%)</label>
          <input type="number" step="0.1" value={form.sugar_percent} onChange={(e) => update("sugar_percent", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Нитрит (ppm)</label>
          <input type="number" value={form.nitrite_ppm} onChange={(e) => update("nitrite_ppm", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Нитрат (ppm)</label>
          <input type="number" value={form.nitrate_ppm} onChange={(e) => update("nitrate_ppm", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Длительность (ч)</label>
          <input type="number" step="0.5" value={form.duration_hours} onChange={(e) => update("duration_hours", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">T (°C)</label>
          <input type="number" step="0.5" value={form.temp_c} onChange={(e) => update("temp_c", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Вода (%)</label>
          <input type="number" step="0.1" value={form.water_percent} onChange={(e) => update("water_percent", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Специи (через запятую)</label>
          <input value={form.spices} onChange={(e) => update("spices", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Описание</label>
        <textarea value={form.description} onChange={(e) => update("description", e.target.value)} rows={3}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y" />
      </div>
      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Примечания</label>
        <textarea value={form.notes} onChange={(e) => update("notes", e.target.value)} rows={2}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y" />
      </div>

      <div className="flex justify-end">
        <button type="submit" disabled={saving || !form.name || !form.slug}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90 disabled:opacity-50">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {initialData ? "Сохранить" : "Создать"}
        </button>
      </div>
    </form>
  );
}
