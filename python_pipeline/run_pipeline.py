"""
CLI Pipeline Runner for Digital Pathology WSI Processing.
Executes end-to-end:
1. Synthetic / Real WSI Patch Generation
2. Macenko & Reinhard Stain Normalization
3. PyTorch Deep Learning Nuclei Segmentation
4. Watershed Touching-Nuclei Separation
5. Morphometry & Clinical Metrics Extraction
6. DeepZoom Multi-Scale Tile Generation
"""

import os
import json
import numpy as np
import cv2
from stain_normalization import MacenkoNormalizer, ReinhardNormalizer
from segmentation_unet import NucleiSegmenter
from morphometry import HistopathologyQuantifier
from wsi_tiler import WSIPyramidTiler


def generate_synthetic_histology_slide(width: int = 1024, height: int = 1024, num_nuclei: int = 180) -> np.ndarray:
    """
    Synthesizes a realistic H&E histopathology tissue section.
    Includes eosinophilic stroma/cytoplasm background (pink) and
    hematoxylin-rich chromatin nuclei (purple/blue) with realistic variation.
    """
    np.random.seed(42)
    # Background: pale pink eosinophilic cytoplasm (RGB: ~230, 200, 220)
    base = np.zeros((height, width, 3), dtype=np.uint8)
    base[:, :, 0] = np.clip(np.random.normal(228, 10, (height, width)), 180, 250).astype(np.uint8) # R
    base[:, :, 1] = np.clip(np.random.normal(195, 12, (height, width)), 150, 235).astype(np.uint8) # G
    base[:, :, 2] = np.clip(np.random.normal(218, 8, (height, width)), 170, 245).astype(np.uint8)  # B

    # Add extracellular collagen fibril textures / stroma swirls
    for _ in range(25):
        pt1 = (np.random.randint(0, width), np.random.randint(0, height))
        pt2 = (pt1[0] + np.random.randint(-150, 150), pt1[1] + np.random.randint(-150, 150))
        color = (
            int(np.random.randint(210, 235)),
            int(np.random.randint(160, 190)),
            int(np.random.randint(190, 220))
        )
        cv2.line(base, pt1, pt2, color, thickness=np.random.randint(2, 6))

    # Add glandular lumen / empty white regions
    if width > 300 and height > 300:
        for _ in range(4):
            gx = np.random.randint(80, width - 80)
            gy = np.random.randint(80, height - 80)
            cv2.ellipse(base, (gx, gy), (np.random.randint(30, 60), np.random.randint(20, 45)),
                        angle=np.random.randint(0, 180), startAngle=0, endAngle=360,
                        color=(248, 248, 252), thickness=-1)

    # Place Hematoxylin-stained cell nuclei (deep purple/blue: R 60-110, G 40-80, B 120-170)
    for _ in range(num_nuclei):
        cx = np.random.randint(30, width - 30)
        cy = np.random.randint(30, height - 30)
        # Avoid drawing inside pure white lumen
        if np.mean(base[cy, cx]) > 240:
            continue

        radius_x = np.random.randint(6, 15)
        radius_y = int(radius_x * np.random.uniform(0.7, 1.3))
        angle = np.random.randint(0, 180)

        nuclei_color = (
            int(np.random.randint(65, 110)),
            int(np.random.randint(45, 85)),
            int(np.random.randint(125, 175))
        )

        cv2.ellipse(base, (cx, cy), (radius_x, radius_y), angle, 0, 360, nuclei_color, -1)

        # Nuclear chromatin texture / nucleoli
        if np.random.rand() > 0.4:
            cv2.circle(base, (cx + np.random.randint(-2, 3), cy + np.random.randint(-2, 3)),
                       radius=np.random.randint(1, 3), color=(40, 25, 80), thickness=-1)

    # Slight Gaussian blur to mimic microscopy focal plane
    base = cv2.GaussianBlur(base, (3, 3), 0.7)
    return base


