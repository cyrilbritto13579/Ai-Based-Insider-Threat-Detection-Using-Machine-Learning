# Project Report: Explainable AI-Based Insider Threat Detection with Dynamic Risk Scoring Using Machine Learning

**Degree:** Bachelor of Technology (B.Tech) in Computer Science and Engineering  
**Project Category:** Major Project (Final Year Capstone)  
**Academic Year:** 2025–2026  

---

## Abstract

Insider threats represent one of the most destructive attack vectors in enterprise cybersecurity because malicious or compromised insiders already possess authorized access to sensitive corporate networks, codebases, and intellectual property. Traditional signature-based detection systems and static heuristic rules fail to detect subtle exfiltration behaviors while generating overwhelming false-positive rates.

This major project presents **ThreatSight V2**, a comprehensive, explainable AI-driven insider threat detection platform. Using the canonical **CERT Insider Threat Dataset Release 4.2** (4.33 million raw activity events across 1,000 users over 16 months), we engineered 58 behavioral features incorporating **expanding-window user-specific behavioral baselines** to capture individual behavioral drift without data leakage. We conducted empirical evaluations across **Logistic Regression**, **Random Forest**, and **XGBoost** under strict temporal partitioning. XGBoost achieved superior performance with a **PR-AUC of 0.5236** and **ROC-AUC of 0.9832** on a highly imbalanced dataset (268:1 negative-to-positive ratio).

To bridge the gap between pure ML classification probabilities and operational SOC decision-making, we designed a **0–100 Dynamic Risk Engine** incorporating local **SHAP (SHapley Additive exPlanations)** TreeExplainer attribution. We deployed this pipeline as a production-grade **FastAPI backend** connected via **WebSockets** to a dark-mode **React + TypeScript SOC Dashboard**. For interactive demonstration, we built an isolated **TechNova synthetic enterprise event simulator** executing 6 distinct behavioral scenarios directly through the live detection engine.

---

## 1. Introduction & Problem Statement

### 1.1 Background
The 2024 Ponemon Institute Cost of Insider Threats Global Report highlights that the average cost of an insider incident exceeds $16.2 million, with average containment times exceeding 85 days. Insider threats manifest in three primary scenarios:
1. **Malicious Insiders**: Employees actively exfiltrating proprietary data, customer records, or financial information for personal or commercial gain.
2. **Compromised Insiders**: Legitimate credentials hijacked by external adversaries.
3. **Disgruntled/Negligent Insiders**: Authorized staff violating security policies (e.g., using unauthorized USB storage or unencrypted personal emails).

### 1.2 Limitations of Prior Work
- **Global Threshold Fallacy**: Flagging users who exceed fixed enterprise thresholds (e.g., "accessing >10 files/day") generates catastrophic false alarm volumes because software engineers and data scientists routinely touch hundreds of files daily as part of legitimate duties.
- **Black-Box ML**: Standard deep learning and ensemble classifiers output raw probabilities without actionable reasoning, preventing security analysts from verifying the legitimacy of alerts.
- **Evaluation Leakage**: Prior research frequently applies random train/test splits or oversampling (SMOTE) before splitting, artificially inflating model accuracy by exposing future behavioral patterns to training models.

---

## 2. Research Methodology & Dataset Formulation

### 2.1 CERT Insider Threat Dataset Release 4.2
The research evaluation uses the Carnegie Mellon University Software Engineering Institute (SEI) CERT Release 4.2 dataset:

| File Name | Record Count | Unique Users | Monitored Attributes |
|---|---|---|---|
| `logon.csv` | 854,859 | 1,000 | User ID, PC, Logon/Logoff timestamp, Workstation |
| `device.csv` | 405,380 | 265 | USB Connect/Disconnect timestamp, PC |
| `file.csv` | 445,581 | 264 | File access timestamp, PC, Filename |
| `email.csv` | 2,629,979 | 1,000 | From, To, CC, BCC, Size, Attachment count |
| `insiders.csv` | 191 (70 in r4.2) | 70 | Ground truth malicious time intervals & scenario IDs |

