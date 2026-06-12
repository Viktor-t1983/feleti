"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/auth";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { ChatOverlay } from "@/components/chat/ChatOverlay";

export function MainLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const restore = useAuthStore((s) => s.restore);
  const isLoginPage = pathname === "/login";
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);

  useEffect(() => {
    restore();
  }, [restore]);

  if (isLoginPage) {
    return <>{children}</>;
  }

  // Скрываем оверлей на странице AI (там уже есть полный чат)
  const hideOverlay = pathname === "/ai" || !isAuthenticated;

  return (
    <div className="flex min-h-screen bg-[#0a0a0a]">
      <Sidebar />
      <div className="flex flex-1 flex-col pl-64">
        <Header />
        <main className="flex-1 p-6">{children}</main>
      </div>
      {!hideOverlay && <ChatOverlay />}
    </div>
  );
}
