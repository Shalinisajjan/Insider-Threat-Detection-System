# 📊 PowerPoint Presentation Outline: ThreatSight AI

**Project Title:** Explainable Insider Threat Intelligence Platform Using User Behavior Analytics and Machine Learning  
**Target Audience:** Cybersecurity leadership, SOC supervisors, academic evaluators, and stakeholders  
**Total Slides:** 20 slides  

---

### Slide 1: Title Slide
* **Title:** ThreatSight AI
* **Subtitle:** An Explainable Insider Threat Intelligence Platform Using User Behavior Analytics and Machine Learning
* **Visual Suggestion:** High-contrast cybersecurity graphic with a glowing network map and a dark theme. Subdued indigo/violet colors showing a magnifying glass over digital assets.
* **Bullet Points:**
  - Designed and developed as a complete full-stack SOC alert and ML triage platform.
  - Resolves internal organizational vulnerabilities via behavioral anomalies.
  - Powered by Explainable AI (XAI) using SHAP (SHapley Additive exPlanations).
* **Speaker Notes:**
  * Welcome everyone to the presentation of ThreatSight AI. Today, we will discuss our comprehensive solution to one of the most persistent and difficult challenges in cybersecurity: the Insider Threat. By combining User Behavior Analytics with advanced Machine Learning models and Explainable AI, we have created an intuitive, reliable, and interpretable defense system.

---

### Slide 2: Problem Statement
* **Title:** The Invisible Danger: Insider Threats
* **Visual Suggestion:** A pie chart showing that 60%+ of security breaches involve a human element or internal user credentials.
* **Bullet Points:**
  - **The Perimeter Blind Spot:** Traditional firewalls and intrusion prevention systems fail to block malicious actions from authorized accounts.
  - **High Financial Cost:** The average cost of an insider incident is over $15M annually.
  - **Detection Latency:** Malicious actors and negligent employees often escape detection for months due to legitimate access credentials.
* **Speaker Notes:**
  * Why focus on insider threats? Because traditional perimeter tools are blind to them. Once an attacker gains legitimate access or a trusted employee decides to act maliciously, standard safeguards are useless. Our system addresses this massive security blind spot.

---

### Slide 3: Project Goals & Core Objectives
* **Title:** ThreatSight AI: Core Objectives
* **Visual Suggestion:** 3 columns representing anomaly detection, risk profiling, and explainability.
* **Bullet Points:**
  - **Behavioral Profiling:** Continuous ingestion and analysis of login, file, and web access patterns.
  - **Real-Time Risk Scoring:** Multi-dimensional dynamic scoring of individual user threat levels.
  - **Explainability (XAI):** Visualizing the *why* behind every neural network and machine learning prediction using SHAP.
* **Speaker Notes:**
  * ThreatSight AI was designed with three foundational goals. We want to profile behavior dynamically, score user risks in real-time, and make the predictive decisions of our models transparent and explainable to security analysts.

---

### Slide 4: System Architecture Overview
* **Title:** System Architecture
* **Visual Suggestion:** A flowchart showing the flow of activity logs through MongoDB, the ML Risk Engine, the SHAP Explainer, the FastAPI Backend, and the React frontend.
* **Bullet Points:**
  - **FastAPI Core:** Ultra-fast async router processing JSON behavioral logs.
  - **NoSQL Document Storage:** MongoDB scales to handle millions of real-time audit logs.
  - **Modular Predict & Explain Pipeline:** Microservice-ready architecture separating training, inference, and attribution.
* **Speaker Notes:**
  * Our technical stack is modern and resilient. We use FastAPI for the backend to handle high-frequency events, MongoDB to store semi-structured activity documents, and a modular python ML directory to separate training, risk calculations, and SHAP explanations.

---

### Slide 5: The Behavioral Dataset
* **Title:** Synthetic CERT Dataset & Features
* **Visual Suggestion:** Table listing all 11 behavioral features with description and data types.
* **Bullet Points:**
  - **Login Metrics:** `login_frequency`, `late_night_logins`, and `failed_login_count`.
  - **Data Transfer Volume:** `file_download_volume`, `usb_transfer_count`, and `external_transfers`.
  - **Browsing & Anomaly Ratios:** `suspicious_url_count` and `anomaly_ratio`.
* **Speaker Notes:**
  * Our machine learning model trains on features modeled after the standard Carnegie Mellon CERT Insider Threat Dataset. We engineered 11 rich indicators that describe activity timing, volume, locations, and deviations.

---

### Slide 6: Machine Learning Pipeline
* **Title:** Machine Learning Pipeline
* **Visual Suggestion:** A schematic block diagram showing preprocessing, feature scaling, model training, and performance metrics generation.
* **Bullet Points:**
  - **Preprocessing:** Handles scaling, missing value imputation, and sequence creation for deep learning.
  - **Heterogeneous Ensemble:** Blends supervised classification with unsupervised anomaly detection.
  - **Dynamic Retraining:** Automatic evaluation of validation metrics upon new training cycles.
