# 推薦模組：本地整合、架構與測試

## 這次整合的範圍

推薦模組以現有 API 與資料讀取流程為基底，提供可獨立呼叫的後端推薦功能與測試。
本次交付包含後端模組、假資料、測試與文件；API 與前端串接由後續整合處理。

現有的 `main.py` 仍回傳固定三筆展示結果，App 透過既有 API 顯示。
本推薦模組目前從函式或命令列獨立執行，不會因為還原檔案就自動改變 App 顯示。

## 模組分工

```text
recommendation/
  validation.py          統一入口與共用型別檢查；支援 v0.1 / v0.2
  source_validation.py   v0.2 主檔、接觸與筆記的資料關聯檢查
  adapters.py            現有資料轉接、原始資料保留與欄位錯誤
  matching.py            驗證需求條件、判斷符合程度與必要條件
  evidence.py            準備有來源、日期與長度限制的文字片段
  semantic.py            BGE 載入、批次編碼、快取與語意分數聚合
  ranking.py             各群組排序、同分處理與 RRF 融合
  engine.py              recommend() 主流程：呼叫上述模組、組成結果
  __main__.py            命令列參數與 JSON 輸入輸出
```

`recommend()` 的主流程是：驗證輸入 → 建立候選與條件明細 → 選擇性語意計分 → 分組排序 → 組成結果。
主流程不直接讀 Google Sheets、不接收 HTTP、不處理畫面。
變更條件判斷時改 `matching.py`，變更文字取樣時改 `evidence.py`，變更融合方式時改 `ranking.py`。
`SemanticScorer` 是模型介面；替換模型或測試時只要提供 `score(query, texts)`。
測試替身只供單元測試使用，實際 `--with-bge` 與正式入口都不會用替身冒充 BGE。

## 不需要 App 的基本測試

在專案根目錄執行，使用 Python 3.11 以上版本：

```powershell
python backend/scripts/check_recommendation.py
```

這支指令不需要 FastAPI、OCR、Google 憑證或 BGE 套件。它會：

1. 執行 `test_recommendation*.py` 的離線測試。
2. 使用 48 家組織與範例需求執行真實條件推薦。
3. 在終端機列出本次推薦的單位名稱與組織編號，並將規則推薦明細與測試摘要寫入 `backend/.cache/recommendation-check/`。
4. 成功回傳 0，測試或範例失敗回傳 1。

本機若 `python` 指到 Windows Store、無法執行，可使用已確認可用的 Anaconda Python：

```powershell
& "$env:USERPROFILE\anaconda3\python.exe" backend/scripts/check_recommendation.py
```

加上 `--verbose` 可列出各項測試名稱。只跑測試、不寫範例報告可在 `backend/` 執行：

```powershell
python -m unittest discover -s tests -p "test_recommendation*.py" -v
```

測試涵蓋：必要條件排除與未知、零人與缺值、資料關聯、重複 ID、錯誤日期、
部分符合、覆蓋率、三種策略差異、同分排序、候選輸入順序、待確認名單隔離、
BGE 分數有效性、批次與快取，以及在不載入第三方套件時執行規則 CLI。

## 使用真實本機 BGE 測試

本機需事先準備好與專案相容的 Sentence Transformers 與中文 BGE 模型：

```powershell
python backend/scripts/check_recommendation.py --with-bge
```

或指定模型目錄：

```powershell
python backend/scripts/check_recommendation.py --with-bge --model "C:\models\bge-small-zh-v1.5"
```

這會先跑離線測試，再跑 rules、bge、hybrid 三份真實推薦報告；模型不存在時明確失敗，不自動下載。
測試假資料只能確認能執行與遵守規則，不能證明推薦品質。比較準確率仍需要人工標註案例。
三種模式依序跑，後面會重用快取，不能直接用報告中的耗時比較策略速度或當 P95。

## 如何檢查輸出

開啟 `backend/.cache/recommendation-check/summary.json` 查看測試數量、候選統計與報告路徑。
未加 `--with-bge` 時只更新 `rules.json` 與摘要；若資料夾內已有 `bge.json` 或 `hybrid.json`，
它們仍是先前執行的結果，終端機會提示本次未更新。
`rules.json`、`bge.json`、`hybrid.json` 分別包含：

- `top_matches`：通過本次必要條件的前 K 家。
- `pending_matches`：必要條件未知或僅部分符合，需確認。
- `excluded`：有明確不符的必要條件。
- 各候選的 `criteria`、`coverage`、`rule_score`、`semantic_score` 與引用片段。

目前範例應有 23 家通過、1 家待確認、24 家排除，Top-K 回傳 10 家。
這些數量只用於檢查此範例，不是演算法固定門檻。修改範例需求後數量可以改變。
報告放在 `.cache`，不會自動加入 Git。

## 與朋友的資料來源如何接合

`database.load_npos_from_sheets()` 目前回傳「分頁名稱 → Worksheet 物件」，
尚不是本推薦模組需要的主檔、接觸、筆記資料列，也尚未接入朋友的展示 API。
後續應在來源轉接層呼叫選定分頁的 `get_all_records()`，確認正式欄名後再轉成 v0.2。
不直接把 Worksheet 丟進 `recommend()`，也不在這次測試連線真實表單。

`tests/test_database.py` 是朋友新增的真實 Sheets 測試，需要憑證與網路；
`tests/test_backend.py` 另有舊 AI 測試，匯入會初始化 OCR/BGE。
本次測試入口刻意只收集推薦測試，不代表上述整個後端測試集已通過。
啟動既有 API 還需要 `python-multipart` 等專案相依套件，與離線推薦測試分開處理。

## 之後與前端同事交接

既有 App 的回傳轉換與卡片期待展示分數及預算／經驗明細；本推薦引擎回傳的是有明確意義的原始分數。
之後由 API 轉換層與前端同事對齊，不把 RRF 直接乘以 100，也不替未知的預算或經驗補分。
核心演算法維持 `recommend(dataset, request, strategy=..., semantic_scorer=...)` 介面，
方便另接新的路由或由既有路由呼叫。
