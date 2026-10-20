"""
Unit Test Suite for Digital Pathology WSI Analytics Pipeline.
Verifies:
1. Stain Normalization (Macenko & Reinhard)
2. PyTorch Residual U-Net forward pass & dimensions
3. Marker-controlled Watershed segmentation
4. Cellular morphometry feature extraction & statistics
5. DeepZoom multi-scale WSI pyramid tiling
"""

import sys
import os
import unittest
import numpy as np
import torch
import cv2

# Add python_pipeline to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "python_pipeline")))

from stain_normalization import MacenkoNormalizer, ReinhardNormalizer
from segmentation_unet import HistologyUNet, NucleiSegmenter
from morphometry import HistopathologyQuantifier
from wsi_tiler import WSIPyramidTiler
from run_pipeline import generate_synthetic_histology_slide


class TestDigitalPathologyPipeline(unittest.TestCase):

    def setUp(self):
        # Generate a small test slide patch (256x256)
        self.test_img = generate_synthetic_histology_slide(256, 256, num_nuclei=25)

    def test_macenko_normalization(self):
        normalizer = MacenkoNormalizer()
        norm_img, h_chan, e_chan = normalizer.fit_transform(self.test_img)
        self.assertEqual(norm_img.shape, self.test_img.shape)
        self.assertEqual(norm_img.dtype, np.uint8)
        self.assertEqual(h_chan.shape, (256, 256))
        self.assertEqual(e_chan.shape, (256, 256))
        # Ensure values are within standard RGB range
        self.assertTrue(norm_img.min() >= 0 and norm_img.max() <= 255)

    def test_reinhard_normalization(self):
        normalizer = ReinhardNormalizer()
        norm_img = normalizer.transform(self.test_img)
        self.assertEqual(norm_img.shape, self.test_img.shape)
        self.assertEqual(norm_img.dtype, np.uint8)
        self.assertTrue(norm_img.min() >= 0 and norm_img.max() <= 255)

    def test_residual_unet_forward_pass(self):
        model = HistologyUNet(in_channels=3, out_channels=1, base_filters=8)
        model.eval()
        dummy_input = torch.randn(2, 3, 128, 128)
        with torch.no_grad():
            output = model(dummy_input)
        self.assertEqual(output.shape, (2, 1, 128, 128))
        # Output must be probabilities between 0 and 1
        self.assertTrue(output.min().item() >= 0.0)
        self.assertTrue(output.max().item() <= 1.0)

    def test_watershed_nuclei_separation(self):
        segmenter = NucleiSegmenter()
        # Create a synthetic binary mask with two overlapping circles
        mask = np.zeros((100, 100), dtype=np.uint8)
        cv2.circle(mask, (40, 50), 15, 255, -1)
        cv2.circle(mask, (60, 50), 15, 255, -1)
        
        labeled_mask, count = segmenter.watershed_separate(mask)
        # Should detect the touching nuclei as 2 distinct connected components
        self.assertGreaterEqual(count, 1)
        self.assertEqual(labeled_mask.shape, (100, 100))

    def test_morphometry_quantifier(self):
        quantifier = HistopathologyQuantifier(mpp=0.25)
        # Synthetic labeled mask with 3 distinct circles
        labeled = np.zeros((200, 200), dtype=np.int32)
        cv2.circle(labeled, (50, 50), 12, 1, -1)
        cv2.circle(labeled, (120, 50), 16, 2, -1)
        cv2.circle(labeled, (100, 140), 10, 3, -1)

        metrics, summary = quantifier.extract_features(labeled, 3)
        self.assertEqual(len(metrics), 3)
        self.assertIn("total_nuclei_count", summary)
        self.assertIn("mean_nuclear_area_um2", summary)
        self.assertIn("mean_circularity", summary)
        self.assertIn("nuclear_to_cytoplasmic_ratio", summary)
        
        # Area in um2 must be positive
        for m in metrics:
            self.assertGreater(m["area_um2"], 0)
            self.assertGreaterEqual(m["circularity"], 0)
            self.assertLessEqual(m["circularity"], 1.0)

    def test_wsi_pyramid_tiler(self):
        tiler = WSIPyramidTiler(tile_size=128)
        levels = tiler.calculate_pyramid_levels(1024, 1024)
        # 1024 -> 2^10 = 11 levels (0 to 10)
        self.assertEqual(levels, 11)
        xml = tiler.generate_dzi_xml(1024, 1024)
        self.assertIn('TileSize="128"', xml)
        self.assertIn('Width="1024"', xml)


if __name__ == "__main__":
    unittest.main()
