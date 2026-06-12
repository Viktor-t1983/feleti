"use client";

import { useState, useEffect, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { Wifi, WifiOff, Droplets, Thermometer, Gauge, AlertTriangle } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
import type { HmiData, TelemetryPoint, ChamberStatus } from "@/lib/types/chamber";
import { STATUS_CONFIG } from "@/lib/types/chamber";
import { TemperatureGauge } from "./TemperatureGauge";
import { PhaseProgress } from "./PhaseProgress";
import { MiniChart } from "./MiniChart";
import { StatusIndicators } from "./StatusIndicators";
import { ControlButtons } from "./ControlButtons";
import { ChamberCamera } from "./ChamberCamera";

interface HmiDashboardProps {
  chamberId: string;
  connected: boolean;
  reconnecting?: boolean;
  reconnectAttempt?: number;
  hmi: HmiData;
  history: TelemetryPoint[];
  chamberName?: string;
}

const MOCK_HMI: HmiData = {
  t_chamber: 72.5,
  t_product: 68.3,
  humidity: 45,
  smoke_density: 35,
  fan_rpm: 1200,
  door_open: false,
  current_phase: "Копчение",
  phase_progress: 65,
  errors: [],
  status: "running",
  batch_number: "B-2026-002",
  t_setpoint: 75,
  humidity_setpoint: 50,
  electro_voltage: 0,
  electro_current: 0,
};

const MOCK_PHASES = [
  { name: "Подсушка", duration_min: 20 },
  { name: "Копчение", duration_min: 90 },
  { name: "Запекание", duration_min: 90 },
  { name: "Охлаждение", duration_min: 15 },
];

function generateMockHistory(): TelemetryPoint[] {
  const data: TelemetryPoint[] = [];
  let tc = 20, tp = 8, h = 40;
  for (let i = 0; i < 60; i++) {
    tc += Math.sin(i / 10) * 2 + (Math.random() - 0.5);
    tp += Math.sin(i / 10) * 1.5 + (Math.random() - 0.5);
    h = Math.max(0, Math.min(100, h + Math.sin(i / 8) * 3 + (Math.random() - 0.5)));
    data.push({
      time: `${i} мин`,
      t_chamber: Math.round(tc * 10) / 10,
      t_product: Math.round(tp * 10) / 10,
      humidity: Math.round(h * 10) / 10,
    });
  }
  return data;
}

export function HmiDashboard({
  chamberId,
  connected,
  reconnecting,
  reconnectAttempt,
  hmi,
  history,
}: HmiDashboardProps) {
  const [elapsed, setElapsed] = useState(1847);
  const [actionLoading, setActionLoading] = useState(false);
  const queryClient = useQueryClient();

  const { data: activeBatch } = useQuery({
    queryKey: ["chambers", chamberId, "active-batch"],
    queryFn: async () => {
      const { data } = await apiClient.get(`/chambers/${chamberId}/active-batch`);
      return data?.active_batch || null;
    },
    refetchInterval: 30000,
  });

  const batchStatus = activeBatch?.status || null;

  useEffect(() => {
    const interval = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(interval);
  }, []);

  const performAction = useCallback(async (action: string) => {
    if (!activeBatch?.id) return;
    setActionLoading(true);
    try {
      if (action === "start") {
        await apiClient.post(`/batches/${activeBatch.id}/start`);
      } else if (action === "pause") {
        await apiClient.post(`/batches/${activeBatch.id}/pause`);
      } else if (action === "resume") {
        await apiClient.post(`/batches/${activeBatch.id}/resume`);
      } else if (action === "stop") {
        await apiClient.post(`/batches/${activeBatch.id}/cancel`);
      }
      await queryClient.invalidateQueries({ queryKey: ["chambers", chamberId, "active-batch"] });
      await queryClient.invalidateQueries({ queryKey: ["batches"] });
    } catch (err) {
      console.error(`Action ${action} failed:`, err);
    } finally {
      setActionLoading(false);
    }
  }, [activeBatch, chamberId, queryClient]);

  const displayHmi = connected ? hmi : MOCK_HMI;
  const displayHistory = useMemo(
    () => history.length > 0 ? history : generateMockHistory(),
    [history]
  );
  const displayPhases = activeBatch?.program || MOCK_PHASES;
  const status = STATUS_CONFIG[displayHmi.status as ChamberStatus] || STATUS_CONFIG.idle;

  const effectiveStatus = batchStatus === "running" ? "running"
    : batchStatus === "paused" ? "paused"
    : displayHmi.status === "running" ? "running"
    : displayHmi.status === "paused" ? "paused"
    : (activeBatch && ["PLANNED", "planned"].includes(batchStatus || "")) ? "idle"
    : "idle";

  const currentPhaseIndex = displayPhases.findIndex(
    (p: { name: string; key?: string }) => p.name === displayHmi.current_phase || p.key === displayHmi.current_phase
  );

  const alarms = [];
  if (displayHmi.t_chamber > 85) alarms.push("Температура камеры выше 85°C");
  if (displayHmi.t_chamber > displayHmi.t_setpoint * 1.1 && displayHmi.t_setpoint > 0)
    alarms.push("Превышение температуры камеры");
  if (displayHmi.humidity > 95) alarms.push("Влажность выше 95%");
  if (displayHmi.door_open) alarms.push("Дверь камеры открыта");

  const allErrors = [...alarms, ...displayHmi.errors];
  const hasAlarms = allErrors.length > 0;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="space-y-5"
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm ${hasAlarms ? "text-red-400 bg-red-500/10 border-red-500/20" : `${status.color} ${status.bg} ${status.border}`}`}
          >
            {hasAlarms ? (
              <AlertTriangle className="h-3.5 w-3.5 animate-pulse" />
            ) : (
              <span className="h-2 w-2 rounded-full" style={{ backgroundColor: status.pulseColor }} />
            )}
            {hasAlarms ? "Тревога" : status.label}
          </span>
          {displayHmi.batch_number && (
            <span className="rounded-md bg-feleti-gold/10 px-2.5 py-1 text-xs font-medium text-feleti-gold border border-feleti-gold/20">
              {displayHmi.batch_number}
            </span>
          )}
        </div>
        <span className="inline-flex items-center gap-1.5 text-xs">
          {connected ? (
            <>
              <Wifi className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-emerald-400 font-medium">В эфире</span>
            </>
          ) : reconnecting ? (
            <>
              <WifiOff className="h-3.5 w-3.5 text-amber-400 animate-pulse" />
              <span className="text-amber-400">Переподключение ({reconnectAttempt})</span>
            </>
          ) : (
            <>
              <WifiOff className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-slate-400">Демо-режим</span>
            </>
          )}
          <span className="text-muted-foreground/40 mx-1">|</span>
          <Gauge className="h-3.5 w-3.5 text-muted-foreground/60" />
          <span className="text-muted-foreground/60">
            {elapsed > 0 ? `${Math.floor(elapsed / 3600)}ч ${Math.floor((elapsed % 3600) / 60)}м` : "0ч 0м"}
          </span>
        </span>
      </div>

      {/* Alarm banner */}
      {hasAlarms && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          className="rounded-xl border border-red-500/20 bg-red-500/10 p-4 overflow-hidden"
        >
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <h3 className="text-sm font-medium text-red-400">Тревоги</h3>
          </div>
          {allErrors.map((error, i) => (
            <p key={i} className="text-sm text-red-400/80 flex items-center gap-2 ml-6">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400 shrink-0" />
              {error}
            </p>
          ))}
        </motion.div>
      )}

      {/* Gauges grid - 2x2 on tablet, 4 cols on desktop */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <TemperatureGauge
          label="Камера"
          value={displayHmi.t_chamber}
          setpoint={displayHmi.t_setpoint}
          color="text-orange-400"
          bg="bg-orange-500/10"
          size="lg"
          alarmHigh={85}
          alarmLow={0}
        />
        <TemperatureGauge
          label="Продукт"
          value={displayHmi.t_product}
          setpoint={displayHmi.t_setpoint - 5}
          color="text-red-400"
          bg="bg-red-500/10"
          icon={Thermometer}
          size="lg"
          alarmHigh={displayHmi.t_setpoint}
        />
        <TemperatureGauge
          label="Влажность"
          value={displayHmi.humidity}
          setpoint={displayHmi.humidity_setpoint}
          unit="%"
          color="text-blue-400"
          bg="bg-blue-500/10"
          icon={Droplets}
          size="lg"
          alarmHigh={95}
        />
        <TemperatureGauge
          label="Вентилятор"
          value={displayHmi.fan_rpm}
          setpoint={1800}
          unit=" об/мин"
          color="text-cyan-400"
          bg="bg-cyan-500/10"
          icon={Gauge}
          size="lg"
        />
      </div>

      {/* Main content area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* Left: Phase + Chart (2/3) */}
        <div className="lg:col-span-2 space-y-5">
          <PhaseProgress
            phaseKey={displayHmi.current_phase}
            progress={displayHmi.phase_progress}
            elapsedSeconds={elapsed}
            smokeDensity={displayHmi.smoke_density}
            doorOpen={displayHmi.door_open}
            phases={displayPhases}
            currentPhaseIndex={currentPhaseIndex >= 0 ? currentPhaseIndex : 0}
            phaseElapsed={elapsed}
          />
          <MiniChart data={displayHistory} showHumidity />
        </div>

        {/* Right: Camera + Status (1/3) */}
        <div className="space-y-5">
          <ChamberCamera enabled={false} />
          <StatusIndicators
            heatingOn={displayHmi.status === "running" || displayHmi.status === "paused"}
            fanRpm={displayHmi.fan_rpm}
            smokeActive={displayHmi.smoke_density > 5}
            steamActive={displayHmi.humidity > 60}
            doorOpen={displayHmi.door_open}
            damperPosition={displayHmi.smoke_density}
          />
        </div>
      </div>

      <ControlButtons
        status={effectiveStatus}
        onStart={() => performAction("start")}
        onPause={() => performAction("pause")}
        onResume={() => performAction("resume")}
        onStop={() => performAction("stop")}
        loading={actionLoading}
      />

      {displayHmi.errors.length > 0 && !hasAlarms && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-red-500/20 bg-red-500/10 p-4"
        >
          <h3 className="text-sm font-medium text-red-400 mb-2">Ошибки</h3>
          {displayHmi.errors.map((error, i) => (
            <p key={i} className="text-sm text-red-400/80 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-red-400 shrink-0" />
              {error}
            </p>
          ))}
        </motion.div>
      )}
    </motion.div>
  );
}
