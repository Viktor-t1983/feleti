"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion } from "framer-motion";
import {
  Globe,
  Plus,
  Trash2,
  Edit3,
  Search,
  ShieldAlert,
  ShieldCheck,
  ExternalLink,
} from "lucide-react";
import { ErrorState } from "@/components/shared/ErrorState";
import { ConfirmationModal } from "@/components/shared/ConfirmationModal";
import {
  listSources,
  createSource,
  updateSource,
  deleteSource,
  type SourceRead,
  type SourceCreate,
  type SourceUpdate,
} from "@/lib/api/sources";
import { useAuthStore } from "@/stores/auth";

const SCORE_BADGE: Record<number, { label: string; color: string; bg: string }> = {
  3: { label: "Высокий", color: "text-emerald-400", bg: "bg-emerald-500/10" },
  2: { label: "Средний", color: "text-amber-400", bg: "bg-amber-500/10" },
  1: { label: "Низкий", color: "text-muted-foreground", bg: "bg-white/5" },
  0: { label: "Неизвестный", color: "text-red-400", bg: "bg-red-500/10" },
};

function SourceFormModal({
  source,
  onClose,
  onSave,
}: {
  source?: SourceRead | null;
  onClose: () => void;
  onSave: (data: SourceCreate | SourceUpdate) => void;
}) {
  const [domain, setDomain] = useState(source?.domain || "");
  const [score, setScore] = useState(source?.score ?? 1);
  const [label, setLabel] = useState(source?.label || "");
  const [notes, setNotes] = useState(source?.notes || "");
  const [blacklisted, setBlacklisted] = useState(source?.is_blacklisted || false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      domain,
      score,
      label: label || null,
      notes: notes || null,
      is_blacklisted: blacklisted,
    } as SourceCreate | SourceUpdate);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={onClose}>
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md rounded-2xl border border-white/10 bg-[#1a1a1a] p-6 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold text-white mb-4">
          {source ? "Редактировать источник" : "Добавить источник"}
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Домен *</label>
            <input
              type="text"
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              required
              placeholder="example.ru"
              className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Название</label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="Мой источник"
              className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Уровень доверия</label>
            <div className="flex gap-2">
              {[1, 2, 3].map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => setScore(s)}
                  className={`flex-1 rounded-xl border py-2 text-sm transition-colors ${
                    score === s
                      ? "border-feleti-gold/30 bg-feleti-gold/10 text-feleti-gold"
                      : "border-white/5 text-muted-foreground hover:text-white"
                  }`}
                >
                  {s} — {SCORE_BADGE[s].label}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-xs text-muted-foreground mb-1">Заметки</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-xl border border-white/5 bg-white/[0.02] px-3 py-2 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none resize-none"
            />
          </div>
          <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={blacklisted}
              onChange={(e) => setBlacklisted(e.target.checked)}
              className="rounded border-white/10"
            />
            В чёрном списке (блокировать)
          </label>
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-xl border border-white/5 px-4 py-2 text-sm text-muted-foreground hover:text-white transition-colors"
            >
              Отмена
            </button>
            <button
              type="submit"
              className="rounded-xl bg-feleti-gold/20 px-4 py-2 text-sm text-feleti-gold hover:bg-feleti-gold/30 transition-colors"
            >
              {source ? "Сохранить" : "Добавить"}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}

