"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { BrineForm, type BrineFormData } from "@/components/brines/BrineForm";
import { apiClient } from "@/lib/api/client";

export default function NewBrinePage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);

  const handleSave = async (data: BrineFormData) => {
    setSaving(true);
    try {
      await apiClient.post("/brines", {
        name: data.name,
        slug: data.slug,
        method: data.method,
        salt_percent: parseFloat(data.salt_percent) || 0,
        sugar_percent: parseFloat(data.sugar_percent) || 0,
        nitrite_ppm: parseInt(data.nitrite_ppm) || 0,
        nitrate_ppm: parseInt(data.nitrate_ppm) || 0,
        duration_hours: parseFloat(data.duration_hours) || 0,
        temp_c: parseFloat(data.temp_c) || 0,
        water_percent: data.water_percent ? parseFloat(data.water_percent) : null,
        description: data.description || null,
        notes: data.notes || null,
        spices: data.spices ? data.spices.split(",").map((s: string) => s.trim()).filter(Boolean) : [],
      });
      toast.success("Рассол создан");
      router.push("/brines");
    } catch (e) {
      toast.error((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка при создании");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href="/brines" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад к рассолам
      </Link>
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
          <Plus className="h-5 w-5 text-feleti-gold" />
        </div>
        <h1 className="text-xl font-bold text-white">Новый рассол</h1>
      </div>
      <BrineForm onSave={handleSave} saving={saving} />
    </div>
  );
}
