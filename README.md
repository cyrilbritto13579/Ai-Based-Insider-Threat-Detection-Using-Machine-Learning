# Explainable AI-Based Insider Threat Detection with Dynamic Risk Scoring Using Machine Learning (V2)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-cyan.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org/)
[![Dataset](https://img.shields.io/badge/Dataset-CERT%20Release%204.2-orange.svg)](https://resources.sei.cmu.edu/library/asset-view.cfm?assetid=508099)

> **B.Tech Major Project** — A full-stack, enterprise-grade Security Operations Center (SOC) platform for real-time insider threat detection combining multi-source activity correlation, user-specific behavioral baselines, tree-based ML classification, 0–100 dynamic risk scoring, and exact local SHAP explainability.

---

## 🛡️ Key Features

1. **CERT Release 4.2 Research Pipeline**: Ingests and correlates **4,335,799 raw activity events** across `logon.csv`, `device.csv`, `file.csv`, and `email.csv` spanning 16 months and 1,000 enterprise users.
2. **Behavioral Feature Engineering & User Baselines**: 58 behavioral features including expanding-window historical user baselines to capture individual deviations without future information leakage.
3. **Temporal Model Benchmark**: Evaluates **Logistic Regression**, **Random Forest**, and **XGBoost** under strict temporal train (209k), validation (56k), and test (65k) splits. Objective selection based on PR-AUC.
4. **Dynamic Multi-Signal Risk Engine**: Computes a 0–100 risk score combining ML classification probability, baseline deviation standard deviations, and cross-source after-hours exfiltration heuristics into 4 tiers (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
5. **Explainable AI (SHAP TreeExplainer)**: Computes local Shapley values for individual security events and synthesizes defensive, non-accusatory security rationales.
6. **Live Synthetic Event Simulator (TechNova)**: 6 realistic demonstration scenarios (Normal Employee, After-Hours, Unusual Device, Unusual File, Suspicious Data Collection, Multi-Signal Anomaly) passing directly through SQLite and the live detection pipeline.
7. **Professional SOC Dashboard**: React + TypeScript + Vite + Tailwind CSS dark-mode interface with 8 comprehensive operational views.
8. **Real-time WebSockets**: Instant event streaming and dynamic risk updates without page refresh.

---

## 🏗️ System Architecture

```text
       ┌────────────────────────────────────────────────────────┐
       │             CERT Release 4.2 Raw Event Logs            │
       │       logon.csv  device.csv  file.csv  email.csv       │
       └───────────────────────────┬────────────────────────────┘
                                   │
                     Chunked Ingestion & Normalization
                                   │
                   User-Day Multi-Source Aggregation
                                   │
            Expanding-Window Behavioral Baseline Deviations
                                   │
                 Temporal Split (Train / Val / Test)
                                   │
        ┌──────────────────────────┴────────────────────────────┐
        │  Model Experiments: LR vs Random Forest vs XGBoost   │
        └──────────────────────────┬────────────────────────────┘
                                   │ (XGBoost Selected: PR-AUC 0.525)
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FASTAPI BACKEND                                 │
│                                                                             │
│  ┌───────────────────────┐  ┌──────────────────────┐  ┌──────────────────┐  │
│  │ SQLite Database & ORM │  │  XGBoost ML Pipeline │  │ SHAP Explainer   │  │
│  │ (Users, Events, Risk) │  │  (Online Inference)  │  │ (TreeExplainer)  │  │
│  └───────────▲───────────┘  └──────────▲───────────┘  └────────▲─────────┘  │
│              │                         │                       │            │
│              └─────────────────────────┼───────────────────────┘            │
│                                        │                                    │
│                             ┌──────────┴──────────┐                         │
│                             │ Dynamic Risk Engine │                         │
│                             │   (0–100 Score)     │                         │
│                             └──────────┬──────────┘                         │
│                                        │                                    │
│                             ┌──────────┴──────────┐                         │
│                             │    Alert Engine     │                         │
│                             │   (Triage System)   │                         │
│                             └──────────┬──────────┘                         │
│                                        │                                    │
│                             ┌──────────┴──────────┐                         │
│                             │ WebSocket Broadcast │                         │
│                             └──────────┬──────────┘                         │
└────────────────────────────────────────┼────────────────────────────────────┘
                                         │ ws://127.0.0.1:8000/ws/live
                                         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 REACT + TYPESCRIPT SOC DASHBOARD (8 PAGES)                  │
│                                                                             │
│  1. Overview           3. User Investigation   5. Analytics & XAI 7. Simulator│
│  2. Alerts Triage      4. Live Telemetry       6. Model Benchmark 8. Settings │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Model Evaluation Results (CERT r4.2 Test Set)

| Model | PR-AUC | F1-Score | Recall | Precision | ROC-AUC | Optimal Threshold |
|---|---|---|---|---|---|---|
| **XGBoost (Tuned)** | **0.5236** | **0.5425** | **0.5747** | **0.5137** | **0.9832** | **0.1184** |
| Random Forest | 0.3585 | 0.4241 | 0.6062 | 0.3262 | 0.9758 | 0.5752 |
| Logistic Regression | 0.0616 | 0.1393 | 0.4092 | 0.0840 | 0.8680 | 0.8682 |

*Evaluated on 65,031 held-out temporal user-days with 268:1 class imbalance (0.40% malicious).*

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Backend Setup & Run

```bash
# Navigate to project root
cd "d:\Insider threat detection v2"

# Install Python dependencies
pip install -r backend/requirements.txt

# Run automated test suite
pytest -v tests/

# Launch FastAPI backend server
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be available at: `http://127.0.0.1:8000/docs`

### 2. Frontend Setup & Run

```bash
# In a new terminal, navigate to frontend
cd "d:\Insider threat detection v2\frontend"

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
Dashboard will open at: `http://localhost:5173`

---

## 📂 Repository Directory Layout

```text
Insider-Threat-Detection-V2/
├── backend/
│   ├── app/
│   │   ├── api/             # REST & WebSocket endpoints
│   │   ├── core/            # Config, settings, and constants
│   │   ├── db/              # SQLAlchemy SQLite models & session
│   │   ├── ml/              # Inference, feature extraction, SHAP
│   │   ├── risk/            # 0-100 Dynamic Risk Engine & Alerting
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Event pipeline orchestrator
│   │   ├── simulation/      # TechNova enterprise & scenarios
│   │   └── main.py          # FastAPI app entry point
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/             # Typed API client
│   │   ├── components/      # Badges, Charts, Navbar, Sidebar
│   │   ├── pages/           # 8 required SOC operational views
│   │   ├── types.ts         # TypeScript schema definitions
│   │   └── App.tsx          # Main router and WebSocket coordinator
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── data/
│   ├── raw/                 # Immutable CERT r4.2 source CSVs
│   ├── processed/           # Labeled user-day parquet splits
│   └── artifacts/           # Model weights, SHAP, and schemas
├── scripts/
│   ├── validate_cert_data.py # Phase 2 dataset validation script
│   ├── build_features.py     # Phases 3-7 data & feature pipeline
│   └── train_models.py       # Phases 8-9 training & evaluation
├── tests/
│   ├── test_backend.py      # Unit test suite
│   └── test_e2e_api.py      # Integration test suite
└── docs/
    ├── ARCHITECTURE.md      # Full architecture specification
    ├── PROJECT_REPORT.md    # Formal academic B.Tech report
    └── VIVA_PREPARATION.md   # Comprehensive Viva Q&A guide
```

---

## ⚖️ Research vs Demonstration Data Boundaries

- **CERT Release 4.2**: Used strictly for offline model training, validation, temporal hyperparameter optimization, and empirical evaluation.
- **TechNova Synthetic Enterprise**: Used strictly for the live demonstration, dashboard telemetry, and interactive threat scenario injection.
- **Privacy Notice**: The system describes anomalies as *suspicious behavior requiring analyst investigation*, never accusing individuals.
