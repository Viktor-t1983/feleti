"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Plus,
  Pencil,
  Trash2,
  Loader2,
  Search,
  Shield,
  ShieldCheck,
  X,
  Check,
  UserCog,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import {
  fetchUsers,
  createUser,
  updateUser,
  deleteUser,
} from "@/lib/api/admin";
import type { User } from "@/lib/api/auth";
import type { UserCreate, UserUpdate } from "@/lib/api/admin";

const ROLE_LABELS: Record<string, string> = {
  admin: "Админ",
  technologist: "Технолог",
  operator: "Оператор",
  manager: "Менеджер",
  viewer: "Наблюдатель",
};

const ROLE_COLORS: Record<string, string> = {
  admin: "text-rose-400 bg-rose-500/10",
  technologist: "text-blue-400 bg-blue-500/10",
  operator: "text-emerald-400 bg-emerald-500/10",
  manager: "text-purple-400 bg-purple-500/10",
  viewer: "text-gray-400 bg-gray-500/10",
};

interface UserFormData {
  username: string;
  email: string;
  password: string;
  full_name: string;
  role: string;
  is_active: boolean;
  is_superuser: boolean;
}

const emptyForm: UserFormData = {
  username: "",
  email: "",
  password: "",
  full_name: "",
  role: "operator",
  is_active: true,
  is_superuser: false,
};

export function AdminUsersTab() {
  const currentUser = useAuthStore((s) => s.user);

  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [form, setForm] = useState<UserFormData>(emptyForm);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchUsers(1, 200);
      setUsers(data.items);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = users.filter(
    (u) =>
      u.username.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      (u.full_name || "").toLowerCase().includes(search.toLowerCase())
  );

  const openCreate = () => {
    setEditingId(null);
    setForm(emptyForm);
    setError("");
    setShowModal(true);
  };

  const openEdit = (u: User) => {
    setEditingId(u.id);
    setForm({
      username: u.username,
      email: u.email,
      password: "",
      full_name: u.full_name || "",
      role: u.role,
      is_active: u.is_active,
      is_superuser: false,
    });
    setError("");
    setShowModal(true);
  };

  const handleSave = async () => {
    setSaving(true);
    setError("");
    try {
      if (editingId) {
        const data: UserUpdate = {
          username: form.username,
          email: form.email,
          full_name: form.full_name || null,
          role: form.role,
          is_active: form.is_active,
        };
        if (form.password) data.password = form.password;
        await updateUser(editingId, data);
      } else {
        await createUser(form as UserCreate);
      }
      setShowModal(false);
      await load();
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail || "Ошибка сохранения";
      setError(detail);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (u: User) => {
    if (!confirm(`Удалить пользователя ${u.username}?`)) return;
    try {
      await deleteUser(u.id);
      await load();
    } catch {
      /* ignore */
    }
  };

  const handleToggleActive = async (u: User) => {
    try {
      await updateUser(u.id, { is_active: !u.is_active });
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
            placeholder="Поиск пользователей..."
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
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium">Пользователь</th>
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium">Email</th>
                  <th className="px-4 py-3 text-left text-muted-foreground font-medium">Роль</th>
                  <th className="px-4 py-3 text-center text-muted-foreground font-medium">Статус</th>
                  <th className="px-4 py-3 text-right text-muted-foreground font-medium">Действия</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((u) => (
                  <tr key={u.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-xs font-medium text-white">
                          {u.username.charAt(0).toUpperCase()}
                        </div>
                        <div>
                          <div className="text-white font-medium">
                            {u.full_name || u.username}
                            {u.is_superuser && (
                              <ShieldCheck className="inline h-3 w-3 ml-1 text-feleti-gold" />
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground">
                            @{u.username}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-muted-foreground">{u.email}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                          ROLE_COLORS[u.role] || ROLE_COLORS.viewer
                        }`}
                      >
                        <UserCog className="h-3 w-3" />
                        {ROLE_LABELS[u.role] || u.role}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <button
                        onClick={() => handleToggleActive(u)}
                        className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors ${
                          u.is_active
                            ? "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20"
                            : "bg-red-500/10 text-red-400 hover:bg-red-500/20"
                        }`}
                      >
                        {u.is_active ? (
                          <><Check className="h-3 w-3" /> Активен</>
                        ) : (
                          <><X className="h-3 w-3" /> Заблокирован</>
                        )}
                      </button>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-1">
                        <button
                          onClick={() => openEdit(u)}
                          disabled={u.id === currentUser?.id}
                          className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors disabled:opacity-30"
                          title="Редактировать"
                        >
                          <Pencil className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(u)}
                          disabled={u.id === currentUser?.id}
                          className="rounded-lg p-2 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors disabled:opacity-30"
                          title="Удалить"
                        >
                          <Trash2 className="h-4 w-4" />
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
              className="relative w-full max-w-lg rounded-2xl border border-white/10 bg-[#121212] p-6 shadow-xl"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <Shield className="h-5 w-5 text-feleti-gold" />
                  <h3 className="text-lg font-semibold text-white">
                    {editingId ? "Редактировать пользователя" : "Создать пользователя"}
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
                <div className="mb-4 rounded-xl border border-red-500/20 bg-red-500/5 p-3 text-sm text-red-300">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Username *</label>
                    <input
                      value={form.username}
                      onChange={(e) => setForm({ ...form, username: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                      placeholder="username"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Email *</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                      placeholder="user@example.com"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm text-muted-foreground mb-1.5">
                    {editingId ? "Пароль (оставьте пустым, чтобы не менять)" : "Пароль *"}
                  </label>
                  <input
                    type="password"
                    value={form.password}
                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="block text-sm text-muted-foreground mb-1.5">Полное имя</label>
                  <input
                    value={form.full_name}
                    onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                    className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    placeholder="Иван Иванов"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm text-muted-foreground mb-1.5">Роль</label>
                    <select
                      value={form.role}
                      onChange={(e) => setForm({ ...form, role: e.target.value })}
                      className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white outline-none focus:border-feleti-gold/50"
                    >
                      <option value="admin">Админ</option>
                      <option value="technologist">Технолог</option>
                      <option value="operator">Оператор</option>
                      <option value="manager">Менеджер</option>
                      <option value="viewer">Наблюдатель</option>
                    </select>
                  </div>
                  <div className="flex items-end pb-2">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <button
                        onClick={() => setForm({ ...form, is_active: !form.is_active })}
                        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                          form.is_active ? "bg-emerald-600" : "bg-white/10"
                        }`}
                      >
                        <span
                          className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                            form.is_active ? "translate-x-6" : "translate-x-1"
                          }`}
                        />
                      </button>
                      <span className="text-sm text-muted-foreground">
                        {form.is_active ? "Активен" : "Неактивен"}
                      </span>
                    </label>
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
                  disabled={saving || !form.username || !form.email || (!editingId && !form.password)}
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
