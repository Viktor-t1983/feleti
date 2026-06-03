"use client";

import { motion } from "framer-motion";
import { Camera, CameraOff } from "lucide-react";

interface ChamberCameraProps {
  enabled?: boolean;
  streamUrl?: string;
}

export function ChamberCamera({ enabled = false, streamUrl }: ChamberCameraProps) {
  if (!enabled) {
    return (
      <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-5">
        <h3 className="text-sm font-medium text-white mb-3">Камера внутри</h3>
        <div className="flex flex-col items-center justify-center rounded-xl bg-black/40 py-8 gap-2">
          <CameraOff className="h-8 w-8 text-muted-foreground/40" />
          <span className="text-xs text-muted-foreground/60">
            Камера не установлена
          </span>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-2xl border border-white/5 bg-black/40 overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-2.5 bg-black/20">
        <div className="flex items-center gap-2">
          <Camera className="h-4 w-4 text-feleti-gold" />
          <h3 className="text-sm font-medium text-white">Камера</h3>
        </div>
        <span className="flex items-center gap-1.5 text-[10px] text-emerald-400">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
          LIVE
        </span>
      </div>

      {streamUrl ? (
        <img
          src={streamUrl}
          alt="Внутри камеры"
          className="w-full aspect-video object-cover"
        />
      ) : (
        <div className="flex flex-col items-center justify-center aspect-video gap-2 bg-black/60">
          <Camera className="h-10 w-10 text-muted-foreground/30" />
          <span className="text-xs text-muted-foreground/50">
            Поток не подключён
          </span>
        </div>
      )}
    </motion.div>
  );
}
