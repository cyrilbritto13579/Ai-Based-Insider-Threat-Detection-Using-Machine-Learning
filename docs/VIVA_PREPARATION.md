# Comprehensive Viva Voce & Defense Preparation Guide

**Project Title:** Explainable AI-Based Insider Threat Detection with Dynamic Risk Scoring Using Machine Learning  
**Target:** External Examiner, Technical Review Committee, Capstone Evaluation  

---

## 🎯 Top 10 Core Viva Questions & Expert Answers

### Q1: What is the main research problem your major project solves?
**Answer:**  
Insider threats are notoriously difficult to detect because insiders possess legitimate privileges to access internal systems, making traditional perimeter security and static threshold rules ineffective. Static rules (like flagging anyone reading >100 files) generate massive false-positive rates because engineers legitimately process large volumes of code and data.  
Our project solves this by combining **user-specific behavioral baselines** (learning what is normal for each individual user) with **multi-source activity correlation**, **tree-based machine learning classification**, **0–100 dynamic risk scoring**, and **local SHAP explainability** to deliver actionable, verifiable threat detection in real time.

---

### Q2: What dataset did you use for training and evaluation? Is it real or synthetic?
**Answer:**  
We used the **CERT Insider Threat Dataset Release 4.2**, created by Carnegie Mellon University's Software Engineering Institute (SEI). It is the canonical academic benchmark for insider threat research.  
- It contains **4,335,799 raw activity events** across 1,000 employees over a 16-month period (Jan 2010 to May 2011).
- It comprises 4 log types: `logon.csv` (854k rows), `device.csv` (405k rows), `file.csv` (445k rows), and `email.csv` (2.63M rows).
- Ground truth is established in `insiders.csv`, containing 70 malicious users across 3 threat scenarios.
- For our **live dashboard demonstration**, we use an isolated synthetic company named **TechNova** to avoid privacy issues and allow safe, reproducible scenario injection.

---

### Q3: How did you handle the severe class imbalance in the dataset?
**Answer:**  
In CERT r4.2, malicious user-days account for only **1,364 out of 330,452 user-days (0.41% positive, or a 268:1 negative-to-positive ratio)**.  
1. **Metric Selection**: We prioritized **PR-AUC (Precision-Recall Area Under Curve)** and **F1-Score** over Accuracy and ROC-AUC, because Accuracy is deceptive when 99.6% of instances are negative.
2. **Model Weighting**: In XGBoost, we configured `scale_pos_weight = 267.9` (matching the exact negative-to-positive ratio in the training set). In Random Forest and Logistic Regression, we used `class_weight='balanced'`.
3. **Threshold Tuning**: Instead of the default 0.5 decision cutoff, we optimized the threshold to **0.1184** on the validation set to maximize the F1-Score on rare events.

---

### Q4: How did you prevent data leakage in your evaluation pipeline?
**Answer:**  
We implemented three strict anti-leakage safeguards:
1. **Strict Temporal Splitting**: We partitioned the 330k user-day observations strictly by date (Train: Jan–Oct 2010, Val: Nov 2010–Jan 2011, Test: Feb–May 2011). No random splitting was used.
2. **Expanding-Window Baselines**: A user's historical baseline on day $d$ was computed exclusively using history from days $\{1, \dots, d-1\}$. The current day's events and future dates were strictly excluded.
3. **Feature Preprocessing Scaling**: The `StandardScaler` used for Logistic Regression was fitted strictly on the training set and applied without refitting to the validation and test sets.

---

### Q5: Why did XGBoost outperform Random Forest and Logistic Regression?
**Answer:**  
- **Logistic Regression (PR-AUC: 0.0616)**: Being a linear classifier, it cannot model non-linear interactions between after-hours logons, USB connections, and sensitive file exfiltrations.
- **Random Forest (PR-AUC: 0.3585)**: While it models non-linear interactions, bagging builds independent deep trees that struggle with extreme 268:1 imbalance compared to boosting.
- **XGBoost (PR-AUC: 0.5236)**: Gradient boosting builds trees sequentially, with subsequent trees focusing specifically on the residual errors (misclassified rare insider samples). Combined with `scale_pos_weight` and column subsampling, it achieved the highest PR-AUC (0.5236) and ROC-AUC (0.9832).

---

### Q6: How does your Dynamic Risk Score differ from raw ML probability?
**Answer:**  
A raw ML probability $p \in [0, 1]$ represents an isolated statistical estimate. In a real SOC, risk must reflect cumulative behavioral drift and critical domain heuristics. Our 0–100 score is formulated as:
$$R = \text{clip}\left(\left\lfloor 45\sqrt{p} + 8.33 \min(3.0, \Delta_{\text{overall}}) + H_{\text{heuristics}} \right\rceil, 0, 100\right)$$
- **ML Probability (up to 45 pts)**: Scaled with square root to differentiate slight anomalies from benign noise.
- **Baseline Deviation (up to 25 pts)**: Rewards consistency; penalizes extreme departure from a user's own historical normal.
- **Domain Heuristics (up to 30 pts)**: Instant high-confidence penalties for multi-signal exfiltration (after-hours triple signal = +20 pts, USB file transfer = +15 pts, external email attachment = +10 pts).

