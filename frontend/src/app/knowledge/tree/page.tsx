"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  BookOpen,
  ChevronRight,
  Fish,
  Beef,
  Shell,
  Wrench,
  Thermometer,
  Snowflake,
  Package,
  Droplets,
  Flame,
  Factory,
  Wind,
  Refrigerator,
  FlaskConical,
  Leaf,
  Building2,
  Globe,
  UtensilsCrossed,
  AlertTriangle,
  Layers,
  Shrink,
  Plus,
  Pencil,
  Trash2,
  type LucideIcon,
} from "lucide-react";
import { apiClient } from "@/lib/api/client";
import Link from "next/link";
import { useAuthStore } from "@/stores/auth";
import { TopicFormModal } from "@/components/knowledge/TopicFormModal";
import { ConfirmationModal } from "@/components/shared/ConfirmationModal";
import {
  createTopic,
  updateTopic,
  deleteTopic,
  type TopicRead,
} from "@/lib/api/topics";

/* ─── Types ─── */

interface TopicTreeNode {
  id: number | null;
  slug: string;
  label: string;
  description: string | null;
  path: string;
  level: number;
  sort_order: number;
  icon: string | null;
  article_count: number;
  children: TopicTreeNode[];
}

/* ─── Icon map ─── */

const ICON_MAP: Record<string, LucideIcon> = {
  technologies: Factory,
  zasol: Droplets,
  "suchoj-zasol": Droplets,
  "mokryj-zasol": Droplets,
  shpricevanie: Droplets,
  termoobrabotka: Thermometer,
  "holodnoe-kopchenie": Snowflake,
  "goryachee-kopchenie": Flame,
  "polugoryachee-kopchenie": Thermometer,
  sushka: Wind,
  varka: Flame,
  "ohlazhdenie-i-hranenie": Refrigerator,
  upakovka: Package,
  "vakuumnaya-upakovka": Package,
  "gaz-mod-sreda": FlaskConical,
  syrio: Leaf,
  ryba: Fish,
  osetr: Fish,
  "losos-forel": Fish,
  skumbriya: Fish,
  ugor: Fish,
  "sig-ryapushka": Fish,
  myaso: Beef,
  svinina: Beef,
  govyadina: Beef,
  ptica: Beef,
  moreprodukty: Shell,
  obolochki: Shrink,
  oborudovanie: Wrench,
  "kamery-koptilnye": Building2,
  "feleti-smok": Building2,
  mid: Building2,
  izhitsa: Building2,
  dymogeneratory: Wind,
  "kompressory-klimat": Wind,
  "mojka-defrostaciya": Droplets,
  recepty: UtensilsCrossed,
  rybnye: Fish,
  myasnye: Beef,
  moreproduktov: Shell,
  "problemy-i-resheniya": AlertTriangle,
  gorech: AlertTriangle,
  peresol: Droplets,
  nedosol: Droplets,
  plesen: AlertTriangle,
  textura: Layers,
  konkurenty: Globe,
  otechestvennye: Globe,
  importnye: Globe,
};

function getIcon(slug: string): LucideIcon {
  return ICON_MAP[slug] || BookOpen;
}

/* ─── TreeNode ─── */

