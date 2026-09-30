/* Turnkey Ops — property operations command center.
   Sample data seeded from data.js; edits persist to localStorage. */
"use strict";

/* ============================== utils ============================== */
const $ = (s, r) => (r || document).querySelector(s);
const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
const esc = s => String(s == null ? "" : s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");
const DAY = 86400000;
const todayISO = () => { const d = new Date(); return d.toISOString().slice(0, 10); };
const parseD = s => s ? new Date(s + "T12:00:00") : null;
const fmtD = s => { const d = parseD(s); return d ? d.toLocaleDateString("en-US", {month:"numeric",day:"numeric",year:"numeric"}) : "—"; };
const daysBetween = (a, b) => Math.round((parseD(b) - parseD(a)) / DAY);
const diffDays = (a, b) => Math.round((parseD(b) - parseD(a)) / DAY);
const clone = o => JSON.parse(JSON.stringify(o));

/* ============================== store ============================== */
const LS_KEY = "turnkey-ops-v1";
const DB = {
  data: null,
  load() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (raw) { this.data = JSON.parse(raw); return; }
    } catch (e) {}
    this.data = clone(window.SEED);
    // stable ids for recovery rows
    this.data.recovery.forEach((r, i) => { if (!r.id) r.id = "RC-" + (i + 1); });
    this.save();
  },
  save() { try { localStorage.setItem(LS_KEY, JSON.stringify(this.data)); } catch (e) {} },
  reset() { localStorage.removeItem(LS_KEY); this.load(); }
};

/* ====================== derived ops logic ====================== */
const SLA_TARGET = { Emergency: 1, High: 3, Standard: 7, Low: 14 };
function woCalc(w) {
  const target = SLA_TARGET[w.priority] || 7;
  const end = w.status === "Closed" && w.closed ? w.closed : todayISO();
  const daysOpen = Math.max(0, diffDays(w.opened, end));
  let sla = "On Track", over = 0, left = target - daysOpen;
  if (w.status === "Closed") sla = "Closed";
  else if (daysOpen > target) { sla = "Breached"; over = daysOpen - target; }
  else if (daysOpen >= target - 1) { sla = "At Risk"; }
  return { target, daysOpen, sla, over, left };
}
const isOpen = w => w.status !== "Closed";
const slaPill = c => {
  if (c.sla === "Breached") return `<span class="pill red">Breached · ${c.over}d over</span>`;
  if (c.sla === "At Risk") return `<span class="pill amber">At Risk · ${c.left}d left</span>`;
  if (c.sla === "Closed") return `<span class="pill gray">Closed</span>`;
  return `<span class="pill green">On Track</span>`;
};
const priPill = p => {
  const m = { Emergency: "red", High: "amber", Standard: "blue", Low: "gray" };
  return `<span class="pill ${m[p] || "gray"}">${esc(p)}</span>`;
};
const statusPill = s => {
  const m = { "Open": "blue", "In Progress": "amber", "Waiting on Parts": "purple", "Closed": "gray" };
  return `<span class="pill ${m[s] || "gray"}">${esc(s)}</span>`;
};
function followUpState(r) {
  if (r.resolved === "Yes") return null;
  if (!r.followUp) return null;
  const d = diffDays(todayISO(), r.followUp);
  if (d < 0) return { cls: "red", label: `overdue ${-d}d` };
  if (d <= 2) return { cls: "amber", label: d === 0 ? "due today" : `due in ${d}d` };
  return null;
}

/* ====================== action center engine ====================== */
function actionItems() {
  const d = DB.data, t = todayISO();
  const breaches = d.workOrders.filter(w => isOpen(w) && woCalc(w).sla === "Breached")
    .map(w => { const c = woCalc(w); return { kind: "breach", title: `${w.id} · Unit ${w.unit}`,
      sub: `${w.priority} · ${w.category} · ${c.over} day${c.over === 1 ? "" : "s"} past SLA`, view: "workorders", key: w.id }; });
  const atRisk = d.workOrders.filter(w => isOpen(w) && woCalc(w).sla === "At Risk")
    .map(w => { const c = woCalc(w); return { kind: "risk", title: `${w.id} · Unit ${w.unit}`,
      sub: `${w.priority} · ${w.category} · ${c.left} day${c.left === 1 ? "" : "s"} of SLA left`, view: "workorders", key: w.id }; });
  const followUps = d.recovery.filter(r => { const s = followUpState(r); return s && (s.cls === "red" || s.cls === "amber"); })
    .map(r => { const s = followUpState(r); return { kind: "follow", title: `Unit ${r.unit} · ${r.category}`,
      sub: `${r.severity} · owner ${r.owner} · follow-up ${s.label}`, view: "recovery", key: r.id }; });
  const qcFails = d.turnover.filter(u => u.qc === "No")
    .map(u => ({ kind: "qc", title: `Unit ${u.unit} · Building ${u.building}`,
      sub: `QC failed · top deficiency: ${u.topDeficiency} · ${u.deficiencies} found`, view: "turnover", key: u.unit }));
  const outreach = d.retention.filter(r => r.intent === "Unknown" || r.intent === "Undecided")
    .map(r => ({ kind: "outreach", title: `Unit ${r.unit} · lease ends ${fmtD(r.leaseEnd)}`,
      sub: `Intent: ${r.intent} · ${r.touches} outreach touch${r.touches === 1 ? "" : "es"}`, view: "retention", key: r.unit }));
  void t;
  return { breaches, atRisk, followUps, qcFails, outreach };
}
const actionCount = () => { const a = actionItems(); return a.breaches.length + a.atRisk.length + a.followUps.length + a.qcFails.length + a.outreach.length; };

/* ============================== chrome ============================== */
const TITLES = { command: "Command", action: "Action Center", workorders: "Work Orders",
  turnover: "Turnover", retention: "Retention", recovery: "Service Recovery", report: "Weekly Report" };