export default function SourcesPage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "admin" || (user as { is_superuser?: boolean } | null)?.is_superuser;

  const [search, setSearch] = useState("");
  const [editSource, setEditSource] = useState<SourceRead | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [deleteTarget, setDeleteTarget] = useState<SourceRead | null>(null);

  const sourcesQuery = useQuery({
    queryKey: ["sources"],
    queryFn: () => listSources(),
    staleTime: 10000,
  });

  const createMut = useMutation({
    mutationFn: (data: SourceCreate) => createSource(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      setShowForm(false);
    },
  });

  const updateMut = useMutation({
    mutationFn: ({ id, data }: { id: number; data: SourceUpdate }) => updateSource(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      setEditSource(null);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: number) => deleteSource(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
      setDeleteTarget(null);
    },
  });

  const sources = sourcesQuery.data || [];
  const filtered = search
    ? sources.filter(
        (s) =>
          s.domain.toLowerCase().includes(search.toLowerCase()) ||
          (s.label?.toLowerCase() || "").includes(search.toLowerCase())
      )
    : sources;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-white">Менеджер источников</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Управление источниками знаний: репутация доменов, чёрный список
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold/20 px-4 py-2 text-sm text-feleti-gold hover:bg-feleti-gold/30 transition-colors"
          >
            <Plus className="h-4 w-4" />
            Добавить
          </button>
        )}
      </div>

      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Поиск по домену..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full rounded-xl border border-white/5 bg-white/[0.02] py-2 pl-10 pr-4 text-sm text-white placeholder:text-muted-foreground focus:border-feleti-gold/30 focus:outline-none"
        />
      </div>

      {sourcesQuery.error ? (
        <ErrorState message="Ошибка загрузки источников" onRetry={() => sourcesQuery.refetch()} />
      ) : sourcesQuery.isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="h-14 animate-pulse rounded-xl bg-white/5" />
          ))}
        </div>
      ) : (
        <div className="space-y-1">
          {filtered.map((source) => {
            const badge = SCORE_BADGE[source.score] || SCORE_BADGE[0];
            const BadgeIcon = source.is_blacklisted ? ShieldAlert : ShieldCheck;
            return (
              <motion.div
                key={source.id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                className="group flex items-center gap-4 rounded-xl border border-white/5 bg-white/[0.02] px-4 py-3 hover:bg-white/[0.03] transition-colors"
              >
                <Globe className="h-4 w-4 text-muted-foreground shrink-0" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-white truncate">{source.domain}</span>
                    {source.label && (
                      <span className="text-xs text-muted-foreground/50 truncate">— {source.label}</span>
                    )}
                  </div>
                  {source.notes && (
                    <p className="text-xs text-muted-foreground/40 truncate mt-0.5">{source.notes}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <span className={`inline-flex items-center gap-1 rounded-full ${badge.bg} px-2 py-0.5 text-xs ${badge.color}`}>
                    <BadgeIcon className="h-3 w-3" />
                    {badge.label}
                  </span>
                  {source.is_blacklisted && (
                    <span className="text-xs text-red-400/70">Заблокирован</span>
                  )}
                  {isAdmin && (
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => { setEditSource(source); setShowForm(true); }}
                        className="rounded-lg p-1.5 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                        title="Редактировать"
                      >
                        <Edit3 className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={() => setDeleteTarget(source)}
                        className="rounded-lg p-1.5 text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Удалить"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  )}
                  <a
                    href={`https://${source.domain}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="rounded-lg p-1.5 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                </div>
              </motion.div>
            );
          })}
          {filtered.length === 0 && (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-12">
              <Globe className="h-10 w-10 text-muted-foreground/30" />
              <p className="mt-3 text-sm text-muted-foreground">Нет источников</p>
            </div>
          )}
        </div>
      )}

      {/* Add / Edit modal */}
      {(showForm || editSource) && (
        <SourceFormModal
          source={editSource}
          onClose={() => { setShowForm(false); setEditSource(null); }}
          onSave={(data) => {
            if (editSource) {
              updateMut.mutate({ id: editSource.id, data: data as SourceUpdate });
            } else {
              createMut.mutate(data as SourceCreate);
            }
          }}
        />
      )}

      {/* Delete confirmation */}
      {deleteTarget && (
        <ConfirmationModal
          open={!!deleteTarget}
          title="Удалить источник"
          message={`Удалить «${deleteTarget.domain}»? Это действие нельзя отменить.`}
          confirmLabel="Удалить"
          variant="danger"
          onConfirm={() => deleteMut.mutate(deleteTarget.id)}
          onClose={() => setDeleteTarget(null)}
        />
      )}
    </div>
  );
}
