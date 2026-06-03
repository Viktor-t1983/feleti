"use client";

import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import {
  ArrowLeft,
  Play,
  Pause,
  Square,
  Thermometer,
  Droplets,
  Wind,
  Zap,
  DoorOpen,
  AlertTriangle,
  Timer,
  Wifi,
  WifiOff,
} from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Area,
  AreaChart,
} from "recharts";

interface TelemetryPoint {
  time: string;
  t_chamber: number;
  t_product: number;
  humidity: number;
}

interface HmiData {
  t_chamber: number;
  t_product: number;
  humidity: number;
  smoke_density: number;
  fan_rpm: number;
  door_open: boolean;
  current_phase: string;
  phase_progress: number;
  errors: string[];
  status: "idle" | "running" | "paused" | "completed" | "error";
  batch_number: string | null;
}

const PHASE_LABELS: Record<string, string> = {
  drying: "Сушка",
  smoking: "Копчение",
  cooking: "Варка",
  shower: "Душирование",
  cooling: "Охлаждение",
  idle: "Ожидание",
};

function useTelemetry(chamberId: string, token: string | null) {
  const [connected, setConnected] = useState(false);
  const [hmi, setHmi] = useState<HmiData>({
    t_chamber: 20,
    t_product: 8,
    humidity: 40,
    smoke_density: 0,
    fan_rpm: 0,
    door_open: false,
    current_phase: "idle",
    phase_progress: 0,
    errors: [],
    status: "idle",
    batch_number: null,
  });
  const [history, setHistory] = useState<TelemetryPoint[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!token) return;

    const wsUrl = `ws://localhost:8000/api/v1/chambers/${chamberId}/telemetry/ws?token=${token}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "telemetry" && msg.data) {
          const d = msg.data;
          setHmi({
            t_chamber: d.t_chamber ?? 20,
            t_product: d.t_product ?? 8,
            humidity: d.humidity ?? 40,
            smoke_density: d.smoke_density ?? 0,
            fan_rpm: d.fan_rpm ?? 0,
            door_open: d.door_open ?? false,
            current_phase: d.current_phase || "idle",
            phase_progress: d.phase_progress ?? 0,
            errors: d.errors || [],
            status: d.status || "idle",
            batch_number: d.batch_number || null,
          });
          setHistory((prev) => {
            const now = new Date();
            const time = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}`;
            const next = [
              ...prev,
              {
                time,
                t_chamber: d.t_chamber ?? 20,
                t_product: d.t_product ?? 8,
                humidity: d.humidity ?? 40,
              },
            ];
            return next.slice(-60);
          });
        }
      } catch {
        // ignore invalid messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
    };

    ws.onerror = () => {
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [chamberId, token]);

  return { connected, hmi, history };
}

