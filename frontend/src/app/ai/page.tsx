"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Brain,
  Loader2,
  Send,
  AlertCircle,
  Settings2,
  BookOpen,
  User,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { askAI } from "@/lib/api/ai";
import type { AIAskResponse } from "@/types/ai";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: AIAskResponse["sources"];
  model?: string;
}

export default function AIPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Привет! Я FELETI-SMOK AI, ассистент технолога коптильного производства. Задай мне вопрос по рецептам, технологиям, оборудованию или проблемам копчения.",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [aiNotConfigured, setAiNotConfigured] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      const q = question.trim();
      if (!q || loading) return;

      setQuestion("");
      setError(null);
      setAiNotConfigured(false);
      setMessages((prev) => [...prev, { role: "user", content: q }]);
      setLoading(true);

      try {
        const response = await askAI(q);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: response.answer,
            sources: response.sources,
            model: response.model,
          },
        ]);
      } catch (err: unknown) {
        const axiosErr = err as { response?: { status?: number } };
        if (axiosErr?.response?.status === 503) {
          setAiNotConfigured(true);
          setMessages((prev) => [
            ...prev,
            {
              role: "assistant",
              content:
                "AI-ассистент не настроен. Перейдите в Настройки, чтобы подключить AI-провайдера (Ollama, OpenAI или совместимый).",
            },
          ]);
        } else {
          setError("Ошибка при получении ответа. Проверьте настройки AI.");
        }
      } finally {
        setLoading(false);
      }
    },
    [question, loading]
  );

  if (isLoadingAuth || !isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between border-b border-white/5 pb-4"
      >
        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-xl bg-purple-500/10 p-2.5">
            <Brain className="h-5 w-5 text-purple-400" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">AI-ассистент</h1>
            <p className="text-sm text-muted-foreground">
              Спросите о технологиях копчения, рецептах, оборудовании
            </p>
          </div>
        </div>
        <button
          onClick={() => router.push("/settings")}
          className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-3 py-2 text-sm text-white transition-colors hover:bg-white/5"
        >
          <Settings2 className="h-4 w-4" />
          Настройки AI
        </button>
      </motion.div>

      {/* Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto py-4">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex gap-3 ${msg.role === "user" ? "justify-end" : ""}`}
          >
            {msg.role === "assistant" && (
              <div className="mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-purple-500/10">
                <Brain className="h-4 w-4 text-purple-400" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-feleti-gold/10 text-white"
                  : "border border-white/5 bg-white/[0.02] text-white"
              }`}
            >
              <p className="whitespace-pre-wrap text-sm leading-relaxed">
                {msg.content}
              </p>

              {/* Sources */}
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-3 border-t border-white/5 pt-2">
                  <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                    <BookOpen className="h-3 w-3" />
                    Источники:
                  </div>
                  <div className="mt-1 flex flex-wrap gap-1.5">
                    {msg.sources.map((s) => (
                      <span
                        key={s.id}
                        className="rounded-lg bg-white/5 px-2 py-0.5 text-xs text-muted-foreground"
                      >
                        {s.title.slice(0, 40)}…
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Model info */}
              {msg.model && (
                <div className="mt-2 text-right text-[10px] text-muted-foreground/50">
                  {msg.model}
                </div>
              )}
            </div>

            {msg.role === "user" && (
              <div className="mt-1 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-feleti-gold/10">
                <User className="h-4 w-4 text-feleti-gold" />
              </div>
            )}
          </motion.div>
        ))}

        {/* Loading */}
        {loading && (
          <div className="flex gap-3">
            <div className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-purple-500/10">
              <Brain className="h-4 w-4 text-purple-400" />
            </div>
            <div className="rounded-2xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                Думаю...
              </div>
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/5 px-4 py-3 text-sm text-red-400">
            <AlertCircle className="h-5 w-5 shrink-0" />
            {error}
          </div>
        )}

        {/* Not configured */}
        {aiNotConfigured && (
          <div className="flex items-center gap-3 rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 text-sm text-amber-400">
            <AlertCircle className="h-5 w-5 shrink-0" />
            <span>
              AI не настроен.{" "}
              <button
                onClick={() => router.push("/settings")}
                className="underline underline-offset-2 hover:text-amber-300"
              >
                Открыть настройки
              </button>
            </span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="flex gap-3 border-t border-white/5 pt-4">
        <div className="relative flex-1">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Спросите о копчении..."
            disabled={loading}
            className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-3 pr-12 text-sm text-white outline-none transition-colors placeholder:text-muted-foreground/50 focus:border-purple-500/50 disabled:opacity-50"
          />
        </div>
        <button
          type="submit"
          disabled={loading || !question.trim()}
          className="inline-flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-3 text-sm font-medium text-white transition-colors hover:bg-purple-500 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Send className="h-4 w-4" />
          )}
        </button>
      </form>
    </div>
  );
}
