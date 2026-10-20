"""
FastAPI REST Service for Digital Pathology WSI Inference and Analysis.
Provides endpoints for stain normalization, nuclei segmentation, and morphometric analytics.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import numpy as np
import base64
import cv2
from stain_normalization import MacenkoNormalizer, ReinhardNormalizer
from segmentation_unet import NucleiSegmenter
from morphometry import HistopathologyQuantifier

app = FastAPI(
    title="HistoWSI Quantitative Analytics Engine",
    description="High-resolution digital pathology WSI analytics, stain normalization, and nuclei morphometry API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

macenko = MacenkoNormalizer()
reinhard = ReinhardNormalizer()
segmenter = NucleiSegmenter(device="cpu")
quantifier = HistopathologyQuantifier(mpp=0.25)


class ImageRequest(BaseModel):
    image_base64: str
    stain_method: str = "macenko"  # "macenko" or "reinhard"
    mpp: float = 0.25


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "HistoWSI Quantitative Analytics Engine",
        "device": "cpu",
        "algorithms": ["Macenko-SVD", "Reinhard-Lab", "Residual-UNet", "Marker-Controlled-Watershed"]
    }


@app.get("/demo-metrics")
def get_demo_metrics():
    return {
        "sample_id": "DX-BRCA-0482",
        "tissue_type": "Invasive Ductal Carcinoma (H&E 40x)",
        "total_nuclei": 218,
        "mean_nuclear_area_um2": 42.6,
        "std_nuclear_area_um2": 14.8,
        "mean_circularity": 0.812,
        "mean_solidity": 0.945,
        "nuclear_to_cytoplasmic_ratio": 0.384,
        "cellular_density_mm2": 872.0,
        "pleomorphism_grade": "Moderate (Grade II)"
    }


@app.post("/analyze")
def analyze_slide_patch(req: ImageRequest):
    try:
        # Decode base64 image
        header, encoded = req.image_base64.split(",", 1) if "," in req.image_base64 else ("", req.image_base64)
        img_bytes = base64.b64decode(encoded)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img_bgr = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise HTTPException(status_code=400, detail="Invalid image payload")
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # Stain normalization
        if req.stain_method == "macenko":
            norm_rgb, h_chan, _ = macenko.fit_transform(img_rgb)
        else:
            norm_rgb = reinhard.transform(img_rgb)
            h_chan = cv2.cvtColor(norm_rgb, cv2.COLOR_RGB2GRAY)

        # Watershed segmentation
        h_norm = cv2.normalize(h_chan, None, 0, 255, cv2.NORM_MINMAX)
        _, h_thresh = cv2.threshold(h_norm, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        labeled_mask, count = segmenter.watershed_separate(h_thresh)

        # Morphometry
        custom_quantifier = HistopathologyQuantifier(mpp=req.mpp)
        nuclei, summary = custom_quantifier.extract_features(labeled_mask, count)

        return {
            "status": "success",
            "summary": summary,
            "detected_nuclei_count": len(nuclei),
            "nuclei_sample": nuclei[:20]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
