let QUIZ = null;
VIEWS.learning = async m => {
  m.innerHTML = `<div class="view"><h2>PDF Learning Assistant</h2>
  <div class="card"><h3>1. Upload a statistics PDF</h3><div class="row"><input type="file" id="pdf" accept="application/pdf"><button id="up">Upload &amp; extract</button><button class="cyan" id="smp">Use sample PDF</button></div>
  <p class="muted">PDF only, max 5 MB. Scanned PDFs need OCR, which this prototype does not provide.</p><div id="docinfo"></div></div>
  <div class="card" style="margin-top:1rem"><h3>2. Study notes</h3><button id="nt" disabled>Generate notes</button><div id="notes"></div></div>
  <div class="card" style="margin-top:1rem"><h3>3. Quiz generator</h3><div class="row">
   <label>Topic <select id="qt"><option>Any</option>${TOPICS.map(t => `<option>${t}</option>`).join("")}</select></label>
   <label>Questions <input id="qn" type="number" min="1" max="15" value="5" style="width:70px"></label>
   <label>Difficulty <select id="qd"><option>easy</option><option selected>medium</option><option>hard</option></select></label>
   <label>Format <select id="qf"><option value="mcq">Multiple choice</option><option value="tf">True / false</option><option value="short">Short answer</option><option value="numeric">Numerical</option><option value="mixed">Mixed</option></select></label>
   <button id="gq">Generate quiz</button></div><div id="quiz"></div></div></div>`;
  $("#up").onclick = () => doUpload(); $("#smp").onclick = () => doUpload(true); $("#nt").onclick = genNotes; $("#gq").onclick = genQuiz;
  if (S.docId) { $("#nt").disabled = false; $("#docinfo").innerHTML = `<p class="note">Using the previously loaded document (#${S.docId}).</p>`; }
};
async function doUpload(sample) {
  const box = $("#docinfo"); const f = $("#pdf").files[0];
  if (!sample && !f) return toast("Choose a PDF file first");
  box.innerHTML = spinner("Extracting text...");
  await safe(async () => {
    let r; if (sample) r = await api("/api/documents/sample", { method: "POST" }); else { const fd = new FormData(); fd.append("file", f); r = await api("/api/documents/upload", { method: "POST", body: fd }); }
    S.docId = r.id; $("#nt").disabled = false;
    box.innerHTML = `<p><b>${esc(r.filename)}</b> - ${r.page_count} page(s). Detected topics: ${r.topics.map(esc).join(", ") || "none"}</p><pre>${esc(r.preview)}</pre>`;
  }, box);
}
const sec = (t, items, f) => items && items.length ? `<h4>${t}</h4>${items.map(f).join("")}` : "";
async function genNotes() {
  const b = $("#notes"); b.innerHTML = spinner("Generating notes..."); const pg = x => x.page ? ` <span class="muted">[Page ${x.page}]</span>` : "";
  await safe(async () => {
    const n = await api("/api/notes/generate", { method: "POST", body: { document_id: S.docId } });
    b.innerHTML = `<div class="note">${n.ai_generated ? "Summary written by AI from your document." : "Demo mode: notes are extracted from your document with rules (no AI key)."} Items marked <i>general knowledge</i> are not from your PDF.</div>
     ${sec("Topic summary", n.summary, x => `<p>${esc(x.text)}${pg(x)}</p>`)}${sec("Important definitions", n.definitions, x => `<p>&bull; ${esc(x.text)}${pg(x)}</p>`)}
     ${sec("Formulas in the document", n.formulas, x => `<pre>${esc(x.text)}</pre>`)}
     ${sec("Worked examples, formulas &amp; applications (general knowledge)", n.general_support, x => `<div class="card" style="margin:.4rem 0"><b>${esc(x.topic)}</b><p>${esc(x.notes)}</p><p><b>Formula:</b> ${esc(x.formula)}</p><p><b>Example:</b> ${esc(x.example)}</p><p><b>Real-world use:</b> ${esc(x.application)}</p><span class="tag sample">general</span></div>`)}
     ${sec("Key takeaways", n.key_takeaways, x => `<p>&#10003; ${esc(x)}</p>`)}${sec("Revision notes", n.revision_notes, x => `<p>&bull; ${esc(x)}</p>`)}`;
  }, b);
}
async function genQuiz() {
  const b = $("#quiz"); b.innerHTML = spinner("Generating quiz...");
  await safe(async () => {
    QUIZ = await api("/api/quiz/generate", { method: "POST", body: { document_id: S.docId, topic: $("#qt").value, n: +$("#qn").value, difficulty: $("#qd").value, format: $("#qf").value } });
    b.innerHTML = (S.docId ? "" : `<div class="note warnbox">No document loaded: questions come from the verified bank / calculators.</div>`) + QUIZ.questions.map((q, i) => `<div class="q"><div class="muted">${i + 1}. ${esc(q.topic)} - ${esc(q.type)} - source: ${esc(q.source)}</div><b>${esc(q.question)}</b>
      ${q.options ? q.options.map((o, j) => `<label class="opt"><input type="radio" name="z${q.id}" value="${j}">${esc(o)}</label>`).join("") : `<div><input id="z${q.id}" placeholder="Your answer" ${q.type === "numeric" ? 'inputmode="decimal"' : ""}></div>`}</div>`).join("") + `<button id="sq">Submit quiz</button><div id="qr"></div>`;
    $("#sq").onclick = submitQuiz;
  }, b);
}
async function submitQuiz() {
  const ans = {}; QUIZ.questions.forEach(q => { if (q.options) { const c = $(`input[name=z${q.id}]:checked`); ans[q.id] = c ? +c.value : null; } else ans[q.id] = $("#z" + q.id).value || null; });
  const out = $("#qr"); $("#sq").disabled = true; out.innerHTML = spinner("Scoring...");
  await safe(async () => {
    const r = await api(`/api/quiz/${QUIZ.quiz_id}/submit`, { method: "POST", body: { answers: ans } });
    out.innerHTML = `<h3>Score: ${r.score}/${r.total} (${r.accuracy}%)</h3>` + r.results.map(x => `<div class="q"><b>${esc(x.question)}</b><p>${x.is_correct ? '<span class="tag strong">Correct</span>' : '<span class="tag weak">Incorrect</span>'} Your answer: ${esc(x.given_text ?? "(none)")} | Correct: ${esc(x.correct_answer)}</p><p class="muted">${esc(x.explanation)} ${x.source ? "(" + esc(x.source) + ")" : ""}</p>
      ${x.is_correct ? "" : `<button class="sm" onclick='explainMistake({source:"quiz",quiz_id:${QUIZ.quiz_id},question_id:${x.id},selected:${JSON.stringify(x.given)}},this.nextElementSibling)'>Explain my mistake</button><div></div>`}</div>`).join("") +
      (r.next_step ? `<div class="note"><b>Next recommended step:</b> ${esc(r.next_step.label)} - ${esc(r.next_step.topic)}. ${esc(r.next_step.reason)} <button class="sm" onclick="go('path')">Learning path</button></div>` : "");
  }, out);
}

