🤝 好事大平台 (Haoshi Platform)
> 一個以隱私優先的全端合作媒合平台，利用本地端繁/簡體中文 OCR 與語意 AI 嵌入技術，將企業 CSR 需求與非政府組織（NPO）進行智慧配對——完全無需付費雲端 API。
<p align="center">
  <img width="380" height="700" alt="好是大平台app_result" src="https://github.com/user-attachments/assets/1faa9968-586d-41ce-878a-4ffb21667ded" />
  &nbsp;&nbsp;&nbsp;&nbsp;
  <img width="380" height="700" alt="好是大平台app_search" src="https://github.com/user-attachments/assets/c3ff1e6c-8617-4f6e-9d87-aa5f4d2fd7f8" />
</p>

---

## 🏗️ 系統架構流程

```mermaid
flowchart TD
    subgraph Frontend["1. 前端 App 介面 (React Native / React Web)"]
        Input["📝 輸入合作需求文字 & 上傳圖片／提案檔案"]
        Result["📊 瀏覽推薦 NPO、匹配分數與理由 & 發送合作信"]
    end

    subgraph Backend["2. Python FastAPI 後端與本地 AI 引擎"]
        API["⚡ FastAPI 接收請求"]
        OCR["🔍 本地端 OCR (PaddleOCR)<br/>從上傳檔案中擷取中文文字"]
        Embed["🧠 本地語意 AI (BGE 模型)<br/>比對需求文字與 NPO 核心任務的語意相似度"]
        Rank["🏆 計算匹配度並排序最佳人選"]
        LLM["🤖 LLM 讀取Skill與回饋<br/>優化推薦內容與說明"]
    end

    subgraph Data["3. 資料中樞"]
        DB[("📄 Google Sheets<br/>NPO 資料庫")]
    end

    Input -- "發送配對請求 (文字 + 附件)" --> API
    API -- "若有附件" --> OCR
    OCR -- "合併擷取文字" --> Embed
    API -- "純文字需求" --> Embed
    DB -- "讀取 NPO 資料" --> Embed
    Embed --> Rank
    Rank --> LLM
    LLM -- "回傳最終推薦結果與理由" --> Result
```

---

## 📂 專案目錄結構

```text
haoshi-platform/
│
├── backend/                 # Python FastAPI 伺服器與 AI 引擎
│   ├── main.py              # FastAPI 端點與 CORS 設定
│   ├── ai_engine.py         # PaddleOCR 與 BGE 語意嵌入邏輯
│   ├── database.py          # gspread 讀取 Google Sheets NPO 資料
│   └── pyproject.toml       # uv 相依套件管理設定檔
│
├── mobile-app/              # React Native / Expo 行動客戶端
│   ├── App.js               # 行動裝置資料輸入介面（文字輸入與圖片選取）
│   ├── components/          # CandidateCard、EmailActionToolbar、RequestBanner
│   └── package.json         # 行動端相依套件
│
└── web-dashboard/           # React + Vite 網頁儀表板
```

---

## 🚀 快速開始與安裝指南

請依照以下步驟在本機端設定並執行後端伺服器與行動應用程式。

### 前置需求

* 已安裝 **Python 3.10+**。
* 已安裝 **`uv`**（快速 Python 套件管理工具）。
* 已安裝 **Node.js** 與 **npm**（用於執行 React Native / Expo 行動應用程式）。
* 已在實體行動裝置上安裝 **Expo Go** 應用程式（或已設定 iOS／Android 模擬器）。

---

### 步驟一：複製儲存庫並設定後端

1. 複製您的儲存庫：
```bash
git clone https://github.com/LV6LASERLOTUS/haoshi-platform.git
cd haoshi-platform/backend
```

2. 使用 `uv` 初始化並啟動 Python 虛擬環境：
```bash
uv venv
```

* **Mac / Linux：** `source .venv/bin/activate`
* **Windows：** `.venv\Scripts\activate`

3. 安裝後端相依套件：
```bash
uv add fastapi uvicorn paddleocr paddlepaddle sentence-transformers gspread pandas numpy
```

4. 啟動 FastAPI 後端伺服器：
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

* 伺服器將在 `http://127.0.0.1:8000` 啟動。
* 可前往 `http://127.0.0.1:8000/docs` 查看互動式 Swagger UI 文件。

---

### 步驟二：設定並執行行動應用程式

1. 開啟新終端機視窗，並切換至 mobile 資料夾：
```bash
cd haoshi-platform/mobile-app
```

2. 安裝相依套件：
```bash
npm install
npx expo install expo-image-picker
```

3. **設定 API 端點（⚠️ 必要，請改成您自己的電腦 IP）：**

> [!IMPORTANT]
> App 透過 `mobile-app/.env` 中的 `EXPO_PUBLIC_API_BASE` 連線到後端。
> 使用**實體手機（Expo Go）**時，**請務必填入您自己電腦的區網 IP**，否則 App 會連不到後端，送出需求後會逾時或失敗。
> `.env` 已列入 `.gitignore`，每位開發者各自設定，不會被 commit。

   * 從範本建立 `.env`：
     ```bash
     cp .env.example .env
     ```
   * 查詢您電腦的區網 IP：
     * **Mac：** `ipconfig getifaddr en0`
     * **Windows：** `ipconfig`（找「IPv4 位址」）
     * **Linux：** `hostname -I`
   * 編輯 `mobile-app/.env`，將 `192.168.x.x` 替換為您的 IP：
     ```bash
     EXPO_PUBLIC_API_BASE=http://<您的電腦IP>:8000
     ```
   * 修改 `.env` 後需**重新啟動** `npx expo start` 才會生效。
   * 若未建立 `.env`，則使用預設值：iOS 模擬器／網頁 → `http://localhost:8000`；Android 模擬器 → `http://10.0.2.2:8000`。
   * 手機與電腦必須連在**同一個 Wi-Fi 網路**，且後端需以 `--host 0.0.0.0` 啟動（見步驟一）。

4. 啟動 Expo 開發伺服器：
```bash
npx expo start
```

5. 使用 iPhone 或 Android 裝置上的 **Expo Go** 掃描 QR 碼，即可載入資料輸入介面。

---

## 🛠️ 技術棧總覽

* **前端輸入：** React Native / Expo（iOS 與 Android）
* **後端 API：** Python（FastAPI）
* **本地端 OCR 引擎：** PaddleOCR（PP-OCRv3，支援繁體及簡體中文）
* **本地端語意 AI：** `BAAI/bge-small-zh-v1.5`（Hugging Face Transformers，完全離線運行）
* **資料中樞：** Google Sheets（透過 `gspread` 管理）
* **儀表板視覺化：** Google Looker Studio / Streamlit / Retool

---