let charts = [];
function destroyCharts() { charts.forEach(c => { try { c.destroy(); } catch (e) {} }); charts = []; }

function renderPulse() {
  const d = DB.data, a = actionItems();
  const notReady = d.turnover.filter(u => u.status !== "Ready" && u.status !== "Ready for QC").length;
  const pills = [
    { cls: "red", n: a.breaches.length, l: "breaches" },
    { cls: "amber", n: a.atRisk.length, l: "at risk" },
    { cls: "blue", n: a.followUps.length, l: "follow-ups" },
    { cls: "purple", n: notReady, l: "units not ready" },
  ];
  $("#pulsePills").innerHTML = pills.map(p =>
    `<span class="ppill ${p.cls}" data-go="action"><b>${p.n}</b> ${p.l}</span>`).join("");
  $$("#pulsePills .ppill").forEach(el => el.onclick = () => go("action"));
  // nav badges
  const set = (id, n) => { const e = $("#cnt-" + id); e.textContent = n; e.classList.toggle("show", n > 0); };
  set("action", actionCount());
  set("workorders", a.breaches.length);
  set("turnover", a.qcFails.length);
  set("retention", a.outreach.length);
  set("recovery", a.followUps.length);
}

function go(view, opts) {
  destroyCharts();
  const h = "#/" + view + (opts && opts.key ? "?key=" + encodeURIComponent(opts.key) : "");
  if (location.hash === h) route();
  else location.hash = h;
}
function route() {
  const m = (location.hash || "#/command").match(/^#\/(\w+)(?:\?key=(.*))?$/);
  render({ view: (m && m[1]) || "command", key: m && m[2] ? decodeURIComponent(m[2]) : null });
}
function render(opts) {
  opts = opts || {};
  const view = opts.view || "command";
  $$("#nav button").forEach(b => b.classList.toggle("active", b.dataset.view === view));
  $("#viewTitle").textContent = TITLES[view] || view;
  $("#dateLine").textContent = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric", year: "numeric" });
  renderPulse();
  const V = { command: vCommand, action: vAction, workorders: vWorkOrders, turnover: vTurnover,
              retention: vRetention, recovery: vRecovery, report: vReport };
  (V[view] || vCommand)(opts);
  window.scrollTo(0, 0);
}

/* ============================== modal / toast ============================== */
function openModal(title, bodyHTML, footHTML) {
  $("#modalRoot").innerHTML =
    `<div class="mback" id="mback"><div class="modal" role="dialog">
       <header><h3>${esc(title)}</h3><button class="x" id="mx">×</button></header>
       <div class="body">${bodyHTML}</div>
       <footer>${footHTML || ""}</footer>
     </div></div>`;
  const close = () => { $("#modalRoot").innerHTML = ""; };
  $("#mx").onclick = close;
  $("#mback").addEventListener("mousedown", e => { if (e.target.id === "mback") close(); });
  return close;
}
function toast(msg) {
  const t = document.createElement("div");
  t.className = "toast"; t.textContent = msg;
  $("#toasts").appendChild(t);
  setTimeout(() => t.remove(), 2600);
}
function fieldOpts(selected, options) {
  return options.map(o => `<option ${o === selected ? "selected" : ""}>${esc(o)}</option>`).join("");
}
function downloadCSV(name, rows) {
  const csv = rows.map(r => r.map(c => `"${String(c == null ? "" : c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([csv], { type: "text/csv" }));
  a.download = name; a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

/* ============================== views ============================== */
function vCommand() {
  const d = DB.data, a = actionItems();
  const notReady = d.turnover.filter(u => u.status !== "Ready" && u.status !== "Ready for QC");
  const cards = [
    { ac: "var(--red)", n: a.breaches.length, l: "SLA breaches", s: "Past target — act now" },
    { ac: "var(--amber)", n: a.atRisk.length, l: "At risk", s: "Due within 2 days" },
    { ac: "var(--blue)", n: a.followUps.length, l: "Follow-ups due", s: "Still open, within 2 days" },
    { ac: "var(--purple)", n: notReady.length, l: "Units not ready", s: "In the make-ready pipeline" },
  ];
  const top = a.breaches.slice(0, 5);
  const openCount = d.workOrders.filter(isOpen).length;
  const renewing = d.retention.filter(r => r.intent === "Renewing").length;
  $("#view").innerHTML = `
    <div class="grid g4">${cards.map(c => `
      <div class="card pulse-card" style="--ac:${c.ac}" data-go="action">
        <div class="num">${c.n}</div><div class="lbl">${c.l}</div><div class="sub">${c.s}</div>
      </div>`).join("")}</div>
    <div class="grid g2" style="margin-top:16px">
      <div class="card">
        <h3>Needs you now — top breaches</h3>
        ${top.length ? top.map(b => `
          <div class="ac-row"><div class="main-info"><div class="t1">${esc(b.title)}</div>
          <div class="t2">${esc(b.sub)}</div></div>
          <button class="btn sm ghost" data-open="${esc(b.key)}" data-view="${b.view}">Open →</button></div>`).join("")
        : `<div class="empty">No breaches. The operation is quiet — for now.</div>`}
      </div>
      <div class="card">
        <h3>SLA status right now</h3>
        <div class="chart-box sm"><canvas id="ch-sla"></canvas></div>
      </div>
    </div>
    <div class="sec-title">Run the operation</div>
    <div class="tiles">
      ${[
        ["▤", "Work Orders", `${openCount} open · ${a.breaches.length} breached`, "workorders"],
        ["🏠", "Turnover", `${d.turnover.length} units tracked · ${notReady.length} not ready`, "turnover"],
        ["🔑", "Retention", `${d.retention.length} leases · ${renewing} renewing`, "retention"],
        ["🛟", "Service Recovery", `${d.recovery.filter(r => r.resolved !== "Yes").length} open loops`, "recovery"],
        ["📄", "Weekly Report", "This week's numbers, print-ready", "report"],
        ["⚡", "Action Center", `${actionCount()} items need you`, "action"],
      ].map(t => `<div class="tile" data-go="${t[3]}"><div class="ti">${t[0]}</div><h4>${t[1]}</h4><p>${t[2]}</p></div>`).join("")}
    </div>`;
  $$("#view [data-go]").forEach(el => el.onclick = () => go(el.dataset.go));
  $$("#view [data-open]").forEach(el => el.onclick = e => { e.stopPropagation(); go(el.dataset.view, { key: el.dataset.open }); });
  const counts = ["Breached", "At Risk", "On Track", "Closed"].map(s =>
    d.workOrders.filter(w => woCalc(w).sla === s).length);
  charts.push(new Chart($("#ch-sla"), { type: "doughnut",
    data: { labels: ["Breached", "At Risk", "On Track", "Closed"],
      datasets: [{ data: counts, backgroundColor: ["#C00000", "#ED7D31", "#2E7D32", "#9aa5b5"] }] },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "right" } } } }));
}

function vAction() {
  const a = actionItems();
  const groups = [
    { id: "breaches", color: "var(--red)", dot: "#C00000", icon: "🔴", title: "SLA breaches — act now", items: a.breaches },
    { id: "atrisk", color: "var(--amber)", dot: "#ED7D31", icon: "🟡", title: "At risk — due within 2 days", items: a.atRisk },
    { id: "follow", color: "var(--blue)", dot: "#2E75B6", icon: "📦", title: "Follow-ups due — still open", items: a.followUps },
    { id: "qc", color: "var(--purple)", dot: "#7030A0", icon: "🏠", title: "Turnover — QC failed", items: a.qcFails },
    { id: "outreach", color: "var(--green)", dot: "#2E7D32", icon: "🔑", title: "Renewal outreach needed", items: a.outreach },
  ];
  const total = actionCount();
  $("#view").innerHTML = `
    <p class="muted" style="margin-bottom:16px">${total === 0
      ? "Nothing needs you. Everything is on track."
      : `${total} item${total === 1 ? "" : "s"} need${total === 1 ? "s" : ""} you — fix it in the source tracker and this queue updates itself.`}</p>
    ${groups.map(g => `
      <div class="ac-group">
        <div class="ac-head">
          <h3>${g.icon} ${g.title}</h3><span class="cnt">${g.items.length}</span></div>
        ${g.items.length ? g.items.map(it => `
          <div class="ac-row"><div class="main-info"><div class="t1">${esc(it.title)}</div>
          <div class="t2">${esc(it.sub)}</div></div>
          <button class="btn sm ghost" data-open="${esc(it.key)}" data-view="${it.view}">Open →</button></div>`).join("")
        : `<div class="empty">Clear.</div>`}
      </div>`).join("")}`;
  $$("#view [data-open]").forEach(el => el.onclick = () => go(el.dataset.view, { key: el.dataset.open }));
}

/* ------------------------- work orders ------------------------- */
const WO_CAT = ["Plumbing", "Electrical", "HVAC", "Appliance", "Lock/Key", "Pest Control", "Interior", "Exterior/Common Area"];
const WO_PRI = ["Emergency", "High", "Standard", "Low"];
const WO_STATUS = ["Open", "In Progress", "Waiting on Parts", "Closed"];
let woFilter = { q: "", status: "", priority: "", category: "" };

function vWorkOrders(opts) {
  const d = DB.data;
  const open = d.workOrders.filter(isOpen);
  const br = d.workOrders.filter(w => isOpen(w) && woCalc(w).sla === "Breached");
  const closedW = d.workOrders.filter(w => w.status === "Closed");
  const avg = closedW.length ? (closedW.reduce((s, w) => s + woCalc(w).daysOpen, 0) / closedW.length).toFixed(1) : "—";
  $("#view").innerHTML = `
    <div class="grid g4">
      <div class="card"><h3>Open work orders</h3><div class="kpi-num">${open.length}</div></div>
      <div class="card"><h3>SLA breaches</h3><div class="kpi-num" style="color:var(--red)">${br.length}</div></div>
      <div class="card"><h3>Avg days to close</h3><div class="kpi-num">${avg}</div></div>
      <div class="card"><h3>Emergency open</h3><div class="kpi-num" style="color:var(--amber)">${open.filter(w => w.priority === "Emergency").length}</div></div>
    </div>
    <div class="card" style="margin-top:16px"><h3>Work orders by category</h3>
      <div class="chart-box sm"><canvas id="ch-cat"></canvas></div></div>
    <div class="toolbar">
      <input type="search" id="fq" placeholder="Search ID, unit, description…" value="${esc(woFilter.q)}">
      <select id="fs"><option value="">All statuses</option>${fieldOpts(woFilter.status, WO_STATUS)}</select>
      <select id="fp"><option value="">All priorities</option>${fieldOpts(woFilter.priority, WO_PRI)}</select>
      <select id="fc"><option value="">All categories</option>${fieldOpts(woFilter.category, WO_CAT)}</select>
      <span class="spacer"></span>
      <button class="btn ghost" id="csvBtn">Export CSV</button>
      <button class="btn primary" id="addBtn">＋ New work order</button>
    </div>
    <div class="tblwrap"><table><thead><tr>
      <th>ID</th><th>Opened</th><th>Unit</th><th>Category</th><th>Priority</th><th>Description</th>
      <th>Assignee</th><th>Status</th><th class="num">SLA</th><th>Flag</th>
    </tr></thead><tbody id="wbody"></tbody></table></div>`;
  const draw = () => {
    const q = woFilter.q.toLowerCase();
    let list = d.workOrders.filter(w =>
      (!woFilter.status || w.status === woFilter.status) &&
      (!woFilter.priority || w.priority === woFilter.priority) &&
      (!woFilter.category || w.category === woFilter.category) &&
      (!q || (w.id + " " + w.unit + " " + w.description).toLowerCase().includes(q)));
    $("#wbody").innerHTML = list.map(w => { const c = woCalc(w); return `
      <tr class="clickable" data-id="${esc(w.id)}" ${opts.key === w.id ? 'id="flashrow"' : ""}>
        <td><b>${esc(w.id)}</b></td><td>${fmtD(w.opened)}</td><td>${esc(w.unit)}</td>
        <td>${esc(w.category)}</td><td>${priPill(w.priority)}</td>
        <td class="desc" title="${esc(w.description)}">${esc(w.description)}</td>
        <td>${esc(w.assignee)}</td><td>${statusPill(w.status)}</td>
        <td class="num">${c.target}d</td><td>${slaPill(c)}</td></tr>`; }).join("") ||
      `<tr><td colspan="10" style="text-align:center;color:var(--muted);padding:24px">No work orders match.</td></tr>`;
    $$("#wbody tr.clickable").forEach(tr => tr.onclick = () => woModal(tr.dataset.id));
    const fr = $("#flashrow"); if (fr) { fr.classList.add("flash"); fr.scrollIntoView({ block: "center" }); }
  };
  $("#fq").oninput = e => { woFilter.q = e.target.value; draw(); };
  $("#fs").onchange = e => { woFilter.status = e.target.value; draw(); };
  $("#fp").onchange = e => { woFilter.priority = e.target.value; draw(); };
  $("#fc").onchange = e => { woFilter.category = e.target.value; draw(); };
  $("#addBtn").onclick = () => woModal(null);
  $("#csvBtn").onclick = () => downloadCSV("work-orders.csv",
    [["ID", "Opened", "Unit", "Category", "Priority", "Description", "Assignee", "Status", "Closed", "SLA Target", "Days Open", "SLA Status"]]
    .concat(d.workOrders.map(w => { const c = woCalc(w); return [w.id, w.opened, w.unit, w.category, w.priority, w.description, w.assignee, w.status, w.closed || "", c.target, c.daysOpen, c.sla]; })));
  draw();
  charts.push(new Chart($("#ch-cat"), { type: "bar",
    data: { labels: WO_CAT, datasets: [{ data: WO_CAT.map(c => d.workOrders.filter(w => w.category === c).length),
      backgroundColor: "#1F3864", borderRadius: 5 }] },
    options: { maintainAspectRatio: false, plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } } }));
}
function woModal(id) {
  const d = DB.data;
  const w = id ? d.workOrders.find(x => x.id === id) :
    { id: "", opened: todayISO(), unit: "", category: "Plumbing", priority: "Standard",
      description: "", assignee: "Unassigned", status: "Open", closed: null };
  const isNew = !id;
  const close = openModal(isNew ? "New work order" : "Edit " + w.id, `
    <div class="f2">
      <div class="frow"><label>Unit</label><input id="f-unit" value="${esc(w.unit)}" placeholder="A-101"></div>
      <div class="frow"><label>Date opened</label><input id="f-opened" type="date" value="${esc(w.opened)}"></div>
    </div>
    <div class="f2">
      <div class="frow"><label>Category</label><select id="f-cat">${fieldOpts(w.category, WO_CAT)}</select></div>
      <div class="frow"><label>Priority</label><select id="f-pri">${fieldOpts(w.priority, WO_PRI)}</select></div>
    </div>
    <div class="frow"><label>Description</label><textarea id="f-desc">${esc(w.description)}</textarea></div>
    <div class="f2">
      <div class="frow"><label>Assigned to</label><input id="f-assignee" value="${esc(w.assignee)}"></div>
      <div class="frow"><label>Status</label><select id="f-status">${fieldOpts(w.status, WO_STATUS)}</select></div>
    </div>
    <div class="frow"><label>Date closed</label><input id="f-closed" type="date" value="${esc(w.closed || "")}"></div>
    <div class="hint" id="slaHint"></div>`,
    `${isNew ? "" : `<button class="btn danger" id="f-del">Delete</button><span class="spacer" style="flex:1"></span>`}
     <button class="btn ghost" id="f-cancel">Cancel</button>
     <button class="btn primary" id="f-save">Save</button>`);
  const hint = () => {
    const p = $("#f-pri").value, t = SLA_TARGET[p];
    $("#slaHint").textContent = `SLA target sets automatically: ${p} → ${t} day${t === 1 ? "" : "s"}.`;
  };
  $("#f-pri").onchange = hint; hint();
  $("#f-cancel").onclick = close;
  if (!isNew) $("#f-del").onclick = () => {
    if (confirm(`Delete ${w.id}?`)) { d.workOrders = d.workOrders.filter(x => x.id !== id); DB.save(); close(); toast("Work order deleted"); render(); }
  };
  $("#f-save").onclick = () => {
    const v = sel => $(sel).value.trim();
    const rec = { id: w.id, opened: v("#f-opened") || todayISO(), unit: v("#f-unit"),
      category: $("#f-cat").value, priority: $("#f-pri").value, description: v("#f-desc"),
      assignee: v("#f-assignee") || "Unassigned", status: $("#f-status").value,
      closed: v("#f-closed") || null };
    if (!rec.unit) { toast("Unit is required"); return; }
    if (rec.status === "Closed" && !rec.closed) rec.closed = todayISO();
    if (rec.status !== "Closed") rec.closed = null;
    if (isNew) {
      const nums = d.workOrders.map(x => parseInt((x.id || "").replace(/\D/g, ""), 10)).filter(n => !isNaN(n));
      rec.id = "WO-" + (Math.max(...nums, 1000) + 1);
      d.workOrders.unshift(rec);
    } else Object.assign(w, rec);
    DB.save(); close(); toast(isNew ? `${rec.id} created` : `${w.id} saved`); render();
  };
}

/* ------------------------- turnover kanban ------------------------- */
const TO_STATUS = ["Not Started", "In Progress", "Ready for QC", "Ready"];
function vTurnover(opts) {
  const d = DB.data;
  const ready = d.turnover.filter(u => u.status === "Ready").length;
  $("#view").innerHTML = `
    <div class="grid g4" style="margin-bottom:16px">
      <div class="card"><h3>Units tracked</h3><div class="kpi-num">${d.turnover.length}</div></div>
      <div class="card"><h3>Ready</h3><div class="kpi-num" style="color:var(--green)">${ready}</div></div>
      <div class="card"><h3>% ready</h3><div class="kpi-num">${d.turnover.length ? Math.round(ready / d.turnover.length * 100) : 0}%</div></div>
      <div class="card"><h3>QC failed</h3><div class="kpi-num" style="color:var(--red)">${d.turnover.filter(u => u.qc === "No").length}</div></div>
    </div>
    <div class="toolbar"><span class="spacer"></span>
      <button class="btn ghost" id="csvBtn">Export CSV</button>
      <button class="btn primary" id="addBtn">＋ Add unit</button></div>
    <div class="kanban">${TO_STATUS.map(s => {
      const cards = d.turnover.filter(u => u.status === s);
      return `<div class="kcol"><h4>${s}<span>${cards.length}</span></h4>
        ${cards.map(u => `
          <div class="kcard" data-unit="${esc(u.unit)}" ${opts.key === u.unit ? 'id="flashrow"' : ""}>
            <div class="u">${esc(u.unit)}</div><div class="b">Building ${esc(u.building)} · moved out ${fmtD(u.moveOut)}</div>
            <div class="meta">
              ${u.qc === "No" ? `<span class="pill red">QC failed</span>` : u.qc === "Pending" ? `<span class="pill amber">QC pending</span>` : `<span class="pill green">QC passed</span>`}
              ${u.deficiencies ? `<span class="pill gray">${u.deficiencies} deficiencies</span>` : ""}
            </div>
            ${u.topDeficiency && u.topDeficiency !== "None" ? `<div class="b" style="margin-top:6px">Top: ${esc(u.topDeficiency)}</div>` : ""}
          </div>`).join("") || `<div class="empty">—</div>`}</div>`;
    }).join("")}</div>`;
  $$("#view .kcard").forEach(c => c.onclick = () => toModal(c.dataset.unit));
  $("#addBtn").onclick = () => toModal(null);
  $("#csvBtn").onclick = () => downloadCSV("turnover.csv",
    [["Unit", "Building", "Move-Out", "Inspected", "Inspector", "Deficiencies", "Top Deficiency", "Status", "QC", "Ready Date"]]
    .concat(d.turnover.map(u => [u.unit, u.building, u.moveOut, u.inspected, u.inspector, u.deficiencies, u.topDeficiency, u.status, u.qc, u.readyDate || ""])));
  const fr = $("#flashrow"); if (fr) { fr.classList.add("flash"); fr.scrollIntoView({ block: "center" }); }
}
function toModal(unit) {
  const d = DB.data;
  const u = unit ? d.turnover.find(x => x.unit === unit) :
    { unit: "", building: "", moveOut: todayISO(), inspected: "", inspector: "",
      deficiencies: 0, topDeficiency: "None", status: "Not Started", qc: "Pending", readyDate: null };
  const isNew = !unit;
  const close = openModal(isNew ? "Add unit" : "Unit " + u.unit, `
    <div class="f2">
      <div class="frow"><label>Unit</label><input id="f-unit" value="${esc(u.unit)}" ${isNew ? "" : "disabled"}></div>
      <div class="frow"><label>Building</label><input id="f-bldg" value="${esc(u.building)}"></div>
    </div>
    <div class="f2">
      <div class="frow"><label>Move-out date</label><input id="f-mo" type="date" value="${esc(u.moveOut || "")}"></div>
      <div class="frow"><label>Inspector</label><input id="f-insp" value="${esc(u.inspector)}"></div>
    </div>
    <div class="f2">
      <div class="frow"><label>Make-ready status</label><select id="f-status">${fieldOpts(u.status, TO_STATUS)}</select></div>
      <div class="frow"><label>QC</label><select id="f-qc">${fieldOpts(u.qc, ["Yes", "No", "Pending"])}</select></div>
    </div>
    <div class="f2">
      <div class="frow"><label>Deficiencies found</label><input id="f-def" type="number" min="0" value="${esc(u.deficiencies)}"></div>
      <div class="frow"><label>Top deficiency</label><select id="f-top">${fieldOpts(u.topDeficiency, ["None", "Paint", "Flooring", "Appliance", "Plumbing", "Electrical", "Cleaning", "Damaged Fixture"])}</select></div>
    </div>`,
    `${isNew ? "" : `<button class="btn danger" id="f-del">Delete</button><span style="flex:1"></span>`}
     <button class="btn ghost" id="f-cancel">Cancel</button>
     <button class="btn primary" id="f-save">Save</button>`);
  $("#f-cancel").onclick = close;
  if (!isNew) $("#f-del").onclick = () => {
    if (confirm(`Remove unit ${u.unit}?`)) { d.turnover = d.turnover.filter(x => x.unit !== unit); DB.save(); close(); toast("Unit removed"); render(); }
  };
  $("#f-save").onclick = () => {
    const v = sel => $(sel).value.trim();
    const rec = { unit: isNew ? v("#f-unit") : u.unit, building: v("#f-bldg"),
      moveOut: v("#f-mo"), inspector: v("#f-insp"),
      deficiencies: parseInt($("#f-def").value, 10) || 0, topDeficiency: $("#f-top").value,
      status: $("#f-status").value, qc: $("#f-qc").value, readyDate: u.readyDate,
      inspected: u.inspected };
    if (!rec.unit) { toast("Unit is required"); return; }
    if (d.turnover.some(x => x.unit === rec.unit) && isNew) { toast("Unit already tracked"); return; }
    if (rec.status === "Ready" && !rec.readyDate) rec.readyDate = todayISO();
    if (isNew) d.turnover.push(rec); else Object.assign(u, rec);
    DB.save(); close(); toast(isNew ? `Unit ${rec.unit} added` : `Unit ${u.unit} saved`); render();
  };
}

/* ------------------------- retention ------------------------- */
const RT_INTENT = ["Renewing", "Undecided", "Unknown", "Not Renewing"];
function vRetention(opts) {
  const d = DB.data;
  const renewing = d.retention.filter(r => r.intent === "Renewing").length;
  const atRisk = d.retention.filter(r => r.intent === "Undecided" || r.intent === "Not Renewing").length;
  const decided = d.retention.filter(r => r.intent !== "Unknown").length;
  const rate = decided ? Math.round(renewing / decided * 100) : 0;
  $("#view").innerHTML = `
    <div class="grid g4">
      <div class="card"><h3>Leases tracked</h3><div class="kpi-num">${d.retention.length}</div></div>
      <div class="card"><h3>Renewing</h3><div class="kpi-num" style="color:var(--green)">${renewing}</div></div>
      <div class="card"><h3>At-risk renewals</h3><div class="kpi-num" style="color:var(--amber)">${atRisk}</div></div>
      <div class="card"><h3>Retention rate</h3><div class="kpi-num">${rate}%</div><div class="sub muted" style="font-size:11.5px;margin-top:4px">on decided units</div></div>
    </div>
    <div class="grid g2" style="margin-top:16px">
      <div class="card"><h3>Renewal intent</h3><div class="chart-box sm"><canvas id="ch-intent"></canvas></div></div>
      <div class="card"><h3>How it works</h3>
        <p class="muted" style="font-size:13px;line-height:1.7">Log every renewal conversation with the <b>+</b> stepper.
        Flip intent the moment a resident decides — the rate, the donut, and the Action Center
        update instantly. Renewals are counted on <b>decided</b> units only; <i>Unknown</i> means
        outreach hasn't happened yet.</p></div>
    </div>
    <div class="toolbar"><span class="spacer"></span>
      <button class="btn ghost" id="csvBtn">Export CSV</button>
      <button class="btn primary" id="addBtn">＋ Add lease</button></div>
    <div class="tblwrap"><table><thead><tr>
      <th>Unit</th><th>Lease end</th><th class="num">Rent</th><th>Offer sent</th><th>Touches</th><th>Intent</th><th>Reason</th>
    </tr></thead><tbody>
    ${d.retention.map(r => {
      const exp = diffDays(todayISO(), r.leaseEnd);
      const intentCls = { Renewing: "green", Undecided: "amber", Unknown: "gray", "Not Renewing": "red" }[r.intent];
      return `<tr ${opts.key === r.unit ? 'id="flashrow"' : ""}>
        <td><b>${esc(r.unit)}</b></td>
        <td>${fmtD(r.leaseEnd)} ${exp >= 0 && exp <= 60 ? `<span class="pill amber">${exp}d</span>` : ""}</td>
        <td class="num">$${esc(r.rent)}</td>
        <td>${r.offerSent === "Yes" ? `<span class="pill green">Yes</span>` : `<span class="pill gray">No</span>`}</td>
        <td><button class="btn sm ghost" data-touch="${esc(r.unit)}" data-d="-1">−</button>
            <b style="margin:0 6px">${r.touches}</b>
            <button class="btn sm ghost" data-touch="${esc(r.unit)}" data-d="1">＋</button></td>
        <td><select data-intent="${esc(r.unit)}" style="border:1px solid var(--line);border-radius:7px;padding:5px 8px;font-size:12.5px">
              ${fieldOpts(r.intent, RT_INTENT)}</select>
            <span class="pill ${intentCls}" style="margin-left:6px">${esc(r.intent)}</span></td>
        <td class="muted">${esc(r.reason || "—")}</td></tr>`;
    }).join("")}</tbody></table></div>`;
  $$("#view [data-touch]").forEach(b => b.onclick = e => {
    e.stopPropagation();
    const r = d.retention.find(x => x.unit === b.dataset.touch);
    r.touches = Math.max(0, r.touches + parseInt(b.dataset.d, 10));
    DB.save(); toast(`Unit ${r.unit}: ${r.touches} touches`); render();
  });
  $$("#view [data-intent]").forEach(s => s.onchange = () => {
    const r = d.retention.find(x => x.unit === s.dataset.intent);
    r.intent = s.value; DB.save(); toast(`Unit ${r.unit} → ${r.intent}`); render();
  });
  $("#csvBtn").onclick = () => downloadCSV("retention.csv",
    [["Unit", "Resident", "Lease End", "Rent", "Offer Sent", "Touches", "Intent", "Reason"]]
    .concat(d.retention.map(r => [r.unit, r.resident, r.leaseEnd, r.rent, r.offerSent, r.touches, r.intent, r.reason || ""])));
  $("#addBtn").onclick = () => {
    const close = openModal("Add lease", `
      <div class="f2"><div class="frow"><label>Unit</label><input id="f-unit"></div>
      <div class="frow"><label>Lease end</label><input id="f-lease" type="date"></div></div>
      <div class="f2"><div class="frow"><label>Monthly rent</label><input id="f-rent" type="number" min="0"></div>
      <div class="frow"><label>Intent</label><select id="f-intent">${fieldOpts("Unknown", RT_INTENT)}</select></div></div>`,
      `<button class="btn ghost" id="f-cancel">Cancel</button><button class="btn primary" id="f-save">Save</button>`);
    $("#f-cancel").onclick = close;
    $("#f-save").onclick = () => {
      const unit = $("#f-unit").value.trim();
      if (!unit) { toast("Unit is required"); return; }
      if (d.retention.some(x => x.unit === unit)) { toast("Unit already tracked"); return; }
      d.retention.push({ unit, resident: "R-" + unit.replace(/\D/g, ""), leaseEnd: $("#f-lease").value,
        rent: parseInt($("#f-rent").value, 10) || 0, offerSent: "No", touches: 0,
        intent: $("#f-intent").value, reason: "", notes: "" });
      DB.save(); close(); toast(`Unit ${unit} added`); render();
    };
  };
  charts.push(new Chart($("#ch-intent"), { type: "doughnut",
    data: { labels: RT_INTENT, datasets: [{ data: RT_INTENT.map(i => d.retention.filter(r => r.intent === i).length),
      backgroundColor: ["#2E7D32", "#ED7D31", "#9aa5b5", "#C00000"] }] },
    options: { maintainAspectRatio: false, plugins: { legend: { position: "right" } } } }));
  const fr = $("#flashrow"); if (fr) { fr.classList.add("flash"); fr.scrollIntoView({ block: "center" }); }
}

/* ------------------------- service recovery ------------------------- */
const RC_CAT = ["Maintenance Delay", "Service Experience", "Noise Complaint", "Move-In Condition", "Package Issue", "Access Issue", "Parking Dispute", "Billing Question", "Pest Control", "Common Area", "Amenity Access", "Other"];
const RC_SEV = ["Low", "Medium", "High", "Critical"];
function vRecovery(opts) {
  const d = DB.data;
  const open = d.recovery.filter(r => r.resolved !== "Yes");
  const scored = d.recovery.filter(r => r.satisfaction);
  const avg = scored.length ? (scored.reduce((s, r) => s + (+r.satisfaction), 0) / scored.length).toFixed(2) : "—";
  $("#view").innerHTML = `
    <div class="grid g4">
      <div class="card"><h3>Open loops</h3><div class="kpi-num" style="color:var(--blue)">${open.length}</div></div>
      <div class="card"><h3>Avg satisfaction</h3><div class="kpi-num">${avg}</div></div>
      <div class="card"><h3>Follow-ups due ≤2d</h3><div class="kpi-num" style="color:var(--amber)">${actionItems().followUps.length}</div></div>
      <div class="card"><h3>Total logged</h3><div class="kpi-num">${d.recovery.length}</div></div>
    </div>
    <div class="toolbar"><span class="spacer"></span>
      <button class="btn ghost" id="csvBtn">Export CSV</button>
      <button class="btn primary" id="addBtn">＋ Log issue</button></div>
    <div class="tblwrap"><table><thead><tr>
      <th>Date</th><th>Unit</th><th>Category</th><th>Severity</th><th>Owner</th><th>Resolved</th><th>Follow-up</th><th>Satisfaction</th>
    </tr></thead><tbody>
    ${d.recovery.map(r => {
      const fu = followUpState(r);
      const sevCls = { Low: "gray", Medium: "blue", High: "amber", Critical: "red" }[r.severity];
      return `<tr class="clickable" data-id="${esc(r.id)}" ${opts.key === r.id ? 'id="flashrow"' : ""}>
        <td>${fmtD(r.date)}</td><td><b>${esc(r.unit)}</b></td><td>${esc(r.category)}</td>
        <td><span class="pill ${sevCls}">${esc(r.severity)}</span></td><td>${esc(r.owner)}</td>
        <td>${r.resolved === "Yes" ? `<span class="pill green">Yes</span>` : `<span class="pill amber">No</span>`}</td>
        <td>${r.followUp ? fmtD(r.followUp) + (fu ? ` <span class="pill ${fu.cls}">${fu.label}</span>` : "") : "—"}</td>
        <td>${r.satisfaction ? `<span class="stars">${"★".repeat(+r.satisfaction)}${"☆".repeat(5 - (+r.satisfaction))}</span>` : `<span class="muted">—</span>`}</td></tr>`;
    }).join("")}</tbody></table></div>`;
  $$("#view tr.clickable").forEach(tr => tr.onclick = () => rcModal(tr.dataset.id));
  $("#addBtn").onclick = () => rcModal(null);
  $("#csvBtn").onclick = () => downloadCSV("service-recovery.csv",
    [["Date", "Unit", "Category", "Description", "Severity", "Owner", "Action Taken", "Resolved", "Follow-Up", "Satisfaction"]]
    .concat(d.recovery.map(r => [r.date, r.unit, r.category, r.description, r.severity, r.owner, r.action, r.resolved, r.followUp || "", r.satisfaction || ""])));
  const fr = $("#flashrow"); if (fr) { fr.classList.add("flash"); fr.scrollIntoView({ block: "center" }); }
}
function rcModal(id) {
  const d = DB.data;
  const r = id ? d.recovery.find(x => x.id === id) :
    { id: "", date: todayISO(), unit: "", category: "Service Experience", description: "",
      severity: "Medium", owner: "", action: "", resolved: "No", followUp: "", satisfaction: "" };
  const isNew = !id;
  const close = openModal(isNew ? "Log service issue" : "Service issue · Unit " + r.unit, `
    <div class="f2"><div class="frow"><label>Date</label><input id="f-date" type="date" value="${esc(r.date)}"></div>
    <div class="frow"><label>Unit</label><input id="f-unit" value="${esc(r.unit)}"></div></div>
    <div class="f2"><div class="frow"><label>Category</label><select id="f-cat">${fieldOpts(r.category, RC_CAT)}</select></div>
    <div class="frow"><label>Severity</label><select id="f-sev">${fieldOpts(r.severity, RC_SEV)}</select></div></div>
    <div class="frow"><label>Description</label><textarea id="f-desc">${esc(r.description)}</textarea></div>
    <div class="f2"><div class="frow"><label>Owner</label><input id="f-owner" value="${esc(r.owner)}"></div>
    <div class="frow"><label>Resolved</label><select id="f-res">${fieldOpts(r.resolved, ["No", "Yes"])}</select></div></div>
    <div class="frow"><label>Action taken</label><textarea id="f-action">${esc(r.action)}</textarea></div>
    <div class="f2"><div class="frow"><label>Follow-up date</label><input id="f-fu" type="date" value="${esc(r.followUp || "")}"></div>
    <div class="frow"><label>Satisfaction (1–5)</label><select id="f-sat"><option value="">—</option>${fieldOpts(String(r.satisfaction || ""), ["1", "2", "3", "4", "5"])}</select></div></div>
    <div class="hint">The loop closes at the follow-up — not at the action. Set a date and come back to confirm.</div>`,
    `${isNew ? "" : `<button class="btn danger" id="f-del">Delete</button><span style="flex:1"></span>`}
     <button class="btn ghost" id="f-cancel">Cancel</button><button class="btn primary" id="f-save">Save</button>`);
  $("#f-cancel").onclick = close;
  if (!isNew) $("#f-del").onclick = () => {
    if (confirm("Delete this entry?")) { d.recovery = d.recovery.filter(x => x.id !== id); DB.save(); close(); toast("Entry deleted"); render(); }
  };
  $("#f-save").onclick = () => {
    const v = sel => $(sel).value.trim();
    const rec = { id: r.id, date: v("#f-date") || todayISO(), unit: v("#f-unit"),
      category: $("#f-cat").value, description: v("#f-desc"), severity: $("#f-sev").value,
      owner: v("#f-owner"), action: v("#f-action"), resolved: $("#f-res").value,
      followUp: v("#f-fu") || "", satisfaction: $("#f-sat").value || "" };
    if (!rec.unit) { toast("Unit is required"); return; }
    if (isNew) { rec.id = "RC-" + Date.now().toString(36).toUpperCase(); d.recovery.unshift(rec); }
    else Object.assign(r, rec);
    DB.save(); close(); toast(isNew ? "Issue logged" : "Entry saved"); render();
  };
}

/* ------------------------- weekly report ------------------------- */
function vReport() {
  const d = DB.data, t = todayISO(), weekAgo = new Date(Date.now() - 6 * DAY).toISOString().slice(0, 10);
  const closedWk = d.workOrders.filter(w => w.status === "Closed" && w.closed && w.closed >= weekAgo).length;
  const closedAll = d.workOrders.filter(w => w.status === "Closed");
  const avg = closedAll.length ? (closedAll.reduce((s, w) => s + woCalc(w).daysOpen, 0) / closedAll.length).toFixed(1) : "—";
  const br = d.workOrders.filter(w => isOpen(w) && woCalc(w).sla === "Breached");
  const readyWk = d.turnover.filter(u => u.readyDate && u.readyDate >= weekAgo).length;
  const renew = d.retention.filter(r => r.intent === "Renewing").length;
  const scored = d.recovery.filter(r => r.satisfaction);
  const sat = scored.length ? (scored.reduce((s, r) => s + (+r.satisfaction), 0) / scored.length).toFixed(2) : "—";
  const top3 = br.slice(0, 3);
  $("#view").innerHTML = `
    <div class="toolbar no-print"><span class="spacer"></span>
      <button class="btn primary" onclick="window.print()">🖨 Print / Save PDF</button></div>
    <div class="report">
      <h1>Weekly Operations Report</h1>
      <div class="wk">Week of ${fmtD(weekAgo)} – ${fmtD(t)}</div>
      <div class="rkpis">
        ${[["Work orders closed", closedWk], ["Avg days to close", avg], ["SLA breaches now", br.length],
           ["Units made ready", readyWk], ["Renewals secured", renew], ["Avg satisfaction", sat]]
          .map(k => `<div class="rkpi"><div class="n">${k[1]}</div><div class="l">${k[0]}</div></div>`).join("")}
      </div>
      <h3 style="font-size:14px;margin-bottom:10px">Top breaches</h3>
      ${top3.length ? `<div class="tblwrap"><table><thead><tr><th>ID</th><th>Unit</th><th>Priority</th><th class="num">Days overdue</th></tr></thead>
        <tbody>${top3.map(w => { const c = woCalc(w); return `<tr><td><b>${esc(w.id)}</b></td><td>${esc(w.unit)}</td>
        <td>${priPill(w.priority)}</td><td class="num" style="color:var(--red);font-weight:700">${c.over}</td></tr>`; }).join("")}</tbody></table></div>`
        : `<div class="empty">No breaches this week.</div>`}
      <p class="muted" style="margin-top:18px;font-size:12px">Generated ${fmtD(t)} · sample data for demonstration. Full detail lives in the Action Center.</p>
    </div>`;
}

/* ============================== init ============================== */
document.addEventListener("DOMContentLoaded", () => {
  DB.load();
  $$("#nav button").forEach(b => b.onclick = () => go(b.dataset.view));
  $("#resetBtn").onclick = () => { if (confirm("Reset all demo data? Your edits will be lost.")) { DB.reset(); toast("Demo data reset"); render(); } };
  window.addEventListener("hashchange", route);
  route();
});
