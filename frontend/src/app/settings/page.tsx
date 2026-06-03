"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Settings, Loader2 } from "lucide-react";
import { useAuthStore } from "@/stores/auth";

export default function SettingsPage() {
  const router = useRouter();
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);
  const user = useAuthStore((s) => s.user);

  useEffect(() => {
    if (!isLoadingAuth && !isAuthenticated) {
      router.push("/login");
    }
  }, [isAuthenticated, isLoadingAuth, router]);

  if (isLoadingAuth || !isAuthenticated) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-feleti-gold" />
      </div>
    );
  }

  return (
    <div>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <h1 className="text-2xl font-bold text-white">Настройки</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Конфигурация системы
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="mt-8 space-y-4"
      >
        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
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
              <span className="text-white capitalize">{user?.role}</span>
            </div>
            <div className="flex justify-between border-b border-white/5 py-2">
              <span className="text-muted-foreground">Статус</span>
              <span className="text-emerald-400">
                {user?.is_active ? "Активен" : "Неактивен"}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
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
          </div>
        </div>
      </motion.div>
    </div>
  );
}
