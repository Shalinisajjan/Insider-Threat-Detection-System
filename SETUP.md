# ⚙️ Setup and Installation Guide: ThreatSight AI

Welcome to **ThreatSight AI** — the Explainable Insider Threat Intelligence Platform. This guide walks you through setting up the complete full-stack platform, from generating synthetic threat datasets and training Machine Learning/Deep Learning models, to running the FastAPI backend, React frontend, and MongoDB database.

---

## 🛠️ Prerequisites

Ensure you have the following installed on your system:
- **Python 3.10 or 3.11** (Python 3.12+ can sometimes have compatibility issues with tensorflow/shap libraries depending on build platforms)
- **Node.js (v18 or higher)** & npm
- **MongoDB Community Server** (running locally on port `27017`)
- **Docker & Docker Compose** (Optional — for running the entire system in containerized mode)

---

## 📂 Project Structure

```text
insider-threat-platform/
├── backend/               # FastAPI Backend Service
│   ├── ml/                # ML Pipelines, saved models, and explainability scripts
│   ├── models/            # Pydantic schemas
│   ├── routes/            # API endpoints (auth, risk, activities, shap, etc.)
│   └── seed_demo_data.py  # Seeder for demo dashboard profiles
├── dataset/               # Synthetic CERT Insider Threat dataset generation
├── docs/                  # Academic documents (SRS, research paper, reports)
├── frontend/              # Vite + React (TypeScript/JS) Dashboard
└── notebooks/             # Research & Tuning Jupyter Notebooks (.py percent cell format)
```

---

## 🚀 Step-by-Step Local Setup

### 1. Database Setup
Ensure your local **MongoDB** server is running. By default, it runs on:
`mongodb://localhost:27017`

### 2. Backend Setup
Open a terminal in the root directory of the project and perform the following steps:

1. **Navigate to backend and create a Python Virtual Environment:**
   ```bash
   cd backend
   python -m venv venv
   ```
2. **Activate the Virtual Environment:**
   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Configure Environment Variables:**
   A standard configured `.env` file has been created at the root of `insider-threat-platform/`. For the backend to find it, copy it into the `backend/` directory or run the backend from the root:
   ```bash
   cp ../.env .env
   ```

### 3. Generate Data & Train Machine Learning Models
To run the platform, you must first generate the threat behaviors dataset and train the ML models (Random Forest, XGBoost, Isolation Forest, LSTM).

1. **Generate the Synthetic CERT Dataset:**
   From the root folder or `dataset/` folder, run:
   ```bash
   python ../dataset/generate_synthetic.py
   ```
   This generates `synthetic_insider_threat.csv` inside `dataset/` containing login patterns, USB transfers, browser alerts, and anomalous rates for employees.

2. **Train All AI Models:**
   Activate your virtual environment and run the model training pipeline:
   ```bash
   python ml/train_all.py
   ```
   This trains and evaluates all four models, saving them in `backend/ml/saved_models/` along with a performance summary:
   - `random_forest.joblib`
   - `xgboost.joblib`
   - `isolation_forest.joblib`
   - `lstm_model.h5`
   - `training_summary.json` (stores evaluation metrics for the UI page)

### 4. Seed MongoDB Demo Profiles
To populate your dashboard with historical activities, active security alerts, and threat risk scoring curves, seed the database:
```bash
python seed_demo_data.py
```
This populates multiple employees with diverse timelines representing normal employees, suspicious behaviors (e.g. data exfiltration attempts), and active critical threat actors.

### 5. Launch the FastAPI Backend
Start the backend server using `uvicorn`:
```bash
uvicorn main:app --reload
```
The backend API is now running on: **`http://localhost:8000`**
- Interactive Swagger docs: `http://localhost:8000/docs`
- Redoc API documentation: `http://localhost:8000/redoc`

---

### 6. Frontend Setup
Open a separate terminal window and navigate to the `frontend/` directory:

1. **Install Dependencies:**
   ```bash
   cd frontend
   npm install
   ```
2. **Launch Vite Development Server:**
   ```bash
   npm run dev
   ```
The frontend is now active on: **`http://localhost:5173`**
- It communicates with the backend via the Vite proxy configured at `http://localhost:8000/api`.

---

## 🔒 SOC Analyst Credentials

You can log in to the ThreatSight AI Analyst Dashboard using the pre-seeded admin accounts:

| Role | Username | Password |
| :--- | :--- | :--- |
| **Security Analyst (Admin)** | `admin@threatsight.ai` | `Admin@123456` |
| **SOC Analyst (Read-only)** | `sarah@threatsight.ai` | `Analyst@123` |

---

## 🐳 Containerized Quick Start (Docker Compose)

If you prefer running the entire stack (FastAPI, React Vite, MongoDB) inside Docker containers without installing local packages:

1. Run the following command from the root directory:
   ```bash
   docker-compose up --build
   ```
2. The containers will automatically:
   - Start MongoDB on port `27017`.
   - Spin up the FastAPI server on port `8000`.
   - Seed the database and train the models automatically inside the container during startup.
   - Run the React development server on port `5173`.
3. Open your browser to `http://localhost:5173` to explore the dashboard.

---

## 📊 Exploration and Research: Jupyter Notebooks

For model tuning and further research, explore the pre-packaged Jupyter notebooks located in `notebooks/` directory. They are built in the **Percent Cell format (`# %%`)** to ensure compatibility with VS Code Jupyter extension and standard Jupyter converters:
1. `01_EDA_and_Feature_Engineering.py` — Deep Exploratory Data Analysis & visual correlation plots.
2. `02_ML_Model_Training_and_Evaluation.py` — Custom training routines and interactive ROC plotting.
3. `03_SHAP_Explainability.py` — Generation of Beeswarm, Waterfall, and Dependence Explainable AI plots.
4. `04_Risk_Scoring_Analysis.py` — Engine threshold analysis and ROC tuning curves.

All figure graphics generated from these notebooks are saved to `notebooks/figures/` for incorporation in research studies or slide presentations.
