"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Check, X, Info, Cpu, AlertTriangle, BarChart3 } from "lucide-react";
import type { Competitor } from "./CompetitorCard";

const tabs = [
  { id: "overview", label: "Обзор", icon: Info },
  { id: "models", label: "Модели", icon: Cpu },
  { id: "problems", label: "Проблемы", icon: AlertTriangle },
  { id: "compare", label: "Сравнение", icon: BarChart3 },
];

interface CompetitorDetailsProps {
  competitor: Competitor;
}

export function CompetitorDetails({ competitor }: CompetitorDetailsProps) {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <div className="mt-4">
      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-white/5 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex flex-1 items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? "text-white"
                : "text-muted-foreground hover:text-white"
            }`}
          >
            {activeTab === tab.id && (
              <motion.div
                layoutId="activeTab"
                className="absolute inset-0 rounded-lg bg-white/10"
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )}
            <tab.icon className="relative h-4 w-4" />
            <span className="relative hidden sm:inline">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="mt-4"
      >
        {activeTab === "overview" && <OverviewTab competitor={competitor} />}
        {activeTab === "models" && <ModelsTab competitor={competitor} />}
        {activeTab === "problems" && <ProblemsTab competitor={competitor} />}
        {activeTab === "compare" && <CompareTab competitor={competitor} />}
      </motion.div>
    </div>
  );
}

function OverviewTab({ competitor }: { competitor: Competitor }) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-muted-foreground leading-relaxed">
        {competitor.description}
      </p>

      <div className="grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl bg-white/5 p-4">
          <h4 className="mb-3 text-sm font-medium text-emerald-400 flex items-center gap-2">
            <Check className="h-4 w-4" />
            Сильные стороны
          </h4>
          <ul className="space-y-2">
            {competitor.strengths.map((s, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="mt-1.5 h-1 w-1 rounded-full bg-emerald-400" />
                {s}
              </li>
            ))}
          </ul>
        </div>

        <div className="rounded-xl bg-white/5 p-4">
          <h4 className="mb-3 text-sm font-medium text-red-400 flex items-center gap-2">
            <X className="h-4 w-4" />
            Слабые стороны
          </h4>
          <ul className="space-y-2">
            {competitor.weaknesses.map((w, i) => (
              <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                <span className="mt-1.5 h-1 w-1 rounded-full bg-red-400" />
                {w}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}

function ModelsTab({ competitor }: { competitor: Competitor }) {
  return (
    <div className="space-y-3">
      {competitor.models.map((model, i) => (
        <div key={i} className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
          <div className="flex items-start justify-between mb-3">
            <h4 className="font-medium text-white">{model.name}</h4>
            {model.automation_level && (
              <span className="text-xs rounded-full bg-white/5 px-2 py-0.5 text-muted-foreground">
                {model.automation_level}
              </span>
            )}
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
            <ModelMetric label="Загрузка" value={model.max_load_kg ? `${model.max_load_kg} кг` : "—"} />
            <ModelMetric label="Мощность" value={model.power_kw ? `${model.power_kw} кВт` : "—"} />
            <ModelMetric label="Напряжение" value={model.voltage_v ? `${model.voltage_v}В` : "—"} />
            <ModelMetric label="Вес" value={model.weight_kg ? `${model.weight_kg} кг` : "—"} />
          </div>
          
          {model.dimensions && (
            <p className="text-xs text-muted-foreground mb-2">
              Габариты: {model.dimensions}
            </p>
          )}
          
          {model.modes && model.modes.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {model.modes.map((mode, j) => (
                <span key={j} className="text-xs rounded-full bg-feleti-gold/10 px-2 py-0.5 text-feleti-gold/80">
                  {mode}
                </span>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}

function ModelMetric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-sm font-medium text-white">{value}</div>
    </div>
  );
}

function ProblemsTab({ competitor }: { competitor: Competitor }) {
  const severityStyles = {
    low: "border-l-emerald-500/50",
    medium: "border-l-amber-500/50",
    high: "border-l-red-500/50",
  };

  const severityLabels = {
    low: "Низкая",
    medium: "Средняя",
    high: "Высокая",
  };

  return (
    <div className="space-y-3">
      {competitor.problems.map((problem, i) => (
        <div
          key={i}
          className={`rounded-xl border border-white/5 border-l-4 bg-white/[0.02] p-4 ${severityStyles[problem.severity]}`}
        >
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-white">{problem.title}</h4>
            <span className="text-xs text-muted-foreground">
              {severityLabels[problem.severity]} · {problem.frequency}
            </span>
          </div>
          <p className="text-sm text-muted-foreground">{problem.description}</p>
          <p className="mt-2 text-xs text-muted-foreground/60">
            Источник: {problem.source}
          </p>
        </div>
      ))}
    </div>
  );
}

function CompareTab({ competitor }: { competitor: Competitor }) {
  const features = [
    { label: "Облако", feleti: true, them: competitor.hasCloud },
    { label: "Мобильное приложение", feleti: true, them: competitor.hasMobileApp },
    { label: "Удаленный мониторинг", feleti: true, them: competitor.hasRemoteMonitoring },
    { label: "Видеокамера", feleti: true, them: competitor.hasVideoCamera },
    { label: "Telegram-бот", feleti: true, them: false },
    { label: "ERP интеграция", feleti: true, them: false },
    { label: "Web-интерфейс", feleti: true, them: false },
  ];

  return (
    <div className="overflow-hidden rounded-xl border border-white/5">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/5 bg-white/5">
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Функция</th>
            <th className="px-4 py-3 text-center font-medium text-feleti-gold">FELETI-SMOK</th>
            <th className="px-4 py-3 text-center font-medium text-white">{competitor.name}</th>
          </tr>
        </thead>
        <tbody>
          {features.map((feature, i) => (
            <tr key={i} className="border-b border-white/5 hover:bg-white/[0.02]">
              <td className="px-4 py-3 text-muted-foreground">{feature.label}</td>
              <td className="px-4 py-3 text-center">
                {feature.feleti ? (
                  <Check className="mx-auto h-5 w-5 text-emerald-400" />
                ) : (
                  <X className="mx-auto h-5 w-5 text-red-400" />
                )}
              </td>
              <td className="px-4 py-3 text-center">
                {feature.them ? (
                  <Check className="mx-auto h-5 w-5 text-emerald-400" />
                ) : (
                  <X className="mx-auto h-5 w-5 text-red-400" />
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
