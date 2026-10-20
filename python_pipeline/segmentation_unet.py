"""
PyTorch Deep Learning Nuclei Segmentation Model with Residual U-Net Architecture
and Watershed Overlap Separation Post-Processing.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
import cv2
from scipy import ndimage


class ResidualBlock(nn.Module):
    """Residual Convolutional Block with Skip Connection"""
    def __init__(self, in_channels: int, out_channels: int):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_channels)

        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, bias=False),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.shortcut = nn.Identity()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        res = self.shortcut(x)
        out = self.relu(self.bn1(self.conv1(x)))
        out = self.bn2(self.conv2(out))
        out = self.relu(out + res)
        return out


class HistologyUNet(nn.Module):
    """
    Residual U-Net Architecture optimized for histopathology nuclei segmentation.
    Includes multi-scale encoder-decoder with skip connections.
    """
    def __init__(self, in_channels: int = 3, out_channels: int = 1, base_filters: int = 16):
        super().__init__()
        bf = base_filters
        
        # Encoder
        self.enc1 = ResidualBlock(in_channels, bf)
        self.pool1 = nn.MaxPool2d(2, 2)

        self.enc2 = ResidualBlock(bf, bf * 2)
        self.pool2 = nn.MaxPool2d(2, 2)

        self.enc3 = ResidualBlock(bf * 2, bf * 4)
        self.pool3 = nn.MaxPool2d(2, 2)

        # Bottleneck
        self.bottleneck = ResidualBlock(bf * 4, bf * 8)

        # Decoder
        self.up3 = nn.ConvTranspose2d(bf * 8, bf * 4, kernel_size=2, stride=2)
        self.dec3 = ResidualBlock(bf * 8, bf * 4)

        self.up2 = nn.ConvTranspose2d(bf * 4, bf * 2, kernel_size=2, stride=2)
        self.dec2 = ResidualBlock(bf * 4, bf * 2)

        self.up1 = nn.ConvTranspose2d(bf * 2, bf, kernel_size=2, stride=2)
        self.dec1 = ResidualBlock(bf * 2, bf)

        # Output head
        self.out_conv = nn.Conv2d(bf, out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Encoder path
        e1 = self.enc1(x)
        p1 = self.pool1(e1)

        e2 = self.enc2(p1)
        p2 = self.pool2(e2)

        e3 = self.enc3(p2)
        p3 = self.pool3(e3)

        # Bottleneck
        b = self.bottleneck(p3)

        # Decoder path with skip connections
        d3 = self.up3(b)
        d3 = torch.cat([d3, e3], dim=1)
        d3 = self.dec3(d3)

        d2 = self.up2(d3)
        d2 = torch.cat([d2, e2], dim=1)
        d2 = self.dec2(d2)

        d1 = self.up1(d2)
        d1 = torch.cat([d1, e1], dim=1)
        d1 = self.dec1(d1)

        logits = self.out_conv(d1)
        probs = torch.sigmoid(logits)
        return probs


class NucleiSegmenter:
    """
    High-level segmenter combining PyTorch inference with
    marker-controlled Watershed for overlapping nuclei separation.
    """
    def __init__(self, device: str = "cpu"):
        self.device = torch.device(device)
        self.model = HistologyUNet().to(self.device)
        self.model.eval()

    def predict_mask(self, img_rgb: np.ndarray, prob_threshold: float = 0.5) -> np.ndarray:
        """
        Runs model inference on an input RGB image patch (H, W, 3).
        """
        h, w = img_rgb.shape[:2]
        # Pad to multiple of 8 if needed
        pad_h = (8 - h % 8) % 8
        pad_w = (8 - w % 8) % 8
        if pad_h > 0 or pad_w > 0:
            img_padded = cv2.copyMakeBorder(img_rgb, 0, pad_h, 0, pad_w, cv2.BORDER_REFLECT)
        else:
            img_padded = img_rgb

        # Preprocess: float32 normalized [0, 1]
        tensor = torch.from_numpy(img_padded).permute(2, 0, 1).float() / 255.0
        # Normalize with ImageNet / histology standard
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        tensor = (tensor - mean) / std
        tensor = tensor.unsqueeze(0).to(self.device)

        with torch.no_grad():
            prob_map = self.model(tensor).squeeze().cpu().numpy()

        if pad_h > 0 or pad_w > 0:
            prob_map = prob_map[:h, :w]

        binary_mask = (prob_map >= prob_threshold).astype(np.uint8)
        return binary_mask, prob_map

    def watershed_separate(self, binary_mask: np.ndarray, min_distance: int = 5) -> tuple[np.ndarray, int]:
        """
        Separates touching nuclei using Euclidean distance transform and watershed algorithm.
        Returns:
            labeled_mask: 2D array where each nucleus has a unique integer ID (1..N)
            num_nuclei: Total count of detected nuclei
        """
        # Morphological opening to remove noise
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        opening = cv2.morphologyEx(binary_mask, cv2.MORPH_OPEN, kernel, iterations=1)

        # Sure background area via dilation
        sure_bg = cv2.dilate(opening, kernel, iterations=2)

        # Sure foreground area via distance transform
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        # Threshold at 35% of max distance
        ret, sure_fg = cv2.threshold(dist_transform, 0.35 * dist_transform.max() if dist_transform.max() > 0 else 0, 255, 0)
        sure_fg = np.uint8(sure_fg)

        # Unknown boundary region
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labelling
        ret, markers = cv2.connectedComponents(sure_fg)
        # Add 1 to all labels so sure background is 1, not 0
        markers = markers + 1
        # Mark unknown region as 0
        markers[unknown == 255] = 0

        # Run watershed
        dummy_bgr = np.zeros((*binary_mask.shape, 3), dtype=np.uint8)
        dummy_bgr[binary_mask > 0] = 255
        markers = cv2.watershed(dummy_bgr, markers)

        # Post-clean: background is <= 1, boundaries are -1
        labeled_mask = np.zeros_like(markers, dtype=np.int32)
        unique_labels = np.unique(markers)
        current_id = 1
        for lbl in unique_labels:
            if lbl > 1:  # 1 is background, -1 is watershed boundary
                mask_lbl = (markers == lbl)
                if np.sum(mask_lbl) >= 8:  # filter artifacts < 8 pixels
                    labeled_mask[mask_lbl] = current_id
                    current_id += 1

        num_nuclei = current_id - 1
        return labeled_mask, num_nuclei
