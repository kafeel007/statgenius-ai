let ASSESS = null;
VIEWS.assessment = async m => {
  ASSESS = await api("/api/assessment/questions?per_topic=2");
  m.innerHTML = `<div class="view"><h2>Competency Assessment</h2><div class="note">${ASSESS.length} verified questions across 9 topics. Confidence rating is optional and used only as a supplementary signal.</div><div id="qs"></div><button id="sub">Submit assessment</button><div id="res"></div></div>`;
  $("#qs").innerHTML = ASSESS.map((q, i) => `<div class="card q"><div class="muted">${i + 1}. ${esc(q.topic)} - ${esc(q.difficulty)}</div><b>${esc(q.question)}</b>
    ${q.options.map((o, j) => `<label class="opt"><input type="radio" name="q${q.id}" value="${j}">${esc(o)}</label>`).join("")}
    <label class="muted">Confidence: <select id="cf${q.id}"><option value="">(skip)</option><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label></div>`).join("");
  $("#sub").onclick = submitAssessment;
};
async function submitAssessment() {
  const answers = ASSESS.map(q => { const c = $(`input[name=q${q.id}]:checked`), cf = $("#cf" + q.id).value;
    return { question_id: q.id, selected: c ? +c.value : null, confidence: cf || null }; });
  const un = answers.filter(a => a.selected === null).length;
  if (un && !confirm(`${un} question(s) unanswered will count as incorrect. Submit anyway?`)) return;
  const res = $("#res"); $("#sub").disabled = true; res.innerHTML = spinner("Scoring...");
  await safe(async () => {
    const r = await api("/api/assessment/submit", { method: "POST", body: { answers } });
    res.innerHTML = `<h2>Results</h2><div class="grid g3"><div class="card stat"><b>${r.correct}/${r.total}</b><span>Total score</span></div><div class="card stat"><b>${r.accuracy}%</b><span>Accuracy</span></div>
     <div class="card stat"><b>${esc(r.report.priority[0] || "None")}</b><span>Top priority topic</span></div></div>
     <div class="grid g2" style="margin-top:1rem"><div class="card"><h3>Topic-wise scores</h3>${r.report.topics.map(t => `<div style="margin:.5rem 0">${esc(t.topic)} <span class="tag ${t.level}">${t.level}</span> ${t.score}%${bar(t.score, t.level)}</div>`).join("")}<p class="muted">${esc(r.report.note)}</p></div><div class="card"><canvas id="ar"></canvas></div></div>
     <div class="card" style="margin-top:1rem"><h3>Comparison with previous profile</h3><table>${r.comparison.map(c => `<tr><td>${esc(c.topic)}</td><td>${c.previous ?? "-"}%</td><td>${c.current}%</td><td>${c.delta == null ? "" : (c.delta > 0 ? "+" : "") + c.delta}</td></tr>`).join("")}</table></div>
     ${r.insights.length ? `<div class="card" style="margin-top:1rem"><h3>Confidence insights <span class="muted">(supplementary signal)</span></h3>${r.insights.map(i => `<p>${esc(i.topic)}: ${esc(i.message)}</p>`).join("")}</div>` : ""}
     <div class="note">Recommendations below are rule-based suggestions from these scores.</div><button onclick="go('path')">See my learning path</button>
     <h3 style="margin-top:1rem">Review answers</h3>${r.review.map(q => `<div class="card q"><b>${esc(q.question)}</b>${q.options.map((o, j) => `<div class="opt ${j === q.correct_index ? "right" : (j === q.selected ? "wrong" : "")}">${esc(o)}${j === q.selected ? " (your answer)" : ""}</div>`).join("")}
       ${q.is_correct ? '<span class="tag strong">Correct</span>' : `<button class="sm" onclick='explainMistake({source:"assessment",question_id:${q.question_id},selected:${q.selected ?? "null"}},this.nextElementSibling)'>Explain my mistake</button><div></div>`}</div>`).join("")}`;
    radar("ar", Object.fromEntries(r.report.topics.map(t => [t.topic, t.score]))); res.scrollIntoView({ behavior: "smooth" });
  }, res); $("#sub").disabled = false;
}
async function explainMistake(body, mount) {
  mount.innerHTML = spinner("Analysing your answer...");
  await safe(async () => {
    const e = await api("/api/mistake/explain", { method: "POST", body }); const p = e.practice_question;
    mount.innerHTML = `<div class="explain"><h3>Explain My Mistake</h3><p><b>Your answer:</b> ${esc(e.your_answer)}<br><b>Correct answer:</b> ${esc(e.correct_answer)}</p>
     <p><b>Why it's incorrect:</b> ${esc(e.why_wrong)} ${e.ai_generated ? '<span class="tag sample">AI-written</span>' : ""}</p><p><b>Underlying concept:</b> ${esc(e.concept)}</p><p><b>Simple explanation:</b> ${esc(e.simple_explanation)}</p>
     ${e.formula ? `<p><b>Formula:</b> ${esc(e.formula)}</p>` : ""}${e.worked_example ? `<p><b>Worked example:</b> ${esc(e.worked_example)}</p>` : ""}${e.study_material ? `<p><b>Study:</b> ${esc(e.study_material)} <span class="muted">(${esc(e.study_material_source)})</span></p>` : ""}
     ${p ? `<h4>Try a similar question</h4><b>${esc(p.question)}</b>${p.options.map((o, j) => `<label class="opt"><input type="radio" name="pp${p.bank_id}" value="${j}" onchange="checkPractice(${p.bank_id},${j},this)">${esc(o)}</label>`).join("")}<div class="pr"></div>` : ""}</div>`;
  }, mount);
}
async function checkPractice(id, j, el) {
  const out = el.closest(".explain").querySelector(".pr");
  await safe(async () => { const r = await api("/api/practice/check", { method: "POST", body: { bank_id: id, selected: j } });
    out.innerHTML = `<p><span class="tag ${r.is_correct ? "strong" : "weak"}">${r.is_correct ? "Correct!" : "Not quite"}</span> Answer: ${esc(r.correct_answer)}. ${esc(r.explanation)}</p>`; });
}
