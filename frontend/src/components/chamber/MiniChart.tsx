"use client";

import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { TelemetryPoint } from "@/lib/types/chamber";

interface MiniChartProps {
  data: TelemetryPoint[];
  height?: number;
  showHumidity?: boolean;
}

export function MiniChart({ data, height = 240, showHumidity = false }: MiniChartProps) {
  return (
    <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
      <h3 className="text-sm font-medium text-white mb-4">
        {showHumidity ? "Температура и влажность" : "Температурный график"}
      </h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data} margin={{ top: 5, right: 5, bottom: 5, left: 0 }}>
          <defs>
            <linearGradient id="gradChamber" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f97316" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradProduct" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
            {showHumidity && (
              <linearGradient id="gradHumidity" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            )}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
          <XAxis
            dataKey="time"
            tick={{ fill: "#666", fontSize: 10 }}
            axisLine={{ stroke: "rgba(255,255,255,0.06)" }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            tick={{ fill: "#666", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={35}
            domain={["dataMin - 5", "dataMax + 5"]}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1a1a1a",
              border: "1px solid rgba(255,255,255,0.1)",
              borderRadius: "8px",
              color: "#fff",
              fontSize: "12px",
            }}
            labelStyle={{ color: "#999" }}
          />
          <Area
            type="monotone"
            dataKey="t_chamber"
            stroke="#f97316"
            fillOpacity={1}
            fill="url(#gradChamber)"
            strokeWidth={2}
            name="Камера"
            dot={false}
            activeDot={{ r: 3, fill: "#f97316" }}
          />
          <Area
            type="monotone"
            dataKey="t_product"
            stroke="#ef4444"
            fillOpacity={1}
            fill="url(#gradProduct)"
            strokeWidth={2}
            name="Продукт"
            dot={false}
            activeDot={{ r: 3, fill: "#ef4444" }}
          />
          {showHumidity && (
            <Area
              type="monotone"
              dataKey="humidity"
              stroke="#3b82f6"
              fillOpacity={1}
              fill="url(#gradHumidity)"
              strokeWidth={1.5}
              strokeDasharray="4 2"
              name="Влажность"
              dot={false}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
