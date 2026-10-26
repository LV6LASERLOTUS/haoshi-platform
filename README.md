
# 🤝 好事大平台 (Haoshi Platform)
> A privacy-first, full-stack partnership matching platform connecting corporate CSR requests with Non-Profit Organizations (NPOs) using local Chinese OCR and semantic AI embeddings—with zero paid cloud APIs required.

---

## 🏗️ System Architecture Workflow

```text
[ 1. INTAKE: Mobile App ] 
  • React Native / Expo Mobile App (iOS & Android)
  • Chinese Text Box + Image / Proposal Upload
               │
               ▼ (HTTP REST API / POST)
[ 2. PROCESSING ENGINE: Python Backend ]
  • API Framework: FastAPI
  • Local OCR: PaddleOCR (Extracts text from images/PDFs)
  • Local Embeddings: BAAI/bge-small-zh-v1.5 (Semantic matching)
  • Syncs with Google Sheets API (gspread)
               │
               ▼ (Updates Match Records)
[ 3. DATABASE HUB: Master Google Sheet ]
  • Tabs: `NPO_Database`, `Business_Database`, `Match_Engine`
               │
               ▼ (Pulls Live Data)
[ 4. DISPLAY: Web Dashboard ]
  • UI: Looker Studio, Streamlit, or Retool
  • Reverse Query: AI Recommendations + Rationale + Caution Context

```

---

## 📂 Project Directory Structure

```text
haoshi-platform/
│
├── backend/                 # Python FastAPI Server & AI Engine
│   ├── main.py              # FastAPI endpoints & CORS configuration
│   ├── ai_engine.py         # PaddleOCR & BGE semantic embedding logic
│   └── pyproject.toml       # uv dependency management configuration
│
└── mobile-app/              # React Native / Expo Mobile Client
    ├── App.js               # Mobile intake UI (Text input & image picker)
    └── package.json         # Mobile dependencies

```

---

## 🚀 Getting Started & Installation Guide

Follow these instructions to set up and run both the backend server and the mobile app locally.

### Prerequisites

* **Python 3.10+** installed on your machine.
* **`uv`** (Fast Python package manager) installed.
* **Node.js** & **npm** (for running the React Native / Expo mobile app).
* **Expo Go** app installed on your physical mobile device (or an iOS/Android simulator).

---

### Step 1: Clone the Repository & Setup Backend

1. Clone your repository:
```bash
git clone https://github.com/LV6LASERLOTUS/haoshi-platform.git
cd haoshi-platform/backend

```


2. Initialize and activate your Python virtual environment using `uv`:
```bash
uv venv

```


* **Mac / Linux:** `source .venv/bin/activate`
* **Windows:** `.venv\Scripts\activate`


3. Install backend dependencies:
```bash
uv add fastapi uvicorn paddleocr paddlepaddle sentence-transformers gspread pandas numpy

```


4. Run the FastAPI backend server:
```bash
uvicorn main:app --reload

```


* The server will start at `http://127.0.0.1:8000`.
* You can check the interactive Swagger UI documentation at `http://127.0.0.1:8000/docs`.



---

### Step 2: Setup and Run the Mobile App

1. Open a new terminal window and navigate to the mobile folder:
```bash
cd haoshi-platform/mobile-app

```


2. Install dependencies:
```bash
npm install
npx expo install expo-image-picker

```


3. **Configure API Endpoint (Important for physical devices):**
* Open `App.js` and locate the `fetch` URL.
* If running on an **iOS Simulator**, keep it as `http://127.0.0.1:8000/api/v1/match`.
* If running on a **Physical Device (via Expo Go)**, replace `127.0.0.1` with your computer's local network IP address (e.g., `http://192.168.1.15:8000/api/v1/match`).


4. Start the Expo development server:
```bash
npx expo start

```


5. Scan the QR code using the **Expo Go** app on your iPhone or Android device to load the intake interface.

---

## 🛠️ Tech Stack Summary

* **Frontend Intake:** React Native / Expo (iOS & Android)
* **Backend API:** Python (FastAPI)
* **Local OCR Engine:** PaddleOCR (PP-OCRv3 supporting Traditional/Simplified Chinese)
* **Local Semantic AI:** `BAAI/bge-small-zh-v1.5` (Hugging Face Transformers running completely offline)
* **Database Hub:** Google Sheets (managed via `gspread`)
* **Dashboard Visualizer:** Google Looker Studio / Streamlit / Retool

---