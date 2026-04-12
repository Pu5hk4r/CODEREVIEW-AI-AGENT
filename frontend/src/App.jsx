import React, { useState, useEffect } from "react";

const API = "https://codereview-backend-668034153514.asia-south1.run.app/reviews";

const SEVERITY_COLOR = {
  critical:   { bg: "#ff47571a", border: "#ff4757", text: "#ff4757", icon: "🔴" },
  warning:    { bg: "#ffd60a1a", border: "#ffd60a", text: "#ffd60a", icon: "🟡" },
  suggestion: { bg: "#00e5ff1a", border: "#00e5ff", text: "#00e5ff", icon: "🔵" },
};

function StatCard({ label, value, color = "#f0f0f0" }) {
  return (
    <div style={{
      background: "#161616", border: "1px solid #2a2a2a", borderRadius: 4,
      padding: "20px 24px", flex: 1, minWidth: 120,
    }}>
      <div style={{ fontSize: 11, color: "#666", letterSpacing: 2, marginBottom: 8 }}>{label}</div>
      <div style={{ fontSize: 32, fontWeight: 700, color }}>{value}</div>
    </div>
  );
}

function ReviewCard({ review, onClick, selected }) {
  const border = selected ? "#00e5ff" : "#2a2a2a";
  return (
    <div
      onClick={() => onClick(review)}
      style={{
        background: "#161616", border: `1px solid ${border}`, borderRadius: 4,
        padding: "18px 20px", cursor: "pointer", transition: "border-color .15s",
        borderLeft: `3px solid ${review.approved ? "#00ff88" : "#ff4757"}`,
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <div style={{ fontSize: 12, fontWeight: 600, marginBottom: 4 }}>
            PR #{review.pr_number} — {review.pr_title || "Untitled"}
          </div>
          <div style={{ fontSize: 10, color: "#666", marginBottom: 8 }}>{review.repo_name}</div>
        </div>
        <span style={{
          fontSize: 9, padding: "3px 10px", borderRadius: 2, letterSpacing: 1,
          background: review.approved ? "#00ff8812" : "#ff475712",
          border: `1px solid ${review.approved ? "#00ff8844" : "#ff475744"}`,
          color: review.approved ? "#00ff88" : "#ff4757",
        }}>
          {review.approved ? "APPROVED" : "CHANGES NEEDED"}
        </span>
      </div>
      <div style={{ display: "flex", gap: 12, fontSize: 10 }}>
        <span style={{ color: "#ff4757" }}>🔴 {review.critical_count} critical</span>
        <span style={{ color: "#ffd60a" }}>🟡 {review.warning_count} warnings</span>
        <span style={{ color: "#00e5ff" }}>🔵 {review.suggestion_count} suggestions</span>
      </div>
      <div style={{ fontSize: 9, color: "#444", marginTop: 8 }}>
        {new Date(review.reviewed_at).toLocaleString()}
      </div>
    </div>
  );
}

function CommentItem({ comment }) {
  const s = SEVERITY_COLOR[comment.severity] || SEVERITY_COLOR.suggestion;
  return (
    <div style={{
      background: s.bg, border: `1px solid ${s.border}22`, borderRadius: 3,
      padding: "14px 16px", marginBottom: 10,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
        <span>{s.icon}</span>
        <span style={{ fontSize: 9, color: s.text, letterSpacing: 1 }}>{comment.severity.toUpperCase()}</span>
        <span style={{ fontSize: 12, fontWeight: 600 }}>{comment.title}</span>
      </div>
      <div style={{ fontSize: 10, color: "#888", marginBottom: 6 }}>
        📄 {comment.file_path}{comment.line_number ? ` line ${comment.line_number}` : ""}
      </div>
      <div style={{ fontSize: 11, color: "#ccc", lineHeight: 1.7 }}>{comment.body}</div>
      {comment.suggestion && (
        <pre style={{
          marginTop: 10, padding: "10px 12px", background: "#0a0a0a",
          border: "1px solid #333", borderRadius: 3, fontSize: 10,
          color: "#c3e88d", overflowX: "auto",
        }}>{comment.suggestion}</pre>
      )}
    </div>
  );
}

export default function App() {
  const [reviews, setReviews] = useState([]);
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`${API}/reviews`)
      .then(r => r.json())
      .then(d => { setReviews(d.reviews || []); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, []);

  const totalCritical = reviews.reduce((s, r) => s + (r.critical_count || 0), 0);
  const totalWarnings = reviews.reduce((s, r) => s + (r.warning_count || 0), 0);
  const approved      = reviews.filter(r => r.approved).length;

  return (
    <div style={{ background: "#0f0f0f", minHeight: "100vh", color: "#f0f0f0", fontFamily: "'IBM Plex Mono', monospace" }}>

      {/* Header */}
      <div style={{ borderBottom: "1px solid #2a2a2a", padding: "20px 32px", display: "flex", alignItems: "center", gap: 16 }}>
        <div style={{ width: 8, height: 8, borderRadius: "50%", background: "#00ff88" }} />
        <span style={{ fontSize: 13, fontWeight: 600, letterSpacing: 1 }}>CodeReview AI Agent</span>
        <span style={{ fontSize: 10, color: "#444", marginLeft: 8 }}>powered by Groq</span>
      </div>

      <div style={{ padding: 32 }}>

        {/* Stats */}
        <div style={{ display: "flex", gap: 12, marginBottom: 32, flexWrap: "wrap" }}>
          <StatCard label="TOTAL REVIEWS"    value={reviews.length} />
          <StatCard label="APPROVED"         value={approved}         color="#00ff88" />
          <StatCard label="CRITICAL ISSUES"  value={totalCritical}    color="#ff4757" />
          <StatCard label="WARNINGS"         value={totalWarnings}    color="#ffd60a" />
        </div>

        {/* Main content */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1.5fr", gap: 24, alignItems: "flex-start" }}>

          {/* Left: Review list */}
          <div>
            <div style={{ fontSize: 10, color: "#444", letterSpacing: 2, marginBottom: 12 }}>
              RECENT REVIEWS // {reviews.length} total
            </div>

            {loading && <div style={{ color: "#666", fontSize: 12 }}>Loading reviews...</div>}
            {error   && <div style={{ color: "#ff4757", fontSize: 12 }}>Error: {error}<br/>Make sure the API is running at {API}</div>}
            {!loading && !error && reviews.length === 0 && (
              <div style={{ color: "#666", fontSize: 12, lineHeight: 2 }}>
                No reviews yet.<br/>
                Open a PR to trigger a review,<br/>
                or run: python scripts/test_phase4.py
              </div>
            )}

            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {reviews.map(r => (
                <ReviewCard key={r.id} review={r} onClick={setSelected} selected={selected?.id === r.id} />
              ))}
            </div>
          </div>

          {/* Right: Review detail */}
          <div>
            {!selected ? (
              <div style={{
                background: "#161616", border: "1px solid #2a2a2a", borderRadius: 4,
                padding: 40, textAlign: "center", color: "#444", fontSize: 11,
              }}>
                Select a review to see details
              </div>
            ) : (
              <div style={{ background: "#161616", border: "1px solid #2a2a2a", borderRadius: 4, padding: 24 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                    PR #{selected.pr_number} — {selected.pr_title}
                  </div>
                  <div style={{ fontSize: 10, color: "#666" }}>
                    {selected.repo_name} · by {selected.pr_author} · {new Date(selected.reviewed_at).toLocaleString()}
                  </div>
                </div>

                <div style={{
                  padding: "12px 16px", background: "#0f0f0f", borderRadius: 3,
                  border: `1px solid ${selected.approved ? "#00ff8833" : "#ff475733"}`,
                  marginBottom: 20, fontSize: 11, lineHeight: 1.7, color: "#ccc",
                }}>
                  {selected.summary}
                </div>

                <div style={{ fontSize: 10, color: "#444", letterSpacing: 2, marginBottom: 12 }}>
                  ISSUES — {selected.comments?.length || 0} total
                </div>

                {(selected.comments || []).length === 0 ? (
                  <div style={{ color: "#666", fontSize: 11 }}>No issues found — clean PR! ✅</div>
                ) : (
                  selected.comments.map((c, i) => <CommentItem key={i} comment={c} />)
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
