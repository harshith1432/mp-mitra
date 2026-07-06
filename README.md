# 🇮🇳 MP MITRA: National AI-Driven Governance & Decision Intelligence Platform

MP Mitra is a production-grade, multi-agent AI Decision Intelligence and Constituency Digital Twin Platform designed to bridge the gap between citizens and their elected Members of Parliament (MPs). It translates real-time citizen suggestions, infrastructure defect photographs, and Indic voice recordings into actionable, evidence-based project portfolios optimized against national guidelines and local budgets.

---

## 💻 Command Line Interface (CLI) Installation & Usage

MP Mitra features a professional command-line interface (`mpmitra`) to manage local services, databases, configurations, and software updates.

### 1. Installation on Windows

#### Option A: 1-Click Automatic Installation (Recommended)
Open **PowerShell** and run the following command to download, extract, install dependencies, compile the frontend dashboard, and register the `mpmitra` command in your PATH automatically:
```powershell
powershell -ExecutionPolicy Bypass -c "irm -useb https://raw.githubusercontent.com/harshith1432/mp-mitra/main/install.ps1 | iex"
```

#### Option B: Manual Installation
1. **Download the Package:** Download the latest `mpmitra-windows-x64.zip` release from the GitHub Releases page.
2. **Extract:** Extract the zip folder to a permanent location (e.g., `C:\Program Files\MPMitra` or `C:\Users\<User>\AppData\Local\Programs\MPMitra`).
3. **Register PATH:** Add the folder path containing `mpmitra.exe` to your Windows System environment `PATH` variable.
4. **Verify Installation:** Open Command Prompt or PowerShell from any directory and type:
   ```bash
   mpmitra version
   ```


---

## 📦 Datasets Setup

MP Mitra utilizes 6 national government datasets for demographic, infrastructure, health, and education planning across all Indian villages. Due to GitHub's file size limits, these datasets must be downloaded separately and placed in the project directory.

### 1. Download Datasets
Download the optimized dataset package zip file (~121 MB) from Google Drive here:
👉 **[DOWNLOAD MP MITRA DATASETS (ZIP)]()** *(Paste your Google Drive link here)*

### 2. Extract & Place Files
Extract the contents of the downloaded `MPMitraDatasets.zip` file directly into the following path under your project root directory:
```
DATASET/Village Amenities/
```
Once placed, the directory structure should look like this:
```
DATASET/
└── Village Amenities/
    ├── Basic_habitation_info_2012_04_01.csv
    ├── geocode_health_centre.csv
    ├── pincode.csv
    ├── road.csv
    ├── school.csv
    └── Water_quality_affected_habitation_2012_04_01.csv
```

### 3. Active Datasets Summary

| Dataset File | Description | Records | Key Columns Used |
| :--- | :--- | :--- | :--- |
| **`pincode.csv`** | All-India Pincode Directory | 150K+ | Pincode, District, State, Latitude, Longitude |
| **`geocode_health_centre.csv`** | Geocoded Health Center Directory | 200K+ | Facility Name, Type, Subdistrict, Latitude, Longitude |
| **`road.csv`** | PMGSY Road Network Database | 100K+ | Road Name, Surface Type, Connected Habitations, Cost, Length |
| **`school.csv`** | National UDISE School Database | 1.5M+ | School Name, Village, Students Count, Teachers Count, Geolocations |
| **`Basic_habitation_info_2012_04_01.csv`** | Census Habitation Demographics | 1.2M+ | Village, Habitation, SC/ST Population, General Population |
| **`Water_quality_affected_habitation_2012_04_01.csv`** | Drinking Water Quality Contaminants | 100K+ | Habitation, Contaminant (Fluoride, Arsenic, Iron, etc.), Status |

---


## 🛠️ CLI Reference Manual

Manage your deployment using the following core CLI commands:

| Command | Usage | Description |
| :--- | :--- | :--- |
| **`start`** | `mpmitra start` | Launches uvicorn backend server in the background and automatically opens the browser dashboard on http://localhost:8000. |
| **`stop`** | `mpmitra stop` | Gracefully terminates all active background MP Mitra services. |
| **`restart`**| `mpmitra restart` | Restarts background services. |
| **`status`** | `mpmitra status` | Displays process ID, service health, active update channel, and database connection profiles. |
| **`logs`** | `mpmitra logs -f` | Displays or streams real-time log outputs from the background uvicorn servers. |
| **`config`** | `mpmitra config set GROQ_API_KEY <key>` | Safely reads/writes configuration settings. Sensitive keys (passwords, tokens, credentials) are stored encrypted. |
| **`doctor`** | `mpmitra doctor` | Runs diagnostic health checks on read/write permissions, database connectivity, and external APIs. |
| **`backup`** | `mpmitra backup <path>` | Archives current local SQLite database and config files to the target folder. |
| **`restore`**| `mpmitra restore <path>`| Restores local databases and configurations from a backup directory. |
| **`update`** | `mpmitra update` | Queries the GitHub Release servers and downloads update packages securely. |
| **`reset`**  | `mpmitra reset` | Safely resets all local configurations, database files, and logs. |

