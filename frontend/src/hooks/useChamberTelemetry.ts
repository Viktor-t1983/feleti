"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type { HmiData, TelemetryPoint } from "@/lib/types/chamber";

const WS_HEARTBEAT_INTERVAL = 30000;
const WS_RECONNECT_BASE_DELAY = 1000;
const WS_RECONNECT_MAX_DELAY = 30000;
const WS_RECONNECT_MAX_ATTEMPTS = 20;
const HISTORY_MAX = 120;

function createDefaultHmi(): HmiData {
  return {
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
    t_setpoint: 0,
    humidity_setpoint: 0,
    electro_voltage: 0,
    electro_current: 0,
  };
}

function backoffWithJitter(attempt: number): number {
  const base = Math.min(
    WS_RECONNECT_BASE_DELAY * Math.pow(2, attempt),
    WS_RECONNECT_MAX_DELAY
  );
  const jitter = 0.7 + Math.random() * 0.6;
  return Math.round(base * jitter);
}

export function useChamberTelemetry(chamberId: string) {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const [reconnectAttempt, setReconnectAttempt] = useState(0);
  const [hmi, setHmi] = useState<HmiData>(createDefaultHmi);
  const [history, setHistory] = useState<TelemetryPoint[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const attemptRef = useRef(0);
  const mountedRef = useRef(true);
  const hiddenRef = useRef(false);

  const connect = useCallback(() => {
    if (!mountedRef.current || hiddenRef.current) return;

    const token = localStorage.getItem("access_token");
    if (!token) return;

    const baseUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";
    const wsUrl = `${baseUrl}/chambers/${chamberId}/telemetry/ws?token=${token}`;

    if (wsRef.current) {
      wsRef.current.onclose = null;
      wsRef.current.onerror = null;
      wsRef.current.close();
      wsRef.current = null;
    }

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      if (!mountedRef.current) { ws.close(); return; }
      setConnected(true);
      setReconnecting(false);
      setReconnectAttempt(0);
      attemptRef.current = 0;

      heartbeatRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ action: "ping" }));
        }
      }, WS_HEARTBEAT_INTERVAL);
    };

    ws.onmessage = (event) => {
      if (!mountedRef.current) return;
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
            t_setpoint: d.t_setpoint ?? 0,
            humidity_setpoint: d.humidity_setpoint ?? 0,
            electro_voltage: d.electro_voltage ?? 0,
            electro_current: d.electro_current ?? 0,
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
            return next.slice(-HISTORY_MAX);
          });
        }
      } catch {
        // ignore
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
      if (!mountedRef.current || hiddenRef.current) return;
      attemptRef.current++;
      if (attemptRef.current > WS_RECONNECT_MAX_ATTEMPTS) {
        setReconnecting(false);
        return;
      }
      setReconnecting(true);
      setReconnectAttempt(attemptRef.current);
      const delay = backoffWithJitter(attemptRef.current - 1);
      reconnectRef.current = setTimeout(connect, delay);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [chamberId]);

  useEffect(() => {
    mountedRef.current = true;
    connect();

    const handleVisibility = () => {
      hiddenRef.current = document.hidden;
      if (!document.hidden) {
        connect();
      }
    };
    document.addEventListener("visibilitychange", handleVisibility);

    return () => {
      mountedRef.current = false;
      document.removeEventListener("visibilitychange", handleVisibility);
      if (wsRef.current) {
        wsRef.current.onclose = null;
        wsRef.current.onerror = null;
        wsRef.current.close();
        wsRef.current = null;
      }
      if (heartbeatRef.current) {
        clearInterval(heartbeatRef.current);
        heartbeatRef.current = null;
      }
      if (reconnectRef.current) {
        clearTimeout(reconnectRef.current);
        reconnectRef.current = null;
      }
    };
  }, [connect]);

  return { connected, reconnecting, reconnectAttempt, hmi, history };
}