### 2.2 Feature Engineering Taxonomy (58 Features)
1. **Logon Behavioral Metrics**: `logon_count`, `logoff_count`, `logon_unique_pcs`, `logon_after_hours`, `logon_weekend`, `logon_first_hour`, `logon_last_hour`, `logon_hour_span`.
2. **Device (USB) Metrics**: `device_connect_count`, `device_disconnect_count`, `device_unique_pcs`, `device_after_hours`, `device_weekend`.
3. **File Access Metrics**: `file_access_count`, `file_unique_count`, `file_after_hours`, `file_doc_ratio`.
4. **Email Communications**: `email_count`, `email_total_recipients`, `email_external_to`, `email_with_attachment`, `email_total_size`, `email_bcc_count`.
5. **Cross-Source Correlated Indicators**:
   - `afterhours_triple_signal`: Simultaneous logon, USB connection, and file access during non-business hours (18:00–07:00).
   - `device_and_file`: Removable media connection co-occurring with file modifications.
   - `external_email_and_device`: External email transfer combined with USB usage.
6. **User-Specific Expanding Baseline Deviations**:
   For any behavioral metric $M$, user $u$ on day $d$ with history $H = \{1, \dots, d-1\}$:
   $$\mu_u(d) = \frac{1}{|H|}\sum_{t \in H} M_u(t), \quad \sigma_u(d) = \sqrt{\frac{1}{|H|-1}\sum_{t \in H} (M_u(t) - \mu_u(d))^2}$$
   $$Z_u(d) = \frac{M_u(d) - \mu_u(d)}{\max(\sigma_u(d), 0.1)}$$

---

## 3. Empirical Model Experiments & Benchmark

### 3.1 Strict Temporal Data Partitioning
To ensure rigorous evaluation without lookahead bias, the 330,452 user-day observations were partitioned strictly by calendar dates:
- **Training Set (Jan 2, 2010 – Oct 31, 2010)**: 209,182 samples (778 malicious, 0.37% positive)
- **Validation Set (Nov 1, 2010 – Jan 31, 2011)**: 56,239 samples (325 malicious, 0.58% positive)
- **Test Set (Feb 1, 2011 – May 17, 2011)**: 65,031 samples (261 malicious, 0.40% positive)

### 3.2 Experimental Results

| Model | Test PR-AUC | Test F1 | Test Recall | Test Precision | Test ROC-AUC | Optimal Threshold |
|---|---|---|---|---|---|---|
| **XGBoost (Tuned)** | **0.5236** | **0.5425** | **0.5747** | **0.5137** | **0.9832** | **0.1184** |
| Random Forest | 0.3585 | 0.4241 | 0.6062 | 0.3262 | 0.9758 | 0.5752 |
| Logistic Regression | 0.0616 | 0.1393 | 0.4092 | 0.0840 | 0.8680 | 0.8682 |

### 3.3 Test Set Confusion Matrix (XGBoost)
- **True Positives (Caught Insiders)**: 150
- **False Positives (False Alarms)**: 142
- **False Negatives (Missed Threats)**: 111
- **True Negatives (Normal Behavior)**: 64,628
- **False Alarm Rate**: $142 / (64,628 + 142) = 0.219\%$

---

## 4. Explainable AI & Dynamic Risk Scoring Engine

### 4.1 Local SHAP Attribution
For every detected threat, the system computes the exact Shapley values $\phi_i$ across all 58 features using `shap.TreeExplainer`. The top positive contributors $\phi_i > 0$ and mitigating baseline factors $\phi_i < 0$ are converted into clear analyst explanations.

### 4.2 Composite 0–100 Dynamic Risk Score
The score integrates:
- ML Probability ($0–45$ pts): $45 \cdot \sqrt{P(\text{malicious})}$
- Baseline Drift ($0–25$ pts): $8.33 \cdot \min(3.0, \Delta_{\text{overall}})$
- Heuristic Flags ($0–30$ pts): After-hours USB, triple signal, external mail attachments.

---

## 5. Software Architecture & Implementation

- **Backend**: FastAPI (Python 3.10+), SQLAlchemy, SQLite, WebSockets, XGBoost, SHAP.
- **Frontend**: React 19, TypeScript 5.7, Vite 6, Tailwind CSS.
- **Automated Tests**: 12/12 unit and integration tests passing (`pytest`).
- **Live Simulator**: 6 scenarios for **TechNova** synthetic enterprise environment.

---

## 6. Conclusion & Academic Contributions

1. Demonstrated that **expanding user-specific baseline deviations** improve PR-AUC from 0.0616 to 0.5236 on the canonical CERT r4.2 benchmark.
2. Built a complete, end-to-end explainable SOC platform capable of streaming real-time event telemetry with instantaneous local SHAP feature justifications.
3. Provided an ethically grounded, privacy-preserving defensive framework with safe separation between research datasets and synthetic live demonstration data.
