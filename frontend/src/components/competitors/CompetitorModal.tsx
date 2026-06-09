"use client";

import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X } from "lucide-react";
import { CompetitorDetails } from "./CompetitorDetails";
import type { Competitor } from "./CompetitorCard";

interface CompetitorModalProps {
  competitor: Competitor | null;
  onClose: () => void;
}

export function CompetitorModal({ competitor, onClose }: CompetitorModalProps) {
  useEffect(() => {
    if (competitor) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [competitor]);

  return (
    <AnimatePresence>
      {competitor && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: "spring", bounce: 0.2, duration: 0.5 }}
            className="fixed inset-4 md:inset-x-auto md:inset-y-6 md:left-1/4 md:right-1/4 z-50 overflow-hidden rounded-2xl border border-white/10 bg-[#0f0f0f] shadow-2xl"
          >
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/5 px-6 py-4">
              <div>
                <h2 className="text-lg font-semibold text-white">{competitor.name}</h2>
                <p className="text-sm text-muted-foreground">
                  {competitor.country}
                  {competitor.segment && <span> · {competitor.segment}</span>}
                </p>
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-2 text-muted-foreground hover:text-white hover:bg-white/5 transition-colors"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Scrollable content */}
            <div className="overflow-y-auto" style={{ maxHeight: "calc(100vh - 180px)" }}>
              <div className="p-6">
                <CompetitorDetails competitor={competitor} />
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
