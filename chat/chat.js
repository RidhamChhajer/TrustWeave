"use strict";
const $ = id => document.getElementById(id);
let ws, state, retry, browserRetries = 0;
function command(command, fields = {}) {
  if (ws?.readyState !== WebSocket.OPEN) { $("error").textContent = "Local service disconnected."; return; }
  ws.send(JSON.stringify({command, ...fields}));
}
function render(data) {
  state = data;
  $("title").textContent = `${data.role === "alice" ? "Alice" : "Bob"} · Private chat`;
  $("badge").textContent = data.state;
  $("unlock").hidden = data.unlocked;
  $("connection").hidden = !data.unlocked;
  $("address-label").hidden = data.role !== "alice";
  $("start").textContent = data.role === "alice" ? "Connect to Bob" : "Start server";
  $("start").disabled = data.role === "bob" ? data.listening : !["LOCKED", "CLOSED", "RESTRICTED"].includes(data.state);
  $("addresses").textContent = data.role === "bob" ? `Your private IPv4: ${data.addresses.join(", ") || "No private IPv4 found — connect to private Wi-Fi"} · TLS port ${data.port}` : "Enter Bob's address shown on his laptop.";
  $("error").textContent = data.error || "";
  $("condition").hidden = !data.condition;
  $("condition").textContent = data.condition || "";
  $("send").disabled = data.state !== "ACTIVE";
  $("text").disabled = data.state !== "ACTIVE";
  const messages = $("messages");
  const atBottom = messages.scrollHeight - messages.scrollTop - messages.clientHeight < 50;
  messages.replaceChildren(...data.messages.map(message => {
    const bubble = document.createElement("div"); bubble.className = "bubble" + (message.sender === data.role ? " mine" : "");
    bubble.textContent = message.text;
    const caption = document.createElement("small");
    caption.textContent = `${message.sender} · ${new Date(message.timestamp).toLocaleTimeString()} · ${message.status || "received"}`;
    bubble.append(caption); return bubble;
  }));
  if (atBottom) messages.scrollTop = messages.scrollHeight;
  if (data.pending) {
    $("restore-pending").hidden = data.role !== "alice" || data.observatory?.mode === "normal";
    $("code").textContent = data.pending.code;
    $("reason").textContent = data.pending.reason;
    $("decision-state").textContent = data.pending.local_decision ? "Your decision was submitted. Waiting for the peer." : "Choose after comparing both screens.";
    document.querySelectorAll("[data-decision]").forEach(b => b.disabled = !!data.pending.local_decision);
    if (!$("verification").open) $("verification").showModal();
  } else $("verification").close();
  if (typeof renderObservatory === "function") renderObservatory(data);
}
function connectBrowser() {
  ws = new WebSocket(`ws://${location.host}/ws`);
  ws.onmessage = event => { const value = JSON.parse(event.data); if (value.event === "state") render(value.data); else if (value.event === "error") $("error").textContent = value.message; };
  ws.onclose = () => { $("badge").textContent = "Local service disconnected"; $("send").disabled = true; $("text").disabled = true; clearTimeout(retry); if (browserRetries++ < 3) retry = setTimeout(connectBrowser, 1500); else $("error").textContent = "Local service unavailable. Restart the launcher if needed, then refresh this page."; };
}
$("unlock").onsubmit = event => { event.preventDefault(); command("unlock", {password: $("password").value}); $("password").value = ""; };
$("start").onclick = () => state.role === "bob" ? command("start_server") : command("connect", {address: $("address").value.trim()});
$("disconnect").onclick = () => command("disconnect");
$("restore-pending").onclick = () => command("set_demo_mode", {mode: "normal"});
$("compose").onsubmit = event => { event.preventDefault(); const text = $("text").value; if (new TextEncoder().encode(text).length > 4096 || !text.trim()) { $("error").textContent = "Enter a message up to 4096 UTF-8 bytes."; return; } command("send_chat", {text}); $("text").value = ""; };
document.querySelectorAll("[data-decision]").forEach(button => button.onclick = () => command("confirm_verification", {request_id: state.pending.id, decision: button.dataset.decision}));
$("verification").addEventListener("cancel", event => { event.preventDefault(); if (state.pending) command("confirm_verification", {request_id: state.pending.id, decision: "CANCEL"}); });
connectBrowser();

function renderObservatory(data) {
  const host = $("observatory");
  if (data.role !== "alice") { host.hidden = true; host.replaceChildren(); return; }
  host.hidden = false;
  if (!host.firstChild) {
    const title = document.createElement("h2"); title.textContent = "Adaptive-trust observatory";
    const metrics = document.createElement("div"); metrics.className = "metrics"; metrics.id = "metrics";
    const chart = document.createElement("canvas"); chart.id = "trust-chart"; chart.width = 1000; chart.height = 180;
    chart.setAttribute("aria-label", "Trust score history; red vertical lines mark verification triggers"); chart.setAttribute("role", "img");
    const details = document.createElement("pre"); details.className = "telemetry"; details.id = "telemetry";
    const timeline = document.createElement("pre"); timeline.className = "telemetry"; timeline.id = "timeline";
    const controls = document.createElement("div");
    [["Induce latency", "latency"], ["Reconnect burst", "reconnect_burst"], ["Simulate IP continuity change", "ip_change"], ["Restore normal", "normal"]].forEach(([label, mode]) => {
      const button = document.createElement("button"); button.textContent = label; button.onclick = () => command("set_demo_mode", {mode}); controls.append(button);
    });
    const condition = document.createElement("p"); condition.id = "condition-label";
    host.append(title, controls, condition, metrics, chart, details, timeline);
  }
  const t = data.observatory;
  $("condition-label").textContent = `${t.condition_label} · ${t.mode}`;
  $("metrics").replaceChildren(...[["Trust", t.score?.toFixed(1) ?? "—"], ["Delta", t.delta?.toFixed(1) ?? "—"], ["Transport", t.session?.protocol ?? "—"]].map(([name, value]) => {
    const node = document.createElement("div"); node.className = "metric"; node.textContent = name;
    const number = document.createElement("b"); number.textContent = value; node.append(number); return node;
  }));
  $("telemetry").textContent = JSON.stringify({relationship: t.relationship_id, key_epoch: t.key_id, session: t.session,
    raw_signals: t.signals, normalized: t.normalized, decision: t.decision, outcome: t.outcome, key_action: t.key_action}, null, 2);
  $("timeline").textContent = t.timeline.map(row => `${row.timestamp}  ${row.event}  ${JSON.stringify(row.metadata)}`).join("\n");
  const ctx = $("trust-chart").getContext("2d"); ctx.clearRect(0, 0, 1000, 180);
  ctx.strokeStyle = "#c8d5de"; ctx.beginPath(); ctx.moveTo(0, 90); ctx.lineTo(1000, 90); ctx.stroke();
  const history = t.history; ctx.strokeStyle = "#08757b"; ctx.lineWidth = 3; ctx.beginPath();
  history.forEach((row, i) => { const x = i * 1000 / Math.max(1, history.length - 1), y = 175 - row.score * 1.7; if (i) ctx.lineTo(x, y); else ctx.moveTo(x, y); }); ctx.stroke();
  ctx.strokeStyle = "#c44950"; ctx.lineWidth = 1;
  history.forEach((row, i) => { if (row.triggered) { const x = i * 1000 / Math.max(1, history.length - 1); ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, 180); ctx.stroke(); } });
}