* **Speaker Notes:**
  * The machine learning pipeline is fully automated. Preprocessing converts raw activity inputs into scaled feature vectors, which are evaluated by four distinct models.

---

### Slide 7: Model 1: Random Forest
* **Title:** Random Forest Classification
* **Visual Suggestion:** Diagram of a decision forest voting on a class label.
* **Bullet Points:**
  - Ensembles dozens of independent decision trees to reduce variance.
  - Extremely robust against overfitting on noisy audit logs.
  - Serves as the primary baseline classifier with 96%+ accuracy.
* **Speaker Notes:**
  * Random Forest is our first model, offering robust, non-linear classification across the 11 engineered features. It performs with high generalizability and forms the basis for tree-based SHAP explainability.

---

### Slide 8: Model 2: XGBoost
* **Title:** eXtreme Gradient Boosting (XGBoost)
* **Visual Suggestion:** Serial model boosting diagram showing corrective updates across training iterations.
* **Bullet Points:**
  - Employs gradient boosting framework to minimize loss functions sequentially.
  - High computational efficiency and state-of-the-art predictive power.
  - Excels at identifying complex, sparse threat patterns (e.g. slow data leaks).
* **Speaker Notes:**
  * XGBoost builds trees sequentially, correcting errors made by previous trees. It is highly optimized and provides incredible sensitivity for sparse threat signals.

---

### Slide 9: Model 3: Isolation Forest
* **Title:** Isolation Forest Anomaly Detection
* **Visual Suggestion:** A plot showing outliers isolated near the edges of a feature space with fewer splits.
* **Bullet Points:**
  - **Unsupervised Paradigm:** Does not require pre-labeled threat datasets to function.
  - Isolates anomalies by randomly partitioning feature values.
  - Ideal for identifying zero-day threat patterns never seen in training history.
* **Speaker Notes:**
  * To catch attackers using brand-new techniques, we employ Isolation Forest. Because it isolates anomalies based on feature partition lengths rather than historical templates, it is perfect for zero-day threat detection.

---

### Slide 10: Model 4: Sequential LSTM
* **Title:** Deep Sequential LSTM Networks
* **Visual Suggestion:** LSTM cell diagram showing input, forget, and output gates.
* **Bullet Points:**
  - Captures time-series trends over sequential employee behaviors.
  - Retains memory of events over extended periods (e.g. gradual data accumulation).
  - Outperforms traditional static classifiers on progressive threats.
* **Speaker Notes:**
  * Some threat actions are harmless in isolation but dangerous when repeated over days. Our Bidirectional LSTM processes behavioral timelines sequentially, using forget gates to remember or discard context over time.

---

### Slide 11: Experimental Results & Comparison
* **Title:** Model Performance Matrix
* **Visual Suggestion:** A styled chart comparing Accuracy, Precision, Recall, F1, and ROC-AUC across all models.
* **Bullet Points:**
  - **XGBoost & RF:** Outstanding supervised metrics, exceeding 97% ROC-AUC.
  - **Isolation Forest:** High recall, capturing odd anomalies with expected trade-offs in precision.
  - **LSTM:** Excellent F1-Score, showing great potential for complex sequential multi-day actions.
* **Speaker Notes:**
  * Here are our model results. The supervised models (Random Forest and XGBoost) achieved top scores, while Isolation Forest successfully isolated outliers.

---

### Slide 12: Explainable AI (XAI) with SHAP
* **Title:** Inside the Black Box: SHAP
* **Visual Suggestion:** Graphic showing an input image passing through an ML model, but annotated with red and blue feature contribution bars.
* **Bullet Points:**
  - Provides mathematical attribution based on game theory Shapley values.
  - Explains individual predictions locally and feature importances globally.
  - **Analyst Empowerment:** Converts vague scores into clear, reviewable reasons.
* **Speaker Notes:**
  * A security analyst cannot trust a model blindly without knowing the reasoning. ThreatSight AI leverages SHAP to explain exactly *why* a user's risk is high, showing the contribution of each behavioral feature.

---

### Slide 13: Local and Global Interpretability
* **Title:** Visualizing Explanations
* **Visual Suggestion:** Two charts side-by-side: a SHAP Global Beeswarm Plot and a Local Waterfall explanation.
* **Bullet Points:**
  - **Global Beeswarm:** Reveals the macro-impact of feature values on classification.
  - **Local Waterfall:** Displays step-by-step additions/subtractions driving an individual risk rating.
  - Enables audit trails for administrative or legal compliance actions.
