export type ChamberStatus = "idle" | "running" | "paused" | "completed" | "error";

export interface TelemetryPoint {
  time: string;
  t_chamber: number;
  t_product: number;
  humidity: number;
}

export interface HmiData {
  t_chamber: number;
  t_product: number;
  humidity: number;
  smoke_density: number;
  fan_rpm: number;
  door_open: boolean;
  current_phase: string;
  phase_progress: number;
  errors: string[];
  status: ChamberStatus;
  batch_number: string | null;
  t_setpoint: number;
  humidity_setpoint: number;
  electro_voltage: number;
  electro_current: number;
}

export interface ProgramPhase {
  id: string;
  name: string;
  temperature: number;
  time_minutes: number;
  humidity: number;
  smoke_density: number;
  condition: "time" | "core_temp" | "combined";
  condition_value: number;
}

export interface RecipeProgram {
  id: string;
  name: string;
  chamber_id: number;
  phases: ProgramPhase[];
  created_at: string;
  updated_at: string;
}

export interface BatchSummary {
  id: number;
  batch_number: string;
  status: string;
  product_name: string;
  weight_kg: number;
  started_at: string;
  finished_at: string | null;
  phases: ProgramPhase[];
}

export const PHASE_LABELS: Record<string, string> = {
  preheat: "Прогрев",
  drying: "Сушка",
  frying: "Жарка",
  smoking: "Копчение",
  cooking: "Варка",
  baking: "Запекание",
  shower: "Душирование",
  cooling: "Охлаждение",
  ventilation: "Проветривание",
  idle: "Ожидание",
};

export const PHASE_COLORS: Record<string, string> = {
  preheat: "#f97316",
  drying: "#eab308",
  frying: "#ef4444",
  smoking: "#a855f7",
  cooking: "#3b82f6",
  baking: "#dc2626",
  shower: "#06b6d4",
  cooling: "#0ea5e9",
  ventilation: "#22c55e",
  idle: "#6b7280",
};

export const STATUS_CONFIG: Record<ChamberStatus, {
  label: string;
  color: string;
  bg: string;
  border: string;
  pulseColor: string;
}> = {
  idle: {
    label: "Ожидание",
    color: "text-slate-400",
    bg: "bg-slate-500/10",
    border: "border-slate-500/20",
    pulseColor: "#94a3b8",
  },
  running: {
    label: "В работе",
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    pulseColor: "#34d399",
  },
  paused: {
    label: "Пауза",
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    pulseColor: "#fbbf24",
  },
  completed: {
    label: "Завершено",
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    pulseColor: "#60a5fa",
  },
  error: {
    label: "Ошибка",
    color: "text-red-400",
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    pulseColor: "#f87171",
  },
};
