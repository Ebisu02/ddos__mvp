"""
HTML templates (dashboard mockup aligned with report figure 2.3).

No external CSS/JS dependencies: pure HTML + CSS + vanilla JS (Canvas/SVG).
"""
from __future__ import annotations


def render_dashboard(metrics_url: str, incidents_url: str, analysis_url: str, top_sources_url: str) -> str:
    return f"""<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Панель мониторинга DDoS</title>
  <style>
    :root {{
      --bg: #f3f4f6;
      --card: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --border: #e5e7eb;
      --shadow: 0 6px 18px rgba(0,0,0,.06);
      --radius: 14px;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    .wrap {{ max-width: 1160px; margin: 22px auto 40px; padding: 0 18px; }}
    .topbar {{
      display:flex; align-items:center; justify-content:space-between;
      margin-bottom: 14px;
    }}
    .title {{
      font-size: 18px; font-weight: 700;
      display:flex; gap:10px; align-items:center;
    }}
    .badge {{
      font-size: 12px; color: var(--muted);
      border:1px solid var(--border);
      background:#fff;
      padding: 4px 10px; border-radius: 999px;
    }}

    .kpis {{
      display:grid; grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      margin: 14px 0 16px;
    }}
    .kpi {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 12px 12px 10px;
      min-height: 72px;
    }}
    .kpi .label {{ font-size: 12px; color: var(--muted); display:flex; justify-content:space-between; }}
    .kpi .value {{ font-size: 18px; font-weight: 800; margin-top: 6px; }}
    .kpi .delta {{ font-size: 12px; color: var(--muted); margin-top: 2px; }}

    .grid2 {{
      display:grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 12px;
      margin-bottom: 12px;
    }}
    .grid2b {{
      display:grid;
      grid-template-columns: 1.6fr 1fr;
      gap: 12px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 12px;
    }}
    .cardhead {{
      display:flex; justify-content:space-between; align-items:center;
      margin-bottom: 10px;
    }}
    .cardtitle {{ font-size: 13px; font-weight: 800; color: #111827; }}
    .linkbtn {{
      font-size: 12px; color: #111827; background:#fff;
      border:1px solid var(--border); border-radius: 10px;
      padding: 6px 10px; cursor: default;
    }}

    /* charts */
    .chartwrap {{ width: 100%; height: 220px; }}
    canvas {{ width:100%; height:220px; border-radius: 10px; background:#fff; }}
    .legend {{
      margin-top: 6px; font-size: 12px; color: var(--muted);
      display:flex; gap: 14px; align-items:center;
    }}
    .dot {{ width: 10px; height: 10px; border-radius: 999px; display:inline-block; border: 2px solid #111; }}
    .dot.out {{ border-style: dashed; }}

    /* table */
    table {{ width:100%; border-collapse: collapse; }}
    th, td {{ padding: 8px 8px; font-size: 12px; text-align:left; }}
    thead th {{ color: var(--muted); font-weight: 700; border-bottom:1px solid var(--border); }}
    tbody td {{ border-bottom: 1px solid #f0f1f3; }}
    .pill {{
      display:inline-flex; align-items:center; gap:6px;
      padding: 3px 10px; border-radius: 999px;
      border:1px solid var(--border);
      background:#fff; color:#111827; font-size: 12px;
    }}
    .sev-high {{ font-weight:800; }}
    .sev-med {{ font-weight:700; }}
    .sev-low {{ color: var(--muted); }}

    /* right bar list */
    .bars {{ display:flex; flex-direction:column; gap: 10px; }}
    .barrow {{ display:grid; grid-template-columns: 1fr; gap: 6px; }}
    .barrowtop {{ display:flex; justify-content:space-between; align-items:center; }}
    .barrow .ip {{ font-size: 12px; color:#111827; }}
    .bar {{
      height: 8px; border-radius: 999px;
      background: #eef0f3; border:1px solid #e6e7ea; overflow:hidden;
    }}
    .bar > span {{
      display:block; height:100%;
      background:#111827; opacity:.72;
      width: 20%;
    }}
    .barrow .count {{ font-size: 12px; color: var(--muted); }}

    /* donuts */
    .donuts {{ display:flex; gap: 14px; align-items:flex-start; justify-content:space-between; }}
    .donut {{
      display:flex; flex-direction:column; align-items:center; gap: 6px;
      width: 33%;
    }}
    .donut svg {{ width: 86px; height: 86px; }}
    .donut .num {{ font-size: 16px; font-weight: 800; }}
    .donut .cap {{ font-size: 12px; color: var(--muted); text-align:center; }}
    .footnote {{ margin-top: 10px; color: var(--muted); font-size: 11px; }}

    @media (max-width: 980px) {{
      .kpis {{ grid-template-columns: 1fr 1fr; }}
      .grid2, .grid2b {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="topbar">
      <div class="title">Панель мониторинга <span class="badge">MVP • синтетические данные</span></div>
      <div class="badge" id="now_badge">—</div>
    </div>

    <div class="kpis">
      <div class="kpi">
        <div class="label"><span>Трафик</span><span id="kpi_tr_delta">—</span></div>
        <div class="value" id="kpi_tr">—</div>
        <div class="delta">Входящий (bps)</div>
      </div>
      <div class="kpi">
        <div class="label"><span>Активные сессии</span><span id="kpi_sess_delta">—</span></div>
        <div class="value" id="kpi_sess">—</div>
        <div class="delta">Оценка unique_src</div>
      </div>
      <div class="kpi">
        <div class="label"><span>Обнаружено угроз</span><span id="kpi_thr_delta">—</span></div>
        <div class="value" id="kpi_thr">—</div>
        <div class="delta">Аномалии (окно)</div>
      </div>
      <div class="kpi">
        <div class="label"><span>Средний риск</span><span id="kpi_risk_delta">—</span></div>
        <div class="value" id="kpi_risk">—</div>
        <div class="delta">Сводный score</div>
      </div>
      <div class="kpi">
        <div class="label"><span>Критические инциденты</span><span id="kpi_inc_delta">—</span></div>
        <div class="value" id="kpi_inc">—</div>
        <div class="delta">severity=high</div>
      </div>
    </div>

    <div class="grid2">
      <div class="card">
        <div class="cardhead">
          <div class="cardtitle">История трафика</div>
          <div class="linkbtn">Все инциденты</div>
        </div>
        <div class="chartwrap">
          <canvas id="traffic_canvas" width="900" height="220"></canvas>
          <div class="legend">
            <span><span class="dot"></span> Входящий трафик</span>
            <span><span class="dot out"></span> Исходящий трафик</span>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="cardhead">
          <div class="cardtitle">Топ источников атак</div>
          <div class="linkbtn">Подробнее</div>
        </div>
        <div class="bars" id="top_sources">—</div>
      </div>
    </div>

    <div class="grid2b">
      <div class="card">
        <div class="cardhead">
          <div class="cardtitle">Текущие инциденты</div>
          <div class="linkbtn">Все инциденты</div>
        </div>
        <table>
          <thead>
            <tr><th>ID</th><th>Время</th><th>Тип</th><th>Статус</th><th>Уровень</th></tr>
          </thead>
          <tbody id="inc_tbl"></tbody>
        </table>
      </div>

      <div class="card">
        <div class="cardhead">
          <div class="cardtitle">Индикаторы угроз</div>
          <div class="linkbtn">—</div>
        </div>
        <div class="donuts">
          <div class="donut">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="38" fill="none" stroke="#eef0f3" stroke-width="10"/>
              <circle id="d_high" cx="50" cy="50" r="38" fill="none" stroke="#111827" stroke-width="10"
                stroke-linecap="round" transform="rotate(-90 50 50)" stroke-dasharray="0 999"/>
            </svg>
            <div class="num" id="n_high">0</div>
            <div class="cap">Высокий<br/>уровень</div>
          </div>
          <div class="donut">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="38" fill="none" stroke="#eef0f3" stroke-width="10"/>
              <circle id="d_med" cx="50" cy="50" r="38" fill="none" stroke="#111827" stroke-width="10"
                stroke-linecap="round" transform="rotate(-90 50 50)" stroke-dasharray="0 999" opacity=".72"/>
            </svg>
            <div class="num" id="n_med">0</div>
            <div class="cap">Средний<br/>уровень</div>
          </div>
          <div class="donut">
            <svg viewBox="0 0 100 100">
              <circle cx="50" cy="50" r="38" fill="none" stroke="#eef0f3" stroke-width="10"/>
              <circle id="d_low" cx="50" cy="50" r="38" fill="none" stroke="#111827" stroke-width="10"
                stroke-linecap="round" transform="rotate(-90 50 50)" stroke-dasharray="0 999" opacity=".45"/>
            </svg>
            <div class="num" id="n_low">0</div>
            <div class="cap">Низкий<br/>уровень</div>
          </div>
        </div>
        <div class="footnote">Индикаторы формируются по severity инцидентов (последние 50 записей).</div>
      </div>
    </div>
  </div>

<script>
const METRICS_URL = "{metrics_url}";
const INCIDENTS_URL = "{incidents_url}";
const ANALYSIS_URL = "{analysis_url}";
const TOP_SOURCES_URL = "{top_sources_url}";

function fmtBps(bps) {{
  if (bps >= 1e9) return (bps/1e9).toFixed(2) + " Гбит/с";
  if (bps >= 1e6) return (bps/1e6).toFixed(2) + " Мбит/с";
  return bps + " бит/с";
}}

function pctDelta(cur, prev) {{
  if (!prev || prev === 0) return "—";
  const d = ((cur - prev) / prev) * 100;
  const s = (d >= 0 ? "+" : "") + d.toFixed(0) + "%";
  return s;
}}

function setDonut(el, value, max) {{
  const r = 38;
  const c = 2 * Math.PI * r;
  const p = (max <= 0) ? 0 : Math.max(0, Math.min(1, value / max));
  const dash = (p * c).toFixed(2) + " " + (c - p * c).toFixed(2);
  el.setAttribute("stroke-dasharray", dash);
}}

function drawTraffic(canvas, incoming, outgoing) {{
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0,0,w,h);

  // margins
  const m = {{l:40, r:12, t:10, b:26}};
  const iw = w - m.l - m.r;
  const ih = h - m.t - m.b;

  const maxV = Math.max(...incoming, ...outgoing, 1);
  const minV = 0;

  // grid
  ctx.strokeStyle = "#eef0f3";
  ctx.lineWidth = 1;
  for (let i=0;i<=4;i++) {{
    const y = m.t + (ih*i/4);
    ctx.beginPath(); ctx.moveTo(m.l, y); ctx.lineTo(w-m.r, y); ctx.stroke();
  }}

  // axis labels (left)
  ctx.fillStyle = "#6b7280";
  ctx.font = "11px Segoe UI, Arial";
  for (let i=0;i<=4;i++) {{
    const v = maxV * (1 - i/4);
    const y = m.t + (ih*i/4);
    const label = (v).toFixed(0);
    ctx.fillText(label, 8, y+4);
  }}
  ctx.fillText("Мбит/с", 8, h-8);

  function plot(series, dashed) {{
    ctx.save();
    ctx.strokeStyle = "#111827";
    ctx.lineWidth = 2;
    if (dashed) ctx.setLineDash([6,4]);
    ctx.beginPath();
    series.forEach((v, idx) => {{
      const x = m.l + (iw * idx / Math.max(1, series.length-1));
      const y = m.t + ih - (ih * (v - minV) / (maxV - minV));
      if (idx===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
    }});
    ctx.stroke();
    ctx.restore();
  }}

  plot(incoming, false);
  plot(outgoing, true);
}}

function pseudoIp(seedStr) {{
  // deterministic pseudo-ip from string
  let h = 2166136261;
  for (let i=0;i<seedStr.length;i++) {{
    h ^= seedStr.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }}
  const a = 80 + (h & 63);
  const b = 10 + ((h >> 8) & 243);
  const c = 10 + ((h >> 16) & 243);
  const d = 10 + ((h >> 24) & 243);
  return `${{a}}.${{b}}.${{c}}.${{d}}`;
}}

function renderTopSources(container, incidents) {{
  const m = new Map();
  incidents.slice(0, 12).forEach((inc) => {{
    const ip = pseudoIp(String(inc.id) + inc.kind + inc.severity);
    const base = inc.severity === "high" ? 280 : (inc.severity === "medium" ? 180 : 120);
    const cnt = base + (inc.id % 50);
    m.set(ip, (m.get(ip)||0) + cnt);
  }});

  let arr = Array.from(m.entries());
  if (arr.length < 5) {{
    const seeds = ["185.XXX.242.21","95.XXX.85.133","174.XXX.55.18","213.XXX.132.27","162.XXX.91.240"];
    arr = seeds.map((s, idx) => [s, 320 - idx*40]);
  }}
  arr.sort((a,b)=>b[1]-a[1]);
  arr = arr.slice(0,5);

  const max = arr[0][1] || 1;
  container.innerHTML = "";
  arr.forEach(([ip, cnt]) => {{
    const row = document.createElement("div");
    row.className = "barrow";
    row.innerHTML = `
      <div class="barrowtop">
        <div class="ip">${{ip}}</div>
        <div class="count">${{cnt}}</div>
      </div>
      <div class="bar"><span style="width:${{Math.round((cnt/max)*100)}}%"></span></div>
    `;
    container.appendChild(row);
  }});
}}

function renderIncidents(tbody, incidents) {{
  tbody.innerHTML = "";
  incidents.slice(0, 8).forEach((inc) => {{
    const sevText = inc.severity === "high" ? "Критич." : (inc.severity === "medium" ? "Средн." : "Низкий");
    const sevCls = inc.severity === "high" ? "sev-high" : (inc.severity === "medium" ? "sev-med" : "sev-low");
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>#${{inc.id}}</td>
      <td>${{new Date(inc.start_ts*1000).toLocaleString("ru-RU")}}</td>
      <td>${{inc.kind}}</td>
      <td>Открыт</td>
      <td class="${{sevCls}}">${{sevText}}</td>
    `;
    tbody.appendChild(tr);
  }});
}}

async function load() {{
  const now = new Date();
  document.getElementById("now_badge").textContent = now.toLocaleString("ru-RU");

  const metrics = await (await fetch(METRICS_URL)).json();
  const incidents = await (await fetch(INCIDENTS_URL)).json();
  const analysis = await (await fetch(ANALYSIS_URL)).json();
  const topSources = await (await fetch(TOP_SOURCES_URL)).json();

  const mAsc = metrics.slice().reverse();
  const last = mAsc[mAsc.length-1];
  const prev = mAsc[mAsc.length-2];

  const bps = last ? last.bps : 0;
  const bpsPrev = prev ? prev.bps : 0;
  document.getElementById("kpi_tr").textContent = fmtBps(bps);
  document.getElementById("kpi_tr_delta").textContent = pctDelta(bps, bpsPrev);

  const sess = last ? last.unique_src : 0;
  const sessPrev = prev ? prev.unique_src : 0;
  document.getElementById("kpi_sess").textContent = sess.toLocaleString("ru-RU");
  document.getElementById("kpi_sess_delta").textContent = pctDelta(sess, sessPrev);

  const aAsc = analysis.slice().reverse();
  const window = aAsc.slice(-60);
  const threats = window.filter(r => r.is_anomaly).length;
  const threatsPrev = aAsc.slice(-120, -60).filter(r => r.is_anomaly).length || 0;
  document.getElementById("kpi_thr").textContent = threats.toLocaleString("ru-RU");
  document.getElementById("kpi_thr_delta").textContent = pctDelta(threats, threatsPrev);

  const avgScore = window.length ? (window.reduce((s,r)=>s+r.score,0)/window.length) : 0;
  const prevScoreWindow = aAsc.slice(-120, -60);
  const prevAvgScore = prevScoreWindow.length ? (prevScoreWindow.reduce((s,r)=>s+r.score,0)/prevScoreWindow.length) : 0;
  document.getElementById("kpi_risk").textContent = avgScore.toFixed(2);
  document.getElementById("kpi_risk_delta").textContent = pctDelta(avgScore, prevAvgScore);

  const highCnt = incidents.filter(i => i.severity === "high").length;
  const medCnt  = incidents.filter(i => i.severity === "medium").length;
  const lowCnt  = incidents.filter(i => i.severity === "low").length;
  document.getElementById("kpi_inc").textContent = highCnt.toLocaleString("ru-RU");
  document.getElementById("kpi_inc_delta").textContent = "—";

  document.getElementById("n_high").textContent = highCnt;
  document.getElementById("n_med").textContent  = medCnt;
  document.getElementById("n_low").textContent  = lowCnt;
  const maxDon = Math.max(highCnt, medCnt, lowCnt, 1);
  setDonut(document.getElementById("d_high"), highCnt, maxDon);
  setDonut(document.getElementById("d_med"), medCnt, maxDon);
  setDonut(document.getElementById("d_low"), lowCnt, maxDon);

  const incoming = mAsc.map(x => x.bps/1e6); // Мбит/с
  const outgoing = mAsc.map(x => (x.bps*0.65 + x.rps*8000)/1e6);
  drawTraffic(document.getElementById("traffic_canvas"), incoming, outgoing);

  renderTopSources(document.getElementById("top_sources"), topSources);
  renderIncidents(document.getElementById("inc_tbl"), incidents);
}}

load();
setInterval(load, 2000);
</script>
</body>
</html>"""
