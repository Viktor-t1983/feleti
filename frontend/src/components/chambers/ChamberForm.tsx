"use client";

import { useState, useEffect } from "react";
import { Loader2 } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import type { ChamberType } from "@/lib/api/chambers";
import { CHAMBER_TYPES } from "@/lib/api/chambers";

interface ManufacturerOption {
  id: number;
  name: string;
}

export interface ChamberFormData {
  model: string;
  slug: string;
  manufacturer_id: string;
  type: ChamberType;
  max_load_kg: string;
  power_kw: string;
  num_chambers: string;
  num_carts: string;
  num_probes: string;
  supports_static_smoke: boolean;
  supports_electro: boolean;
  supports_cold_smoke: boolean;
  supports_cooling: boolean;
  supports_freezing: boolean;
  supports_joint: boolean;
  price_rrp_rub: string;
  description: string;
}

interface ChamberFormProps {
  initialData?: ChamberFormData;
  onSave: (data: ChamberFormData) => Promise<void>;
  saving: boolean;
}

export function ChamberForm({ initialData, onSave, saving }: ChamberFormProps) {
  const [manufacturers, setManufacturers] = useState<ManufacturerOption[]>([]);
  const [form, setForm] = useState<ChamberFormData>(
    initialData || {
      model: "", slug: "", manufacturer_id: "", type: "горячее",
      max_load_kg: "", power_kw: "", num_chambers: "1", num_carts: "1", num_probes: "1",
      supports_static_smoke: false, supports_electro: false, supports_cold_smoke: false,
      supports_cooling: false, supports_freezing: false, supports_joint: false,
      price_rrp_rub: "", description: "",
    }
  );

  useEffect(() => {
    apiClient.get("/manufacturers?size=200").then(({ data }) => {
      const page = data as { items: ManufacturerOption[] };
      setManufacturers(page?.items || []);
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (initialData) setForm(initialData);
  }, [initialData]);

  const update = <K extends keyof ChamberFormData>(key: K, value: ChamberFormData[K]) =>
    setForm((prev) => ({
      ...prev,
      [key]: value,
      ...(key === "model" && !initialData
        ? { slug: String(value).toLowerCase().replace(/[^a-zа-яё0-9]+/g, "-").replace(/-+/g, "-").replace(/^-|-$/g, "") }
        : {}),
    }));

  return (
    <form onSubmit={(e) => { e.preventDefault(); onSave(form); }} className="space-y-6">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Модель *</label>
          <input value={form.model} onChange={(e) => update("model", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" required />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Slug</label>
          <input value={form.slug} onChange={(e) => update("slug", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white/70 outline-none focus:border-feleti-gold/50 font-mono" required />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Производитель</label>
          <select value={form.manufacturer_id} onChange={(e) => update("manufacturer_id", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50">
            <option value="">Не выбран</option>
            {manufacturers.map((m) => <option key={m.id} value={String(m.id)}>{m.name}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Тип *</label>
          <select value={form.type} onChange={(e) => update("type", e.target.value as ChamberType)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50">
            {CHAMBER_TYPES.map((t) => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Макс. загрузка (кг)</label>
          <input type="number" step="0.5" value={form.max_load_kg} onChange={(e) => update("max_load_kg", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Мощность (кВт)</label>
          <input type="number" step="0.1" value={form.power_kw} onChange={(e) => update("power_kw", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Цена (₽)</label>
          <input type="number" step="1000" value={form.price_rrp_rub} onChange={(e) => update("price_rrp_rub", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Камер</label>
          <input type="number" value={form.num_chambers} onChange={(e) => update("num_chambers", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Тележек</label>
          <input type="number" value={form.num_carts} onChange={(e) => update("num_carts", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
        <div>
          <label className="block text-sm text-muted-foreground mb-1.5">Щупов</label>
          <input type="number" value={form.num_probes} onChange={(e) => update("num_probes", e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50" />
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-2">Режимы</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { key: "supports_static_smoke", label: "Статический дым" },
            { key: "supports_electro", label: "Электро" },
            { key: "supports_cold_smoke", label: "Холодный дым" },
            { key: "supports_cooling", label: "Охлаждение" },
            { key: "supports_freezing", label: "Заморозка" },
            { key: "supports_joint", label: "Объединение" },
          ].map(({ key, label }) => (
            <label key={key} className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox"
                checked={form[key as keyof ChamberFormData] as boolean}
                onChange={(e) => update(key as keyof ChamberFormData, e.target.checked)}
                className="h-4 w-4 rounded border-white/20 bg-white/5 text-feleti-gold focus:ring-feleti-gold" />
              <span className="text-sm text-muted-foreground">{label}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm text-muted-foreground mb-1.5">Описание</label>
        <textarea value={form.description} onChange={(e) => update("description", e.target.value)} rows={3}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y" />
      </div>

      <div className="flex justify-end">
        <button type="submit" disabled={saving || !form.model || !form.slug}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-5 py-2.5 text-sm font-medium text-black transition-colors hover:bg-feleti-gold/90 disabled:opacity-50">
          {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
          {initialData ? "Сохранить" : "Создать"}
        </button>
      </div>
    </form>
  );
}
