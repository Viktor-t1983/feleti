"use client";

import { ArrowLeft, Construction } from "lucide-react";
import Link from "next/link";

export default function NewBatchPage() {
  return (
    <div className="space-y-6">
      <div>
        <Link
          href="/batches"
          className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-white transition-colors mb-4"
        >
          <ArrowLeft className="h-4 w-4" />
          Назад к партиям
        </Link>
      </div>

      <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-24">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-feleti-gold/10 mb-6">
          <Construction className="h-8 w-8 text-feleti-gold" />
        </div>
        <h1 className="text-2xl font-bold text-white mb-2">Запуск новой партии</h1>
        <p className="text-muted-foreground text-sm mb-8">
          Форма создания партии будет реализована в следующей версии
        </p>
        <Link
          href="/batches"
          className="inline-flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.02] px-5 py-2.5 text-sm text-white hover:bg-white/[0.04] transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Вернуться к партиям
        </Link>
      </div>
    </div>
  );
}
