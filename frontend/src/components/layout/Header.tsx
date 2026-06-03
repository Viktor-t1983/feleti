"use client";

import { useAuthStore } from "@/stores/auth";
import { User } from "lucide-react";

export function Header() {
  const user = useAuthStore((s) => s.user);

  return (
    <header className="sticky top-0 z-30 border-b border-white/5 bg-[#0f0f0f]/80 backdrop-blur-xl">
      <div className="flex h-14 items-center justify-between px-6">
        <div className="text-sm text-muted-foreground">
          {new Date().toLocaleDateString("ru-RU", {
            weekday: "long",
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-feleti-gold/20">
            <User className="h-4 w-4 text-feleti-gold" />
          </div>
          <div className="text-sm">
            <div className="font-medium text-white">
              {user?.full_name || user?.username || "Гость"}
            </div>
            <div className="text-xs text-muted-foreground capitalize">
              {user?.role || "operator"}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
