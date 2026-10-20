"use client";

import React, { useState, useRef, useEffect } from "react";
import { ZoomIn, ZoomOut, Maximize2, RotateCcw, Crosshair } from "lucide-react";
import { SlideData, ViewMode, NucleusMetric } from "@/lib/types";

interface WSIViewerProps {
  slide: SlideData;
  viewMode: ViewMode;
  selectedNucleus: NucleusMetric | null;
  onSelectNucleus: (nucleus: NucleusMetric | null) => void;
}

export default function WSIViewer({
  slide,
  viewMode,
  selectedNucleus,
  onSelectNucleus,
}: WSIViewerProps) {
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [cursorCoord, setCursorCoord] = useState<{ x: number; y: number; umX: number; umY: number }>({
    x: 0,
    y: 0,
    umX: 0,
    umY: 0,
  });

  const containerRef = useRef<HTMLDivElement>(null);

  // Reset pan and zoom when slide changes
  useEffect(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, [slide.id]);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }

    if (containerRef.current) {
      const rect = containerRef.current.getBoundingClientRect();
      const relX = Math.round((e.clientX - rect.left - pan.x) / zoom);
      const relY = Math.round((e.clientY - rect.top - pan.y) / zoom);
      setCursorCoord({
        x: relX,
        y: relY,
        umX: Math.round(relX * 0.25),
        umY: Math.round(relY * 0.25),
      });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.15 : 0.85;
    setZoom((prev) => Math.min(Math.max(prev * zoomFactor, 0.75), 8));
  };

  const getCurrentImage = () => {
    switch (viewMode) {
      case "macenko":
        return slide.images.macenko;
      case "reinhard":
        return slide.images.reinhard;
      case "overlay":
        return slide.images.overlay;
      case "heatmap":
        return slide.images.heatmap;
      case "raw":
      default:
        return slide.images.raw;
    }
  };

  return (
    <div className="relative flex-1 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col shadow-2xl">
      {/* Top Viewer Toolbar */}
      <div className="px-4 py-2.5 bg-slate-950/80 border-b border-slate-800 backdrop-blur-md flex items-center justify-between z-10">
        <div className="flex items-center space-x-3">
          <span className="text-xs font-semibold uppercase tracking-wider text-cyan-400 bg-cyan-950/60 border border-cyan-800/60 px-2 py-0.5 rounded">
            Virtual WSI Viewport
          </span>
          <span className="text-sm font-medium text-slate-300 truncate max-w-xs md:max-w-md">
            {slide.title}
          </span>
          <span className="text-xs text-slate-500 hidden sm:inline">
            (Resolution: 1024×1024 px | 0.25 µm/px)
          </span>
        </div>

        {/* Viewport Control Buttons */}
        <div className="flex items-center space-x-1.5">
          <button
            onClick={() => setZoom((z) => Math.min(z * 1.25, 8))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Zoom In"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z / 1.25, 0.75))}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Zoom Out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition"
            title="Reset View"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <div className="px-2 py-1 bg-slate-800/80 rounded text-xs font-mono text-cyan-300">
            {(zoom * 40).toFixed(0)}× ({zoom.toFixed(1)}x)
          </div>
        </div>
      </div>

      {/* Main Interactive Pan/Zoom Canvas Area */}
      <div
        ref={containerRef}
        className="relative flex-1 cursor-grab active:cursor-grabbing overflow-hidden bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] flex items-center justify-center min-h-[480px]"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <div
          className="relative transition-transform duration-75 select-none"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "center center",
          }}
        >
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={getCurrentImage()}
            alt={slide.title}
            className="max-w-none w-[640px] h-[640px] object-cover shadow-2xl rounded-sm border border-slate-700/50 pointer-events-none"
            draggable={false}
          />

          {/* Interactive Nuclei Markers if in overlay or raw mode */}
          {(viewMode === "overlay" || viewMode === "raw") &&
            slide.nuclei_sample.map((nucleus) => {
              const isSelected = selectedNucleus?.id === nucleus.id;
              // Coordinates scaled to 640/1024
              const scale = 640 / 1024;
              const cx = nucleus.centroid_x * scale;
              const cy = nucleus.centroid_y * scale;

              return (
                <div
                  key={nucleus.id}
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectNucleus(nucleus);
                  }}
                  className={`absolute rounded-full -translate-x-1/2 -translate-y-1/2 cursor-pointer transition-transform duration-150 ${
                    isSelected
                      ? "ring-4 ring-yellow-400 bg-yellow-400/50 scale-150 z-20"
                      : "hover:scale-150 hover:ring-2 hover:ring-cyan-300 opacity-60 hover:opacity-100"
                  }`}
                  style={{
                    left: `${cx}px`,
                    top: `${cy}px`,
                    width: `${Math.max(8, nucleus.bounding_box[2] * scale)}px`,
                    height: `${Math.max(8, nucleus.bounding_box[3] * scale)}px`,
                    border: isSelected
                      ? "2px solid #facc15"
                      : "1px dashed rgba(56, 189, 248, 0.7)",
                  }}
                  title={`Nucleus #${nucleus.id} (Area: ${nucleus.area_um2} µm²)`}
                />
              );
            })}
        </div>

        {/* Viewport Scale Bar Overlay */}
        <div className="absolute bottom-4 left-4 bg-slate-950/80 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-300 flex items-center space-x-2 pointer-events-none">
          <div className="w-16 h-1 bg-cyan-400 rounded-sm"></div>
          <span>50 µm</span>
        </div>

        {/* Cursor Coordinate Tracker Overlay */}
        <div className="absolute bottom-4 right-4 bg-slate-950/80 backdrop-blur-md border border-slate-800 px-3 py-1.5 rounded-lg text-xs font-mono text-slate-400 flex items-center space-x-2 pointer-events-none">
          <Crosshair className="w-3.5 h-3.5 text-cyan-400" />
          <span>
            X: {cursorCoord.x} px ({cursorCoord.umX} µm) | Y: {cursorCoord.y} px ({cursorCoord.umY} µm)
          </span>
        </div>
      </div>
    </div>
  );
}
