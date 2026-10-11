// Core: API client, router, auth, shared helpers. API key never appears here (server-side only).
const API = (location.port === "8000" || location.protocol === "https:") ? "" : "http://localhost:8000";
const S = { token: localStorage.getItem("sg_token"), user: null, docId: null, charts: [] };
const VIEWS = {};
const TOPICS = ["Descriptive Statistics","Probability","Sampling Techniques","Statistical Inference","Hypothesis Testing","Regression Analysis","Data Visualization","Survey Methodology","Data Quality and Validation"];
const $ = (s, r = document) => r.querySelector(s);
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const spinner = (t = "Loading...") => `<p><span class="spin"></span> ${esc(t)}</p>`;
function toast(m) { const t = $("#toast"); t.textContent = m; t.style.display = "block"; clearTimeout(toast.h); toast.h = setTimeout(() => t.style.display = "none", 5000); }

async function api(path, opts = {}) {
  const h = { ...(opts.headers || {}) };
  if (S.token) h.Authorization = "Bearer " + S.token;
  if (opts.body && !(opts.body instanceof FormData)) { h["Content-Type"] = "application/json"; opts.body = JSON.stringify(opts.body); }
  let r;
  try { r = await fetch(API + path, { ...opts, headers: h }); }
  catch { throw new Error("Cannot reach the server. Is the backend running on port 8000?"); }
  const data = await r.json().catch(() => ({}));
  if (r.status === 401) { logout(true); throw new Error("Please sign in again"); }
  if (!r.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Request failed (check your input)");
  return data;
}
async function safe(fn, mount) { try { return await fn(); } catch (e) { toast(e.message); if (mount) mount.innerHTML = `<div class="note warnbox">${esc(e.message)}</div>`; } }

function bar(pct, cls) { return `<div class="bar" role="progressbar" aria-valuenow="${pct}" aria-valuemin="0" aria-valuemax="100"><div class="${cls}" style="width:${pct}%"></div></div>`; }
function chart(id, cfg) { const c = new Chart($("#" + id), cfg); S.charts.push(c); return c; }
function radar(id, scores) { chart(id, { type: "radar", data: { labels: Object.keys(scores), datasets: [{ label: "Assessment score %", data: Object.values(scores), backgroundColor: "rgba(109,74,255,.25)", borderColor: "#6d4aff", pointBackgroundColor: "#06b6d4" }] }, options: { scales: { r: { min: 0, max: 100 } }, plugins: { legend: { display: false } } } }); }

// ---- auth ----
function setAuthUI() {
  $("#auth").innerHTML = S.user ? `<span class="muted" style="color:#cfd9ff">${esc(S.user.name)}</span> <button class="ghost sm" onclick="logout()">Sign out</button>` : `<button class="sm" onclick="showLogin()">Sign in</button>`;
  $("#nav").innerHTML = S.user ? [["dashboard","Dashboard"],["assessment","Assessment"],["learning","PDF Learning"],["path","Learning Path"],["lab","Practice Lab"],["chatbot","AI Tutor"]].map(([k, l]) => `<a data-v="${k}" onclick="go('${k}')">${l}</a>`).join("") : "";
}
function logout(silent) { S.token = null; S.user = null; localStorage.removeItem("sg_token"); setAuthUI(); if (!silent) go("home"); else render(); }
async function demoLogin(to = "dashboard") { await safe(async () => { const r = await api("/api/auth/demo", { method: "POST" }); await onAuth(r); go(to); }); }
async function onAuth(r) { S.token = r.token; S.user = r.user; localStorage.setItem("sg_token", r.token); setAuthUI(); }
function showLogin() {
  $("#view").innerHTML = `<div class="card view" style="max-width:480px;margin:auto"><h2>Sign in or register</h2>
   <div class="note">Prototype: use <b>Demo mode</b> to explore with clearly labelled SAMPLE data.</div>
   <button class="cyan" onclick="demoLogin()">Enter Demo mode (sample data)</button><hr>
   <form id="af" class="grid"><input id="em" type="email" placeholder="Email" required autocomplete="username"><input id="pw" type="password" minlength="8" placeholder="Password (8+ chars)" required autocomplete="current-password">
   <input id="nm" placeholder="Name (register only)"><input id="rl" placeholder="Learning role (e.g. Statistical Assistant)">
   <input id="gl" placeholder="Goals: comma-separated topics (optional)"><div class="row"><button type="submit">Log in</button><button type="button" class="ghost" id="reg">Register</button></div></form></div>`;
  const doit = async reg => safe(async () => {
    const body = { email: $("#em").value, password: $("#pw").value };
    if (reg) Object.assign(body, { name: $("#nm").value || "Learner", role: $("#rl").value || "Learner", goals: $("#gl").value.split(",").map(s => s.trim()).filter(Boolean) });
    await onAuth(await api(reg ? "/api/auth/register" : "/api/auth/login", { method: "POST", body })); go("dashboard");
  });
  $("#af").onsubmit = e => { e.preventDefault(); doit(false); }; $("#reg").onclick = () => doit(true);
}

// ---- router ----
function go(v) { if (location.hash === "#" + v) render(); else location.hash = v; }
async function render() {
  S.charts.forEach(c => c.destroy()); S.charts = [];
  const v = location.hash.slice(1) || "home", m = $("#view");
  if (v !== "home" && !S.user) { showLogin(); return; }
  document.querySelectorAll("nav a").forEach(a => a.classList.toggle("active", a.dataset.v === v));
  m.innerHTML = spinner(); const f = VIEWS[v] || VIEWS.home; await safe(() => f(m), m); window.scrollTo(0, 0);
}
async function boot() {
  document.documentElement.dataset.theme = localStorage.getItem("sg_theme") || "light";
  $("#theme").onclick = () => { const t = document.documentElement.dataset.theme === "dark" ? "light" : "dark"; document.documentElement.dataset.theme = t; localStorage.setItem("sg_theme", t); };
  if (S.token) { try { S.user = await api("/api/me"); } catch { S.token = null; } }
  setAuthUI(); window.addEventListener("hashchange", render); render();
}

// ---- landing page ----
VIEWS.home = async m => {
  const f = [["Competency Assessment","Verified question bank with topic-wise scoring from your actual answers."],["Gap Detection","Strong / moderate / weak levels with configurable thresholds and a radar chart."],["PDF to Notes & Quiz","Upload a statistics PDF; get notes, definitions, formulas and quizzes with page references."],["Explain My Mistake","Why your answer was wrong, the concept, a worked example and a fresh practice question."],["Adaptive Learning Path","Rule-based next steps from stored performance - never random."],["Practice Lab","Validated calculators with step-by-step working."],["AI Tutor","Ask statistics questions; demo library works without an API key."],["iGOT-ready","Sample course mapping with a clear path to authorised integration."]];
  m.innerHTML = `<section class="hero view"><h1>Learn Smarter. Measure Progress. Master Statistics.</h1>
  <p>Your AI-powered learning companion for identifying skill gaps, mastering statistical concepts, and building professional competencies.</p>
  <div class="row"><button onclick="demoLogin('dashboard')">Start Learning</button><button class="cyan" onclick="demoLogin('assessment')">Take Competency Assessment</button><button class="ghost" style="color:#fff;border-color:#fff" onclick="document.getElementById('features').scrollIntoView({behavior:'smooth'})">Explore Features</button></div></section>
  <h2 id="features">Platform features</h2><div class="grid g3">${f.map(x => `<div class="card"><h3>${x[0]}</h3><p class="muted">${x[1]}</p></div>`).join("")}</div>
  <h2 style="margin-top:2rem">How the learning process works</h2><div class="flow"><span>ASSESS</span><i>&rarr;</i><span>IDENTIFY GAPS</span><i>&rarr;</i><span>LEARN</span><i>&rarr;</i><span>PRACTICE</span><i>&rarr;</i><span>IMPROVE</span></div>
  <h2 style="margin-top:2rem">Personalised learning benefits</h2><div class="grid g3"><div class="card">Focus time on your weakest topics first.</div><div class="card">Understand <i>why</i> an answer was wrong, not just that it was.</div><div class="card">Turn your own PDFs into notes and practice questions.</div></div>
  <h2 style="margin-top:2rem">Statistical learning modules</h2><div class="row">${TOPICS.map(t => `<span class="tag" style="background:var(--navy)">${t}</span>`).join("")}</div>
  <h2 style="margin-top:2rem">Progress tracking preview</h2><div class="card"><canvas id="pv"></canvas><p class="muted">Illustrative preview with SAMPLE numbers. Your dashboard uses your real results.</p></div>
  <div class="hero" style="margin-top:2rem"><h2>Ready to find your learning gaps?</h2><button class="cyan" onclick="demoLogin('assessment')">Try the demo</button></div>`;
  chart("pv", { type: "bar", data: { labels: ["Descriptive","Probability","Sampling","Inference"], datasets: [{ label: "Sample score %", data: [85, 45, 30, 70], backgroundColor: ["#16a34a","#d97706","#dc2626","#6d4aff"] }] }, options: { scales: { y: { max: 100 } } } });
};
