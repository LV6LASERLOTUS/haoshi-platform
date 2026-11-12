// 後端媒合 API：負責網路請求，並把後端回傳格式轉成 ResultCard 使用的格式
import { Platform } from 'react-native';

// 在 mobile-app/.env 設定 EXPO_PUBLIC_API_BASE（實體手機請填電腦的區網 IP，見 .env.example）
// 未設定時的預設值：iOS 模擬器 / 網頁 → localhost；Android 模擬器 → 10.0.2.2
export const API_BASE =
  process.env.EXPO_PUBLIC_API_BASE ??
  (Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000');

const REQUEST_TIMEOUT_MS = 20000;

export async function fetchMatches({ text, category, area, budget, file }) {
  const form = new FormData();
  form.append('request_text', text);
  // 後端目前尚未讀取以下欄位 — 準備好後在 main.py 加上對應的 Form(...) 參數
  form.append('category', category);
  form.append('area', area);
  form.append('budget', budget);
  if (file) form.append('uploaded_file', { uri: file.uri, name: file.name, type: file.type });

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
  try {
    const response = await fetch(`${API_BASE}/api/v1/match`, {
      method: 'POST',
      body: form,
      signal: controller.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const json = await response.json();
    return (json.top_matches ?? []).map(toCard);
  } finally {
    clearTimeout(timeoutId);
  }
}

// 後端格式 → ResultCard 格式（見 ARCHITECTURE.md 第 4 節）
function toCard(match) {
  const percent = Math.round(match.match_score * 100);
  return {
    n: match.npo_name,
    p: percent,
    why: match.reason,
    c: match.category ?? '—',
    a: match.area ?? '—',
    t: match.tags ?? [],
    w: match.warnings ?? [],
    s: match.breakdown ?? { 領域: percent, 地區: percent, 預算: percent, 經驗: percent },
  };
}
