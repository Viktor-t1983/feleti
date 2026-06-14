"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Shield,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { ErrorState } from "@/components/shared/ErrorState";
import { useAuthStore } from "@/stores/auth";
import {
  listFacts,
  updateFactStatus,
  getVerificationReport,
  runAutoVerify,
  type FactItem,
} from "@/lib/api/facts";

const PREDICATE_LABELS: Record<string, string> = {
  uses_brine: "Рассолы",
  uses_equipment: "Оборудование",
  uses_technology: "Технологии",
  has_parameter: "Параметры",
  regulated_by: "ГОСТы / ТУ",
  has_category: "Категоризация",
  contains: "Состав",
  derived_from: "Сырьё",
  shelf_life: "Срок хранения",
  storage_condition: "Условия хранения",
  process_step: "Техпроцесс",
  mentions: "Упоминания",
};

const STATUS_STYLES: Record<string, string> = {
  candidate: "text-yellow-400 bg-yellow-500/10 border-yellow-500/20",
  confirmed: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  deprecated: "text-red-400 bg-red-500/10 border-red-500/20",
  contradicted: "text-orange-400 bg-orange-500/10 border-orange-500/20",
};

function confidenceColor(c: number): string {
  if (c >= 0.8) return "text-green-400";
  if (c >= 0.5) return "text-yellow-400";
  return "text-red-400";
}

function FactCard({ fact, onConfirm, onDeprecate }: {
  fact: FactItem;
  onConfirm: () => void;
  onDeprecate: () => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const predicateLabel = PREDICATE_LABELS[fact.predicate] || fact.predicate;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-lg border border-white/5 bg-white/[0.02] overflow-hidden"
    >
      <div className="flex items-start gap-3 p-3">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${STATUS_STYLES[fact.status] || "border-white/5 text-muted-foreground"}`}>
              {fact.status}
            </span>
            <span className="text-sm font-medium text-white">{fact.subject_name}</span>
            <span className="text-xs text-muted-foreground">--{predicateLabel}--&gt;</span>
            <span className="text-sm text-feleti-gold">{fact.object_name}</span>
            <span className={`text-[10px] font-medium ${confidenceColor(fact.confidence)}`}>
              {Math.round(fact.confidence * 100)}%
            </span>
          </div>
          {fact.source_text && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="mt-1.5 flex items-center gap-1 text-[11px] text-muted-foreground/60 hover:text-muted-foreground transition-colors"
            >
              {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
              источник
            </button>
          )}
          {expanded && fact.source_text && (
            <div className="mt-1 pl-4 border-l border-white/5">
              <p className="text-[11px] italic text-muted-foreground/70 leading-relaxed">
                «{fact.source_text}»
              </p>
            </div>
          )}
        </div>
        <div className="flex items-center gap-1 shrink-0">
          <a
            href={`/knowledge/${fact.article_id}`}
            className="p-1.5 text-muted-foreground hover:text-feleti-gold transition-colors"
            title="Открыть статью"
          >
            <ExternalLink className="h-3.5 w-3.5" />
          </a>
          {fact.status === "candidate" && (
            <>
              <button
                onClick={onConfirm}
                className="p-1.5 text-emerald-500/60 hover:text-emerald-400 transition-colors"
                title="Подтвердить"
              >
                <CheckCircle2 className="h-4 w-4" />
              </button>
              <button
                onClick={onDeprecate}
                className="p-1.5 text-red-500/60 hover:text-red-400 transition-colors"
                title="Отклонить"
              >
                <XCircle className="h-4 w-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function FactReviewPage() {
  const queryClient = useQueryClient();
  const user = useAuthStore((s) => s.user);
  const [filterStatus, setFilterStatus] = useState<string>("candidate");
  const [filterPredicate, setFilterPredicate] = useState<string>("");

  const { data: facts, isLoading, error } = useQuery({
    queryKey: ["facts", filterStatus, filterPredicate],
    queryFn: () =>
      listFacts({
        status: filterStatus || undefined,
        predicate: filterPredicate || undefined,
        limit: 100,
      }),
  });

  const { data: report } = useQuery({
    queryKey: ["verify-report"],
    queryFn: () => getVerificationReport(),
  });

  const confirmMutation = useMutation({
    mutationFn: (factId: number) => updateFactStatus(factId, "confirmed"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      queryClient.invalidateQueries({ queryKey: ["verify-report"] });
    },
  });

  const deprecateMutation = useMutation({
    mutationFn: (factId: number) => updateFactStatus(factId, "deprecated"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      queryClient.invalidateQueries({ queryKey: ["verify-report"] });
    },
  });

  const autoVerifyMutation = useMutation({
    mutationFn: () => runAutoVerify(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["facts"] });
      queryClient.invalidateQueries({ queryKey: ["verify-report"] });
    },
  });

  if (!user || user.role !== "ADMIN") {
    return (
      <div className="flex items-center justify-center py-20">
        <p className="text-muted-foreground">Только для администраторов</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-semibold text-white">Ревью фактов</h1>
        <button
          onClick={() => autoVerifyMutation.mutate()}
          disabled={autoVerifyMutation.isPending}
          className="flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.03] px-3 py-1.5 text-xs text-muted-foreground hover:text-white transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${autoVerifyMutation.isPending ? "animate-spin" : ""}`} />
          Авто-верификация
        </button>
      </div>

      {/* Verification report */}
      {report && (report.duplicates.length > 0 || report.contradictions.length > 0) && (
        <div className="space-y-2">
          {report.duplicates.length > 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-yellow-500/20 bg-yellow-500/5 px-3 py-2">
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
              <span className="text-xs text-muted-foreground">
                {report.duplicates.length} групп дубликатов
              </span>
            </div>
          )}
          {report.contradictions.length > 0 && (
            <div className="flex items-center gap-2 rounded-lg border border-orange-500/20 bg-orange-500/5 px-3 py-2">
              <AlertTriangle className="h-4 w-4 text-orange-400" />
              <span className="text-xs text-muted-foreground">
                {report.contradictions.length} противоречий
              </span>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-3">
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="rounded-lg border border-white/5 bg-white/[0.03] px-2.5 py-1.5 text-xs text-muted-foreground"
        >
          <option value="candidate">Кандидаты</option>
          <option value="confirmed">Подтверждённые</option>
          <option value="deprecated">Отклонённые</option>
          <option value="">Все</option>
        </select>
        <input
          value={filterPredicate}
          onChange={(e) => setFilterPredicate(e.target.value)}
          placeholder="Предикат..."
          className="flex-1 rounded-lg border border-white/5 bg-white/[0.03] px-2.5 py-1.5 text-xs text-muted-foreground placeholder:text-muted-foreground/30"
        />
      </div>

      {/* Facts list */}
      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-16 animate-pulse rounded-lg bg-white/5" />
          ))}
        </div>
      ) : error ? (
        <ErrorState message="Ошибка загрузки фактов" />
      ) : facts && facts.length > 0 ? (
        <AnimatePresence mode="popLayout">
          <div className="space-y-2">
            {facts.map((fact) => (
              <FactCard
                key={fact.id}
                fact={fact}
                onConfirm={() => confirmMutation.mutate(fact.id)}
                onDeprecate={() => deprecateMutation.mutate(fact.id)}
              />
            ))}
          </div>
        </AnimatePresence>
      ) : (
        <div className="flex flex-col items-center justify-center py-16">
          <Shield className="h-10 w-10 text-muted-foreground/30" />
          <p className="mt-3 text-sm text-muted-foreground">Нет фактов для отображения</p>
        </div>
      )}
    </div>
  );
}
