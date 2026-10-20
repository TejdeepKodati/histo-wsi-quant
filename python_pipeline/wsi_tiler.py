"""
Multi-Scale DeepZoom Pyramid Tiler for High-Resolution Whole-Slide Images (WSI).
Enables tiling and streaming of gigapixel histopathology slides (e.g. 50K x 50K)
into standardized 256x256 image pyramids.
"""

import os
import math
import numpy as np
import cv2
from typing import List, Dict, Any, Tuple


class WSIPyramidTiler:
    """
    Splits ultra-high-resolution images into multi-resolution pyramids (DeepZoom specification).
    Allows interactive pan/zoom viewing and patch-based deep learning inference.
    """
    def __init__(self, tile_size: int = 256, overlap: int = 0, format_ext: str = "png"):
        self.tile_size = tile_size
        self.overlap = overlap
        self.format_ext = format_ext

    def calculate_pyramid_levels(self, width: int, height: int) -> int:
        """Computes the number of downsampling levels required to reach 1x1 base."""
        max_dim = max(width, height)
        return int(math.ceil(math.log2(max_dim))) + 1

    def generate_dzi_xml(self, width: int, height: int) -> str:
        """Returns standard DeepZoom Image (DZI) descriptor XML."""
        return (
            f'<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<Image xmlns="http://schemas.microsoft.com/deepzoom/2008"\n'
            f'  Format="{self.format_ext}"\n'
            f'  Overlap="{self.overlap}"\n'
            f'  TileSize="{self.tile_size}">\n'
            f'  <Size Width="{width}" Height="{height}"/>\n'
            f'</Image>'
        )

    def tile_slide(self, img_rgb: np.ndarray, output_dir: str) -> Dict[str, Any]:
        """
        Generates full pyramid tiles for the given slide image.
        Outputs tiles to: {output_dir}/{level}/{col}_{row}.{format_ext}
        """
        os.makedirs(output_dir, exist_ok=True)
        h, w = img_rgb.shape[:2]
        num_levels = self.calculate_pyramid_levels(w, h)

        # Write DZI metadata descriptor
        dzi_path = os.path.join(output_dir, "slide.dzi")
        with open(dzi_path, "w", encoding="utf-8") as f:
            f.write(self.generate_dzi_xml(w, h))

        tiles_dir = os.path.join(output_dir, "slide_files")
        os.makedirs(tiles_dir, exist_ok=True)

        current_img = img_rgb.copy()
        current_w, current_h = w, h
        tile_manifest: List[Dict[str, Any]] = []

        # Iterate from highest resolution (level = num_levels - 1) down to level 0
        for level in range(num_levels - 1, -1, -1):
            level_dir = os.path.join(tiles_dir, str(level))
            os.makedirs(level_dir, exist_ok=True)

            cols = int(math.ceil(current_w / self.tile_size))
            rows = int(math.ceil(current_h / self.tile_size))

            for r in range(rows):
                for c in range(cols):
                    # Compute bounds with overlap
                    y1 = max(0, r * self.tile_size - self.overlap)
                    y2 = min(current_h, (r + 1) * self.tile_size + self.overlap)
                    x1 = max(0, c * self.tile_size - self.overlap)
                    x2 = min(current_w, (c + 1) * self.tile_size + self.overlap)

                    tile = current_img[y1:y2, x1:x2]
                    tile_filename = f"{c}_{r}.{self.format_ext}"
                    tile_path = os.path.join(level_dir, tile_filename)

                    # Save tile (RGB to BGR for cv2.imwrite)
                    cv2.imwrite(tile_path, cv2.cvtColor(tile, cv2.COLOR_RGB2BGR))

                    tile_manifest.append({
                        "level": level,
                        "col": c,
                        "row": r,
                        "width": tile.shape[1],
                        "height": tile.shape[0],
                        "rel_path": f"{level}/{tile_filename}"
                    })

            # Downsample by factor of 2 for next lower level
            if current_w > 1 or current_h > 1:
                next_w = max(1, current_w // 2)
                next_h = max(1, current_h // 2)
                current_img = cv2.resize(current_img, (next_w, next_h), interpolation=cv2.INTER_AREA)
                current_w, current_h = next_w, next_h

        return {
            "slide_width": w,
            "slide_height": h,
            "levels": num_levels,
            "tile_size": self.tile_size,
            "total_tiles": len(tile_manifest),
            "dzi_path": dzi_path
        }

    def extract_patch(self, img_rgb: np.ndarray, x: int, y: int, size: int = 512) -> np.ndarray:
        """Extracts a high-magnification region of interest with edge boundary clamping."""
        h, w = img_rgb.shape[:2]
        x1 = max(0, min(x, w - size))
        y1 = max(0, min(y, h - size))
        x2 = min(w, x1 + size)
        y2 = min(h, y1 + size)
        return img_rgb[y1:y2, x1:x2]
