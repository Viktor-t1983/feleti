"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search,
  Loader2,
  Pencil,
  Plus,
  X,
  Check,
  ExternalLink,
  Factory,
  Globe,
} from "lucide-react";
import {
  fetchManufacturersAdmin,
  createManufacturer,
  updateManufacturer,
  deleteManufacturer,
} from "@/lib/api/admin-manufacturers";
import type { Manufacturer, ManufacturerCreate } from "@/lib/api/admin-manufacturers";

interface EditForm {
  name: string;
  short_name: string;
  country: string;
  city: string;
  founded_year: string;
  website: string;
  description: string;
  is_our_brand: boolean;
  is_competitor: boolean;
  sort_order: string;
}

const emptyForm: EditForm = {
  name: "",
  short_name: "",
  country: "",
  city: "",
  founded_year: "",
  website: "",
  description: "",
  is_our_brand: false,
  is_competitor: false,
  sort_order: "100",
};

export function AdminManufacturersTab() {
  const [items, setItems] = useState<Manufacturer[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<EditForm>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchManufacturersAdmin(1, 200);
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
    (m) =>
      m.name.toLowerCase().includes(search.toLowerCase()) ||
      (m.country || "").toLowerCase().includes(search.toLowerCase()) ||
      (m.short_name || "").toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const openEdit = (m: Manufacturer) => {
    setEditingId(m.id);
    setForm({
      name: m.name,
      short_name: m.short_name || "",
      country: m.country || "",
      city: m.city || "",
      founded_year: m.founded_year?.toString() || "",
      website: m.website || "",
      description: m.description || "",
      is_our_brand: m.is_our_brand,
      is_competitor: m.is_competitor,
      sort_order: m.sort_order.toString(),
    });
    setError("");
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      const data = {
        name: form.name,
        short_name: form.short_name || null,
        country: form.country || null,
        city: form.city || null,
        founded_year: form.founded_year ? parseInt(form.founded_year) : null,
        website: form.website || null,
        description: form.description || null,
        is_our_brand: form.is_our_brand,
        is_competitor: form.is_competitor,
        sort_order: parseInt(form.sort_order) || 100,
      };

      if (editingId) {
        await updateManufacturer(editingId, data);
      } else {
        await createManufacturer({ slug: form.name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, ""), ...data } as ManufacturerCreate);
      }
      setShowModal(false);
      await load();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail || "Ошибка сохранения";
      setError(detail);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (m: Manufacturer) => {
    if (!confirm(`Удалить производителя ${m.name}?`)) return;
    try {
      await deleteManufacturer(m.id);
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
            placeholder="Поиск производителей..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-white/10 bg-white/5 py-2.5 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none"
          />
        </div>
        <button
          onClick={openCreate}
          className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-4 py-2.5 text-sm font-medium text-black hover:bg-feleti-gold/90 transition-colors"
        >
          <Plus className="h-4 w-4" />
          Создать
        </button>
        <span className="text-xs text-muted-foreground">{filtered.length} / {items.length}</span>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/5">
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium">Производитель</th>
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium">Страна</th>
                  <th className="px-4 py-3 text-center text-muted-foreground font-medium">Бренд</th>
                  <th className="px-4 py-3 text-center text-muted-foreground font-medium">Конкурент</th>
                  <th className="px-4 py-3 text-center text-muted-foreground font-medium">Порядок</th>
                  <th className="px-4 py-3 text-right text-muted-foreground font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((m) => (
                  <tr key={m.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-feleti-gold/10">
                          <Factory className="h-4 w-4 text-feleti-gold" />
                        </div>
                        <div>
                          <div className="text-white font-medium">{m.name}</div>
                          {m.short_name && (
                            <div className="text-xs text-muted-foreground">{m.short_name}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">
                      <span className="inline-flex items-center gap-1">
                        {m.country && <Globe className="h-3 w-3" />}
                        {m.country || "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {m.is_our_brand ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 px-2 py-0.5 text-xs text-emerald-400">
                          <Check className="h-3 w-3" /> FELETI
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {m.is_competitor ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-orange-500/10 px-2 py-0.5 text-xs text-orange-400">
                          Конкурент
                        </span>
                      ) : (
                        <span className="text-xs text-muted-foreground">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center text-muted-foreground">{m.sort_order}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        {m.website && (
                          <a
                            href={m.website}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        <button
                          onClick={() => openEdit(m)}
                          className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(m)}
                          className="rounded-lg p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60" onClick={() => setShowModal(false)} />
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="relative w-full max-w-2xl rounded-2xl border border-white/10 bg-[#121212] p-6 shadow-xl max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Factory className="h-5 w-5 text-feleti-gold" />
                  <h3 className="text-lg font-semibold text-white">
                    {editingId ? "Редактировать производителя" : "Создать производителя"}
                  </h3>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="rounded-lg p-1.5 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                >
                  <X className="h-5 w-5" />
                </button>
              </div>

              {error && (
                <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-300">{error}</div>
              )}

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Название *</label>
                    <input
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Короткое название</label>
                    <input
                      value={form.short_name}
                      onChange={(e) => setForm({ ...form, short_name: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Страна</label>
                    <input
                      value={form.country}
                      onChange={(e) => setForm({ ...form, country: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Город</label>
                    <input
                      value={form.city}
                      onChange={(e) => setForm({ ...form, city: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Год основания</label>
                    <input
                      value={form.founded_year}
                      onChange={(e) => setForm({ ...form, founded_year: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                      placeholder="1950"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-muted-foreground mb-1.5">Веб-сайт</label>
                  <input
                    value={form.website}
                    onChange={(e) => setForm({ ...form, website: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    placeholder="https://..."
                  />
                </div>

                <div>
                  <label className="block text-sm text-muted-foreground mb-1.5">Описание</label>
                  <textarea
                    value={form.description}
                    onChange={(e) => setForm({ ...form, description: e.target.value })}
                    rows={3}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50 resize-y"
                  />
                </div>

                <div className="flex items-center gap-6">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <button
                      onClick={() => setForm({ ...form, is_our_brand: !form.is_our_brand })}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        form.is_our_brand ? "bg-emerald-600" : "bg-white/10"
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          form.is_our_brand ? "translate-x-[18px]" : "translate-x-1"
                        }`}
                      />
                    </button>
                    <span className="text-sm text-muted-foreground">Наш бренд (FELETI)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <button
                      onClick={() => setForm({ ...form, is_competitor: !form.is_competitor })}
                      className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                        form.is_competitor ? "bg-orange-600" : "bg-white/10"
                      }`}
                    >
                      <span
                        className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${
                          form.is_competitor ? "translate-x-[18px]" : "translate-x-1"
                        }`}
                      />
                    </button>
                    <span className="text-sm text-muted-foreground">Конкурент</span>
                  </label>
                  <div className="ml-auto">
                    <label className="block text-xs text-muted-foreground mb-1">Порядок сортировки</label>
                    <input
                      type="number"
                      value={form.sort_order}
                      onChange={(e) => setForm({ ...form, sort_order: e.target.value })}
                      className="w-20 rounded-xl border border-white/10 bg-white/5 px-3 py-1.5 text-sm text-white outline-none focus:border-feleti-gold/50 text-center"
                    />
                  </div>
                </div>
              </div>

              <div className="mt-6 flex gap-3 justify-end">
                <button
                  onClick={() => setShowModal(false)}
                  className="rounded-xl border border-white/10 px-4 py-2.5 text-sm text-white hover:bg-white/5 transition-colors"
                >
                  Отмена
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving || !form.name}
                  className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold px-4 py-2.5 text-sm font-medium text-black hover:bg-feleti-gold/90 transition-colors disabled:opacity-50"
                >
                  {saving ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Check className="h-4 w-4" />
                  )}
                  {editingId ? "Сохранить" : "Создать"}
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
