const SUGGEST = ["Explain standard deviation with an example", "What is the difference between population and sample?", "Teach me sampling techniques", "Explain hypothesis testing in simple English", "Generate five questions about probability"];
let HIST = [];
VIEWS.chatbot = async m => {
  m.innerHTML = `<div class="view"><h2>StatGenius AI Tutor</h2><div class="note">Statistics learning only. ${S.docId ? "Document loaded: answers will say 'From your document' when they use it." : "No document loaded: answers are general explanations."} Without an AI key the tutor uses a small demo library.</div>
  <div class="row" style="margin-bottom:.6rem">${SUGGEST.map((s, i) => `<button class="sm ghost" onclick="ask(SUGGEST[${i}])">${esc(s)}</button>`).join("")}</div>
  <div class="card"><div class="chat" id="chat" aria-live="polite"></div><div class="row"><input id="cin" style="flex:1" placeholder="Ask about a statistical concept..." maxlength="1000"><button id="csend">Send</button></div></div></div>`;
  $("#csend").onclick = () => ask($("#cin").value); $("#cin").onkeydown = e => { if (e.key === "Enter") ask($("#cin").value); };
  HIST.forEach(h => add(h.role === "user" ? "u" : "a", h.content));
};
function add(c, t) { const d = document.createElement("div"); d.className = "msg " + c; d.textContent = t; $("#chat").appendChild(d); $("#chat").scrollTop = 1e6; return d; }
async function ask(q) {
  q = (q || "").trim(); if (!q) return; $("#cin").value = ""; add("u", q); const w = add("a", "Thinking...");
  try { const r = await api("/api/chat", { method: "POST", body: { message: q, document_id: S.docId, history: HIST.slice(-6) } });
    w.textContent = r.answer; HIST.push({ role: "user", content: q }, { role: "assistant", content: r.answer }); }
  catch (e) { w.textContent = "Sorry - " + e.message; }
}
