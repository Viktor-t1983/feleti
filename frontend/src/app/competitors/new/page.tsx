"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Globe, CheckCircle, XCircle, ArrowLeft, ExternalLink, BookOpen } from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { apiClient } from "@/lib/api/client";
import { useEffect } from "react";

enum OnboardStep {
  FORM = "form",
  DISCOVERY = "discovery",
  CRAWL = "crawl",
  DONE = "done",
  ERROR = "error",
}

interface OnboardResponse {
  competitor: {
    id: number;
    name: string;
    slug: string;
    base_url: string;
    sitemap_url: string | null;
    crawl_status: string;
    articles_count: number;
  };
  discovery: {
    name: string;
    slug: string;
    base_url: string;
    sitemap_url: string | null;
    encoding: string | null;
    title: string | null;
    description: string | null;
    page_count: number;
    error: string | null;
  };
  articles_created: number;
  articles_skipped: number;
}

export default function NewCompetitorPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);

  const [url, setUrl] = useState("");
  const [customName, setCustomName] = useState("");
  const [step, setStep] = useState<OnboardStep>(OnboardStep.FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<OnboardResponse | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  const handleSubmit = async () => {
    if (!url.trim()) return;
    setLoading(true);
    setStep(OnboardStep.DISCOVERY);
    setError("");

    try {
      const payload: { url: string; name?: string } = { url: url.trim() };
      if (customName.trim()) {
        payload.name = customName.trim();
      }
      const response = await apiClient.post<OnboardResponse>("/competitors/onboard", payload, {
        timeout: 300000,
      });
      setResult(response.data);
      setStep(OnboardStep.DONE);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || "Ошибка при онбординге. Проверьте URL и попробуйте снова.");
      setStep(OnboardStep.ERROR);
    } finally {
      setLoading(false);
    }
  };

  if (isLoadingAuth || !isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  return (
    <main className="min-h-screen">
      <section className="px-6 py-12">
        <div className="mx-auto max-w-2xl">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <button
              onClick={() => router.push("/competitors")}
              className="mb-6 flex items-center gap-2 text-sm text-muted-foreground hover:text-white transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              Назад к списку конкурентов
            </button>

            <div className="flex items-center gap-3 mb-4">
              <Globe className="h-6 w-6 text-feleti-gold" />
              <h1 className="text-3xl font-bold text-white">Добавить конкурента</h1>
            </div>
            <p className="text-muted-foreground max-w-xl">
              Введите URL сайта конкурента — система найдёт карту сайта, 
              извлечёт статьи и добавит в базу знаний.
            </p>
          </motion.div>

          <AnimatePresence mode="wait">
            {(step === OnboardStep.FORM || step === OnboardStep.ERROR) && (
              <motion.div
                key="form"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mt-8 space-y-4"
              >
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    URL сайта конкурента *
                  </label>
                  <input
                    type="url"
                    placeholder="https://example.com"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 px-4 text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none focus:ring-1 focus:ring-feleti-gold/50 disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-muted-foreground mb-2">
                    Название (необязательно)
                  </label>
                  <input
                    type="text"
                    placeholder="Будет извлечено из домена"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    disabled={loading}
                    className="w-full rounded-xl border border-white/10 bg-white/5 py-3 px-4 text-white placeholder:text-muted-foreground focus:border-feleti-gold/50 focus:outline-none focus:ring-1 focus:ring-feleti-gold/50 disabled:opacity-50"
                  />
                </div>

                {step === OnboardStep.ERROR && (
                  <div className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
                    <div className="flex items-start gap-3">
                      <XCircle className="h-5 w-5 text-red-400 mt-0.5 shrink-0" />
                      <p className="text-sm text-red-300">{error}</p>
                    </div>
                  </div>
                )}

                <button
                  onClick={handleSubmit}
                  disabled={loading || !url.trim()}
                  className="w-full rounded-xl bg-feleti-gold py-3 font-medium text-black hover:bg-feleti-gold/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <span className="flex items-center justify-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Обработка...
                    </span>
                  ) : (
                    "Запустить онбординг"
                  )}
                </button>
              </motion.div>
            )}

            {step === OnboardStep.DISCOVERY && loading && (
              <motion.div
                key="discovery"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-12 text-center"
              >
                <Loader2 className="h-12 w-12 animate-spin text-feleti-gold mx-auto mb-4" />
                <h2 className="text-xl font-semibold text-white mb-2">Разведка сайта</h2>
                <p className="text-muted-foreground">Проверяем доступность, ищем sitemap, определяем кодировку...</p>
              </motion.div>
            )}

            {step === OnboardStep.DONE && result && (
              <motion.div
                key="done"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-8 space-y-6"
              >
                <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-6">
                  <div className="flex items-center gap-3 mb-4">
                    <CheckCircle className="h-6 w-6 text-emerald-400" />
                    <h2 className="text-xl font-semibold text-white">Готово!</h2>
                  </div>
                  <p className="text-muted-foreground">
                    Конкурент <span className="text-white font-medium">{result.competitor.name}</span> добавлен.
                  </p>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/[0.02] p-6 space-y-4">
                  <h3 className="font-medium text-white">Результаты</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-lg bg-white/5 p-3">
                      <div className="text-2xl font-bold text-feleti-gold">{result.articles_created}</div>
                      <div className="text-xs text-muted-foreground mt-1">Статей создано</div>
                    </div>
                    <div className="rounded-lg bg-white/5 p-3">
                      <div className="text-2xl font-bold text-muted-foreground">{result.articles_skipped}</div>
                      <div className="text-xs text-muted-foreground mt-1">Пропущено</div>
                    </div>
                  </div>

                  {result.discovery.sitemap_url && (
                    <div className="flex items-center gap-2 text-sm">
                      <ExternalLink className="h-4 w-4 text-muted-foreground" />
                      <span className="text-muted-foreground">Sitemap:</span>
                      <a
                        href={result.discovery.sitemap_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-feleti-gold hover:underline truncate"
                      >
                        {result.discovery.sitemap_url}
                      </a>
                    </div>
                  )}
                </div>

                <div className="flex gap-3">
                  <button
                    onClick={() => router.push(`/competitors`)}
                    className="flex-1 rounded-xl border border-white/10 py-3 text-sm text-white hover:bg-white/5 transition-colors"
                  >
                    К списку конкурентов
                  </button>
                  <button
                    onClick={() => router.push(`/knowledge?competitor_id=${result.competitor.id}`)}
                    className="flex-1 rounded-xl bg-feleti-gold py-3 text-sm font-medium text-black hover:bg-feleti-gold/90 transition-colors flex items-center justify-center gap-2"
                  >
                    <BookOpen className="h-4 w-4" />
                    Смотреть статьи
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>
    </main>
  );
}