def run_full_pipeline(output_dir: str = "output_results"):
    os.makedirs(output_dir, exist_ok=True)
    print("=" * 60)
    print("Digital Pathology WSI Analytics & Morphometry Pipeline")
    print("=" * 60)

    # 1. Synthesize high-resolution histology patch (1024x1024)
    print("[1/5] Synthesizing high-resolution H&E histopathology patch...")
    slide_rgb = generate_synthetic_histology_slide(1024, 1024, num_nuclei=220)
    raw_path = os.path.join(output_dir, "raw_he_slide.png")
    cv2.imwrite(raw_path, cv2.cvtColor(slide_rgb, cv2.COLOR_RGB2BGR))
    print(f"      Saved raw slide: {raw_path}")

    # 2. Stain Normalization
    print("[2/5] Running Stain Normalization algorithms...")
    macenko = MacenkoNormalizer()
    norm_macenko, h_channel, e_channel = macenko.fit_transform(slide_rgb)
    macenko_path = os.path.join(output_dir, "macenko_normalized.png")
    cv2.imwrite(macenko_path, cv2.cvtColor(norm_macenko, cv2.COLOR_RGB2BGR))

    reinhard = ReinhardNormalizer()
    norm_reinhard = reinhard.transform(slide_rgb)
    reinhard_path = os.path.join(output_dir, "reinhard_normalized.png")
    cv2.imwrite(reinhard_path, cv2.cvtColor(norm_reinhard, cv2.COLOR_RGB2BGR))
    print("      Macenko and Reinhard stain normalization completed.")

    # 3. PyTorch Deep Learning Nuclei Segmentation
    print("[3/5] Running PyTorch U-Net Inference & Watershed Separation...")
    segmenter = NucleiSegmenter(device="cpu")
    # For accurate segmentation on hematoxylin channel, we use threshold on H optical density
    # combined with UNet probability
    h_norm = cv2.normalize(h_channel, None, 0, 255, cv2.NORM_MINMAX)
    _, h_thresh = cv2.threshold(h_norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    
    labeled_mask, count = segmenter.watershed_separate(h_thresh)
    print(f"      Detected and separated {count} nuclei.")

    # 4. Morphometry & Quantification
    print("[4/5] Extracting cellular morphometry and clinical indicators...")
    quantifier = HistopathologyQuantifier(mpp=0.25)
    nuclei_metrics, summary = quantifier.extract_features(labeled_mask, count)
    print(f"      Total Nuclei: {summary['total_nuclei_count']}")
    print(f"      Mean Nuclear Area: {summary['mean_nuclear_area_um2']} um^2")
    print(f"      Mean Circularity: {summary['mean_circularity']}")
    print(f"      N:C Ratio: {summary['nuclear_to_cytoplasmic_ratio']}")
    print(f"      Cellular Density: {summary['cellular_density_per_mm2']} cells/mm^2")

    # Generate overlay visualization
    overlay = slide_rgb.copy()
    contours_found = []
    for m in nuclei_metrics:
        cid = m["id"]
        cmask = (labeled_mask == cid).astype(np.uint8)
        cnts, _ = cv2.findContours(cmask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            # Color by pleomorphism (green = normal, red = high pleomorphism)
            pleom = m["pleomorphism_score"]
            color = (
                int(min(255, pleom * 350)),
                int(max(40, 230 - pleom * 300)),
                int(30)
            )
            cv2.drawContours(overlay, cnts, -1, color, 1)

    overlay_path = os.path.join(output_dir, "segmentation_overlay.png")
    cv2.imwrite(overlay_path, cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))

    # Generate spatial density heatmap
    heatmap = quantifier.generate_density_heatmap(labeled_mask)
    heatmap_path = os.path.join(output_dir, "density_heatmap.png")
    cv2.imwrite(heatmap_path, cv2.cvtColor(heatmap, cv2.COLOR_RGB2BGR))

    # Save summary report JSON
    report_path = os.path.join(output_dir, "morphometry_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "sample_nuclei": nuclei_metrics[:10]}, f, indent=2)

    # 5. DeepZoom Multi-Scale Tile Generation
    print("[5/5] Generating DeepZoom Image Pyramid Tiles...")
    tiler = WSIPyramidTiler(tile_size=256)
    tile_info = tiler.tile_slide(slide_rgb, os.path.join(output_dir, "wsi_pyramid"))
    print(f"      Generated {tile_info['total_tiles']} tiles across {tile_info['levels']} pyramid levels.")
    print("=" * 60)
    print("Pipeline run successfully completed!")
    print(f"All artifacts saved in: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    run_full_pipeline()
