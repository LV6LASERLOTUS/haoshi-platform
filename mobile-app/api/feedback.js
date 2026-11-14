// 回饋修正 API：FeedbackSheet 送出時呼叫
// payload 形狀：{ question_id, question_text, ai_summary, rating, feedback_type, feedback_content }
import { API_BASE } from './match';

// 丟出錯誤時，FeedbackSheet 會顯示「送出失敗，請稍後再試一次」。
export async function submitFeedback(payload) {
  if (typeof __DEV__ !== 'undefined' && __DEV__) console.log('[feedback]', payload);
  const response = await fetch(`${API_BASE}/api/v1/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

// 每次搜尋產生一個問題 ID，例如 Q-20261113-0042
export function makeQuestionId(searchId, date = new Date()) {
  const ymd = `${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}`;
  return `Q-${ymd}-${String(searchId).padStart(4, '0')}`;
}
