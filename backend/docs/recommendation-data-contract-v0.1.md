# 獨立條件推薦：資料契約草案 v0.1

> 已封存的早期假設。最新欄位依使用者提供的圖片修正，見 [v0.2](recommendation-data-contract.md)。

本文件定義企業需求、NPO 與合作方案的內部格式，作為接下來實作條件推薦的依據。
這是可調整的第一版規格，資料驗證與舊資料轉接已實作於 `backend/recommendation/`，
尚未接入 API，也沒有改變現有 BGE 推薦。
可讀取的舊假資料見 [recommendation-example-v0.1.json](./recommendation-example-v0.1.json)。

## 1. 目的與資料流

讓 BGE 推薦與新的條件推薦共用資料入口，兩套策略可以獨立執行。

```text
假資料 / Google Sheets / 未來資料來源
                  ↓
來源轉接層：欄位對應、單位轉換、格式檢查
                  ↓
企業需求 + NPO + 合作方案
                  ↓
         BGE 策略 / 條件推薦策略
```

新來源若能表達同樣的業務概念，主要調整來源轉接層。新增概念或修改條件意義時，
仍須修改契約與比對規則；統一格式不代表任意資料都可直接使用。

## 2. 共通規則

- 根物件使用 `schema_version: "0.1"`，表示本文件的結構版本。
- ID 統一為非空字串，不以組織名稱識別資料。
- 日期使用 `YYYY-MM-DD`；`updated_at` 表示來源資料最後更新時間，使用含時區的 ISO 8601 字串。
- 金額使用指定幣別的主要單位，例如 TWD 的元；不接受「15 萬」這種字串。
  此版本範例只使用 TWD，不做自動換匯。
- 人數與準備天數使用非負整數，且不能用 `0` 表示未知。
- `null` 表示未知；缺少選填欄位時，轉接層轉為 `null`。
- 能力清單為 `null` 表示未知，`[]` 表示已確認沒有列出的能力。
  需求清單為 `null` 或 `[]` 表示該項未提出條件。
- 地點以內部地區代碼表示。範例 `TW-CHA` 表示彰化縣；同義名稱由轉接層對應。
  第一版比對縣市，不從「中部」自行推論所有縣市，也不實作距離計算。
- 標籤採可擴充的穩定代碼，顯示文字另行對應；不能讓演算法直接依賴中文名稱。
  例如 `children`（兒童）、`digital_education`（數位教育）、`coding_camp`（程式營隊）。
  正式接入前建立對照表，未識別標籤留下提示，不自動猜測為其他標籤。
- `source` 與 `updated_at` 保留資料依據；無法確認的時間應為 `null`，不可填入匯入時間冒充。
- 保留原始資料供追溯。無法轉換的值回報欄位錯誤，不靜默當成未知或零。

## 3. 企業合作需求 `request`

必填 `id`、`text`；其餘業務條件允許缺漏。結構化條件先由表單或來源提供，
自由文字與 OCR 內容保留在 `text`，不預設第一版已能自動抽取所有條件。

| 欄位 | 型別 | 意義 |
| --- | --- | --- |
| `id` | string | 本次需求識別碼 |
| `text` | string | 原始需求文字，可包含 OCR 內容 |
| `target_groups` | string[] / null | 服務對象 |
| `issue_tags` | string[] / null | 關注議題，與服務對象分開 |
| `activity_types` | string[] / null | 希望執行的活動類型 |
| `cooperation_modes` | string[] / null | 員工志工、捐款、活動共辦等合作方式 |
| `location_codes` | string[] / null | 希望活動發生的地區 |
| `budget` | object / null | `max_amount`、`currency`；本次專案總預算上限 |
| `event_dates` | string[] / null | 必須執行活動的日期清單；空清單表示未指定 |
| `submitted_on` | date / null | 提出需求的日期，用來計算準備期；缺漏時不能判定準備期 |
| `beneficiary_count` | integer / null | 預計服務人數 |
| `employee_volunteer_count` | integer / null | 預計參與的企業員工志工人數 |
| `required_fields` | string[] | 哪些條件為必要條件，其餘已填條件為偏好 |

`required_fields` 只能引用上述可比對的條件欄位，不能包含未填值的欄位。
已知 `submitted_on` 時，需求日期不得早於該日。同欄位多值的意義須固定：
`location_codes` 表示任一地區均可；`target_groups`、`issue_tags`、`activity_types`、
`cooperation_modes` 表示希望全部涵蓋，部分涵蓋則為部分符合。
`event_dates` 是全部必須可執行的日期，不是任選日期。