function TreeNode({
  node,
  depth,
  isAdmin,
  onEdit,
  onDelete,
}: {
  node: TopicTreeNode;
  depth: number;
  isAdmin: boolean | undefined;
  onEdit: (n: TopicTreeNode) => void;
  onDelete: (n: TopicTreeNode) => void;
}) {
  const [open, setOpen] = useState(depth < 1);
  const hasChildren = node.children.length > 0;
  const Icon = getIcon(node.slug);

  return (
    <div className="group">
      <div
        className="flex items-center"
        style={{ paddingLeft: `${12 + depth * 20}px` }}
      >
        {hasChildren ? (
          <motion.button
            animate={{ rotate: open ? 90 : 0 }}
            transition={{ duration: 0.15 }}
            onClick={() => setOpen(!open)}
            className="shrink-0 text-muted-foreground/50 hover:text-white mr-1"
          >
            <ChevronRight className="h-3.5 w-3.5" />
          </motion.button>
        ) : (
          <span className="w-[18px] shrink-0 mr-1" />
        )}

        <Link
          href={node.article_count > 0 ? `/knowledge?topic_id=${node.id}` : "#"}
          className={`flex flex-1 items-center gap-2 rounded-xl px-2 py-2 text-sm transition-colors ${
            node.article_count > 0
              ? "text-white hover:bg-feleti-gold/10 hover:text-feleti-gold"
              : "text-muted-foreground hover:text-white hover:bg-white/5"
          }`}
        >
          <Icon
            className={`h-4 w-4 shrink-0 ${
              depth === 0
                ? "text-feleti-gold"
                : "text-muted-foreground group-hover:text-feleti-gold/70"
            }`}
          />
          <span className="truncate flex-1">{node.label}</span>
          {node.article_count > 0 && (
            <span className="shrink-0 rounded-full bg-feleti-gold/10 px-2 py-0.5 text-[11px] text-feleti-gold">
              {node.article_count}
            </span>
          )}
        </Link>

        {/* Admin actions */}
        {isAdmin && (
          <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity shrink-0 ml-1">
            <button
              onClick={() => onEdit(node)}
              className="p-1 rounded-lg text-muted-foreground/50 hover:text-white hover:bg-white/5 transition-colors"
              title="Редактировать"
            >
              <Pencil className="h-3.5 w-3.5" />
            </button>
            {node.article_count === 0 && (
              <button
                onClick={() => onDelete(node)}
                className="p-1 rounded-lg text-muted-foreground/50 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                title="Удалить"
              >
                <Trash2 className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {node.description && open && (
        <p
          className="text-xs text-muted-foreground/60 px-3 mt-0.5"
          style={{ paddingLeft: `${40 + depth * 20}px` }}
        >
          {node.description}
        </p>
      )}

      <AnimatePresence initial={false}>
        {open && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="overflow-hidden"
          >
            {node.children.map((child) => (
              <TreeNode
                key={child.slug}
                node={child}
                depth={depth + 1}
                isAdmin={isAdmin}
                onEdit={onEdit}
                onDelete={onDelete}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function countArticles(total: number, node: TopicTreeNode): number {
  return total + node.article_count + node.children.reduce(countArticles, 0);
}

/* ─── Page ─── */

export default function KnowledgeTreePage() {
  const user = useAuthStore((s) => s.user);
  const isAdmin = user?.role === "admin" || (user as { is_superuser?: boolean } | null)?.is_superuser;
  const queryClient = useQueryClient();

  const [showForm, setShowForm] = useState(false);
  const [editNode, setEditNode] = useState<TopicTreeNode | null>(null);
  const [deleteNode, setDeleteNode] = useState<TopicTreeNode | null>(null);

  const treeQuery = useQuery({
    queryKey: ["knowledge-topics-tree"],
    queryFn: () =>
      apiClient.get("/knowledge/topics/tree").then((r) => r.data as TopicTreeNode[]),
    staleTime: 60000,
  });

  const flatQuery = useQuery({
    queryKey: ["knowledge-topics-flat"],
    queryFn: () =>
      apiClient.get("/knowledge/topics").then((r) => r.data as TopicRead[]),
    staleTime: 60000,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteTopic(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["knowledge-topics-tree"] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-topics-flat"] });
    },
  });

  const handleSave = useCallback(
    async (data: { label: string; slug: string; description: string; parent_id: number | null; sort_order: number; icon: string }) => {
      if (editNode && editNode.id) {
        await updateTopic(editNode.id, {
          label: data.label,
          description: data.description || null,
          parent_id: data.parent_id,
          sort_order: data.sort_order,
          icon: data.icon || null,
        });
      } else {
        await createTopic({
          label: data.label,
          slug: data.slug,
          description: data.description || null,
          parent_id: data.parent_id,
          sort_order: data.sort_order,
          icon: data.icon || null,
        });
      }
      queryClient.invalidateQueries({ queryKey: ["knowledge-topics-tree"] });
      queryClient.invalidateQueries({ queryKey: ["knowledge-topics-flat"] });
    },
    [editNode, queryClient],
  );

  const totalArticles = treeQuery.data?.reduce(countArticles, 0) ?? 0;

  return (
    <div className="flex gap-6 h-[calc(100vh-7rem)]">
      {/* Tree panel */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-lg font-semibold text-white">
              Семантическое дерево знаний
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">
              {treeQuery.data?.length ?? 0} корневых тем · {totalArticles} статей
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/knowledge"
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/5 px-3 py-1.5 text-xs text-muted-foreground hover:text-white hover:border-white/10 transition-colors"
            >
              <BookOpen className="h-3.5 w-3.5" />
              Список статей
            </Link>
            {isAdmin && (
              <button
                onClick={() => { setEditNode(null); setShowForm(true); }}
                className="inline-flex items-center gap-1.5 rounded-xl bg-feleti-gold/10 px-3 py-1.5 text-xs text-feleti-gold hover:bg-feleti-gold/20 transition-colors"
              >
                <Plus className="h-3.5 w-3.5" />
                Новая тема
              </button>
            )}
          </div>
        </div>

        {/* Tree */}
        <div className="flex-1 overflow-y-auto pr-2 scrollbar-thin">
          {treeQuery.error ? (
            <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-16">
              <AlertTriangle className="h-12 w-12 text-red-400/50" />
              <p className="mt-4 text-muted-foreground">Ошибка загрузки дерева</p>
              <button
                onClick={() => treeQuery.refetch()}
                className="mt-2 text-sm text-feleti-gold hover:underline"
              >
                Повторить
              </button>
            </div>
          ) : treeQuery.isLoading ? (
            <div className="space-y-1">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="h-7 animate-pulse rounded-xl bg-white/5"
                  style={{
                    marginLeft: `${(i % 4) * 20}px`,
                    width: `${60 + Math.random() * 30}%`,
                  }}
                />
              ))}
            </div>
          ) : (
            (treeQuery.data ?? []).map((node) => (
              <TreeNode
                key={node.slug}
                node={node}
                depth={0}
                isAdmin={isAdmin}
                onEdit={(n) => { setEditNode(n); setShowForm(true); }}
                onDelete={(n) => setDeleteNode(n)}
              />
            ))
          )}
        </div>
      </div>

      {/* Info panel */}
      <aside className="w-72 shrink-0 hidden lg:block">
        <div className="sticky top-0 rounded-2xl border border-white/5 bg-white/[0.02] p-4 space-y-4">
          <h3 className="text-sm font-semibold text-white">О дереве</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Семантическое дерево — иерархия знаний о копчении. Каждый узел — тема.
            Статьи привязаны к одному или нескольким узлам.
          </p>
          <div className="space-y-2 text-xs">
            <div className="flex items-center gap-2 text-muted-foreground">
              <Factory className="h-3.5 w-3.5 text-feleti-gold" />
              Корневые разделы
            </div>
            <div className="flex items-center gap-2 text-muted-foreground">
              <span className="inline-flex items-center justify-center h-3.5 w-3.5 rounded-full bg-feleti-gold/10 text-[10px] text-feleti-gold font-medium">
                i
              </span>
              Число — количество статей
            </div>
          </div>
          <div className="h-px bg-white/5" />
          <p className="text-xs text-muted-foreground">
            {isAdmin
              ? "Наведите на узел: ✏️ редактировать, 🗑️ удалить. +Новая тема — создать."
              : "Клик по узлу со статьями → фильтр. Стрелка → развернуть."}
          </p>
        </div>
      </aside>

      {/* Create/Edit modal */}
      <TopicFormModal
        open={showForm}
        onClose={() => { setShowForm(false); setEditNode(null); }}
        onSave={handleSave}
        topics={flatQuery.data ?? []}
        editTopic={
          editNode
            ? {
                id: editNode.id ?? 0,
                slug: editNode.slug,
                label: editNode.label,
                description: editNode.description,
                path: editNode.path,
                parent_id: null,
                level: editNode.level,
                sort_order: editNode.sort_order,
                icon: editNode.icon,
                article_count: editNode.article_count,
                created_at: "",
                updated_at: "",
              }
            : null
        }
      />

      {/* Delete confirmation */}
      <ConfirmationModal
        open={deleteNode !== null}
        onClose={() => setDeleteNode(null)}
        onConfirm={async () => {
          if (deleteNode?.id) {
            await deleteMutation.mutateAsync(deleteNode.id);
            setDeleteNode(null);
          }
        }}
        title="Удалить тему?"
        message={`Вы уверены, что хотите удалить «${deleteNode?.label}»? Дочерние темы тоже будут удалены.`}
        confirmLabel="Удалить"
        variant="danger"
        loading={deleteMutation.isPending}
      />
    </div>
  );
}


