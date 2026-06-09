"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  Pencil,
  Star,
  ExternalLink,
  X,
  Check,
  Globe,
  Save,
} from "lucide-react";
import { fetchCompetitorsAdmin, updateCompetitor, deleteCompetitor } from "@/lib/api/admin-competitors";
import type { Competitor } from "@/components/competitors/CompetitorCard";

const SEGMENT_COLORS: Record<string, string> = {
  premium: "text-amber-400 bg-amber-500/10",
  industrial: "text-blue-400 bg-blue-500/10",
  middle: "text-emerald-400 bg-emerald-500/10",
  budget: "text-gray-400 bg-gray-500/10",
  horeca: "text-purple-400 bg-purple-500/10",
  profi: "text-orange-400 bg-orange-500/10",
};

interface EditForm {
  name: string;
  country: string;
  founded_year: string;
  segment: string;
  is_main_competitor: boolean;
  base_url: string;
  description: string;
}

export function AdminCompetitorsTab() {
  const [items, setItems] = useState<Competitor[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState<EditForm | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchCompetitorsAdmin(1, 200);
      setItems(data.items);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = items.filter(
    (c) =>
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      (c.country || "").toLowerCase().includes(search.toLowerCase()) ||
      (c.segment || "").toLowerCase().includes(search.toLowerCase())
  );

  const openEdit = (c: Competitor) => {
    setEditingId(c.id.toString());
    setForm({
      name: c.name,
      country: c.country || "",
      founded_year: c.founded_year?.toString() || "",
      segment: c.segment || "",
      is_main_competitor: c.is_main_competitor,
      base_url: c.base_url || "",
      description: c.description || "",
    });
  };

  const handleSave = async () => {
    if (!editingId || !form) return;
    setSaving(true);
    try {
      await updateCompetitor(editingId, {
        name: form.name,
        country: form.country || null,
        founded_year: form.founded_year ? parseInt(form.founded_year) : null,
        segment: form.segment || null,
        is_main_competitor: form.is_main_competitor,
        base_url: form.base_url || null,
        description: form.description || null,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
      await load();
    } catch {
      /* ignore */
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (c: Competitor) => {
    if (!confirm(`Удалить конкурента ${c.name}? Это действие необратимо.`)) return;
    try {
      await deleteCompetitor(c.id);
      await load();
    } catch {
      /* ignore */
    }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Поиск конкурентов..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none"
          />
        </div>
        <span className="text-xs text-muted-foreground">{filtered.length} / {items.length}</span>
      </div>

      {/* List */}
      <div className="space-y-2">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
          </div>
        ) : (
          filtered.map((c) => (
            <motion.div
              key={c.id}
              layout
              className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden"
            >
              {/* Header row */}
              <div className="flex items-center gap-4 px-4 py-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white truncate">{c.name}</span>
                    {c.is_main_competitor && (
                      <Star className="h-3.5 w-3.5 fill-feleti-gold text-feleti-gold shrink-0" />
                    )}
                    {c.segment && (
                      <span
                        className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                          SEGMENT_COLORS[c.segment.toLowerCase()] || "text-muted-foreground bg-white/5"
                        }`}
                      >
                        {c.segment}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-3 mt-0.5 text-xs text-muted-foreground">
                    <span>{c.country || "—"}</span>
                    {c.founded_year && <span>с {c.founded_year}</span>}
                    <span>{c.models?.length || 0} моделей</span>
                  </div>
                </div>

                {editingId === c.id.toString() ? (
                  <button
                    onClick={handleSave}
                    disabled={saving}
                    className="inline-flex items-center gap-1.5 rounded-xl bg-feleti-gold px-3 py-1.5 text-xs font-medium text-black hover:bg-feleti-gold/90 transition-colors disabled:opacity-50"
                  >
                    {saving ? (
                      <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    ) : saved ? (
                      <Check className="h-3.5 w-3.5" />
                    ) : (
                      <Save className="h-3.5 w-3.5" />
                    )}
                    {saved ? "Сохранено" : "Сохранить"}
                  </button>
                ) : (
                  <div className="flex items-center gap-1">
                    {c.base_url && (
                      <a
                        href={c.base_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}
                    {c.dealers && c.dealers.length > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                        <Globe className="h-3 w-3" />
                        {c.dealers.length}
                      </span>
                    )}
                    <button
                      onClick={() => openEdit(c)}
                      className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                    >
                      <Pencil className="h-4 w-4" />
                    </button>
                    <button
                      onClick={() => handleDelete(c)}
                      className="rounded-lg p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>

              {/* Edit form */}
              <AnimatePresence>
                {editingId === c.id.toString() && form && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="border-t border-white/5"
                  >
                    <div className="p-4 space-y-3">
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Название</label>
                          <input
                            value={form.name}
                            onChange={(e) => setForm({ ...form, name: e.target.value })}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Страна</label>
                          <input
                            value={form.country}
                            onChange={(e) => setForm({ ...form, country: e.target.value })}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Год основания</label>
                          <input
                            value={form.founded_year}
                            onChange={(e) => setForm({ ...form, founded_year: e.target.value })}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                            placeholder="1950"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">Сегмент</label>
                          <select
                            value={form.segment}
                            onChange={(e) => setForm({ ...form, segment: e.target.value })}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                          >
                            <option value="">—</option>
                            <option value="premium">Premium</option>
                            <option value="industrial">Industrial</option>
                            <option value="middle">Middle</option>
                            <option value="budget">Budget</option>
                            <option value="horeca">Horeca</option>
                            <option value="profi">Profi</option>
                          </select>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs text-muted-foreground mb-1">URL</label>
                          <input
                            value={form.base_url}
                            onChange={(e) => setForm({ ...form, base_url: e.target.value })}
                            className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                            placeholder="https://..."
                          />
                        </div>
                        <div className="flex items-end pb-1.5">
                          <label className="flex items-center gap-2 cursor-pointer">
                            <button
                              onClick={() => setForm({ ...form, is_main_competitor: !form.is_main_competitor })}
                              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                                form.is_main_competitor ? "bg-feleti-gold" : "bg-white/10"
                              }`}
                            >
                              <span
                                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                                  form.is_main_competitor ? "translate-x-[18px]" : "translate-x-1"
                                }`}
                              />
                            </button>
                            <span className={`text-xs ${form.is_main_competitor ? "text-feleti-gold" : "text-muted-foreground"}`}>
                              <Star className={`inline h-3 w-3 mr-0.5 ${form.is_main_competitor ? "fill-feleti-gold" : ""}`} />
                              Главный конкурент
                            </span>
                          </label>
                        </div>
                      </div>

                      <div>
                        <label className="block text-xs text-muted-foreground mb-1">Описание</label>
                        <textarea
                          value={form.description}
                          onChange={(e) => setForm({ ...form, description: e.target.value })}
                          rows={3}
                          className="w-full rounded-lg border border-white/10 bg-white/5 px-2.5 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y"
                        />
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))
        )}
      </div>
    </div>
  );
}
