export interface NucleusMetric {
  id: number;
  centroid_x: number;
  centroid_y: number;
  area_px: number;
  area_um2: number;
  perimeter_px: number;
  circularity: number;
  aspect_ratio: number;
  solidity: number;
  pleomorphism_score: number;
  bounding_box: [number, number, number, number];
}

export interface SlideSummary {
  total_nuclei_count: number;
  tissue_area_um2: number;
  nuclear_to_cytoplasmic_ratio: number;
  mean_nuclear_area_um2: number;
  std_nuclear_area_um2: number;
  mean_circularity: number;
  mean_solidity: number;
  cellular_density_per_mm2: number;
}

export interface SlideData {
  id: string;
  title: string;
  summary: SlideSummary;
  nuclei_sample: NucleusMetric[];
  images: {
    raw: string;
    macenko: string;
    reinhard: string;
    overlay: string;
    heatmap: string;
  };
}

export type ViewMode = 'raw' | 'macenko' | 'reinhard' | 'overlay' | 'heatmap';
