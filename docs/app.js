// Korea Memory Pulse - dashboard renderer
// Fetches docs/data/latest.json and paints all the panels.

const DATA_URL = "data/latest.json";

const $ = (id) => document.getElementById(id);

// ---- formatters ----
const fmtNum = (n, d = 2) => {
  if (n == null || isNaN(n)) return "—";
  return Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
};
const fmtVol = (n) => {
  if (n == null || isNaN(n)) return "—";
  if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return String(n);
};
const fmtChg = (chg, pct) => {
  if (chg == null || pct == null) return "—";
  const sign = chg > 0 ? "+" : "";
  return `${sign}${fmtNum(chg)}  (${sign}${fmtNum(pct)}%)`;
};
const fmtTimeAgo = (iso) => {
  if (!iso) return "—";
  const t = new Date(iso);
  const mins = Math.floor((Date.now() - t.getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const h = Math.floor(mins / 60);
  if (h < 24) return `${h}h ${mins % 60}m ago`;
  return t.toISOString().slice(0, 16) + "Z";
};
const fmtTimeUntil = (iso) => {
  if (!iso) return "—";
  const t = new Date(iso);
  const mins = Math.floor((t.getTime() - Date.now()) / 60000);
  if (mins <= 0) return "due";
  if (mins < 60) return `${mins}m`;
  return `${Math.floor(mins / 60)}h ${mins % 60}m`;
};

// ---- market state ----
function marketState() {
  // KRX trades 09:00-15:30 KST = 00:00-06:30 UTC
  const utcH = new Date().getUTCHours();
  const utcM = new Date().getUTCMinutes();
  const utcMins = utcH * 60 + utcM;
  if (utcMins >= 0 && utcMins < 390) return { label: "KR OPEN", cls: "open" };
  // US regular session: 14:30-21:00 UTC
  if (utcMins >= 870 && utcMins < 1260) return { label: "US OPEN", cls: "open" };
  return { label: "AFTER HOURS", cls: "closed" };
}

// ---- ticker card ----
function paintTicker(sym, q, adrQ) {
  if (!q) return;
  $(`price-${sym.split(".")[0]}`).textContent = fmtNum(q.price, sym.endsWith("KS") ? 0 : 2);
  const chgEl = $(`change-${sym.split(".")[0]}`);
  chgEl.textContent = fmtChg(q.change, q.change_pct);
  chgEl.classList.remove("up", "down");
  if (q.change > 0) chgEl.classList.add("up");
  else if (q.change < 0) chgEl.classList.add("down");

  $(`vol-${sym.split(".")[0]}`).textContent = fmtVol(q.volume);
  $(`prev-${sym.split(".")[0]}`).textContent = fmtNum(q.prev_close, sym.endsWith("KS") ? 0 : 2);

  if (adrQ && adrQ.change_pct != null) {
    const sign = adrQ.change_pct > 0 ? "+" : "";
    $(`adr-${sym.split(".")[0]}`).textContent = `${sign}${fmtNum(adrQ.change_pct)}%`;
  } else {
    $(`adr-${sym.split(".")[0]}`).textContent = "—";
  }
}

// ---- peers table ----
function paintPeers(peersData) {
  const tbody = document.querySelector("#peer-table tbody");
  tbody.innerHTML = "";
  const rows = Object.entries(peersData)
    .map(([sym, p]) => ({
      sym, name: p.name, group: p.group,
      price: p.price, change: p.change, change_pct: p.change_pct,
    }))
    .sort((a, b) => (b.change_pct || 0) - (a.change_pct || 0));

  for (const r of rows) {
    const tr = document.createElement("tr");
    const cls = r.change > 0 ? "up" : r.change < 0 ? "down" : "";
    tr.innerHTML = `
      <td class="sym">${r.sym}</td>
      <td>${r.name || ""}</td>
      <td class="group">${r.group || ""}</td>
      <td class="num">${fmtNum(r.price, 2)}</td>
      <td class="num ${cls}">${r.change != null ? (r.change > 0 ? "+" : "") + fmtNum(r.change, 2) : "—"}</td>
      <td class="num ${cls}">${r.change_pct != null ? (r.change_pct > 0 ? "+" : "") + fmtNum(r.change_pct, 2) + "%" : "—"}</td>
    `;
    tbody.appendChild(tr);
  }
}

// ---- macro table ----
function paintMacro(macroData) {
  const tbody = document.querySelector("#macro-table tbody");
  tbody.innerHTML = "";
  for (const [sym, m] of Object.entries(macroData)) {
    const cls = m.change > 0 ? "up" : m.change < 0 ? "down" : "";
    const chg = m.change_pct != null ? (m.change_pct > 0 ? "+" : "") + fmtNum(m.change_pct, 2) + "%" : "—";
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><span class="muted">${sym}</span> ${m.label || ""}</td>
      <td class="num">${fmtNum(m.price, 2)}</td>
      <td class="num ${cls}">${chg}</td>
    `;
    tbody.appendChild(tr);
  }
}

// ---- filings + news lists ----
function paintFilings(filings) {
  const ul = $("filings-list");
  ul.innerHTML = "";
  if (!filings || !filings.length) {
    ul.innerHTML = '<li class="muted">No flagged filings.</li>';
    return;
  }
  for (const f of filings) {
    const li = document.createElement("li");
    if (f.material) li.classList.add("material");
    li.innerHTML = `
      <div class="item-head">
        <span class="item-co">${f.company || ""}</span>
        ${f.url ? `<a href="${f.url}" target="_blank" rel="noopener">DART ↗</a>` : ""}
      </div>
      <div class="item-body">${f.summary_en || f.report_nm_kr || ""}</div>
    `;
    ul.appendChild(li);
  }
}

function paintNews(news) {
  const ul = $("news-list");
  ul.innerHTML = "";
  if (!news || !news.length) {
    ul.innerHTML = '<li class="muted">No flagged news in the last cycle.</li>';
    return;
  }
  for (const n of news) {
    const li = document.createElement("li");
    li.innerHTML = `
      <div class="item-head">
        <span class="item-co">${n.source || ""}</span>
        ${n.url ? `<a href="${n.url}" target="_blank" rel="noopener">LINK ↗</a>` : ""}
      </div>
      <div class="item-body">${n.headline || ""}</div>
      ${n.implication ? `<div class="item-implication">${n.implication}</div>` : ""}
    `;
    ul.appendChild(li);
  }
}

function paintWatch(items) {
  const ol = $("watch-list");
  ol.innerHTML = "";
  for (const it of (items || [])) {
    const li = document.createElement("li");
    li.textContent = it;
    ol.appendChild(li);
  }
}

// ---- main ----
async function load() {
  let payload;
  try {
    const r = await fetch(DATA_URL, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    payload = await r.json();
  } catch (e) {
    $("headline").textContent = "Data feed unavailable.";
    $("summary").textContent = String(e);
    return;
  }

  const brief = payload.brief || {};
  const data = payload.data || {};
  const quotes = data.quotes || {};

  // hero
  $("hero-time").textContent = payload.generated_at || "—";
  $("headline").textContent = brief.headline || "—";
  $("summary").textContent = brief.summary || "";
  const conf = (brief.confidence || "—").toLowerCase();
  const cEl = $("confidence");
  cEl.textContent = `CONF ${conf.toUpperCase()}`;
  cEl.classList.remove("high", "medium", "low");
  if (["high", "medium", "low"].includes(conf)) cEl.classList.add(conf);

  // primary tickers
  const primary = quotes.primary || {};
  const adrs = quotes.adrs || {};
  paintTicker("005930.KS", primary["005930.KS"], adrs["SSNLF"]);
  paintTicker("000660.KS", primary["000660.KS"], adrs["HXSCL"]);

  // panels
  $("pair-trade").textContent = brief.pair_trade_view || "—";
  const mc = brief.memory_cycle || {};
  $("cycle-stage").textContent = mc.stage || "—";
  $("cycle-notes").textContent = mc.notes || "";
  $("hbm-pulse").textContent = brief.hbm_pulse || "—";
  $("derivatives").textContent = brief.derivatives_signal || "—";

  // tables
  paintPeers(quotes.peers || {});
  paintMacro(quotes.macro || {});
  paintFilings(brief.key_filings);
  paintNews(brief.news_pulse);
  paintWatch(brief.watch_for_next_3h);

  // status bar
  const ms = marketState();
  $("market-state").textContent = ms.label;
  $("market-state").className = "status-item " + ms.cls;
  $("last-refresh").textContent = fmtTimeAgo(payload.generated_at);
  const next = new Date(new Date(payload.generated_at).getTime() + 3 * 3600 * 1000);
  $("next-refresh").textContent = fmtTimeUntil(next.toISOString());

  // footer
  $("generation-info").textContent = `payload: ${(JSON.stringify(payload).length / 1024).toFixed(1)}kb`;
}

load();
// Auto-refresh display every 60s (page-level, doesn't re-fetch unless data changed)
setInterval(load, 60_000);
