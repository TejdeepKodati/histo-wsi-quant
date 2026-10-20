# HistoWSI Quant: High-Resolution Digital Pathology WSI Analytics & Nuclei Morphometry Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![PyTorch](https://img.shields.io/badge/PyTorch-2.0+-red.svg)](https://pytorch.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-5.0+-green.svg)](https://opencv.org/)

An enterprise-grade, end-to-end digital pathology image analysis platform designed for processing ultra-high-resolution Whole Slide Images (WSI, up to ~50K x 50K pixels). The system implements stain normalization (Macenko SVD & Reinhard CIELab), deep learning-based nuclei segmentation (Residual U-Net in PyTorch), marker-controlled watershed overlap separation, clinical morphometric quantification, and multi-scale DeepZoom pyramid tile streaming.

---

## Key Engineering Capabilities

1. **Stain Normalization**:
   - **Macenko Optical Density Method**: Decomposes stained tissue into optical density (OD) space via $-\log_{10}((I + 1)/255)$, uses Singular Value Decomposition (SVD) on the OD covariance matrix to extract plane eigenvectors, identifies extreme angular percentiles for Hematoxylin and Eosin stain vectors, deconvolves stain concentration matrices, and standardizes to calibrated reference vectors.
   - **Reinhard Color Transfer**: Statistical alignment of luminance ($L$) and chrominance ($a, b$) channels in CIELab space to eliminate laboratory-to-laboratory staining variance.

2. **Deep Learning Nuclei Segmentation**:
   - PyTorch implementation of **Residual U-Net** featuring multi-scale encoder-decoder pathways, residual convolutional skip blocks, batch normalization, and probability map generation.
   - Hybrid post-processing combining Euclidean distance transform and marker-controlled watershed to resolve tightly clustered and touching cellular nuclei.

3. **Quantitative Cellular Morphometry & Biomarkers**:
   - Extraction of geometric descriptors per cell: Area ($\mu\text{m}^2$), Perimeter, Circularity ($4\pi \cdot \text{Area} / \text{Perimeter}^2$), Aspect Ratio, and Convexity Solidity.
   - Clinical tissue-level metrics: Nuclear-to-Cytoplasmic (N:C) biomass ratio, spatial cellular density ($\text{cells/mm}^2$), pleomorphism variance score, and 2D kernel density heatmaps.

4. **Multi-Scale DeepZoom (DZI) WSI Tiler**:
   - High-throughput tiling engine generating $256 \times 256$ multi-resolution image pyramids across 11 downsampling mipmap levels with XML metadata descriptors for real-time virtual microscopy pan/zoom.

5. **Interactive Full-Stack Web Platform**:
   - Responsive Next.js 14 web application featuring an interactive virtual microscope viewport, real-time micron scale bar, cursor coordinate tracker, layer switcher (raw, normalized, segmentation mask, heatmap), and clinical JSON report export.

---

## Directory Structure

```text
histo-wsi-quant/
├── python_pipeline/
│   ├── stain_normalization.py   # Macenko SVD & Reinhard Lab normalizers
│   ├── segmentation_unet.py     # PyTorch Residual U-Net & Watershed separation
│   ├── morphometry.py           # Cellular morphometry & biomarker quantifier
│   ├── wsi_tiler.py             # DeepZoom pyramid generator for gigapixel WSI
│   ├── api.py                   # FastAPI REST backend for inference & analytics
│   └── run_pipeline.py          # End-to-end CLI demonstration pipeline
├── tests/
│   └── test_patho_pipeline.py   # Comprehensive unit test suite
├── app/
│   ├── layout.tsx               # Next.js root layout with branding
│   ├── page.tsx                 # Main pathology workstation application
│   └── globals.css              # Styling & themes
├── components/
│   ├── WSIViewer.tsx            # Interactive virtual slide pan/zoom canvas
│   ├── MorphometryDashboard.tsx # Biomarker cards & distribution charts
│   ├── StainPanel.tsx           # Layer switcher for normalizations & overlays
│   ├── NucleiTable.tsx          # Interactive table of segmented nuclei
│   └── ExportModal.tsx          # Clinical report export modal
├── lib/
│   ├── types.ts                 # TypeScript interfaces
│   └── slideCatalog.json        # Precomputed high-resolution slide database
├── public/
│   └── slides/                  # High-resolution tissue patches & overlays
├── requirements.txt             # Python dependencies
├── package.json                 # Node.js dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher
- **npm** or **yarn**

---

### 1. Python Pipeline Setup & Execution

#### Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### Run Unit Tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```
All unit tests verify:
- SVD optical density matrix decomposition and deconvolution
- CIELab Reinhard color transfer
- PyTorch Residual U-Net forward pass and tensor dimensions
- Marker-controlled Watershed touching-nuclei separation
- Morphometric feature extraction and unit conversions
- DeepZoom XML descriptor generation and mipmap pyramid calculation

#### Run the End-to-End Pipeline:
```bash
cd python_pipeline
python run_pipeline.py
```
This executes the full pipeline:
- Synthesizes an ultra-high-resolution $1024 \times 1024$ H&E histopathology specimen.
- Applies Macenko and Reinhard stain normalizations.
- Performs PyTorch U-Net inference and Watershed segmentation.
- Quantifies nuclear features and computes clinical summary metrics.
- Generates 29 DeepZoom pyramid tiles across 11 levels and saves all outputs to `output_results/`.

#### Run the FastAPI REST Backend:
```bash
cd python_pipeline
uvicorn api:app --reload --port 8000
```
Open `http://localhost:8000/docs` to inspect the Swagger API documentation.

---

### 2. Next.js Web Application Setup & Execution

#### Install Node dependencies:
```bash
npm install
```

#### Run the local development server:
```bash
npm run dev
```
Open `http://localhost:3000` in your web browser.

#### Build for production:
```bash
npm run build
npm start
```

---

## Mathematical Formulation

### Macenko Optical Density Decomposition
Given an RGB image pixel $I = [R, G, B]^T$, its optical density vector is calculated as:
$$\text{OD} = -\log_{10}\left(\frac{I + 1}{255}\right)$$
For pixels exceeding background threshold $\beta$, singular value decomposition (SVD) on the covariance of $\text{OD}$ identifies the plane spanned by the two largest eigenvectors $\mathbf{v}_1, \mathbf{v}_2$. Projecting $\text{OD}$ values onto this plane:
$$\mathbf{T} = \mathbf{OD} \cdot [\mathbf{v}_1, \mathbf{v}_2]^T$$
Angular coordinates $\phi = \arctan2(T_y, T_x)$ at the 1st and 99th percentiles establish the Hematoxylin and Eosin stain vectors $\mathbf{V}_{\text{HE}} \in \mathbb{R}^{3 \times 2}$. Stain concentration matrix $\mathbf{C}$ is solved via linear least squares:
$$\mathbf{C} = (\mathbf{V}_{\text{HE}}^T \mathbf{V}_{\text{HE}})^{-1} \mathbf{V}_{\text{HE}}^T \mathbf{OD}^T$$

---

## License

MIT License. Designed and built with high engineering rigor.
