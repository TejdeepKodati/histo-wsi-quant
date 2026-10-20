"use client";

import React from "react";
import { SlideData } from "@/lib/types";
import { Download, FileJson, X, Check } from "lucide-react";

interface ExportModalProps {
  slide: SlideData;
  isOpen: boolean;
  onClose: () => void;
}

export default function ExportModal({ slide, isOpen, onClose }: ExportModalProps) {
  if (!isOpen) return null;

  const downloadJSON = () => {
    const reportData = {
      specimen_id: slide.id,
      tissue_type: slide.title,
      timestamp: new Date().toISOString(),
      optical_resolution_mpp: 0.25,
      stain_normalization: "Macenko Optical Density SVD Decomposition",
      morphometry_summary: slide.summary,
      cellular_sample_data: slide.nuclei_sample,
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pathology_quantification_${slide.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Download className="w-5 h-5 text-cyan-400" />
            <h3 className="text-base font-semibold text-slate-100">
              Export Morphometric Biopsy Analysis
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-xs text-slate-300 leading-relaxed">
          Export clinical quantitative histology metrics including total nuclear counts,
          mean cellular areas (µm²), circularity distributions, nuclear-to-cytoplasmic
          ratios, and spatial density estimations formatted for clinical informatics systems.
        </p>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800/80 space-y-2 text-xs">
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Specimen:</span>
            <span className="font-mono text-cyan-300">{slide.title}</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Total Cell Count:</span>
            <span className="font-mono text-slate-200">{slide.summary.total_nuclei_count} nuclei</span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">N:C Biomass Ratio:</span>
            <span className="font-mono text-slate-200">
              {(slide.summary.nuclear_to_cytoplasmic_ratio * 100).toFixed(1)}%
            </span>
          </div>
          <div className="flex justify-between text-slate-300">
            <span className="text-slate-400">Cellular Density:</span>
            <span className="font-mono text-slate-200">
              {slide.summary.cellular_density_per_mm2} cells/mm²
            </span>
          </div>
        </div>

        <div className="flex justify-end space-x-2 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-300 transition"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              downloadJSON();
              onClose();
            }}
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white flex items-center space-x-2 shadow-lg shadow-cyan-600/30 transition"
          >
            <FileJson className="w-4 h-4" />
            <span>Download Quantitative JSON</span>
          </button>
        </div>
      </div>
    </div>
  );
}