// ---------- Learning path + iGOT (sample) ----------
VIEWS.path = async m => {
  const r = await api("/api/recommendations"), tr = await api("/api/igot/tracked"), me = await api("/api/me");
  m.innerHTML = `<div class="view"><h2>Personalised Learning Path</h2>
  ${r.next ? `<div class="card"><h3>Next activity</h3><p><b>${esc(r.next.label)}</b> - ${esc(r.next.topic)} (~${r.next.minutes} min, ${esc(r.next.difficulty)})</p><p class="muted">${esc(r.next.reason)}</p></div>` : ""}
  <div class="note">Rules, not randomness: priority comes from your stored scores; steps complete when you do them (notes, worked example via Explain My Mistake, practice quizzes, follow-up assessment).</div>
  <div class="card" style="margin:1rem 0"><b>Score thresholds</b> weak below <input id="tw" type="number" value="${me.thresholds.weak}" style="width:70px"> strong from <input id="ts" type="number" value="${me.thresholds.strong}" style="width:70px"> <button class="sm" id="sth">Save</button></div>
  <div class="grid g2">${r.path.map(p => `<div class="card"><div class="row" style="justify-content:space-between"><h3>${esc(p.topic)}</h3><span class="tag ${p.priority}">${p.priority} priority</span></div>
   ${bar(p.score, p.level)}<p class="muted">Score ${p.score}% (${p.level}) - ${esc(p.status)} - ~${p.est_minutes} min left - next difficulty: ${esc(p.next_difficulty)}</p>
   ${p.steps.map(s => `<div class="row" style="justify-content:space-between"><span>${s.done ? "&#9989;" : "&#9744;"} ${esc(s.label)} (${s.minutes} min)</span>${!s.done && (s.kind === "notes" || s.kind === "example") ? `<button class="sm ghost" onclick="markDone('${esc(p.topic)}','${s.kind}',${s.minutes})">Mark done</button>` : ""}</div>`).join("")}</div>`).join("")}</div>
  <h2 style="margin-top:1.5rem">Recommended courses <span class="tag sample">SAMPLE - not connected to iGOT Karmayogi</span></h2>
  <p class="muted">Demonstration records mapped from your gaps. A live integration would require authorised iGOT API access.</p>
  <div class="grid g3">${r.courses.map(c => `<div class="card"><b>${esc(c.title)}</b><p class="muted">${esc(c.description)} (${esc(c.duration)})</p><button class="sm" onclick="trackCourse('${esc(c.topic)}','${esc(c.title)}')">Track locally</button></div>`).join("") || "<p>No gaps found.</p>"}</div>
  <p class="muted">Locally tracked: ${tr.map(t => esc(t.title)).join("; ") || "none"}</p></div>`;
  $("#sth").onclick = () => safe(async () => { await api("/api/me/thresholds", { method: "PUT", body: { weak: +$("#tw").value, strong: +$("#ts").value } }); toast("Thresholds saved"); render(); });
};
async function markDone(topic, kind, minutes) { await safe(async () => { await api("/api/activities/complete", { method: "POST", body: { topic, kind, minutes } }); render(); }); }
async function trackCourse(topic, title) { await safe(async () => { const r = await api("/api/igot/track", { method: "POST", body: { topic, title } }); toast(r.note); render(); }); }

