"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import {
  Brain,
  MessageCircle,
  Send,
  StopCircle,
  X,
  BookOpen,
  User,
  Sparkles,
  History,
  Trash2,
  Plus,
} from "lucide-react";
import { askAIStream } from "@/lib/api/ai";
import type { SSEEvent } from "@/lib/api/ai";
import {
  createSession,
  deleteSession,
  getSession,
  listSessions,
  addMessage,
} from "@/lib/api/chat";
import type { ChatSessionSummary, ChatMessageRead } from "@/lib/api/chat";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { id: number; title: string; slug: string }[];
  model?: string;
}

function getPageContext(pathname: string): string {
  if (pathname.startsWith("/chambers/")) return "На странице камеры";
  if (pathname === "/chambers") return "На странице камер";
  if (pathname.startsWith("/recipes")) return "На странице рецептов";
  if (pathname.startsWith("/products")) return "На странице продуктов";
  if (pathname.startsWith("/ingredients")) return "На странице ингредиентов";
  if (pathname.startsWith("/brines")) return "На странице рассолов";
  if (pathname.startsWith("/batches")) return "На странице партий";
  if (pathname.startsWith("/knowledge")) return "На странице базы знаний";
  if (pathname.startsWith("/competitors")) return "На странице конкурентов";
  if (pathname.startsWith("/manufacturers")) return "На странице производителей";
  if (pathname === "/") return "На главной";
  return "";
}

