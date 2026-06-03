"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Flame,
  BarChart3,
  BookOpen,
  Settings,
  LogOut,
  Home,
  Package,
  Lightbulb,
} from "lucide-react";
import { useAuthStore } from "@/stores/auth";

const navItems = [
  { href: "/", label: "Главная", icon: Home },
  { href: "/chambers", label: "Камеры", icon: Flame },
  { href: "/recipes", label: "Рецепты", icon: BookOpen },
  { href: "/batches", label: "Партии", icon: Package },
  { href: "/knowledge", label: "Знания", icon: Lightbulb },
  { href: "/competitors", label: "Конкуренты", icon: BarChart3 },
  { href: "/settings", label: "Настройки", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const logout = useAuthStore((s) => s.logout);

  return (
    <aside className="fixed left-0 top-0 z-40 h-screen w-64 border-r border-white/5 bg-[#0f0f0f]">
      <div className="flex h-full flex-col">
        {/* Logo */}
        <div className="flex items-center gap-3 px-6 py-5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-feleti-gold/20">
            <Flame className="h-4 w-4 text-feleti-gold" />
          </div>
          <span className="text-lg font-bold tracking-tight text-white">
            FELETI<span className="text-feleti-gold">-SMOK</span>
          </span>
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 px-3 py-4">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link key={item.href} href={item.href}>
                <div
                  className={`group relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors ${
                    isActive
                      ? "text-white"
                      : "text-muted-foreground hover:text-white"
                  }`}
                >
                  {isActive && (
                    <motion.div
                      layoutId="sidebar-active"
                      className="absolute inset-0 rounded-xl bg-white/5"
                      transition={{ type: "spring", duration: 0.5 }}
                    />
                  )}
                  <item.icon className="relative h-4 w-4" />
                  <span className="relative">{item.label}</span>
                </div>
              </Link>
            );
          })}
        </nav>

        {/* Logout */}
        <div className="border-t border-white/5 p-3">
          <button
            onClick={logout}
            className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-white/5 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Выйти
          </button>
        </div>
      </div>
    </aside>
  );
}
