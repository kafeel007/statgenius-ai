VIEWS.dashboard = async m => {
  const d = await api("/api/progress"), st = await api("/api/status");
  const sample = d.user.is_demo ? `<span class="tag sample">SAMPLE DATA</span>` : "";
  m.innerHTML = `<div class="view"><h2>Welcome, ${esc(d.user.name)} ${sample}</h2>
  <div class="note">${st.ai_available ? "AI mode active (server-side)." : "Demo mode: deterministic content, no AI key configured."} Scores come from short quizzes and are indicators only, not a measure of professional competency.</div>
  <div class="grid g5">
   <div class="card stat"><b>${d.overall}%</b><span>Overall competency (quiz-based)</span></div>
   <div class="card stat"><b>${d.completed_activities}</b><span>Learning activities completed</span></div>
   <div class="card stat"><b>${d.quiz_accuracy ?? "-"}${d.quiz_accuracy != null ? "%" : ""}</b><span>Practice quiz accuracy (${d.quizzes_taken} quizzes)</span></div>
   <div class="card stat"><b>${d.minutes} min</b><span>Learning time</span></div>
   <div class="card stat"><b>${d.report.priority.length}</b><span>Topics needing improvement</span></div></div>
  <div class="card" style="margin:1rem 0"><h3>Recommended next activity</h3>${d.next ? `<p><b>${esc(d.next.label)}</b> - ${esc(d.next.topic)} (~${d.next.minutes} min, ${esc(d.next.difficulty)})</p><p class="muted">${esc(d.next.reason)}</p><button onclick="go('path')">Open learning path</button>` : "<p>All steps complete - take a new assessment.</p>"}</div>
  <div class="grid g2"><div class="card"><h3>Competency radar</h3><canvas id="c1"></canvas></div><div class="card"><h3>Topic-wise performance</h3><canvas id="c2"></canvas></div>
  <div class="card"><h3>Assessment history</h3><canvas id="c3"></canvas></div><div class="card"><h3>Learning progress (minutes per day)</h3><canvas id="c4"></canvas></div></div>
  <div class="grid g3" style="margin-top:1rem"><div class="card"><h3>Learning streak</h3><b style="font-size:1.6rem">${d.streak} day(s)</b></div>
   <div class="card"><h3>Recent quiz results</h3>${d.recent_quizzes.map(q => `<p>${esc(q.topic)}: ${q.score}/${q.total} (${q.accuracy}%) <span class="muted">${q.date}</span></p>`).join("") || '<p class="muted">No quizzes yet.</p>'}</div>
   <div class="card"><h3>Goals &amp; completed</h3><p>Goals: ${d.goals.map(esc).join(", ") || "-"}</p><p class="muted">Recent: ${d.completed.map(c => esc(c.topic + " (" + c.kind + ")")).join("; ") || "-"}</p></div></div>
  <h3 style="margin-top:1rem">Topic levels</h3><div class="card">${d.report.topics.map(t => `<div style="margin:.5rem 0"><div class="row" style="justify-content:space-between"><span>${esc(t.topic)}</span><span><span class="tag ${t.level}">${t.level}</span> ${t.score}%</span></div>${bar(t.score, t.level)}</div>`).join("")}</div></div>`;
  radar("c1", d.scores);
  chart("c2", { type: "bar", data: { labels: Object.keys(d.scores), datasets: [{ data: Object.values(d.scores), backgroundColor: "#06b6d4" }] }, options: { plugins: { legend: { display: false } }, scales: { y: { max: 100 } } } });
  chart("c3", { type: "line", data: { labels: d.history.map(h => h.date + (h.sample ? " (sample)" : "")), datasets: [{ label: "Accuracy %", data: d.history.map(h => h.accuracy), borderColor: "#6d4aff", tension: .3 }] }, options: { scales: { y: { max: 100, min: 0 } } } });
  const days = Object.keys(d.minutes_per_day).sort();
  chart("c4", { type: "bar", data: { labels: days, datasets: [{ label: "Minutes", data: days.map(x => d.minutes_per_day[x]), backgroundColor: "#6d4aff" }] } });
};
