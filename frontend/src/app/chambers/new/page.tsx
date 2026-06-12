"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowLeft, Plus } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { ChamberForm, type ChamberFormData } from "@/components/chambers/ChamberForm";
import { apiClient } from "@/lib/api/client";

export default function NewChamberPage() {
  const router = useRouter();
  const [saving, setSaving] = useState(false);

  const handleSave = async (data: ChamberFormData) => {
    setSaving(true);
    try {
      await apiClient.post("/chambers", {
        model: data.model,
        slug: data.slug,
        manufacturer_id: data.manufacturer_id ? parseInt(data.manufacturer_id) : null,
        type: data.type,
        max_load_kg: data.max_load_kg ? parseFloat(data.max_load_kg) : null,
        power_kw: data.power_kw ? parseFloat(data.power_kw) : null,
        num_chambers: parseInt(data.num_chambers) || 1,
        num_carts: parseInt(data.num_carts) || 1,
        num_probes: parseInt(data.num_probes) || 1,
        supports_static_smoke: data.supports_static_smoke,
        supports_electro: data.supports_electro,
        supports_cold_smoke: data.supports_cold_smoke,
        supports_cooling: data.supports_cooling,
        supports_freezing: data.supports_freezing,
        supports_joint: data.supports_joint,
        price_rrp_rub: data.price_rrp_rub ? parseFloat(data.price_rrp_rub) : null,
        description: data.description || null,
      });
      toast.success("Камера создана");
      router.push("/chambers");
    } catch (e) {
      toast.error((e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка при создании");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl py-8">
      <Link href="/chambers" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад к камерам
      </Link>
      <div className="mb-6 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-feleti-gold/10">
          <Plus className="h-5 w-5 text-feleti-gold" />
        </div>
        <h1 className="text-xl font-bold text-white">Новая камера</h1>
      </div>
      <ChamberForm onSave={handleSave} saving={saving} />
    </div>
  );
}
