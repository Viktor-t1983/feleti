"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  LayoutDashboard,
  FileEdit,
  Maximize2,
  Minimize2,
  Pencil,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useChamberTelemetry } from "@/hooks/useChamberTelemetry";
import { HmiDashboard } from "@/components/chamber/HmiDashboard";
import { HmiProgramEditor } from "@/components/chamber/HmiProgramEditor";

const TABS = [
  { id: "dashboard", label: "Дашборд", icon: LayoutDashboard },
  { id: "program", label: "Программа", icon: FileEdit },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function ChamberHmiPage() {
  const params = useParams();
  const chamberId = params.id as string;
  const [activeTab, setActiveTab] = useState<TabId>("dashboard");
  const [isFullscreen, setIsFullscreen] = useState(false);
  const { connected, reconnecting, reconnectAttempt, hmi, history } = useChamberTelemetry(chamberId);

  const toggleFullscreen = useCallback(() => {
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().then(() => setIsFullscreen(true)).catch(() => {});
    } else {
      document.exitFullscreen().then(() => setIsFullscreen(false)).catch(() => {});
    }
  }, []);

  useEffect(() => {
    const handler = () => setIsFullscreen(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", handler);
    return () => document.removeEventListener("fullscreenchange", handler);
  }, []);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement || e.target instanceof HTMLSelectElement) return;
      if (activeTab !== "dashboard") return;
      if (e.code === "Space") {
        e.preventDefault();
        const btn = document.querySelector('[data-hmi-action="start"], [data-hmi-action="resume"]') as HTMLButtonElement;
        btn?.click();
      }
      if (e.code === "Escape" && !document.fullscreenElement) {
        const btn = document.querySelector('[data-hmi-action="stop"]') as HTMLButtonElement;
        btn?.click();
      }
      if (e.code === "KeyF" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        toggleFullscreen();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [activeTab, toggleFullscreen]);

  return (
    <div className={`space-y-6 ${isFullscreen ? "p-4" : ""}`}>
      {!isFullscreen && (
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <Link
              href="/chambers"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-white transition-colors mb-2 group"
            >
              <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
              Назад к камерам
            </Link>
            <h1 className="text-2xl font-bold text-white">
              Камера <span className="text-feleti-gold">#{chamberId}</span>
            </h1>
          </div>

          <div className="flex items-center gap-2">
            <Link
              href={`/chambers/${chamberId}/edit`}
              className="inline-flex items-center gap-2 rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2.5 text-sm text-muted-foreground hover:text-white hover:bg-white/10 transition-colors"
            >
              <Pencil className="h-4 w-4" />
            </Link>
            <div className="flex gap-1 rounded-xl border border-white/5 bg-white/[0.02] p-1">
              {TABS.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`relative flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                      isActive ? "text-white" : "text-muted-foreground hover:text-white/70"
                    }`}
                  >
                    {isActive && (
                      <motion.div
                        layoutId="chamber-tab"
                        className="absolute inset-0 rounded-lg bg-white/10"
                        transition={{ type: "spring", bounce: 0.2, duration: 0.4 }}
                      />
                    )}
                    <tab.icon className="h-4 w-4 relative z-10" />
                    <span className="relative z-10">{tab.label}</span>
                  </button>
                );
              })}
            </div>
            <button
              onClick={toggleFullscreen}
              className="rounded-lg border border-white/5 bg-white/[0.02] p-2.5 text-muted-foreground hover:text-white hover:bg-white/10 transition-colors"
              title={isFullscreen ? "Выйти из полноэкранного" : "Полноэкранный режим (Ctrl+F)"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>
          </div>
        </div>
      )}

      {isFullscreen && (
        <div className="fixed top-3 right-3 z-50 flex gap-2">
          <button
            onClick={() => setActiveTab(activeTab === "dashboard" ? "program" : "dashboard")}
            className="rounded-lg border border-white/10 bg-black/60 backdrop-blur-xl p-2.5 text-muted-foreground hover:text-white transition-colors"
            title="Переключить режим"
          >
            {activeTab === "dashboard" ? <FileEdit className="h-4 w-4" /> : <LayoutDashboard className="h-4 w-4" />}
          </button>
          <button
            onClick={toggleFullscreen}
            className="rounded-lg border border-white/10 bg-black/60 backdrop-blur-xl p-2.5 text-muted-foreground hover:text-white transition-colors"
            title="Выйти из полноэкранного"
          >
            <Minimize2 className="h-4 w-4" />
          </button>
        </div>
      )}

      <AnimatePresence mode="wait">
        {activeTab === "dashboard" && (
          <motion.div
            key="dashboard"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <HmiDashboard
              chamberId={chamberId}
              connected={connected}
              reconnecting={reconnecting}
              reconnectAttempt={reconnectAttempt}
              hmi={hmi}
              history={history}
            />
          </motion.div>
        )}
        {activeTab === "program" && (
          <motion.div
            key="program"
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.2 }}
          >
            <HmiProgramEditor />
          </motion.div>
        )}
      </AnimatePresence>

      {!isFullscreen && (
        <div className="text-center text-[10px] text-muted-foreground/30 pb-2">
          <kbd className="rounded border border-white/5 px-1.5 py-0.5 text-[9px]">Space</kbd> Пуск/Пауза ·{" "}
          <kbd className="rounded border border-white/5 px-1.5 py-0.5 text-[9px]">Esc</kbd> Стоп ·{" "}
          <kbd className="rounded border border-white/5 px-1.5 py-0.5 text-[9px]">Ctrl+F</kbd> Полный экран
        </div>
      )}
    </div>
  );
}
