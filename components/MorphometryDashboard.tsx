"use client";

import React from "react";
import { SlideSummary } from "@/lib/types";
import { Activity, Layers, Disc, BarChart3, AlertCircle } from "lucide-react";

interface MorphometryDashboardProps {
  summary: SlideSummary;
}

export default function MorphometryDashboard({ summary }: MorphometryDashboardProps) {
  const getPleomorphismGrade = () => {
    if (summary.mean_circularity < 0.75 || summary.std_nuclear_area_um2 > 18) {
      return { grade: "Grade III (High Atypia)", color: "text-rose-400 bg-rose-950/60 border-rose-800" };
    }
    if (summary.mean_circularity < 0.83 || summary.std_nuclear_area_um2 > 12) {
      return { grade: "Grade II (Moderate Pleomorphism)", color: "text-amber-400 bg-amber-950/60 border-amber-800" };
    }
    return { grade: "Grade I (Uniform / Well-Differentiated)", color: "text-emerald-400 bg-emerald-950/60 border-emerald-800" };
  };

  const pleom = getPleomorphismGrade();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xl space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-semibold text-slate-100">
            Cellular Morphometry & Quantitative Biomarkers
          </h2>
        </div>
        <div className={`px-2.5 py-1 rounded text-xs font-semibold border ${pleom.color}`}>
          {pleom.grade}
        </div>
      </div>

      {/* Grid of Key Diagnostic Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">Detected Nuclei</span>
          <span className="text-2xl font-bold font-mono text-cyan-300">
            {summary.total_nuclei_count}
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Segmented via U-Net</span>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">Mean Nuclear Area</span>
          <span className="text-2xl font-bold font-mono text-indigo-300">
            {summary.mean_nuclear_area_um2} <span className="text-xs font-normal text-slate-400">µm²</span>
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">± {summary.std_nuclear_area_um2} µm²</span>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">Cellular Density</span>
          <span className="text-2xl font-bold font-mono text-emerald-300">
            {summary.cellular_density_per_mm2}
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">cells / mm² tissue</span>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">N:C Area Ratio</span>
          <span className="text-2xl font-bold font-mono text-violet-300">
            {(summary.nuclear_to_cytoplasmic_ratio * 100).toFixed(1)}%
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Fraction of nuclear biomass</span>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">Mean Circularity</span>
          <span className="text-2xl font-bold font-mono text-amber-300">
            {summary.mean_circularity}
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Form Factor (4πA/P²)</span>
        </div>

        <div className="bg-slate-950/70 border border-slate-800/80 rounded-lg p-3">
          <span className="text-xs text-slate-400 block mb-1">Mean Solidity</span>
          <span className="text-2xl font-bold font-mono text-sky-300">
            {summary.mean_solidity}
          </span>
          <span className="text-[10px] text-slate-500 block mt-0.5">Area / Convex Hull Area</span>
        </div>
      </div>

      {/* Morphological Feature Breakdown Bars */}
      <div className="space-y-3 pt-1">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center space-x-1.5">
          <BarChart3 className="w-3.5 h-3.5 text-cyan-400" />
          <span>Morphometric Shape & Regularity Indices</span>
        </h3>

        <div className="space-y-2">
          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Nuclear Sphericity / Circularity Index</span>
              <span className="font-mono text-cyan-300">{(summary.mean_circularity * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-cyan-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${summary.mean_circularity * 100}%` }}
              ></div>
            </div>
          </div>

          <div>
            <div className="flex justify-between text-xs text-slate-300 mb-1">
              <span>Convexity / Edge Solidity Metric</span>
              <span className="font-mono text-indigo-300">{(summary.mean_solidity * 100).toFixed(1)}%</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
              <div
                className="bg-indigo-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${summary.mean_solidity * 100}%` }}
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
