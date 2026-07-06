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
👉 **[DOWNLOAD MP MITRA DATASETS (ZIP)](https://drive.google.com/file/d/1-qEFBlpDg3jDZV7HwFefOB7O-LCTa0JI/view?usp=sharing)**

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


### AI pipeline Specifications

| Agent / Model | AI Technology / Model Used | Input Data (What it takes) | Output Generated (What it gives) | Role in Constituency Decision Making |
| :--- | :--- | :--- | :--- | :--- |
| **🗣️ Indic Translation Agent** | Whisper / SeamlessM4T (STT) + Llama-3 (translation) | Voice recordings or text in any of 22 Scheduled Indian languages | Normalized English text transcription + Language Detected | Allows all citizens to submit suggestions in their native regional language. |
| **👁️ YOLOv11 Defect Agent** | YOLOv11 (Fine-tuned Object Detection) | Citizen-uploaded photographs of infrastructure deficits | Bounding boxes, identified defect classes (`Pothole`, `Broken Light`, `Garbage`, etc.), & confidence | Automatically verifies the existence and severity of reported physical defects. |
| **📄 OCR & VLM Scanner Agent** | Tesseract OCR / Qwen2-VL | Official PDF letters, meeting minutes, and village panchayat reports | Structured JSON containing requested budgets, project scopes, and locations | Ingests and registers official paper-based development requests automatically. |
| **🔗 Clustering & Duplicate Agent** | TF-IDF Vectorizer + Cosine Similarity | Newly submitted raw complaint texts in the area | Grouped complaint clusters (similarity threshold $>0.55$) with support counts | Consolidates individual complaints into macro "Grievance Events" to prevent spam. |
| **📖 RAG Policy Advisor Agent** | ChromaDB / Qdrant + SentenceTransformers + Llama-3.1 | Central policies (PMGSY, JJM, NHM, RTE) & MP natural language queries | Citation-backed advisory responses and matching local statistics | Guides the MP on whether a project matches national policy rules and local needs. |
| **⚖️ Knapsack ILP Optimizer** | Mixed Integer Linear Programming (MILP via PuLP) | Candidate projects, budget limits, and importance weights | Mathematical globally-optimal project selection portfolio | Solves the best projects checklist that maximizes development impact under budget. |
| **📊 SHAP Attribution Agent** | Shapley Additive Explanations (SHAP) | Prioritized project portfolios | Mathematical attribution percentages for each priority factor (Demand, Urgency, etc.) | Explains the exact mathematical reasoning behind every automated recommendation. |

---

## 🌐 22 Scheduled Indian Languages Multi-Language Support

MP Mitra features a complete localization switcher on every screen, allowing both citizens and representatives to toggle the interface dynamically between English and all **22 official languages of India** (Hindi, Kannada, Telugu, Tamil, Marathi, Gujarati, Bengali, Malayalam, Punjabi, Odia, Urdu, Assamese, Sanskrit, Kashmiri, Konkani, Nepali, Manipuri, Bodo, Dogri, Maithili, Santali, and Sindhi).

* **How it works**: Uses static local dictionaries (zero-dependency, offline-first) with a global React `LanguageContext`.
* **RTL Layouts**: Automatically mirrors layout direction (`dir="rtl"`) when switching to right-to-left scripts such as Urdu and Kashmiri.
* **Persistent Settings**: Local storage remembers user language preferences across reloads.

---

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

## 🌐 Real-Time Crawler & Offline Data Unification Architecture

This architecture details how the real-time web crawler, offline government databases, RAG retrieval system, and Firebase synchronizer merge to power the MP MITRA digital twin, dashboard, and geospatial map interfaces.

### 🗺️ System Architecture Flowchart

```mermaid
graph TD
    %% Scraped Web Data Sources
    subgraph Web_Scraper [Real-Time Web Scraper]
        RSS[Google News RSS Feed]
        TND[Scraped Government Tenders]
        SCH[myscheme.gov.in RSS/Webpages]
    end

    %% Offline Datasets
    subgraph Offline_Data [Physical Datasets]
        UDISE[UDISE School Demographics]
        JJM[Jal Jeevan Mission Habitations]
        PMGSY[PMGSY Road Construction]
        WQ[Water Quality Database]
    end

    %% Storage & Search Engines
    subgraph Storage [Databases & Intelligence Store]
        PG[(PostgreSQL / SQLite Database)]
        FB[(Firebase Firestore & RTDB)]
        VS[(ChromaDB Vector Store)]
    end

    %% Backend Services
    subgraph Backend [FastAPI API Routers]
        CR[crawler_rt_stages.py / crawler_manager.py]
        CO[copilot.py - Conversational Agent]
        RA[rag_agent.py - RAG Search Engine]
        RE[recommendations.py - Priority Engine]
        GE[geo.py - Geospatial API Router]
    end

    %% Frontend App
    subgraph Client [React Digital Twin Interface]
        DB_WDG[Dashboard Widgets: Health Score, Gaps, Risk Alerts]
        LF_MAP[Leaflet Geospatial Map Interface]
        CO_AI[MP Copilot Chat Interface]
    end

    %% Data Connections
    RSS -->|Parse articles| CR
    TND -->|Parse tenders| CR
    SCH -->|Parse schemes| CR
    CR -->|Store crawled_news/tenders/schemes| PG
    CR -->|Sync alerts| FB

    UDISE -->|Bulk import| PG
    JJM -->|Bulk import| PG
    PMGSY -->|Bulk import| PG
    WQ -->|Bulk import| PG

    PG -->|Feed text items| VS
    
    %% API Services
    PG -->|Read infrastructure details| RE
    FB -->|Read citizen complaints| RE
    RE -->|Calculate composite priorities| GE
    
    GE -->|Heatmap data & AI recommended pins| LF_MAP
    GE -->|/expand-intelligence POST RAG Rerank| RA
    RA -->|Vector search| VS
    RA -->|Direct text fallback lookup| PG
    
    PG -->|Read constituency counts| Backend
    Backend -->|/api/constituency/data| DB_WDG
    
    CO -->|Natural Language Conversational RAG| CO_AI
```

### 🔍 Core Data Unification Details

#### 1. Real-time Aggregation
- **Web Crawler**: Scrapes news articles, local tenders, and schemes in real-time, matching them to specific Gram Panchayats, Villages, and Taluks.
- **Offline Datasets**: Loaded from public census, education (UDISE), health (NHM), water (JJM), and roads (PMGSY) data, georeferenced by Taluk/Block.

#### 2. Algorithmic Merging
- **Constituency Health Score**: 
  \[
  \text{Health Score} = \text{PTR Score} + \text{Clinic Coverage} + \text{Water Coverage} + \text{Road Completion} - \text{Active Crawled Alerts Penalty}
  \]
- **AI Recommendation Engine**: Scans physical deficit datasets, clusters them with citizen suggestions, and generates recommended pins for the Leaflet map sidebar dynamically.
- **Expand Intelligence RAG Hub**: Takes any map deficit location, queries ChromaDB embeddings for web-scraped context, and calls the LLM orchestrator to explain scheme fits, causes, and projected benefits.

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
* Note: During local development, the backend runs the APIs on port `8000`, while the frontend uses Vite's hot-reload server on port `5173` (requests proxy automatically).

---

## 🚀 Production Deployment Guidelines

In production, frontend compilation is treated as a **build-time step** rather than an application-startup step. This ensures that the FastAPI backend runs with zero dependency on Node.js at runtime, preventing crashes in serverless or containerized cloud platforms.

If the frontend build (`frontend/dist`) is missing, the backend continues to start successfully, serving a styled diagnostic page for frontend routes instead of raising a `RuntimeError`.

### 1. Render Deployment Config

Configure your Render web service with these settings:
* **Runtime**: `Python`
* **Python Version**: `3.11.9`
* **Build Command**:
  ```bash
  # Install Node.js locally inside the build environment (no root required)
  mkdir -p $HOME/.node
  curl -fsSL https://nodejs.org/dist/v18.19.0/node-v18.19.0-linux-x64.tar.xz | tar -xJ --strip-components=1 -C $HOME/.node
  export PATH=$HOME/.node/bin:$PATH

  # Compile frontend
  cd frontend
  npm install
  npm run build

  # Compile backend
  cd ../backend
  pip install --upgrade pip
  pip install --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt
  ```
* **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 2. Railway Ingestion Config

Railway uses Nixpacks to automatically detect project environments. Create a `nixpacks.toml` at the root of the project to tell Railway to setup both Node.js and Python for building:
```toml
[providers]
providers = ["node", "python"]

[phases.setup]
nixPkgs = ["nodejs", "python311"]

[phases.build]
cmds = [
  "cd frontend && npm install && npm run build",
  "cd ../backend && pip install --upgrade pip && pip install -r requirements.txt"
]
```
* **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 3. Docker Container Build

Use this multi-stage Dockerfile to build the frontend and serve it using Python:
```dockerfile
# --- Stage 1: Build Frontend ---
FROM node:18-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Serve Backend ---
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./backend/
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r backend/requirements.txt

COPY backend/ ./backend/
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

EXPOSE 8000
ENV PORT=8000
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. GitHub Actions CI/CD Pipeline

Use this workflow snippet to validate frontend and backend compilation in your pull requests:
```yaml
name: Build and Validate
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Use Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      - name: Build Frontend
        run: |
          cd frontend
          npm install
          npm run build
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - name: Build Backend
        run: |
          cd backend
          pip install --upgrade pip
          pip install -r requirements.txt
```