export function ChatOverlay() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState<ChatSessionSummary[]>([]);
  const [showSessions, setShowSessions] = useState(false);
  const sessionIdRef = useRef<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const initializedRef = useRef(false);

  // Загружаем список сессий
  const loadSessions = useCallback(async () => {
    try {
      const data = await listSessions();
      setSessions(data.items);
    } catch {
      // игнорируем
    }
  }, []);

  // Создать новую сессию
  const newSession = useCallback(async () => {
    try {
      const ctx = getPageContext(pathname);
      const session = await createSession("Новый диалог", ctx || undefined);
      sessionIdRef.current = session.id;
      setMessages([]);
      await loadSessions();
    } catch {
      sessionIdRef.current = null;
    }
  }, [pathname, loadSessions]);

  // Загрузить конкретную сессию
  const loadSession = useCallback(async (id: number) => {
    try {
      const session = await getSession(id);
      sessionIdRef.current = session.id;
      setMessages(
        session.messages.map((m: ChatMessageRead) => ({
          role: m.role,
          content: m.content,
          sources: m.sources || undefined,
          model: m.model || undefined,
        })),
      );
      setShowSessions(false);
    } catch {
      // игнорируем
    }
  }, []);

  // Удалить сессию
  const handleDeleteSession = useCallback(
    async (id: number, e: React.MouseEvent) => {
      e.stopPropagation();
      try {
        await deleteSession(id);
        if (sessionIdRef.current === id) {
          sessionIdRef.current = null;
          setMessages([]);
        }
        await loadSessions();
      } catch {
        // игнорируем
      }
    },
    [loadSessions],
  );

  // При открытии создаём сессию или загружаем последнюю
  useEffect(() => {
    if (isOpen && !initializedRef.current) {
      initializedRef.current = true;
      (async () => {
        try {
          const data = await listSessions(1, 1);
          if (data.items.length > 0) {
            await loadSession(data.items[0].id);
          } else {
            await newSession();
          }
        } catch {
          await newSession();
        }
      })();
    }
    if (!isOpen) {
      initializedRef.current = false;
    }
  }, [isOpen, loadSession, newSession]);

  useEffect(() => {
    if (isOpen) setTimeout(() => inputRef.current?.focus(), 100);
  }, [isOpen]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Сохранить сообщение в БД (fire-and-forget на фронтенде)
  const persistMessage = useCallback(
    async (
      role: "user" | "assistant",
      content: string,
      sources?: { id: number; title: string; slug: string }[],
      model?: string,
    ) => {
      const sid = sessionIdRef.current;
      if (!sid) return;
      try {
        await addMessage(sid, role, content, sources || null, model || null);
        await loadSessions();
      } catch {
        // офлайн-режим: сообщение уже в локальном стейте
      }
    },
    [loadSessions],
  );

  const handleSubmit = useCallback(
    async (e?: React.FormEvent) => {
      e?.preventDefault();
      const q = question.trim();
      if (!q || loading) return;

      const ctx = getPageContext(pathname);
      const fullQuestion = ctx ? `[${ctx}] ${q}` : q;

      // Если нет сессии — создаём с заголовком из первого вопроса
      if (!sessionIdRef.current) {
        try {
          const title = q.length > 100 ? q.slice(0, 97) + "..." : q;
          const session = await createSession(title, ctx || undefined);
          sessionIdRef.current = session.id;
          await loadSessions();
        } catch {
          return;
        }
      }

      setQuestion("");
      const userMsg: Message = { role: "user", content: q };
      const assistantMsg: Message = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, userMsg, assistantMsg]);
      setLoading(true);

      // сохраняем вопрос пользователя
      await persistMessage("user", q);
      // заголовок сессии обновится первым вопросом при создании

      const controller = new AbortController();
      abortRef.current = controller;

      let responseContent = "";
      let responseSources: { id: number; title: string; slug: string }[] | undefined;
      let responseModel: string | undefined;

      try {
        await askAIStream(
          fullQuestion,
          (event: SSEEvent) => {
            if (event.type === "token") {
              responseContent += event.content;
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                if (last?.role === "assistant") last.content = responseContent;
                return copy;
              });
            } else if (event.type === "sources") {
              responseSources = event.articles;
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                if (last?.role === "assistant") last.sources = event.articles;
                return copy;
              });
            } else if (event.type === "done") {
              responseModel = event.model;
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                if (last?.role === "assistant") last.model = event.model;
                return copy;
              });
            } else if (event.type === "error") {
              if (!responseContent) responseContent = "Ошибка при получении ответа.";
              setMessages((prev) => {
                const copy = [...prev];
                const last = copy[copy.length - 1];
                if (last?.role === "assistant" && !last.content) {
                  last.content = "Ошибка при получении ответа.";
                }
                return copy;
              });
            }
          },
          5,
          controller.signal,
        );
      } catch {
        if (!responseContent) responseContent = "Не удалось получить ответ.";
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy[copy.length - 1];
          if (last?.role === "assistant" && !last.content) {
            last.content = responseContent;
          }
          return copy;
        });
      } finally {
        setLoading(false);
        abortRef.current = null;
        // сохраняем ответ ассистента
        if (responseContent) {
          await persistMessage(
            "assistant",
            responseContent,
            responseSources,
            responseModel,
          );
        }
      }
    },
    [question, loading, pathname, messages.length, loadSessions, persistMessage],
  );

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-purple-800 text-white shadow-lg shadow-purple-900/30 transition-all hover:scale-105 hover:shadow-purple-900/50"
      >
        <MessageCircle className="h-6 w-6" />
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />

            <motion.div
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.95 }}
              transition={{ type: "spring", duration: 0.4 }}
              className="fixed bottom-24 right-6 z-50 flex h-[520px] w-[380px] flex-col rounded-2xl border border-white/10 bg-[#0f0f0f] shadow-2xl shadow-black/50"
            >
              {/* Header */}
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <div className="flex items-center gap-2.5">
                  <div className="inline-flex rounded-lg bg-purple-500/10 p-1.5">
                    <Brain className="h-4 w-4 text-purple-400" />
                  </div>
                  <div>
                    <span className="text-sm font-semibold text-white">
                      AI-ассистент
                    </span>
                    {pathname !== "/ai" && (
                      <span className="ml-2 inline-flex items-center gap-1 rounded-md bg-white/5 px-1.5 py-0.5 text-[10px] text-muted-foreground">
                        <Sparkles className="h-3 w-3" />
                        {getPageContext(pathname) || "Главная"}
                      </span>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => {
                      setShowSessions(!showSessions);
                      if (!showSessions) loadSessions();
                    }}
                    className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-white/5 hover:text-white"
                    title="История диалогов"
                  >
                    <History className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => setIsOpen(false)}
                    className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-white/5 hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Sessions list */}
              <AnimatePresence>
                {showSessions && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden border-b border-white/5"
                  >
                    <div className="max-h-[180px] space-y-0.5 overflow-y-auto px-2 py-2">
                      <button
                        onClick={() => {
                          newSession();
                          setShowSessions(false);
                        }}
                        className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-xs text-purple-400 transition-colors hover:bg-white/5"
                      >
                        <Plus className="h-3.5 w-3.5" />
                        Новый диалог
                      </button>
                      {sessions.map((s) => (
                        <div
                          key={s.id}
                          onClick={() => loadSession(s.id)}
                          className={`group flex cursor-pointer items-center justify-between rounded-lg px-2.5 py-2 text-xs transition-colors hover:bg-white/5 ${
                            s.id === sessionIdRef.current
                              ? "bg-white/5"
                              : ""
                          }`}
                        >
                          <div className="min-w-0 flex-1">
                            <div className="truncate text-white">
                              {s.title}
                            </div>
                            <div className="text-[10px] text-muted-foreground">
                              {s.message_count} сообщ.
                            </div>
                          </div>
                          <button
                            onClick={(e) => handleDeleteSession(s.id, e)}
                            className="ml-2 shrink-0 rounded p-1 text-muted-foreground opacity-0 transition-opacity hover:text-red-400 group-hover:opacity-100"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* Messages */}
              <div className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
                {messages.length === 0 && (
                  <div className="flex h-full flex-col items-center justify-center text-center">
                    <div className="mb-3 inline-flex rounded-2xl bg-purple-500/10 p-3">
                      <Brain className="h-8 w-8 text-purple-400" />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Спросите о копчении, рецептах, оборудовании или проблемах
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground/50">
                      Например: «как коптить осетра» или «температура для скумбрии»
                    </p>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {["температура для скумбрии", "ошибки при копчении", "рецепт свиной шеи"].map(
                        (s) => (
                          <button
                            key={s}
                            onClick={() => {
                              setQuestion(s);
                              setTimeout(() => handleSubmit(), 50);
                            }}
                            className="rounded-lg border border-white/10 px-2.5 py-1 text-xs text-muted-foreground transition-colors hover:bg-white/5"
                          >
                            {s}
                          </button>
                        ),
                      )}
                    </div>
                  </div>
                )}

                {messages.map((msg, i) => (
                  <div
                    key={i}
                    className={`flex gap-2.5 ${msg.role === "user" ? "justify-end" : ""}`}
                  >
                    {msg.role === "assistant" && (
                      <div className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-purple-500/10">
                        <Brain className="h-3.5 w-3.5 text-purple-400" />
                      </div>
                    )}
                    <div
                      className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 ${
                        msg.role === "user"
                          ? "bg-purple-600/20 text-white"
                          : "border border-white/5 bg-white/[0.02] text-white"
                      }`}
                    >
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">
                        {msg.content}
                        {loading &&
                          i === messages.length - 1 &&
                          msg.role === "assistant" && (
                            <span className="ml-0.5 inline-flex h-4 w-2 animate-pulse bg-purple-400" />
                          )}
                      </p>
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="mt-2 flex items-center gap-1.5 border-t border-white/5 pt-2 text-xs text-muted-foreground">
                          <BookOpen className="h-3 w-3 shrink-0" />
                          <span className="truncate">
                            {msg.sources[0].title.slice(0, 40)}
                            {msg.sources.length > 1 &&
                              ` +${msg.sources.length - 1}`}
                          </span>
                        </div>
                      )}
                    </div>
                    {msg.role === "user" && (
                      <div className="mt-1 inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-feleti-gold/10">
                        <User className="h-3.5 w-3.5 text-feleti-gold" />
                      </div>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </div>

              {/* Input */}
              <form
                onSubmit={handleSubmit}
                className="flex items-center gap-2 border-t border-white/5 px-4 py-3"
              >
                <input
                  ref={inputRef}
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="Спросите о копчении..."
                  disabled={loading}
                  className="flex-1 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2.5 text-sm text-white outline-none transition-colors placeholder:text-muted-foreground/50 focus:border-purple-500/50 disabled:opacity-50"
                />
                {loading ? (
                  <button
                    type="button"
                    onClick={handleStop}
                    className="inline-flex items-center justify-center rounded-xl bg-red-600 p-2.5 text-white transition-colors hover:bg-red-500"
                  >
                    <StopCircle className="h-4 w-4" />
                  </button>
                ) : (
                  <button
                    type="submit"
                    disabled={!question.trim()}
                    className="inline-flex items-center justify-center rounded-xl bg-purple-600 p-2.5 text-white transition-colors hover:bg-purple-500 disabled:opacity-50"
                  >
                    <Send className="h-4 w-4" />
                  </button>
                )}
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
