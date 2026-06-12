"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { ChamberForm, type ChamberFormData } from "@/components/chambers/ChamberForm";
import { apiClient } from "@/lib/api/client";

interface ChamberRead {
  id: number;
  model: string;
  slug: string;
  manufacturer_id: number | null;
  manufacturer?: { name: string } | null;
  type: string;
  max_load_kg: number | null;
  power_kw: number | null;
  num_chambers: number;
  num_carts: number;
  num_probes: number;
  supports_static_smoke: boolean;
  supports_electro: boolean;
  supports_cold_smoke: boolean;
  supports_cooling: boolean;
  supports_freezing: boolean;
  supports_joint: boolean;
  price_rrp_rub: number | null;
  description: string | null;
}

export default function EditChamberPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;
  const [saving, setSaving] = useState(false);
  const [initialData, setInitialData] = useState<ChamberFormData | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    apiClient.get(`/chambers/${id}`).then(({ data }: { data: ChamberRead }) => {
      setInitialData({
        model: data.model,
        slug: data.slug,
        manufacturer_id: data.manufacturer_id != null ? String(data.manufacturer_id) : "",
        type: data.type as ChamberFormData["type"],
        max_load_kg: data.max_load_kg != null ? String(data.max_load_kg) : "",
        power_kw: data.power_kw != null ? String(data.power_kw) : "",
        num_chambers: String(data.num_chambers),
        num_carts: String(data.num_carts),
        num_probes: String(data.num_probes),
        supports_static_smoke: data.supports_static_smoke,
        supports_electro: data.supports_electro,
        supports_cold_smoke: data.supports_cold_smoke,
        supports_cooling: data.supports_cooling,
        supports_freezing: data.supports_freezing,
        supports_joint: data.supports_joint,
        price_rrp_rub: data.price_rrp_rub != null ? String(data.price_rrp_rub) : "",
        description: data.description || "",
      });
    }).catch(() => {
      toast.error("Не удалось загрузить камеру");
      router.push("/chambers");
    }).finally(() => setLoading(false));
  }, [id, router]);

  const handleSave = async (formData: ChamberFormData) => {
    setSaving(true);
    try {
      await apiClient.patch(`/chambers/${id}`, {
        model: formData.model,
        slug: formData.slug,
        manufacturer_id: formData.manufacturer_id ? parseInt(formData.manufacturer_id) : null,
        type: formData.type,
        max_load_kg: formData.max_load_kg ? parseFloat(formData.max_load_kg) : null,
        power_kw: formData.power_kw ? parseFloat(formData.power_kw) : null,
        num_chambers: parseInt(formData.num_chambers) || 1,
        num_carts: parseInt(formData.num_carts) || 1,
        num_probes: parseInt(formData.num_probes) || 1,
        supports_static_smoke: formData.supports_static_smoke,
        supports_electro: formData.supports_electro,
        supports_cold_smoke: formData.supports_cold_smoke,
        supports_cooling: formData.supports_cooling,
        supports_freezing: formData.supports_freezing,
        supports_joint: formData.supports_joint,
        price_rrp_rub: formData.price_rrp_rub ? parseFloat(formData.price_rrp_rub) : null,
        description: formData.description || null,
      });
      toast.success("Камера сохранена");
      router.push(`/chambers/${id}`);
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
      <Link href={`/chambers/${id}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад
      </Link>
      <h1 className="text-xl font-bold text-white mb-6">Редактировать камеру</h1>
      <ChamberForm initialData={initialData} onSave={handleSave} saving={saving} />
    </div>
  );
}
