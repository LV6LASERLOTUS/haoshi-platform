"""Versioned V1 policy assumptions, not empirically calibrated parameters."""

VERSION = "csr-v1.2.0"
UNKNOWN_BASELINE = 30.0
COVERAGE_THRESHOLD = 0.60
# No maximum age: a two-year half-life is a transparent policy assumption, not
# a calibrated probability. Old evidence stays searchable and attributable.
EVIDENCE_HALF_LIFE_DAYS = 730
UNDATED_EVIDENCE_TRUST = 0.35
CONFIRMATION_TRUST_THRESHOLD = 0.60
# Aggregate at most three distinct passages AFTER semantic search, not before it.
SEMANTIC_REFERENCE_LIMIT = 3

# direct / adjacent / weak describe resource needs, never organizational quality.
RESOURCES = {
    "marketing": {"label": "公關行銷與對外溝通培力", "direct": ("公關", "行銷", "社群經營", "社群溝通"), "adjacent": ("對外溝通", "影響力故事", "募款故事", "募款"), "weak": ("年度成果報告", "資訊公開")},
    "finance": {"label": "財務管理與內控制度培力", "direct": ("財務", "財報", "會計", "內控", "帳務"), "adjacent": ("現金周轉", "安全準備金", "職能分立"), "weak": ("資訊公開",)},
    "digital": {"label": "數位工具與資訊安全培力", "direct": ("數位工具", "資安", "資訊安全", "雲端協作", "AI工具", "AI 工具"), "adjacent": ("行政時間", "資料整理"), "weak": ()},
    "impact": {"label": "社會影響力衡量與成效指標培力", "direct": ("影響力衡量", "成效指標", "建立指標", "數據呈現"), "adjacent": ("影響力", "組織的改變"), "weak": ("年度成果報告",)},
    "volunteers": {"label": "企業志工與活動合作資源", "direct": ("志工", "活動協助", "活動人力"), "adjacent": ("人力支援",), "weak": ()},
    "funding": {"label": "資金與經費支持", "direct": ("資金", "經費", "補助", "現金周轉"), "adjacent": ("募款",), "weak": ()},
    "materials": {"label": "物資與設備支持", "direct": ("物資", "設備", "電腦捐贈"), "adjacent": (), "weak": ()},
    "other": {"label": "企業指定資源", "direct": (), "adjacent": (), "weak": ()},
}

TEMPLATES = {
    "professional_resources": {"resource_need": .50, "readiness": .25, "time": .15, "size": .10},
    "issue_collaboration": {"semantic": .50, "issue": .20, "target": .15, "area": .15},
    "volunteering": {"resource_need": .50, "readiness": .20, "time": .15, "area": .15},
    "resource_support": {"resource_need": .65, "time": .15, "area": .20},
}
OPTIONAL_WEIGHTS = {"issue": .10, "target": .10, "area": .10, "size": .10, "membership": .05, "time": .15}
DIMENSIONS = ("resource_need", "semantic", "readiness", "time", "size", "issue", "target", "area", "membership", "participation")
PROFILE_COLUMNS = ("組織編號", "組織名稱", "一句話簡介", "議題", "服務對象", "區域", "成立年", "入會年", "會籍", "全職人數", "財報類型", "桑基圖上架", "陪跑分級")
