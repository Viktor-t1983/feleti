"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Settings,
  Loader2,
  Save,
  Zap,
  CheckCircle2,
  XCircle,
  Brain,
  Cpu,
  Key,
  Sliders,
  FileText,
  Power,
  Globe,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import {
  getAISettings,
  updateAISettings,
  testAI,
} from "@/lib/api/ai";
import type { AISettings as AISettingsType, AITestResult } from "@/types/ai";

export default function SettingsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);
  const user = useAuthStore((s) => s.user);

  const [aiSettings, setAiSettings] = useState<AISettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<AITestResult | null>(null);
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  useEffect(() => {
    if (isAuthenticated) {
      getAISettings()
        .then(setAiSettings)
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [isAuthenticated]);

  const handleSave = useCallback(async () => {
    if (!aiSettings) return;
    setSaving(true);
    setSaveMessage(null);
    try {
      const updated = await updateAISettings({
        provider: aiSettings.provider,
        endpoint: aiSettings.endpoint,
        api_key: aiSettings.api_key,
        model_name: aiSettings.model_name,
        temperature: aiSettings.temperature,
        max_tokens: aiSettings.max_tokens,
        system_prompt: aiSettings.system_prompt,
        enabled: aiSettings.enabled,
      });
      setAiSettings(updated);
      setSaveMessage("Сохранено");
      setTimeout(() => setSaveMessage(null), 2000);
    } catch {
      setSaveMessage("Ошибка сохранения");
    } finally {
      setSaving(false);
    }
  }, [aiSettings]);

  const handleTest = useCallback(async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testAI();
      setTestResult(result);
    } catch {
      setTestResult({ success: false, model: null, latency_ms: null, error: "Ошибка подключения" });
    } finally {
      setTesting(false);
    }
  }, []);

  if (isLoadingAuth || !isAuthenticated || loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-2xl font-bold text-white">Настройки</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Конфигурация системы и AI-ассистента
        </p>
      </motion.div>

      {/* Пользователь */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="rounded-2xl border border-white/5 bg-white/[0.02] p-6"
      >
        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-xl bg-feleti-gold/10 p-3">
            <Settings className="h-5 w-5 text-feleti-gold" />
          </div>
          <div>
            <h3 className="font-semibold text-white">Пользователь</h3>
            <p className="text-sm text-muted-foreground">
              {user?.full_name || user?.username} ({user?.email})
            </p>
          </div>
        </div>
        <div className="mt-4 grid gap-2 text-sm">
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">Роль</span>
            <span className="capitalize text-white">{user?.role}</span>
          </div>
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">Статус</span>
            <span className="text-emerald-400">
              {user?.is_active ? "Активен" : "Неактивен"}
            </span>
          </div>
        </div>
      </motion.div>

      {/* AI-ассистент */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="rounded-2xl border border-white/5 bg-white/[0.02] p-6"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="inline-flex rounded-xl bg-purple-500/10 p-3">
              <Brain className="h-5 w-5 text-purple-400" />
            </div>
            <div>
              <h3 className="font-semibold text-white">AI-ассистент</h3>
              <p className="text-sm text-muted-foreground">
                Настройка AI-провайдера для умных ответов
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {saveMessage && (
              <span className="text-sm text-emerald-400">{saveMessage}</span>
            )}
            <button
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-2 rounded-xl bg-feleti-gold/10 px-4 py-2 text-sm font-medium text-feleti-gold transition-colors hover:bg-feleti-gold/20 disabled:opacity-50"
            >
              {saving ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Save className="h-4 w-4" />
              )}
              Сохранить
            </button>
          </div>
        </div>

        {aiSettings && (
          <div className="mt-6 grid gap-6 md:grid-cols-2">
            {/* Провайдер */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Cpu className="h-4 w-4" />
                Провайдер
              </label>
              <select
                value={aiSettings.provider}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, provider: e.target.value })
                }
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
              >
                <option value="ollama">Ollama (локальный)</option>
                <option value="openai">OpenAI</option>
                <option value="custom">Custom (OpenAI-совместимый)</option>
              </select>
            </div>

            {/* Model */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Brain className="h-4 w-4" />
                Модель
              </label>
              <input
                value={aiSettings.model_name}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, model_name: e.target.value })
                }
                placeholder="qwen2.5:7b / gpt-4o / deepseek-chat"
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
              />
            </div>

            {/* Endpoint */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Globe className="h-4 w-4" />
                Endpoint
              </label>
              <input
                value={aiSettings.endpoint}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, endpoint: e.target.value })
                }
                placeholder="http://host.docker.internal:11434/v1"
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
              />
            </div>

            {/* API Key */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Key className="h-4 w-4" />
                API Key
              </label>
              <input
                type="password"
                value={aiSettings.api_key || ""}
                onChange={(e) =>
                  setAiSettings({ ...aiSettings, api_key: e.target.value || null })
                }
                placeholder="sk-..."
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
              />
            </div>

            {/* Temperature */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <Sliders className="h-4 w-4" />
                Temperature ({aiSettings.temperature})
              </label>
              <input
                type="range"
                min="0"
                max="2"
                step="0.1"
                value={aiSettings.temperature}
                onChange={(e) =>
                  setAiSettings({
                    ...aiSettings,
                    temperature: parseFloat(e.target.value),
                  })
                }
                className="mt-2 w-full accent-purple-500"
              />
            </div>

            {/* Max tokens */}
            <div>
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <FileText className="h-4 w-4" />
                Max tokens
              </label>
              <input
                type="number"
                value={aiSettings.max_tokens}
                onChange={(e) =>
                  setAiSettings({
                    ...aiSettings,
                    max_tokens: parseInt(e.target.value) || 2048,
                  })
                }
                className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
              />
            </div>

            {/* Enabled */}
            <div className="flex items-center gap-3 md:col-span-2">
              <button
                onClick={() =>
                  setAiSettings({ ...aiSettings, enabled: !aiSettings.enabled })
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  aiSettings.enabled ? "bg-purple-600" : "bg-white/10"
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    aiSettings.enabled ? "translate-x-6" : "translate-x-1"
                  }`}
                />
              </button>
              <span className="flex items-center gap-2 text-sm text-muted-foreground">
                <Power className="h-4 w-4" />
                AI-ассистент {aiSettings.enabled ? "включён" : "отключён"}
              </span>

              <button
                onClick={handleTest}
                disabled={testing || !aiSettings.enabled}
                className="ml-auto inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2 text-sm text-white transition-colors hover:bg-white/5 disabled:opacity-50"
              >
                {testing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4" />
                )}
                Тест
              </button>
            </div>
          </div>
        )}

        {/* System prompt */}
        <div className="mt-4">
          <label className="flex items-center gap-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            Системный промпт
          </label>
          <textarea
            value={aiSettings?.system_prompt || ""}
            onChange={(e) =>
              aiSettings &&
              setAiSettings({ ...aiSettings, system_prompt: e.target.value })
            }
            rows={4}
            className="mt-1 w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm text-white outline-none focus:border-purple-500/50"
          />
        </div>

        {/* Test result */}
        {testResult && (
          <div
            className={`mt-4 flex items-center gap-3 rounded-xl border p-4 text-sm ${
              testResult.success
                ? "border-emerald-500/20 bg-emerald-500/5 text-emerald-400"
                : "border-red-500/20 bg-red-500/5 text-red-400"
            }`}
          >
            {testResult.success ? (
              <CheckCircle2 className="h-5 w-5 shrink-0" />
            ) : (
              <XCircle className="h-5 w-5 shrink-0" />
            )}
            <div>
              {testResult.success
                ? `Подключение успешно: ${testResult.model} (${testResult.latency_ms}ms)`
                : `Ошибка: ${testResult.error}`}
            </div>
          </div>
        )}
      </motion.div>

      {/* О системе */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="rounded-2xl border border-white/5 bg-white/[0.02] p-6"
      >
        <h3 className="font-semibold text-white">О системе</h3>
        <div className="mt-4 grid gap-2 text-sm">
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">Версия</span>
            <span className="text-white">0.1.0</span>
          </div>
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">Backend</span>
            <span className="text-white">FastAPI + PostgreSQL</span>
          </div>
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">Frontend</span>
            <span className="text-white">Next.js 14</span>
          </div>
          <div className="flex justify-between border-b border-white/5 py-2">
            <span className="text-muted-foreground">База знаний</span>
            <span className="text-white">109 статей</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-muted-foreground">AI</span>
            <span className="text-white">
              {aiSettings?.enabled
                ? `${aiSettings.provider} / ${aiSettings.model_name}`
                : "Не настроен"}
            </span>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