## 4. NPO 組織 `organizations[]`

必填 `id`、`name`；其他欄位允許缺漏。

| 欄位 | 型別 | 意義 |
| --- | --- | --- |
| `id` | string | 穩定的組織識別碼 |
| `name` | string | 組織名稱 |
| `description` | string / null | 使命與服務介紹；可供 BGE 使用 |
| `target_groups` | string[] / null | 組織整體服務對象 |
| `issue_tags` | string[] / null | 組織關注議題 |
| `service_location_codes` | string[] / null | 實際可服務地區，不是總部地址 |
| `source` | string / null | 資料來源識別或網址 |
| `updated_at` | datetime / null | 來源最後更新時間 |

第一版轉接現有資料時：`id → id`、`name → name`、`focus → description`，
其他未知條件保留 `null`，不從名稱推論地區或能力。

## 5. 合作方案 `programs[]`

必填 `id`、`organization_id`、`name`。`organization_id` 必須指向存在的組織。
費用、容量與時程屬於具體方案，不能直接當成整個 NPO 的固定屬性。

| 欄位 | 型別 | 意義 |
| --- | --- | --- |
| `id` | string | 方案識別碼 |
| `organization_id` | string | 所屬 NPO |
| `name` | string | 方案名稱 |
| `description` | string / null | 方案內容 |
| `target_groups` | string[] / null | 此方案服務對象 |
| `issue_tags` | string[] / null | 此方案議題 |
| `activity_types` | string[] / null | 此方案具備的活動能力 |
| `cooperation_modes` | string[] / null | 此方案接受的合作方式 |
| `service_location_codes` | string[] / null | 此方案可執行地區 |
| `cost` | object / null | `min_amount`、`max_amount`、`currency`、`includes_all_costs` |
| `max_beneficiaries` | integer / null | 此方案可服務人數上限 |
| `max_employee_volunteers` | integer / null | 此方案可接待企業員工志工人數上限 |
| `minimum_lead_days` | integer / null | 最少準備天數，以日曆天計算 |
| `available_dates` | string[] / null | 在 `availability_window` 內已確認可執行的日期 |
| `availability_window` | object / null | 已確認檔期的 `start` 與 `end`（含起訖日） |
| `source` | string / null | 方案資料來源 |
| `updated_at` | datetime / null | 來源最後更新時間 |

金額上下限皆非負且 `min_amount <= max_amount`。
費用區間與企業預算有交集僅代表「可能可行」，不保證在指定規模下足夠。
`includes_all_costs` 為 false 或未知時，提示交通、材料等費用待確認。
幣別不同時標示未知，不直接比較數字。

檔期範圍外一律為未知；範圍內未列入 `available_dates` 的日期才算不可執行。
可用日期必須落在範圍內；日期清單與範圍須一起提供或一起未知。
方案能力不自動繼承組織資料；組織整體有能力，不等於每個方案都提供。
只有組織介紹而沒有方案時，仍可走 BGE 或組織層比對，但方案條件保持未知。

## 6. 下一步比對器的輸出約定

每個條件產生：`field`、`status`、`score`、`reason`、`evidence`。

- `status`：`matched`、`partial`、`mismatched`、`unknown`。
- `score`：已知條件為 0～1；未知為 `null`。
- `reason`：說明符合或不足的原因，不能把相似度寫成合作成功機率。
- `evidence`：引用實際使用的欄位值與來源；沒有證據不能生成肯定敘述。

必要條件明確不符時排除；必要條件未知或僅部分符合時列為「待確認」，
不能放進「全部必要條件已通過」的清單。未設定必要條件時不憑空增加門檻。
偏好缺值不直接算零；適配分數與資料涵蓋率分開呈現，避免少量資料造成假高分。
下一步才實作比對與排序，權重尚未在此草案固定。

## 7. 後續順序

1. 已完成：依本契約建立資料驗證與現有假資料轉接層（執行方式見 backend README）。
2. 實作獨立的條件比對器，先做對象、議題、活動、合作方式與服務地區。
3. 加入方案費用、規模、檔期與準備期判斷。
4. 產生帶依據的評分明細與 Top-K，再接 API 與既有卡片。
5. 真實資料到手後建立欄位對照，驗證缺漏率與推薦效果，再比較 BGE。
