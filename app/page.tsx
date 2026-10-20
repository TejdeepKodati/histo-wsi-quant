"use client";

import React, { useState } from "react";
import slideCatalog from "@/lib/slideCatalog.json";
import { SlideData, ViewMode, NucleusMetric } from "@/lib/types";
import WSIViewer from "@/components/WSIViewer";
import MorphometryDashboard from "@/components/MorphometryDashboard";
import StainPanel from "@/components/StainPanel";
import NucleiTable from "@/components/NucleiTable";
import ExportModal from "@/components/ExportModal";
import {
  Microscope,
  Layers,
  BarChart2,
  Download,
  Github,
  Sliders,
  Sparkles,
} from "lucide-react";

export default function Home() {
  const slides: SlideData[] = slideCatalog as SlideData[];
  const [selectedSlideId, setSelectedSlideId] = useState<string>(slides[0].id);
  const [viewMode, setViewMode] = useState<ViewMode>("overlay");
  const [selectedNucleus, setSelectedNucleus] = useState<NucleusMetric | null>(null);
  const [isExportOpen, setIsExportOpen] = useState<boolean>(false);

  const currentSlide = slides.find((s) => s.id === selectedSlideId) || slides[0];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="sticky top-0 z-40 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-xl bg-cyan-600/20 border border-cyan-500/30 text-cyan-400">
            <Microscope className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-base font-bold text-slate-100 tracking-tight">
                HistoWSI Quant
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                v1.0.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Gigapixel Pathology WSI Analytics & Deep Learning Nuclei Morphometry
            </p>
          </div>
        </div>

        {/* Slide Selector & Action Buttons */}
        <div className="flex items-center space-x-3">
          <div className="hidden md:flex items-center space-x-2">
            <span className="text-xs text-slate-400 font-medium">Specimen:</span>
            <select
              value={selectedSlideId}
              onChange={(e) => {
                setSelectedSlideId(e.target.value);
                setSelectedNucleus(null);
              }}
              className="bg-slate-950 border border-slate-700/80 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 font-medium"
            >
              {slides.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.title}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => setIsExportOpen(true)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition"
          >
            <Download className="w-3.5 h-3.5 text-cyan-400" />
            <span className="hidden sm:inline">Export Report</span>
          </button>

          {/* Top-Right Attribution link */}
          <a
            href="https://github.com/TejdeepKodati/histo-wsi-quant"
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs font-medium text-slate-300 hover:text-cyan-400 transition flex items-center space-x-1.5 px-2.5 py-1.5 bg-slate-800/80 rounded-lg border border-slate-700/60"
          >
            <Github className="w-3.5 h-3.5" />
            <span>made with ♥ by Tejdeep</span>
          </a>
        </div>
      </header>

      {/* Mobile Specimen Selector */}
      <div className="md:hidden px-4 py-2 bg-slate-900 border-b border-slate-800 flex items-center justify-between">
        <span className="text-xs text-slate-400 font-medium">Specimen:</span>
        <select
          value={selectedSlideId}
          onChange={(e) => {
            setSelectedSlideId(e.target.value);
            setSelectedNucleus(null);
          }}
          className="bg-slate-950 border border-slate-700 rounded-lg px-2.5 py-1 text-xs text-slate-200"
        >
          {slides.map((s) => (
            <option key={s.id} value={s.id}>
              {s.title}
            </option>
          ))}
        </select>
      </div>

      {/* Main Workspace Layout */}
      <main className="flex-1 p-4 lg:p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 max-w-7xl mx-auto w-full">
        {/* Left / Center: Interactive Virtual WSI Viewer */}
        <div className="lg:col-span-8 flex flex-col space-y-4">
          <WSIViewer
            slide={currentSlide}
            viewMode={viewMode}
            selectedNucleus={selectedNucleus}
            onSelectNucleus={setSelectedNucleus}
          />

          {/* Morphometry Diagnostics Dashboard */}
          <MorphometryDashboard summary={currentSlide.summary} />
        </div>

        {/* Right Sidebar: Stain Normalization Controls & Nuclei Table */}
        <div className="lg:col-span-4 flex flex-col space-y-4">
          <StainPanel viewMode={viewMode} onViewModeChange={setViewMode} />
          
          <NucleiTable
            nuclei={currentSlide.nuclei_sample}
            selectedNucleus={selectedNucleus}
            onSelectNucleus={setSelectedNucleus}
          />
        </div>
      </main>

      {/* Clinical Export Modal */}
      <ExportModal
        slide={currentSlide}
        isOpen={isExportOpen}
        onClose={() => setIsExportOpen(false)}
      />

      {/* Footer with exact required attribution */}
      <footer className="mt-auto border-t border-slate-800/80 bg-slate-950 px-4 lg:px-8 py-3 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-400 gap-2">
        <div className="flex items-center space-x-2">
          <span>Digital Pathology WSI Analytics Platform</span>
          <span>•</span>
          <span>PyTorch Deep Learning & Computer Vision</span>
        </div>

        <div>
          <a
            href="https://github.com/TejdeepKodati/histo-wsi-quant"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-cyan-400 transition font-medium"
          >
            made with ♥ by Tejdeep
          </a>
        </div>
      </footer>
    </div>
  );
}