export default function ChamberHmiPage() {
  const params = useParams();
  const chamberId = params.id as string;
  const [token, setToken] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(1847);

  useEffect(() => {
    const t = localStorage.getItem("feleti_auth_token");
    setToken(t);
  }, []);

  const { connected, hmi, history } = useTelemetry(chamberId, token);

  // Fallback mock data if not connected
  const displayHmi = connected
    ? hmi
    : {
        t_chamber: 72.5,
        t_product: 68.3,
        humidity: 45,
        smoke_density: 35,
        fan_rpm: 1200,
        door_open: false,
        current_phase: "smoking",
        phase_progress: 65,
        errors: [],
        status: "running" as const,
        batch_number: "B-2026-002",
      };

  const displayHistory =
    history.length > 0
      ? history
      : generateMockHistory();

  useEffect(() => {
    const interval = setInterval(() => {
      setElapsed((e) => e + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const statusConfig = {
    idle: { label: "Ожидание", color: "text-slate-400", bg: "bg-slate-500/10", border: "border-slate-500/20" },
    running: { label: "В работе", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
    paused: { label: "Пауза", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
    completed: { label: "Завершено", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
    error: { label: "Ошибка", color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
  };

  const status = statusConfig[displayHmi.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            href="/chambers"
            className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Назад к камерам
          </Link>
          <h1 className="text-2xl font-bold text-white">Камера #{chamberId}</h1>
        </div>
        <div className="flex items-center gap-3">
          <span className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm ${status.color} ${status.bg} ${status.border}`}>
            <span className="h-2 w-2 rounded-full animate-pulse" style={{ backgroundColor: "currentColor" }} />
            {status.label}
          </span>
          {displayHmi.batch_number && (
            <span className="text-sm text-muted-foreground">{displayHmi.batch_number}</span>
          )}
          <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
            {connected ? (
              <>
                <Wifi className="h-3 w-3 text-emerald-400" />
                <span className="text-emerald-400">Live</span>
              </>
            ) : (
              <>
                <WifiOff className="h-3 w-3 text-slate-400" />
                <span>Mock</span>
              </>
            )}
          </span>
        </div>
      </div>

      {/* Main gauges */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <GaugeCard
          label="Температура камеры"
          value={`${displayHmi.t_chamber.toFixed(1)}°C`}
          icon={Thermometer}
          color="text-orange-400"
          bg="bg-orange-500/10"
        />
        <GaugeCard
          label="Температура продукта"
          value={`${displayHmi.t_product.toFixed(1)}°C`}
          icon={Thermometer}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <GaugeCard
          label="Влажность"
          value={`${displayHmi.humidity.toFixed(0)}%`}
          icon={Droplets}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <GaugeCard
          label="Вентилятор"
          value={`${displayHmi.fan_rpm} об/мин`}
          icon={Wind}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </div>

      {/* Phase progress */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-medium text-white">
            Текущая фаза: {PHASE_LABELS[displayHmi.current_phase] || displayHmi.current_phase}
          </h3>
          <span className="text-sm text-muted-foreground">
            {Math.round(displayHmi.phase_progress)}%
          </span>
        </div>
        <div className="h-3 rounded-full bg-white/5 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-feleti-gold"
            initial={{ width: 0 }}
            animate={{ width: `${displayHmi.phase_progress}%` }}
            transition={{ duration: 0.5 }}
          />
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Timer className="h-3 w-3" />
            Прошло: {formatTime(elapsed)}
          </span>
          <span className="flex items-center gap-1">
            <Zap className="h-3 w-3" />
            Дым: {displayHmi.smoke_density}%
          </span>
          {displayHmi.door_open && (
            <span className="flex items-center gap-1 text-amber-400">
              <DoorOpen className="h-3 w-3" />
              Дверь открыта
            </span>
          )}
        </div>
      </motion.div>

      {/* Control buttons */}
      <div className="flex flex-wrap gap-3">
        <ControlButton icon={Play} label="Старт" variant="primary" />
        <ControlButton icon={Pause} label="Пауза" variant="secondary" />
        <ControlButton icon={Square} label="Стоп" variant="danger" />
      </div>

      {/* Temperature chart */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-2xl border border-white/5 bg-white/[0.02] p-5"
      >
        <h3 className="text-sm font-medium text-white mb-4">
          Температурный график
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={displayHistory}>
            <defs>
              <linearGradient id="tChamber" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="tProduct" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
            <XAxis
              dataKey="time"
              tick={{ fill: "#888", fontSize: 11 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
            />
            <YAxis
              tick={{ fill: "#888", fontSize: 12 }}
              axisLine={{ stroke: "rgba(255,255,255,0.1)" }}
              label={{ value: "°C", angle: -90, position: "insideLeft", fill: "#888" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "#1a1a1a",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: "8px",
                color: "#fff",
              }}
            />
            <Area
              type="monotone"
              dataKey="t_chamber"
              stroke="#f97316"
              fillOpacity={1}
              fill="url(#tChamber)"
              strokeWidth={2}
              name="Камера"
            />
            <Area
              type="monotone"
              dataKey="t_product"
              stroke="#ef4444"
              fillOpacity={1}
              fill="url(#tProduct)"
              strokeWidth={2}
              name="Продукт"
            />
          </AreaChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Errors */}
      {displayHmi.errors.length > 0 && (
        <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-red-400" />
            <h3 className="text-sm font-medium text-red-400">Ошибки</h3>
          </div>
          {displayHmi.errors.map((error, i) => (
            <p key={i} className="text-sm text-red-400/80">{error}</p>
          ))}
        </div>
      )}
    </div>
  );
}

function generateMockHistory(): TelemetryPoint[] {
  const data: TelemetryPoint[] = [];
  let t_chamber = 20;
  let t_product = 8;
  let humidity = 40;
  for (let i = 0; i < 60; i++) {
    t_chamber += Math.sin(i / 10) * 2 + Math.random() - 0.5;
    t_product += Math.sin(i / 10) * 1.5 + Math.random() - 0.5;
    humidity = Math.max(0, Math.min(100, humidity + Math.sin(i / 8) * 3 + Math.random() - 0.5));
    data.push({
      time: `${i} мин`,
      t_chamber: Math.round(t_chamber * 10) / 10,
      t_product: Math.round(t_product * 10) / 10,
      humidity: Math.round(humidity * 10) / 10,
    });
  }
  return data;
}

function GaugeCard({
  label,
  value,
  icon: Icon,
  color,
  bg,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  color: string;
  bg: string;
}) {
  return (
    <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`flex h-8 w-8 items-center justify-center rounded-lg ${bg}`}>
          <Icon className={`h-4 w-4 ${color}`} />
        </div>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
      <div className="text-2xl font-bold text-white">{value}</div>
    </div>
  );
}

function ControlButton({
  icon: Icon,
  label,
  variant,
}: {
  icon: React.ElementType;
  label: string;
  variant: "primary" | "secondary" | "danger";
}) {
  const styles = {
    primary: "bg-emerald-500/10 text-emerald-400 hover:bg-emerald-500/20 border-emerald-500/20",
    secondary: "bg-amber-500/10 text-amber-400 hover:bg-amber-500/20 border-amber-500/20",
    danger: "bg-red-500/10 text-red-400 hover:bg-red-500/20 border-red-500/20",
  };

  return (
    <button
      className={`inline-flex items-center gap-2 rounded-xl border px-5 py-2.5 text-sm font-medium transition-colors ${styles[variant]}`}
    >
      <Icon className="h-4 w-4" />
      {label}
    </button>
  );
}
