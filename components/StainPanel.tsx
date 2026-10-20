"use client";

import React from "react";
import { ViewMode } from "@/lib/types";
import { Eye, Layers, Palette, Sparkles, Flame } from "lucide-react";

interface StainPanelProps {
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
}

export default function StainPanel({ viewMode, onViewModeChange }: StainPanelProps) {
  const modes: { id: ViewMode; label: string; desc: string; icon: React.ReactNode }[] = [
    {
      id: "raw",
      label: "Raw H&E Slide",
      desc: "Original digitized biopsy microscopy image with unstabilized stain variation",
      icon: <Eye className="w-4 h-4 text-slate-400" />,
    },
    {
      id: "macenko",
      label: "Macenko Normalization",
      desc: "Optical Density matrix decomposition via SVD with reference stain vectors",
      icon: <Palette className="w-4 h-4 text-pink-400" />,
    },
    {
      id: "reinhard",
      label: "Reinhard Color Transfer",
      desc: "Per-channel CIELab luminance & chrominance distribution alignment",
      icon: <Sparkles className="w-4 h-4 text-purple-400" />,
    },
    {
      id: "overlay",
      label: "AI Nuclei Segmentation",
      desc: "Residual U-Net predictions + Marker-Controlled Watershed contour masks",
      icon: <Layers className="w-4 h-4 text-cyan-400" />,
    },
    {
      id: "heatmap",
      label: "Cellular Density Heatmap",
      desc: "2D spatial kernel density estimating cell proliferation & clustering",
      icon: <Flame className="w-4 h-4 text-amber-400" />,
    },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
      <div className="flex items-center space-x-2 border-b border-slate-800 pb-2.5">
        <Layers className="w-4 h-4 text-cyan-400" />
        <h3 className="text-sm font-semibold text-slate-200">
          Stain Normalization & AI Overlays
        </h3>
      </div>

      <div className="grid grid-cols-1 gap-2">
        {modes.map((m) => {
          const isActive = viewMode === m.id;
          return (
            <button
              key={m.id}
              onClick={() => onViewModeChange(m.id)}
              className={`w-full text-left p-3 rounded-lg border transition-all duration-150 flex items-start space-x-3 ${
                isActive
                  ? "bg-cyan-950/40 border-cyan-500/60 text-white shadow-lg shadow-cyan-950/30"
                  : "bg-slate-950/40 border-slate-800/80 hover:bg-slate-800/50 text-slate-300"
              }`}
            >
              <div className="mt-0.5">{m.icon}</div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <span className={`text-xs font-semibold ${isActive ? "text-cyan-300" : "text-slate-200"}`}>
                    {m.label}
                  </span>
                  {isActive && (
                    <span className="text-[10px] font-mono px-1.5 py-0.2 bg-cyan-500/20 text-cyan-300 rounded border border-cyan-500/40">
                      ACTIVE
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">
                  {m.desc}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
