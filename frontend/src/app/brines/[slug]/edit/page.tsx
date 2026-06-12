"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";
import { BrineForm, type BrineFormData } from "@/components/brines/BrineForm";
import { apiClient } from "@/lib/api/client";

interface BrineRead {
  id: number;
  name: string;
  slug: string;
  method: string;
  salt_percent: number;
  sugar_percent: number;
  nitrite_ppm: number;
  nitrate_ppm: number;
  spices: string[];
  duration_hours: number;
  temp_c: number;
  water_percent: number | null;
  description: string | null;
  notes: string | null;
}

export default function EditBrinePage() {
  const params = useParams();
  const router = useRouter();
  const slug = params?.slug as string;
  const [saving, setSaving] = useState(false);
  const [initialData, setInitialData] = useState<BrineFormData | undefined>(undefined);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    apiClient.get(`/brines/${slug}`).then(({ data }: { data: BrineRead }) => {
      setInitialData({
        name: data.name,
        slug: data.slug,
        method: data.method as BrineFormData["method"],
        salt_percent: String(data.salt_percent),
        sugar_percent: String(data.sugar_percent),
        nitrite_ppm: String(data.nitrite_ppm),
        nitrate_ppm: String(data.nitrate_ppm),
        duration_hours: String(data.duration_hours),
        temp_c: String(data.temp_c),
        water_percent: data.water_percent != null ? String(data.water_percent) : "",
        description: data.description || "",
        notes: data.notes || "",
        spices: data.spices.join(", "),
      });
    }).catch(() => {
      toast.error("Не удалось загрузить рассол");
      router.push("/brines");
    }).finally(() => setLoading(false));
  }, [slug, router]);

  const handleSave = async (formData: BrineFormData) => {
    setSaving(true);
    try {
      await apiClient.patch(`/brines/${slug}`, {
        name: formData.name,
        slug: formData.slug,
        method: formData.method,
        salt_percent: parseFloat(formData.salt_percent) || 0,
        sugar_percent: parseFloat(formData.sugar_percent) || 0,
        nitrite_ppm: parseInt(formData.nitrite_ppm) || 0,
        nitrate_ppm: parseInt(formData.nitrate_ppm) || 0,
        duration_hours: parseFloat(formData.duration_hours) || 0,
        temp_c: parseFloat(formData.temp_c) || 0,
        water_percent: formData.water_percent ? parseFloat(formData.water_percent) : null,
        description: formData.description || null,
        notes: formData.notes || null,
        spices: formData.spices ? formData.spices.split(",").map((s: string) => s.trim()).filter(Boolean) : [],
      });
      toast.success("Рассол сохранён");
      router.push(`/brines/${formData.slug}`);
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
      <Link href={`/brines/${slug}`} className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-6">
        <ArrowLeft className="h-4 w-4" />
        Назад
      </Link>
      <h1 className="text-xl font-bold text-white mb-6">Редактировать рассол</h1>
      <BrineForm initialData={initialData} onSave={handleSave} saving={saving} />
    </div>
  );
}
