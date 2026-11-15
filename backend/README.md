# 推薦功能開發

本地整合與模組分工、離線測試及真實 BGE 測試見 [開發與測試指南](docs/recommendation-development.md)。
在專案根目錄執行 `python backend/scripts/check_recommendation.py` 可一次完成推薦測試與規則推薦範例。

目前先依使用者提供的圖片建立組織資料，再討論推薦演算法：

- [資料規格 v0.2](docs/recommendation-data-contract.md)：圖片欄位對照、待確認的意義與缺漏處理。
- [主要假資料](docs/recommendation-example.json)：48 家組織、200 筆接觸紀錄、20 筆顧問筆記（14 家有）、2 張任務卡。
- [假資料生成器](scripts/generate_mock_data.py)：固定種子與日期，可重現同一份資料。

組織主檔、接觸紀錄與顧問筆記以 `organization_id` 串接，全部為虛構資料。
任務卡是兩種使用情境，不是已計算的推薦結果。
`recommendation/` 已提供資料驗證、獨立條件推薦、BGE 語意推薦與混合排序。
既有 API 與前端尚未切換到新入口。流程與分數說明見 [推薦流程](docs/recommendation-pipeline.md)。

## 執行推薦

在 `backend/` 執行：

```bash
python -m recommendation docs/recommendation-example.json --request docs/recommendation-request-example.json --strategy rules --output .cache/recommendation-rules.json
python -m recommendation docs/recommendation-example.json --request docs/recommendation-request-example.json --strategy compare --output .cache/recommendation-comparison.json
```

`rules` 不需要模型；`bge`、`hybrid` 與 `compare` 在有候選文字時需要本機 BGE 與既有 AI 相依套件。
預設不下載模型，可用 `--model` 指定本機中文 BGE 模型目錄。
[範例需求](docs/recommendation-request-example.json) 將必要地區與偏好條件分開。
先檢查必要條件，再對所有未排除候選各自做規則與語意排序，以 RRF 融合。
未知的必要條件進待確認名單；結果不足時不強湊數量。模型不可用時顯示錯誤，不暗中改用規則。
比較結果的後續策略會重用快取，`elapsed_ms` 不是公平的效能基準，也不是 P95。

## 驗證資料

以下指令在 `backend/` 目錄執行，使用 Python 3.11 以上版本，無需額外套件、模型或憑證：

```bash
python -m recommendation docs/recommendation-example.json
python -m unittest discover -s tests -p "test_recommendation*.py" -v
```

第一個指令依版本驗證 JSON，成功時顯示各類資料數量；失敗時顯示欄位路徑與錯誤代碼，並回傳非零結束碼。
v0.2 檢查跨表組織關聯、重複 ID、日期與欄位型別，不要求正式資料固定為 48 家。

重建假資料（預設更新主要 JSON）：

```bash
python scripts/generate_mock_data.py
```

載入主要資料：

```python
import json
from pathlib import Path
from recommendation import adapt_dataset

payload = json.loads(Path("docs/recommendation-example.json").read_text(encoding="utf-8"))
result = adapt_dataset(payload)
organizations = result.data["organizations"]
contacts = result.data["contacts"]
notes = result.data["consultant_notes"]
```

## 舊版轉接相容性（v0.1）

早期的「企業需求／NPO／合作方案」假設保留於
[舊規格](docs/recommendation-data-contract-v0.1.md) 與 [舊範例](docs/recommendation-example-v0.1.json)。
以下轉接器仍輸出 v0.1，用於相容現有 `id/name/focus`；不會自動產生 v0.2 的接觸紀錄或筆記。

```python
from recommendation import adapt_dataset, adapt_legacy_npos, DataValidationError

# 現有 mock 或 Google Sheets 的 id/name/focus 資料列。
result = adapt_legacy_npos(
    [{"id": 1, "name": "範例協會", "focus": "兒童教育"}],
    {"id": "request-001", "text": "想找教育合作夥伴"},
    source="mock:example",
)

# 來源欄位改名，只調整 mapping；不需要修改後續推薦演算法。
renamed = adapt_legacy_npos(
    [{"編號": "npo-001", "單位名稱": "範例協會", "服務簡介": "兒童教育"}],
    {"id": "request-002", "text": "想找教育合作夥伴"},
    field_mapping={"id": "編號", "name": "單位名稱", "description": "服務簡介"},
    source="sheet:npos",
)

# 已符合資料契約的新資料走同一個驗證入口。
validated = adapt_dataset(result.data)
```

- `result.data`：驗證、補齊未知欄位後的統一資料。
- `result.raw_data`：保留原始輸入的獨立副本，供追溯，未寫入檔案或遠端服務。
- `result.warnings`：舊資料能力不足或有未對應欄位的提示。
- `DataValidationError.issues`：包含 `path`、`code`、`message` 的欄位錯誤清單。

舊資料轉接器只匯入身份與簡介，整數 ID 轉為字串、簡介空字串轉為未知；
不從名稱猜地區，也不把未對應的預算或能力欄位自動用於推薦。
v0.1 檢查英文標籤與地區代碼格式，v0.2 則保留可讀中文類別；兩者不自動互換。
兩版皆未提供正式代碼表或來源別名轉換，未來接入正式資料時再明確定義。
標準格式拒絕未知欄位，以免拼字錯誤造成條件靜默失效。