---

## 🤖 Detailed AI Multi-Agent Architecture

MP Mitra deploys a coordinated pipeline of intelligent, single-responsibility agents:

```mermaid
graph TD
    A[Citizen / WhatsApp Ingestion] --> B[Indic Translation Agent]
    B --> C[YOLOv11 Defect Agent]
    C --> D[OCR / VLM Agent]
    D --> E[TF-IDF Duplicate Agent]
    E --> F[RAG Advisor Agent]
    F --> G[ILP Knapsack Optimizer]
    G --> H[SHAP Attribution Agent]
```

### 1. 🗣️ Indic Translation Agent
* **File Location:** [translate_agent.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/agents/translate_agent.py)
* **Functionality:** Translates text and audio inputs in 22 official Indic languages (Hindi, Kannada, Telugu, Tamil, Marathi, Gujarati, etc.) into English.
* **How it works:** Triggers automatically during WhatsApp or Web Kiosk ingestion, ensuring subsequent processing agents receive clean, normalized English inputs.

### 2. 👁️ YOLOv11 Defect Detection Agent
* **File Location:** [vision_agent.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/agents/vision_agent.py)
* **Functionality:** Scans citizen-uploaded pictures to identify, outline, and classify infrastructure deficits.
* **Classes Detected:** `Pothole`, `Broken Street Light`, `Garbage Heap`, `Water Leakage`.

### 3. 📄 OCR & VLM Document Scanner Agent
* **File Location:** [ocr_agent.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/agents/ocr_agent.py)
* **Functionality:** Scans scanned PDFs, meeting letters, and official panchayat reports submitted by citizen delegations.
* **How it works:** Extracts core project names, budgets, and descriptions using high-accuracy OCR to automate document registration.

### 4. 🔗 TF-IDF & Cosine Similarity Clustering Agent
* **File Location:** [citizen.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/routing/citizen.py#L261-L289)
* **Functionality:** Group incoming complaints to detect duplicates and track unified citizen interest volume.
* **How it works:** Vectorizes incoming complaint texts against previous records in the district. If similarity $> 0.55$, it groups them under a shared cluster ID in Firestore.

### 5. 📖 RAG Policy Advisor Agent
* **File Location:** [copilot.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/routing/copilot.py)
* **Functionality:** Answers MP questions regarding constituency needs, central guidelines (NHM, PMGSY, RTE), and local metrics.
* **How it works:** Embeds government policy documents into ChromaDB/Qdrant vector stores, retrieves relevant context chunks, and provides evidence-backed investment advisories.

### 6. ⚖️ Knapsack ILP Budget Optimizer Agent
* **File Location:** [prioritize.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/routing/prioritize.py)
* **Functionality:** Solves the optimal project selection portfolio under the MP's budget constraints.
* **How it works:** Runs binary (0-1) Integer Linear Programming using the `pulp` library to maximize development impact weight.

### 7. 📊 SHAP Explainable AI Attribution Agent
* **File Location:** [prioritize.py](file:///d:/projects%20softwares/hackthon%20pm/backend/app/routing/prioritize.py#L183-L191)
* **Functionality:** Computes Shapley additive attribution values to explain why a project was prioritized.
* **How it works:** Quantifies the individual percentage weights of Citizen Demand, Urgency, Neglect, and Cost factors to provide transparent mathematical reasoning.

---

## ⚙️ Ingestion & Setup (Development Mode)

### 1. Environment Variables
Configure your database and API keys in `backend/.env`:
```env
DATABASE_URL=postgresql://postgres:PASSWORD@localhost:5432/mp_mitra
GROQ_API_KEY=gsk_your_groq_key
GOOGLE_API_KEY=AIzaSy_your_gemini_key
FIREBASE_SERVICE_ACCOUNT_JSON={...}
```

### 2. Running Local Dev Server
Launch both frontend and backend concurrently using the root runner:
```bash
cd backend
python run.py
```
* Note: The server automatically mounts built frontend static files from `frontend/dist` when packaged, but in dev mode, it runs hot-reloads on port `5173`.