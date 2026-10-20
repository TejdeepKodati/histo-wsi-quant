"""
Cellular and Nuclear Morphometry Quantification Engine for Digital Pathology.
Extracts geometric, morphological, and spatial distribution metrics per nucleus.
"""

import numpy as np
import cv2
from typing import TypedDict, List, Dict, Any


class NucleusMetrics(TypedDict):
    id: int
    centroid_x: float
    centroid_y: float
    area_px: float
    area_um2: float
    perimeter_px: float
    circularity: float
    aspect_ratio: float
    solidity: float
    pleomorphism_score: float
    bounding_box: tuple[int, int, int, int]


class HistopathologyQuantifier:
    """
    Quantifies cellular morphology across segmented histopathology images.
    Converts pixel measurements to clinical units (microns) based on slide resolution (MPP).
    """
    def __init__(self, mpp: float = 0.25):
        """
        Args:
            mpp: Microns Per Pixel (0.25 um/px is standard 40x magnification).
        """
        self.mpp = mpp

    def extract_features(self, labeled_mask: np.ndarray, num_nuclei: int) -> tuple[List[NucleusMetrics], Dict[str, Any]]:
        """
        Computes detailed morphometric descriptors for every segmented nucleus.
        """
        nuclei_list: List[NucleusMetrics] = []
        areas: List[float] = []
        circularities: List[float] = []
        solidities: List[float] = []

        h, w = labeled_mask.shape

        for nucleus_id in range(1, num_nuclei + 1):
            cell_mask = (labeled_mask == nucleus_id).astype(np.uint8)
            contours, _ = cv2.findContours(cell_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if not contours:
                continue

            cnt = max(contours, key=cv2.contourArea)
            area_px = float(cv2.contourArea(cnt))
            if area_px < 6:
                continue

            perimeter_px = float(cv2.arcLength(cnt, True))
            area_um2 = area_px * (self.mpp ** 2)

            # Circularity: 4 * pi * Area / Perimeter^2 (capped at 1.0)
            if perimeter_px > 0:
                circularity = min(1.0, (4.0 * np.pi * area_px) / (perimeter_px ** 2))
            else:
                circularity = 0.0

            # Convex hull and solidity
            hull = cv2.convexHull(cnt)
            hull_area = cv2.contourArea(hull)
            solidity = float(area_px / hull_area) if hull_area > 0 else 1.0

            # Centroid & Bounding Box
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = float(M["m10"] / M["m00"])
                cy = float(M["m01"] / M["m00"])
            else:
                cx, cy = 0.0, 0.0

            x, y, bw, bh = cv2.boundingRect(cnt)

            # Aspect Ratio
            if len(cnt) >= 5:
                (rx, ry), (minor, major), angle = cv2.fitEllipse(cnt)
                aspect_ratio = float(major / minor) if minor > 0 else 1.0
            else:
                aspect_ratio = float(max(bw, bh) / min(bw, bh)) if min(bw, bh) > 0 else 1.0

            # Pleomorphism score: heuristic combining size deviation & irregularity
            # High pleomorphism indicates high grade dysplasia/neoplasia
            pleomorphism = (1.0 - circularity) * 0.6 + (aspect_ratio - 1.0) * 0.4

            metric: NucleusMetrics = {
                "id": nucleus_id,
                "centroid_x": round(cx, 2),
                "centroid_y": round(cy, 2),
                "area_px": round(area_px, 1),
                "area_um2": round(area_um2, 2),
                "perimeter_px": round(perimeter_px, 1),
                "circularity": round(circularity, 3),
                "aspect_ratio": round(aspect_ratio, 2),
                "solidity": round(solidity, 3),
                "pleomorphism_score": round(max(0.0, pleomorphism), 3),
                "bounding_box": (int(x), int(y), int(bw), int(bh))
            }

            nuclei_list.append(metric)
            areas.append(area_um2)
            circularities.append(circularity)
            solidities.append(solidity)

        # Summary statistics
        total_cells = len(nuclei_list)
        tissue_area_um2 = float(h * w * (self.mpp ** 2))
        total_nuclear_area_um2 = float(sum(areas))
        nc_ratio = round(total_nuclear_area_um2 / tissue_area_um2, 4) if tissue_area_um2 > 0 else 0.0

        summary: Dict[str, Any] = {
            "total_nuclei_count": total_cells,
            "tissue_area_um2": round(tissue_area_um2, 2),
            "nuclear_to_cytoplasmic_ratio": nc_ratio,
            "mean_nuclear_area_um2": round(float(np.mean(areas)), 2) if areas else 0.0,
            "std_nuclear_area_um2": round(float(np.std(areas)), 2) if areas else 0.0,
            "mean_circularity": round(float(np.mean(circularities)), 3) if circularities else 0.0,
            "mean_solidity": round(float(np.mean(solidities)), 3) if solidities else 0.0,
            "cellular_density_per_mm2": round((total_cells / (tissue_area_um2 / 1e6)), 1) if tissue_area_um2 > 0 else 0.0
        }

        return nuclei_list, summary

    def generate_density_heatmap(self, labeled_mask: np.ndarray, grid_size: int = 32) -> np.ndarray:
        """
        Generates a 2D spatial cellular density heatmap across the slide image.
        """
        h, w = labeled_mask.shape
        heatmap = np.zeros((h // grid_size, w // grid_size), dtype=np.float32)

        for i in range(heatmap.shape[0]):
            for j in range(heatmap.shape[1]):
                patch = labeled_mask[i * grid_size:(i + 1) * grid_size, j * grid_size:(j + 1) * grid_size]
                unique_cells = len(np.unique(patch[patch > 0]))
                heatmap[i, j] = unique_cells

        # Normalize to 0-255 and apply color mapping
        if heatmap.max() > 0:
            norm_heat = (heatmap / heatmap.max() * 255.0).astype(np.uint8)
        else:
            norm_heat = np.zeros_like(heatmap, dtype=np.uint8)

        heat_resized = cv2.resize(norm_heat, (w, h), interpolation=cv2.INTER_LINEAR)
        color_heatmap = cv2.applyColorMap(heat_resized, cv2.COLORMAP_JET)
        return color_heatmap
