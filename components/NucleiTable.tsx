"use client";

import React from "react";
import { NucleusMetric } from "@/lib/types";
import { Table, CheckCircle2, AlertTriangle } from "lucide-react";

interface NucleiTableProps {
  nuclei: NucleusMetric[];
  selectedNucleus: NucleusMetric | null;
  onSelectNucleus: (n: NucleusMetric | null) => void;
}

export default function NucleiTable({
  nuclei,
  selectedNucleus,
  onSelectNucleus,
}: NucleiTableProps) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xl space-y-3">
      <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
        <div className="flex items-center space-x-2">
          <Table className="w-4 h-4 text-cyan-400" />
          <h3 className="text-sm font-semibold text-slate-200">
            Segmented Nuclei Morphology Roster
          </h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">
          Showing {nuclei.length} Cells
        </span>
      </div>

      <div className="max-h-64 overflow-y-auto rounded-lg border border-slate-800">
        <table className="w-full text-left text-xs text-slate-300">
          <thead className="bg-slate-950 text-slate-400 text-[11px] uppercase tracking-wider sticky top-0 border-b border-slate-800">
            <tr>
              <th className="py-2 px-3 font-medium">ID</th>
              <th className="py-2 px-3 font-medium">Area (µm²)</th>
              <th className="py-2 px-3 font-medium">Circularity</th>
              <th className="py-2 px-3 font-medium">Aspect Ratio</th>
              <th className="py-2 px-3 font-medium">Solidity</th>
              <th className="py-2 px-3 font-medium">Pleomorphism</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60 font-mono">
            {nuclei.map((n) => {
              const isSelected = selectedNucleus?.id === n.id;
              const isHighAtypia = n.pleomorphism_score > 0.45;

              return (
                <tr
                  key={n.id}
                  onClick={() => onSelectNucleus(isSelected ? null : n)}
                  className={`cursor-pointer transition-colors ${
                    isSelected
                      ? "bg-yellow-950/40 text-yellow-200 font-semibold"
                      : "hover:bg-slate-800/50"
                  }`}
                >
                  <td className="py-2 px-3 text-cyan-400">#{n.id}</td>
                  <td className="py-2 px-3">{n.area_um2}</td>
                  <td className="py-2 px-3">{n.circularity}</td>
                  <td className="py-2 px-3">{n.aspect_ratio}</td>
                  <td className="py-2 px-3">{n.solidity}</td>
                  <td className="py-2 px-3">
                    <span
                      className={`inline-flex items-center space-x-1 px-1.5 py-0.5 rounded text-[10px] ${
                        isHighAtypia
                          ? "bg-rose-950/60 text-rose-300 border border-rose-800/80"
                          : "bg-emerald-950/60 text-emerald-300 border border-emerald-800/80"
                      }`}
                    >
                      {isHighAtypia ? (
                        <>
                          <AlertTriangle className="w-2.5 h-2.5" />
                          <span>Atypical ({n.pleomorphism_score})</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="w-2.5 h-2.5" />
                          <span>Regular ({n.pleomorphism_score})</span>
                        </>
                      )}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
