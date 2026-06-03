"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { ArrowLeft, Package, Factory, BookOpen, Weight } from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface Chamber {
  id: number;
  model: string;
  manufacturer: { name: string } | null;
  max_load_kg: number | null;
}

interface RecipeVersion {
  id: number;
  version_number: number;
  yield_percent: number | null;
}

interface Recipe {
  id: number;
  name: string;
  current_version: RecipeVersion | null;
}

async function fetchChambers(): Promise<{ items: Chamber[] }> {
  const { data } = await apiClient.get("/chambers?size=50");
  return data;
}

async function fetchRecipes(): Promise<{ items: Recipe[] }> {
  const { data } = await apiClient.get("/recipes?size=50");
  return data;
}

interface BatchCreate {
  recipe_version_id: number;
  chamber_id: number;
  batch_number: string;
  product_weight_kg: number | null;
  notes: string | null;
}

async function createBatch(batch: BatchCreate) {
  const { data } = await apiClient.post("/batches", batch);
  return data;
}

export default function NewBatchPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [chamberId, setChamberId] = useState("");
  const [recipeVersionId, setRecipeVersionId] = useState("");
  const [batchNumber, setBatchNumber] = useState("");
  const [weight, setWeight] = useState("");
  const [notes, setNotes] = useState("");

  const { data: chambersData } = useQuery({
    queryKey: ["chambers"],
    queryFn: fetchChambers,
  });

  const { data: recipesData } = useQuery({
    queryKey: ["recipes"],
    queryFn: fetchRecipes,
  });

  const mutation = useMutation({
    mutationFn: createBatch,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["batches"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "stats"] });
      router.push("/batches");
    },
  });

  const chambers = chambersData?.items || [];
  const recipes = recipesData?.items || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chamberId || !recipeVersionId || !batchNumber) return;

    mutation.mutate({
      recipe_version_id: parseInt(recipeVersionId),
      chamber_id: parseInt(chamberId),
      batch_number: batchNumber,
      product_weight_kg: weight ? parseFloat(weight) : null,
      notes: notes || null,
    });
  };

  const generateBatchNumber = () => {
    const now = new Date();
    const num = `B-${now.getFullYear()}-${String(Math.floor(Math.random() * 900) + 100).padStart(3, "0")}`;
    setBatchNumber(num);
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/batches"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-2"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к партиям
        </Link>
        <h1 className="text-2xl font-bold text-white">Новая партия</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Создание производственной партии
        </p>
      </div>

      <motion.form
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="space-y-5 rounded-2xl border border-white/5 bg-white/[0.02] p-6"
      >
        {/* Batch number */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Номер партии
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={batchNumber}
              onChange={(e) => setBatchNumber(e.target.value)}
              placeholder="B-2026-001"
              required
              className="flex-1 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
            />
            <button
              type="button"
              onClick={generateBatchNumber}
              className="rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-muted-foreground hover:text-white transition-colors"
            >
              Авто
            </button>
          </div>
        </div>

        {/* Chamber */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            <span className="inline-flex items-center gap-1">
              <Factory className="h-3.5 w-3.5" />
              Камера
            </span>
          </label>
          <select
            value={chamberId}
            onChange={(e) => setChamberId(e.target.value)}
            required
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
          >
            <option value="" className="bg-[#1a1a1a]">Выберите камеру</option>
            {chambers.map((c) => (
              <option key={c.id} value={c.id} className="bg-[#1a1a1a]">
                {c.model} ({c.manufacturer?.name || "—"}) {c.max_load_kg ? `— ${c.max_load_kg} кг` : ""}
              </option>
            ))}
          </select>
        </div>

        {/* Recipe */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            <span className="inline-flex items-center gap-1">
              <BookOpen className="h-3.5 w-3.5" />
              Рецепт
            </span>
          </label>
          <select
            value={recipeVersionId}
            onChange={(e) => setRecipeVersionId(e.target.value)}
            required
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
          >
            <option value="" className="bg-[#1a1a1a]">Выберите рецепт</option>
            {recipes
              .filter((r) => r.current_version)
              .map((r) => (
                <option key={r.current_version!.id} value={r.current_version!.id} className="bg-[#1a1a1a]">
                  {r.name} (выход {r.current_version?.yield_percent || "?"}%)
                </option>
              ))}
          </select>
        </div>

        {/* Weight */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            <span className="inline-flex items-center gap-1">
              <Weight className="h-3.5 w-3.5" />
              Вес загрузки, кг
            </span>
          </label>
          <input
            type="number"
            step="0.1"
            value={weight}
            onChange={(e) => setWeight(e.target.value)}
            placeholder="100"
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
          />
        </div>

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-white mb-2">
            Примечания
          </label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            rows={3}
            placeholder="Дополнительная информация..."
            className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-4 py-2.5 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none resize-none"
          />
        </div>

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold/10 px-6 py-2.5 text-sm font-medium text-feleti-gold border border-feleti-gold/20 hover:bg-feleti-gold/20 transition-colors disabled:opacity-50"
          >
            <Package className="h-4 w-4" />
            {mutation.isPending ? "Создание..." : "Создать партию"}
          </button>
          {mutation.isError && (
            <p className="mt-2 text-sm text-red-400">
              Ошибка создания партии. Проверьте данные.
            </p>
          )}
        </div>
      </motion.form>
    </div>
  );
}
