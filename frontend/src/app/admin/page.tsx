"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import {
  Shield,
  Users,
  BarChart3,
  Factory,
  Cpu,
  Loader2,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";
import { AdminUsersTab } from "@/components/admin/AdminUsersTab";
import { AdminCompetitorsTab } from "@/components/admin/AdminCompetitorsTab";
import { AdminManufacturersTab } from "@/components/admin/AdminManufacturersTab";

const tabs = [
  { id: "users", label: "Пользователи", icon: Users },
  { id: "competitors", label: "Конкуренты", icon: BarChart3 },
  { id: "manufacturers", label: "Производители", icon: Factory },
  { id: "ai", label: "AI-ассистент", icon: Cpu },
];

export default function AdminPage() {
  const router = useRouter();
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  const isLoadingAuth = useAuthStore((s) => s.isLoading);

  const [activeTab, setActiveTab] = useState("users");

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

  const isAdmin = user?.role === "admin" || user?.is_superuser;

  if (!isAdmin) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <Shield className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">Доступ запрещён</h2>
          <p className="text-muted-foreground">Только для администраторов</p>
        </div>
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
        <div className="flex items-center gap-3">
          <div className="inline-flex rounded-xl bg-feleti-gold/10 p-3">
            <Shield className="h-6 w-6 text-feleti-gold" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-white">Панель администратора</h1>
            <p className="text-sm text-muted-foreground">
              Управление пользователями, конкурентами, производителями и настройками
            </p>
          </div>
        </div>
      </motion.div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-white/5 p-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`relative flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-medium transition-colors shrink-0 ${
              activeTab === tab.id
                ? "text-white"
                : "text-muted-foreground hover:text-white"
            }`}
          >
            {activeTab === tab.id && (
              <motion.div
                layoutId="admin-tab"
                className="absolute inset-0 rounded-lg bg-white/10"
                transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
              />
            )}
            <tab.icon className="relative h-4 w-4" />
            <span className="relative">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <motion.div
        key={activeTab}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
      >
        {activeTab === "users" && <AdminUsersTab />}
        {activeTab === "competitors" && <AdminCompetitorsTab />}
        {activeTab === "manufacturers" && <AdminManufacturersTab />}
        {activeTab === "ai" && (
          <iframe
            src="/settings"
            className="w-full h-[calc(100vh-220px)] rounded-2xl border border-white/5 bg-transparent"
          />
        )}
      </motion.div>
    </div>
  );
}