* **Speaker Notes:**
  * Our platform generates beeswarm plots to show the macro-impact of attributes across all users, and waterfall charts to explain individual incidents, ensuring a complete audit trail.

---

### Slide 14: Dynamic Risk Engine
* **Title:** Multi-Dimensional Risk Scoring
* **Visual Suggestion:** Gauge chart showing risk scores divided into Low, Medium, and High bands.
* **Bullet Points:**
  - Blends real-time activity contributions with model threat predictions.
  - Decays risk scores over time if no further anomalous activities occur.
  - Instantly escalates users to High Risk upon detecting critical threshold violations.
* **Speaker Notes:**
  * The risk engine acts as the brain, fusing model probabilities with direct policy rules. It calculates a score from 0 to 100, dynamically updating the database and decaying scores during periods of normal behavior.

---

### Slide 15: Analyst Interface Walkthrough
* **Title:** Command Center: SOC Dashboard
* **Visual Suggestion:** Screenshot or diagram of the ThreatSight AI Dashboard showing stats, trend graphs, and high-risk leaderboards.
* **Bullet Points:**
  - **Unified SOC Monitor:** Real-time summary of alerts, threat counts, and average risk.
  - **Trend Graphing:** 14-day chronological tracker showing rising threats.
  - **Leaderboard:** Quick-access list of the highest-risk employees in the organization.
* **Speaker Notes:**
  * Let's take a tour of the Analyst Dashboard. The command center provides a single-pane-of-glass interface showing active alerts, average risk scores, and the top high-risk users.

---

### Slide 16: Interactive Activity Heatmaps
* **Title:** Inside User Behaviors: Heatmaps
* **Visual Suggestion:** Heatmap rendering showing busy cells at night and borders around after-hours.
* **Bullet Points:**
  - Hours of the day vs. Days of the week grid representation.
  - Color intensity correlates directly to event density.
  - Red boundaries highlight suspicious after-hours activity.
* **Speaker Notes:**
  * We've integrated interactive behavioral heatmaps. Analysts can view when employees are active. Cells with red boundaries highlight anomalous events occurring during suspicious after-hours, aiding fast diagnostics.

---

### Slide 17: Investigation & PDF Reporting
* **Title:** Forensic Triage & Compliance Reports
* **Visual Suggestion:** A mockup of a PDF summary report next to an investigation history log.
* **Bullet Points:**
  - **Interactive Timelines:** Drill down into every single download, USB insertion, or failed login.
  - **One-Click Reports:** Exports formal PDF intelligence documents for administrative actions.
  - **Alert Remediation:** Allows analysts to mark alerts as investigated, closed, or escalated.
* **Speaker Notes:**
  * When an analyst clicks a user, they are taken to the Investigation Profile. Here, they can audit activity logs and generate executive PDF summaries with a single click.

---

### Slide 18: Model Evaluation & Status Dashboard
* **Title:** Real-Time AI Metrics Monitoring
* **Visual Suggestion:** Screenshot of the frontend `/models` page showing card layouts for RF, XGB, IF, and LSTM.
* **Bullet Points:**
  - Displays real-time model operational status and load timestamps.
  - Interactive comparison charts plotting F1 and ROC-AUC side-by-side.
  - Inline training triggers to update models upon new database ingestions.
* **Speaker Notes:**
  * In the operational view, analysts can monitor the performance of all four models side-by-side, inspect their ROC-AUC, and initiate retraining cycles.

---

### Slide 19: Security, Scalability & Compliance
* **Title:** Enterprise Hardening
* **Visual Suggestion:** Lock and database backup graphics showing RBAC controls.
* **Bullet Points:**
  - **Access Control (RBAC):** Restricts data access between security analysts and administrative users.
  - **Rate Limiting & CORS:** Hardens FastAPI endpoints against DDoS and unauthorized origins.
  - **Privacy Constraints:** Protects employee privacy by sanitizing logs before model evaluation.
* **Speaker Notes:**
  * For enterprise readiness, we enforce strict Role-Based Access Control and protect sensitive details to respect employee privacy guidelines while securing the system.

---

### Slide 20: Conclusion & Future Scope
* **Title:** The Path Forward
* **Visual Suggestion:** Icon representing growth, integration, and AI innovation.
* **Bullet Points:**
  - **Achievements:** Designed, built, and tested a unified XAI insider threat platform.
  - **Active Protection:** Dramatically lowers detection times from months to seconds.
  - **Future Scope:** Integrating Active Directory / LDAP synchronization, natural language processing for email text analysis, and federated learning models.
* **Speaker Notes:**
  * In conclusion, ThreatSight AI bridges the gap between machine learning intelligence and analyst trust. We look forward to future integrations like Active Directory sync. Thank you, and I am open to any questions.

---