---

### Q7: How does your SHAP Explainable AI component work?
**Answer:**  
We use `shap.TreeExplainer` on the exact 58-dimensional feature vector evaluated by XGBoost.  
TreeExplainer computes the exact Shapley values $\phi_i$ based on game theory, decomposing the model log-odds output into additive feature contributions:
$$f(x) = \phi_0 + \sum_{i=1}^{58} \phi_i(x)$$
Our system extracts the top positive contributors (e.g., `deviation_device_total_events = +1.288`) and negative mitigating factors (e.g., normal business-hour logon) and converts them into non-accusatory, analyst-ready explanations (e.g., *"Suspicious behavior detected because device connects exceeded baseline by +3.2 std devs"*).

---

### Q8: What are the 3 CERT r4.2 Insider Threat Scenarios modeled in your system?
**Answer:**  
1. **Scenario 1 (30 Users)**: User who previously never used removable drives or worked after hours begins logging in late at night, attaching a USB storage drive, and copying sensitive data.
2. **Scenario 2 (30 Users)**: User begins researching competitor job postings, downloading large volumes of documents, and exfiltrating them via removable thumb drives before resigning.
3. **Scenario 3 (10 Users)**: Disgruntled system administrator passed over for promotion who uses admin rights off-hours to deploy keyloggers and exfiltrate confidential files.

---

### Q9: Why is the separation between CERT research data and TechNova synthetic data important?
**Answer:**  
- **Academic Rigor**: CERT Release 4.2 is used strictly for training, validation, and benchmarking to produce real, un-fabricated empirical statistics.
- **Demonstration Reliability & Privacy**: In a live viva demo, streaming 4.3M historical logs in real-time is impractical. The **TechNova** synthetic enterprise environment provides a controlled, safe environment to inject interactive scenarios without exposing real personal data, while passing events through the exact same SQLite/ML/Risk backend pipeline.

---

### Q10: What are the primary limitations and future work?
**Answer:**  
- **Current Limitations**: The pipeline aggregates events into daily windows; near-instantaneous (second-by-second) streaming graph neural network correlations could further reduce latency.
- **Future Work**: Implementing deep sequence modeling (LSTMs or Temporal Graph Networks) for sub-hourly event bursts, and integrating automated SOAR (Security Orchestration, Automation, and Response) webhooks to automatically isolate compromised endpoints.

---

## 📐 Mathematical Reference Cheatsheet

| Concept | Mathematical Formula | Purpose in Project |
|---|---|---|
| **User Baseline Mean** | $\mu_u(d) = \frac{1}{|H|}\sum_{t \in H} M_u(t)$ | Computes historical mean from prior days only |
| **User Baseline Std** | $\sigma_u(d) = \sqrt{\frac{1}{|H|-1}\sum_{t \in H} (M_u(t) - \mu_u(d))^2}$ | Normalizes metric variance per user |
| **Behavioral Z-Score** | $Z_u(d) = \frac{M_u(d) - \mu_u(d)}{\max(\sigma_u(d), 0.1)}$ | Quantifies user deviation in standard deviations |
| **Composite Risk Score** | $R = \min(100, 45\sqrt{p} + 25\frac{\Delta}{3} + H)$ | 0–100 bounded multi-signal risk metric |
| **Shapley Additive Value** | $f(x) = \phi_0 + \sum_{i=1}^M \phi_i(x)$ | Exact feature attribution for tree models |
| **Precision-Recall AUC** | $\text{PR-AUC} = \sum_{k} (R_k - R_{k-1}) P_k$ | Evaluation metric resilient to extreme imbalance |

---

## 💻 Live Demonstration Script for Examiners

1. **Open Overview Page**: Highlight total users, 0.40% baseline threat concentration, and system health status.
2. **Open Model Performance Page**: Walk through the objective comparison table showing XGBoost (PR-AUC 0.5236) vs Random Forest (0.3585) vs Logistic Regression (0.0616).
3. **Open Simulation Cockpit**: Select `MULTI_SIGNAL_ANOMALY` scenario for target employee `ENG-014` (Victor Thorne). Click **START SCENARIO**.
4. **Switch to Live Monitor**: Observe live WebSocket event stream (off-hours login at 02:15, USB connect, 5 sensitive file downloads, external mail).
5. **Observe Dynamic Alert**: Note the instantaneous risk score shift from 12 (LOW) to 94 (CRITICAL) and real-time toast alert.
6. **Open Deep-Dive User Investigation**: Inspect Victor Thorne's profile, review the +3.4 std dev baseline shift, and examine the SHAP waterfall feature breakdown explaining why the incident was flagged.