// ---------- Practice Lab ----------
const LAB = {
  descriptive: ["Mean, median, mode, variance, SD", [["values", "Values (comma-separated)", "12, 15, 15, 18, 20, 22, 90"]]],
  binomial: ["Probability (binomial)", [["n", "Trials n", 10], ["p", "Success probability p", 0.5], ["k", "Successes k", 5]]],
  ci: ["Confidence interval for a mean", [["values", "Sample values", "5.1, 4.9, 5.6, 5.8, 6.0, 5.2"], ["confidence", "Confidence % (90/95/99)", 95]]],
  ttest: ["Hypothesis test (one-sample t)", [["values", "Sample values", "5.1, 4.9, 5.6, 5.8, 6.0, 5.2"], ["mu0", "Hypothesised mean", 5], ["alpha", "Alpha", 0.05]]],
  regression: ["Correlation & regression", [["x", "x values", "1,2,3,4,5,6"], ["y", "y values", "2.1,3.9,6.2,7.8,10.1,12.2"]]],
  sampling_error: ["Sampling error (SE)", [["sd", "Standard deviation", 10], ["n", "Sample size", 25], ["population", "Population size (optional)", ""]]],
  quality: ["Missing values & data quality", [["values", "Values (blank/NA = missing)", "25, 31, , 28, NA, 250, 31, abc, 40"], ["minimum", "Valid minimum", 0], ["maximum", "Valid maximum", 120]]],
};
VIEWS.lab = async m => {
  m.innerHTML = `<div class="view"><h2>Statistical Practice Lab</h2><div class="note">All numbers here are computed with validated formulas on the server (no AI involved). Sample datasets are pre-filled.</div><div class="grid g2">` +
    Object.entries(LAB).map(([k, [t, f]]) => `<div class="card"><h3>${t}</h3>${f.map(([id, l, v]) => `<label class="muted">${l}<br><input id="${k}_${id}" value="${v}" style="width:100%"></label>`).join("")}<p><button onclick="runLab('${k}')">Calculate</button></p><div id="out_${k}"></div></div>`).join("") + `</div></div>`;
};
async function runLab(k) {
  const o = $("#out_" + k), body = {}; o.innerHTML = spinner("Calculating...");
  LAB[k][1].forEach(([id]) => { let v = $(`#${k}_${id}`).value; body[id] = ["values", "x", "y"].includes(id) ? v.split(",").map(s => s.trim()) : v; });
  if (k === "quality") { /* keep blanks: do not drop empty entries */ }
  else ["values", "x", "y"].forEach(id => { if (body[id]) body[id] = body[id].filter(s => s !== ""); });
  await safe(async () => { const r = await api("/api/lab/" + k, { method: "POST", body });
    o.innerHTML = `<table>${Object.entries(r.result).map(([a, b]) => `<tr><td>${esc(a)}</td><td><b>${esc(JSON.stringify(b))}</b></td></tr>`).join("")}</table><h4>Steps</h4>${r.steps.map(s => `<p class="muted">${esc(s)}</p>`).join("")}<div class="note"><b>Meaning:</b> ${esc(r.meaning)}</div>`; }, o);
}
