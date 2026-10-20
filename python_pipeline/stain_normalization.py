"""
Stain Normalization Module for Digital Pathology.
Implements:
1. Macenko Optical Density Decomposition via SVD
2. Reinhard Color Transfer in CIELab space
"""

import numpy as np
import cv2

class MacenkoNormalizer:
    """
    Stain normalization using the Macenko method (Macenko et al., 2009).
    Decomposes H&E images into Hematoxylin and Eosin stain vectors in optical density space.
    """
    def __init__(self, alpha: float = 1.0, beta: float = 0.15):
        self.alpha = alpha  # Angular percentile tolerance (default 1.0%)
        self.beta = beta    # Optical density threshold for transparent background
        # Default reference stain vectors (OD space) and reference concentrations
        self.HERef = np.array([
            [0.5626, 0.2159],
            [0.7201, 0.8012],
            [0.4062, 0.5581]
        ])
        self.maxCRef = np.array([1.9705, 1.0308])

    def fit_transform(self, img_rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Normalizes an input RGB image to reference H&E stains.
        Returns:
            normalized_img: uint8 RGB image
            H_channel: uint8 Hematoxylin intensity channel
            E_channel: uint8 Eosin intensity channel
        """
        h, w, c = img_rgb.shape
        img = img_rgb.astype(np.float64)

        # 1. Convert to Optical Density (OD = -log10((I + 1) / 255))
        OD = -np.log10((img + 1.0) / 255.0)
        OD_flat = OD.reshape((-1, 3))

        # 2. Filter transparent pixels below beta
        mask = (OD_flat > self.beta).any(axis=1)
        OD_hat = OD_flat[mask]

        if len(OD_hat) < 10:
            # Fallback for empty or near-empty patches
            return img_rgb, np.zeros((h, w), dtype=np.uint8), np.zeros((h, w), dtype=np.uint8)

        # 3. Compute eigenvectors of OD covariance matrix (using SVD)
        _, _, V = np.linalg.svd(OD_hat, full_matrices=False)
        # Two vectors corresponding to the two largest eigenvalues
        # V has shape (3, 3) where rows are right singular vectors
        T_hat = OD_hat @ V[:2].T

        # 4. Project on plane and calculate angles
        phi = np.arctan2(T_hat[:, 1], T_hat[:, 0])

        min_phi = np.percentile(phi, self.alpha)
        max_phi = np.percentile(phi, 100.0 - self.alpha)

        v_min = V[:2].T @ np.array([np.cos(min_phi), np.sin(min_phi)])
        v_max = V[:2].T @ np.array([np.cos(max_phi), np.sin(max_phi)])

        # Ensure first vector is Hematoxylin (higher in red absorption / channel 0)
        if v_min[0] > v_max[0]:
            HE = np.array([v_min, v_max]).T
        else:
            HE = np.array([v_max, v_min]).T

        # 5. Determine concentrations: C = (HE^+)*OD
        # Least squares solve: HE * C = OD^T -> C = pinv(HE) * OD^T
        C = np.linalg.lstsq(HE, OD_flat.T, rcond=None)[0]

        # Normalize concentrations with reference maximums
        maxC = np.percentile(C, 99.0, axis=1)
        maxC[maxC == 0] = 1e-5
        C_norm = C / maxC[:, None] * self.maxCRef[:, None]

        # 6. Reconstruct normalized image
        OD_norm = self.HERef @ C_norm
        img_norm = 255.0 * np.exp(-OD_norm * np.log(10.0))
        img_norm = np.clip(img_norm, 0, 255).T.reshape((h, w, 3)).astype(np.uint8)

        # Separate H & E optical density components
        H_comp = np.clip(255.0 * np.exp(-(self.HERef[:, :1] @ C_norm[:1, :]) * np.log(10.0)), 0, 255)
        H_channel = H_comp.T.reshape((h, w, 3)).mean(axis=2).astype(np.uint8)

        E_comp = np.clip(255.0 * np.exp(-(self.HERef[:, 1:] @ C_norm[1:, :]) * np.log(10.0)), 0, 255)
        E_channel = E_comp.T.reshape((h, w, 3)).mean(axis=2).astype(np.uint8)

        return img_norm, H_channel, E_channel


class ReinhardNormalizer:
    """
    Stain normalization using Reinhard method in CIELab color space.
    Aligns the mean and standard deviation of L, a, b channels to target reference.
    """
    def __init__(self):
        # Reference mean and std in Lab space typical for clinical H&E
        self.target_mean = np.array([148.5, 148.2, 115.1])
        self.target_std = np.array([32.4, 18.3, 14.2])

    def transform(self, img_rgb: np.ndarray) -> np.ndarray:
        """
        Normalizes input RGB image using Reinhard color transfer.
        """
        # Convert RGB to Lab (via OpenCV)
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB).astype(np.float64)
        
        # Calculate source mean and std per channel
        src_mean = np.mean(lab, axis=(0, 1))
        src_std = np.std(lab, axis=(0, 1))
        src_std[src_std == 0] = 1e-5

        # Normalize and align to target distribution
        norm_lab = np.zeros_like(lab)
        for i in range(3):
            norm_lab[:, :, i] = ((lab[:, :, i] - src_mean[i]) / src_std[i]) * self.target_std[i] + self.target_mean[i]

        norm_lab = np.clip(norm_lab, 0, 255).astype(np.uint8)
        norm_rgb = cv2.cvtColor(norm_lab, cv2.COLOR_LAB2RGB)
        return norm_rgb
