# 🇮🇳 MP MITRA — National AI Governance & Decision Intelligence Platform

> **Bridging Citizens and Parliament through Real-Time AI, Infrastructure Analysis & Geospatial Intelligence**

MP Mitra is a production-grade, multi-agent AI Decision Intelligence and Constituency Digital Twin Platform designed to bridge the gap between citizens and their elected Members of Parliament (MPs). It translates real-time citizen suggestions, web-scraped local news, WhatsApp complaints, infrastructure deficit analysis, and government dataset cross-referencing into actionable, evidence-based project portfolios mapped to real village GPS coordinates.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React + Vite](https://img.shields.io/badge/React-Vite-purple.svg)](https://vitejs.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)

---

## 🗺️ Real-Time AI Priority Map

The centrepiece of MP Mitra is the **AI Priority Map & Heat Index** — a live Leaflet-based geospatial view that automatically plots infrastructure problems at their **exact GPS locations** across the district. It shows 4 distinct data sources with different icons:

| Icon | Source | Color | Data Origin |
|------|--------|-------|-------------|
| 📍 | **Citizen Complaint** | 🔴 Red | Citizens submitting via MP Mitra Web Kiosk / App |
| 💬 | **WhatsApp Report** | 🟢 Green | WhatsApp → Firestore pipeline |
| 🤖 | **AI-Detected Deficit** | 🟣 Purple | Cross-referencing UDISE Schools, NHM Health Centres, JJM Habitations |
| 📰 | **Web News Report** | 🟡 Amber | Web crawler scraping Deccan Herald, local news portals |

**Auto-refreshes every 30 seconds** — shows live source counts and last-updated timestamp in the legend.

---

## 🏗️ All 22 Problem Categories

MP Mitra covers the complete spectrum of public governance categories:

| # | Category | # | Category |
|---|----------|---|----------|
| 1 | 🚧 Roads & Transport | 12 | 👴 Senior Citizens |
| 2 | 💧 Drinking Water | 13 | ♿ Disability & Accessibility |
| 3 | 🏥 Healthcare | 14 | 🚓 Public Safety |
| 4 | 🎓 Education | 15 | 🌪️ Disaster Management |
| 5 | ⚡ Electricity | 16 | 🏙️ Urban Development |
| 6 | 🌾 Agriculture | 17 | 🌾 Rural Development |
| 7 | 💼 Employment & Skill Development | 18 | 💻 Digital Connectivity |
| 8 | 🏠 Housing | 19 | 🚌 Public Transport |
| 9 | 🚮 Sanitation & Waste Management | 20 | 🏛️ Tourism & Heritage |
| 10 | 🌳 Environment | 21 | ⚽ Sports & Youth |
| 11 | 👩 Women & Child Welfare | 22 | 🛒 Markets & Local Economy |

---

## 🚀 Key Features

### 🗺️ AI Priority Map (Real-Time)
- Plots citizen complaints, AI-detected infrastructure deficits, WhatsApp reports, and web-scraped news on a live Leaflet map
- Real village GPS from UDISE school database, NHM health centres, and Nominatim OSM geocoding
- **Zero synthetic/fake data** — every marker has a real location from real data
- Auto-refresh every 30 seconds, source counts visible in legend
- Click any marker for detailed AI-generated solution brief, matching government schemes, and MP action buttons

### 📡 Web Scraper (Live Feed)
- Continuously crawls local news portals (Deccan Herald, district portals) for Mandya/district-specific problem reports
- All scraped items stored in PostgreSQL and immediately plotted on the map
- Manual trigger: click "Web Scraping" in the dashboard to pull fresh data
- Saves history so each session starts with accumulated data

### 🤖 AI Infrastructure Analysis
- **Education**: Flags schools with 0 teachers or student:teacher ratio > 40:1 (from UDISE data)
- **Healthcare**: Flags rural Sub-centres/PHCs needing upgrade (from NHM data)
- **Drinking Water**: Flags habitations with "Not Covered" / "Partially Covered" JJM status
- Each flagged location shows exact GPS from government database

### 💬 WhatsApp & Web Kiosk Integration
- Citizens can submit complaints via Web Kiosk embedded in the platform
- WhatsApp-submitted complaints (via Firestore) appear on the map with 💬 green pins
- Shows citizen name, village, category, urgency level, and exact complaint text

### 📊 Dashboard & Analytics
- Live risk alert feed with severity tagging
- Category-wise complaint breakdown charts
- Constituency-level budget optimizer (MPLADS ₹5 crore allocation)
- MP Copilot AI assistant for instant answers on constituency data
- Gap Analysis across all 22 categories

### 🔍 Recommendations Engine
- Pulls from citizen complaints + infrastructure DB + scheme database
- Matches each problem to the best Central/State government scheme
- Generates explainable AI rationale with SHAP-style breakdown

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18 + Vite, Leaflet.js (maps), Vanilla CSS |
| **Backend** | Python 3.11, FastAPI, SQLAlchemy ORM |
| **Database** | PostgreSQL (primary), Firebase Firestore (citizen complaints) |
| **AI/ML** | Gemini 2.0 Flash (via Google AI SDK), DBSCAN clustering |
| **Geocoding** | UDISE DB → NHM DB → Nominatim OSM API (priority chain) |
| **Web Scraping** | BeautifulSoup4 + Requests + Selenium |
| **Auth** | Firebase Authentication |
| **Deployment** | Render.com (backend), Firebase Hosting (frontend) |

---

## 💻 Installation

### Option A: 1-Click Automatic Installation (Windows)

Open **PowerShell as Administrator** and run:
```powershell
powershell -ExecutionPolicy Bypass -c "irm -useb https://raw.githubusercontent.com/harshith1432/mp-mitra/main/install.ps1 | iex"
```

### Option B: Manual Installation

#### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Git

#### Steps

```bash
# 1. Clone the repository
git clone https://github.com/harshith1432/mp-mitra.git
cd mp-mitra

# 2. Install Python dependencies
pip install -r backend/requirements.txt

# 3. Install frontend dependencies
cd frontend && npm install && cd ..

# 4. Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your PostgreSQL and Firebase credentials

# 5. Start the platform (both frontend + backend)
python run.py
```

Then open: **http://localhost:5173**

---

## 📦 Datasets Setup

MP Mitra uses 6 national government datasets. Due to GitHub file size limits, download separately:

👉 **[DOWNLOAD MP MITRA DATASETS (~121 MB)](https://drive.google.com/file/d/1-qEFBlpDg3jDZV7HwFefOB7O-LCTa0JI/view?usp=sharing)**

Extract into:
```
DATASET/Village Amenities/
├── Basic_habitation_info_2012_04_01.csv     ← JJM water coverage
├── geocode_health_centre.csv                 ← NHM health facility GPS
├── pincode.csv                               ← All-India pincode directory
├── road.csv                                  ← PMGSY road data
├── school.csv                                ← UDISE school GPS + stats
└── Water_quality_affected_habitation_2012_04_01.csv
```

### Dataset Summary

| Dataset | Records | Key Use |
|---------|---------|---------|
| `school.csv` | 1.5M+ schools | Teacher deficit detection, exact village GPS |
| `geocode_health_centre.csv` | 170K+ facilities | Rural healthcare gap detection |
| `Basic_habitation_info_2012_04_01.csv` | 600K+ habitations | Water coverage status, population data |
| `pincode.csv` | 150K+ pincodes | District centroid fallback coordinates |
| `road.csv` | 650K+ roads | PMGSY road status per habitation |
| `Water_quality_affected_habitation_2012_04_01.csv` | 80K+ records | Fluoride/Iron/Salinity contamination alerts |

---

## 🔧 Environment Variables

Create `backend/.env`:

```env
# PostgreSQL
DATABASE_URL=postgresql://username:password@localhost:5432/mpmitra

# Firebase (for Firestore citizen complaints + Auth)
FIREBASE_CREDENTIALS_PATH=./mp-mitra-firebase-adminsdk.json

# Google AI (Gemini)
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional: Nominatim geocoding user-agent
GEOCODER_USER_AGENT=mp_mitra_platform_v2
```

---

## 📡 API Endpoints

### Geospatial
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/geo/heatmap` | Returns all map points (citizen + AI + news + WhatsApp) |
| `GET` | `/api/geo/reverse` | Reverse geocode lat/lon to village/district |
| `POST` | `/api/geo/expand-intelligence` | AI deep-dive report for a specific problem point |

### Citizen Data
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/complaints/feed` | Live citizen complaint feed |
| `POST` | `/api/complaints/submit` | Submit a new citizen complaint |
| `GET` | `/api/recommendations/priorities` | AI-ranked priority projects |

### Web Crawler
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/admin/crawler/scrape-one` | Scrape one news article |
| `POST` | `/api/admin/crawler/start` | Start continuous crawler |
| `POST` | `/api/admin/crawler/stop` | Stop crawler |
| `GET` | `/api/admin/crawler/status` | Crawler status |

### Constituency
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/constituency-map/list` | List all constituencies |
| `GET` | `/api/constituency-map/data` | Constituency data for a district |
| `GET` | `/api/data-quality/scores` | Dataset quality metrics |

---

## 🗺️ How the Map Gets Real Coordinates

**Geocoding priority chain** (no random data at any step):

```
Village Name (e.g. "Katteri")
    ↓
1. UDISE School DB — exact GPS if school exists in that village
    ↓ not found
2. NHM Health Centre DB — GPS from health facility in same area
    ↓ not found
3. Habitation DB → nearest school in same village
    ↓ not found
4. Nominatim OSM API → "Katteri, Mandya district, Karnataka, India"
    ↓ not found
5. Pincode table district centroid (fixed, no noise)
    ↓ not found
6. Hard-coded Karnataka district centres
```

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch: `git checkout -b feature/AmazingFeature`
3. Commit your changes: `git commit -m 'Add some AmazingFeature'`
4. Push to the branch: `git push origin feature/AmazingFeature`
5. Open a Pull Request

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👥 Team

Built with ❤️ for the **India AI Hackathon 2026** — empowering India's 543 MPs with real-time AI decision intelligence.

> *"Every citizen complaint becomes a data point. Every data point becomes a policy action."*

---

## 📸 Screenshots

### 🗺️ AI Priority Map — Real-Time 4-Source Intelligence
Real-time Leaflet map showing citizen complaints (📍 red), WhatsApp reports (💬 green), AI-detected infrastructure deficits (🤖 purple), and web-scraped news (📰 amber) plotted at **exact GPS coordinates** across Mandya district, Karnataka. Legend shows live source counts and auto-refresh timestamp.

![AI Priority Map](docs/screenshots/screenshot_map_ai_priority.png)

---

### 📋 Recommendations Dashboard — All 22 Categories
Live priority dashboard showing **253 High Priority**, **187 Mid Priority**, **786 Low Priority** issues across all 22 governance categories. Includes the Real-Time AI Web Scraping Console with Start/Stop control.

![Recommendations Dashboard](docs/screenshots/screenshot_recommendations_dashboard.png)

---

### 💬 WhatsApp Integration — Citizen Onboarding
Citizens message the MP Mitra WhatsApp bot, select their preferred language (English / हिंदी / ಕನ್ನಡ), and are guided through the complaint submission flow — all without needing to install any app.

![WhatsApp Welcome](docs/screenshots/screenshot_whatsapp_welcome.png)

---

### 📲 WhatsApp Complaint Submission — Photo + Text + Location
A citizen from Katteri, Mandya submits a road pothole complaint with a photo via WhatsApp. The bot accepts text, voice notes, photos, videos, documents, and GPS location.

![WhatsApp Submission](docs/screenshots/screenshot_whatsapp_submission.png)

---

### 🤖 AI Scheme Matching via WhatsApp
After the citizen types **DONE**, the AI instantly analyzes the complaint, matches it to **Pradhan Mantri Gram Sadak Yojana (PMGSY)**, and replies with scheme benefits, eligible funding phase, and action plan — all on WhatsApp.

![WhatsApp AI Response](docs/screenshots/screenshot_whatsapp_ai_response.png)

---

### 💰 MPLADS Budget Portfolio Optimizer
Knapsack Integer Linear Programming optimizer for the MPLADS ₹5 crore annual allocation. Set citizen demand weight, infrastructure gap weight, and budget limit — the solver generates the optimal project portfolio with village-level cost breakdown and total beneficiary count.

![Budget Optimizer](docs/screenshots/screenshot_budget_optimizer.png)
