"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import type { TopicRead } from "@/lib/api/topics";

interface FormData {
  label: string;
  slug: string;
  description: string;
  parent_id: number | null;
  sort_order: number;
  icon: string;
}

interface Props {
  open: boolean;
  onClose: () => void;
  onSave: (data: FormData) => Promise<void>;
  topics: TopicRead[];
  editTopic?: TopicRead | null;
}

const defaultForm: FormData = {
  label: "",
  slug: "",
  description: "",
  parent_id: null,
  sort_order: 0,
  icon: "",
};

export function TopicFormModal({ open, onClose, onSave, topics, editTopic }: Props) {
  const [form, setForm] = useState<FormData>(defaultForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (editTopic) {
      setForm({
        label: editTopic.label,
        slug: editTopic.slug,
        description: editTopic.description || "",
        parent_id: editTopic.parent_id,
        sort_order: editTopic.sort_order,
        icon: editTopic.icon || "",
      });
    } else {
      setForm(defaultForm);
    }
  }, [editTopic, open]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (open) document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, onClose]);

  const handleSubmit = async () => {
    setError("");
    if (!form.label.trim()) { setError("Название обязательно"); return; }
    if (!form.slug.trim()) { setError("Slug обязателен"); return; }
    if (!/^[a-z0-9-]+$/.test(form.slug)) { setError("Slug: только a-z, 0-9, дефис"); return; }
    setSaving(true);
    try {
      await onSave(form);
      onClose();
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } }; message?: string };
      setError(err?.response?.data?.detail || err?.message || "Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  };

  const candidates = editTopic
    ? topics.filter((t) => t.id !== editTopic.id && t.path !== `${editTopic.path}/`)
    : topics;

  return (
    <AnimatePresence>
      {open && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative z-10 w-full max-w-lg rounded-2xl border border-white/10 bg-[#121212] p-6 shadow-xl"
          >
            <button
              onClick={onClose}
              className="absolute right-4 top-4 text-muted-foreground hover:text-white transition-colors"
            >
              <X className="h-4 w-4" />
            </button>

            <h3 className="text-lg font-semibold text-white mb-4">
              {editTopic ? "Редактировать тему" : "Новая тема"}
            </h3>

            {error && (
              <p className="mb-4 text-sm text-red-400 bg-red-500/10 rounded-lg px-3 py-2">{error}</p>
            )}

            <div className="space-y-4">
              {/* Label */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Название</label>
                <input
                  type="text"
                  value={form.label}
                  onChange={(e) => setForm({ ...form, label: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
                  placeholder="Например: Осётр"
                />
              </div>

              {/* Slug */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Slug</label>
                <input
                  type="text"
                  value={form.slug}
                  onChange={(e) => setForm({ ...form, slug: e.target.value })}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
                  placeholder="osetr"
                />
                <p className="text-[10px] text-muted-foreground/50 mt-1">a-z, 0-9, дефис</p>
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Описание</label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={3}
                  className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none resize-none"
                  placeholder="Краткое описание темы"
                />
              </div>

              {/* Parent */}
              <div>
                <label className="block text-sm text-muted-foreground mb-1">Родительская тема</label>
                <select
                  value={form.parent_id ?? ""}
                  onChange={(e) => setForm({ ...form, parent_id: e.target.value ? Number(e.target.value) : null })}
                  className="w-full rounded-xl border border-white/10 bg-[#121212] px-3 py-2 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
                >
                  <option value="">Корневой узел</option>
                  {candidates.map((t) => (
                    <option key={t.id} value={t.id}>
                      {"–".repeat(t.level)}{" "}{t.label}
                    </option>
                  ))}
                </select>
              </div>

              {/* Icon + Sort order row */}
              <div className="flex gap-4">
                <div className="flex-1">
                  <label className="block text-sm text-muted-foreground mb-1">Иконка</label>
                  <input
                    type="text"
                    value={form.icon}
                    onChange={(e) => setForm({ ...form, icon: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
                    placeholder="fish / beef / ..."
                  />
                </div>
                <div className="w-24">
                  <label className="block text-sm text-muted-foreground mb-1">Порядок</label>
                  <input
                    type="number"
                    value={form.sort_order}
                    onChange={(e) => setForm({ ...form, sort_order: Number(e.target.value) })}
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white focus:border-feleti-gold/30 focus:outline-none"
                  />
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <button
                onClick={onClose}
                disabled={saving}
                className="rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition-colors hover:bg-white/5 disabled:opacity-50"
              >
                Отмена
              </button>
              <button
                onClick={handleSubmit}
                disabled={saving}
                className="rounded-xl bg-feleti-gold/20 px-4 py-2 text-sm font-medium text-feleti-gold transition-colors hover:bg-feleti-gold/30 disabled:opacity-50"
              >
                {saving ? "Сохранение..." : editTopic ? "Сохранить" : "Создать"}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
