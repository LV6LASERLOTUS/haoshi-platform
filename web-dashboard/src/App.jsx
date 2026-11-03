import React, { useState, useEffect } from 'react';
import './App.css'; // Import regular CSS

export default function App() {
  const [requestContext, setRequestContext] = useState("我們想針對偏鄉國小舉辦為期兩天的科技營隊...");
  const [candidates, setCandidates] = useState([
    { id: 1, name: "台灣偏鄉教育協會", email: "rural.edu@example.org", match_score: 92, rationale: "過去有 5 次偏鄉科技營隊經驗。" },
    { id: 2, name: "青年夢想協進會", email: "youth.dream@example.org", match_score: 85, rationale: "領域契合，但需注意志工調度。" }
  ]);
  const [selectedEmails, setSelectedEmails] = useState(new Set());

  const toggleSelectEmail = (email) => {
    const updated = new Set(selectedEmails);
    if (updated.has(email)) updated.delete(email);
    else updated.add(email);
    setSelectedEmails(updated);
  };

  return (
    <div className="dashboard-container">
      <h1>好事大平台 — 儀表板</h1>

      <div className="card">
        <h3>📌 原始請求脈絡</h3>
        <p>{requestContext}</p>
      </div>

      <div className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span>已選擇 {selectedEmails.size} / {candidates.length} 個單位</span>
        <button 
          className="btn-primary"
          disabled={selectedEmails.size === 0}
          onClick={() => alert(`發送給: ${Array.from(selectedEmails)}`)}
        >
          📧 寄送介紹信
        </button>
      </div>

      <table>
        <thead>
          <tr>
            <th>選取</th>
            <th>排名</th>
            <th>組織名稱與信箱</th>
            <th>適配分數</th>
            <th>推薦理由</th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((c, index) => (
            <tr key={c.id}>
              <td>
                <input 
                  type="checkbox" 
                  checked={selectedEmails.has(c.email)}
                  onChange={() => toggleSelectEmail(c.email)}
                />
              </td>
              <td>#{index + 1}</td>
              <td>
                <strong>{c.name}</strong><br />
                <small style={{ color: '#6b7280' }}>{c.email}</small>
              </td>
              <td>
                <span className="badge">{c.match_score}%</span>
              </td>
              <td>{c.rationale}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}