#!/usr/bin/env python3
"""Generate the self-contained HTML explorer for Asian → MLB pitcher analysis."""
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent

def main():
    with open(OUT / "analysis_data.json") as f:
        data = json.load(f)

    data_json = json.dumps(data, separators=(",", ":"))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Asian League → MLB Pitcher Transition Analysis</title>
<style>
:root {{ --ink:#1c1c1c; --muted:#5a5f6a; --line:#d0d4db; --bg:#f4f5f7; --card:#fff;
  --npb:#c62828; --kbo:#1565c0; --cpbl:#2e7d32; --all:#37474f;
  --pass:#2d6a4f; --cut:#9a3412; --navy:#3d5a80; }}
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{ font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  background:radial-gradient(ellipse 80% 50% at 8% -10%,#dbe4f0,transparent 55%),var(--bg);
  color:var(--ink); line-height:1.45; }}
.wrap {{ max-width:1260px; margin:0 auto; padding:28px 20px 64px; }}
h1 {{ font-family:"IBM Plex Serif",Georgia,serif; font-size:clamp(24px,3.5vw,32px); letter-spacing:-.02em; }}
.sub {{ color:var(--muted); font-size:14px; margin-top:8px; max-width:900px; }}
.tabs {{ display:flex; gap:0; border-bottom:2px solid var(--ink); margin:22px 0 18px; flex-wrap:wrap; }}
.tab {{ font:600 13px inherit; padding:10px 14px; border:none; background:transparent; cursor:pointer;
  color:#666; border-bottom:3px solid transparent; margin-bottom:-2px; white-space:nowrap; }}
.tab.active {{ color:var(--ink); border-bottom-color:var(--navy); }}
.panel {{ display:none; }} .panel.active {{ display:block; }}
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:10px; margin:12px 0 16px; }}
.kpi {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 14px; }}
.kpi .v {{ font-size:20px; font-weight:700; color:var(--navy); }}
.kpi .l {{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin-top:2px; }}
table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
th,td {{ padding:7px 10px; text-align:left; border-bottom:1px solid #eceff3; }}
th {{ font-size:10px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); background:#fafbfc; position:sticky; top:0; }}
tr:hover td {{ background:#f0f4fa; }}
.rnum {{ font-variant-numeric:tabular-nums; font-weight:700; }}
.pill {{ display:inline-block; padding:2px 8px; border-radius:999px; font-size:10px; font-weight:700; }}
.pill.y {{ background:#d8f3e4; color:var(--pass); }}
.pill.n {{ background:#f3e8e2; color:var(--cut); }}
.pill.g {{ background:#e8eef6; color:var(--navy); }}
.note {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:14px; font-size:13px; margin-bottom:14px; color:#333; }}
.note strong {{ color:var(--ink); }}
.section {{ background:var(--card); border:1px solid var(--line); border-radius:10px; margin-bottom:16px; overflow:hidden; }}
.section-h {{ padding:12px 16px; background:var(--ink); color:#fff; }}
.section-h h2 {{ font-size:13px; letter-spacing:.06em; text-transform:uppercase; }}
.section-body {{ padding:16px; }}
.section-body h3 {{ font-size:14px; margin:12px 0 6px; color:var(--navy); }}
.section-body h3:first-child {{ margin-top:0; }}
.section-body p {{ font-size:13px; color:#444; margin-bottom:8px; line-height:1.55; }}
.cols {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }}
@media(max-width:800px) {{ .cols {{ grid-template-columns:1fr; }} }}
.badge {{ display:inline-block; padding:3px 10px; border-radius:4px; font-size:11px; font-weight:700; margin-right:6px; }}
.badge.npb {{ background:#ffcdd2; color:var(--npb); }}
.badge.kbo {{ background:#bbdefb; color:var(--kbo); }}
.badge.cpbl {{ background:#c8e6c9; color:var(--cpbl); }}
.cluster-box {{ background:#f8f9fb; border:1px solid var(--line); border-radius:8px; padding:12px; margin:6px 0; }}
.cluster-box .cid {{ font-weight:700; color:var(--navy); font-size:12px; }}
.cluster-box .metrics {{ font-size:12px; color:#555; margin-top:4px; }}
.arsenal-grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:8px; }}
.pitch-card {{ background:#f8f9fb; border:1px solid var(--line); border-radius:6px; padding:10px 12px; }}
.pitch-card .pname {{ font-weight:700; font-size:13px; }}
.pitch-card .pvelo {{ color:var(--muted); font-size:11px; }}
.pitch-card .pgrade {{ display:inline-block; background:var(--navy); color:#fff; font-size:10px; padding:1px 6px; border-radius:3px; margin-left:6px; }}
.pitch-card .pnotes {{ font-size:11.5px; color:#555; margin-top:4px; }}
.source-list {{ font-size:11px; color:var(--muted); padding:0; list-style:none; }}
.source-list li {{ padding:2px 0; }}
.source-list li::before {{ content:"[" attr(data-n) "] "; font-weight:700; }}
footer {{ margin-top:24px; font-size:11px; color:#888; text-align:center; }}
.bar-wrap {{ display:flex; align-items:center; gap:8px; }}
.bar-bg {{ flex:1; height:6px; background:#e8eaee; border-radius:3px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:3px; }}
.origin-tag {{ display:inline-block; font-size:9px; font-weight:700; padding:1px 5px; border-radius:3px; margin-left:4px; }}
.origin-tag.us {{ background:#e3f2fd; color:#1565c0; }}
.win-tabs {{ display:flex; gap:4px; margin:8px 0 12px; flex-wrap:wrap; }}
.win-tab {{ font:600 11px inherit; padding:5px 10px; border:1px solid var(--line); border-radius:4px;
  background:#fff; cursor:pointer; color:var(--muted); }}
.win-tab.active {{ background:var(--navy); color:#fff; border-color:var(--navy); }}
.win-panel {{ display:none; }} .win-panel.active {{ display:block; }}
</style>
</head>
<body>
<div class="wrap">
<h1>Asian League \u2192 MLB Pitcher Transition Analysis</h1>
<p class="sub">Multi-window stability, redundancy, and significance analysis of {data['meta']['n_pitchers']} pitchers who crossed between Asian professional leagues (CPBL / KBO / NPB) and Major League Baseball. Includes {data['meta'].get('n_asian_born', '')} Asian-born and {data['meta'].get('n_crossover', '')} American crossover pitchers. Data from MLB Stats API, Baseball-Reference Register, and bWAR.</p>

<nav class="tabs">
  <button class="tab active" data-panel="home">Home \u2014 Stability &amp; Redundancy</button>
  <button class="tab" data-panel="npb">NPB (Japan)</button>
  <button class="tab" data-panel="kbo">KBO (Korea)</button>
  <button class="tab" data-panel="cpbl">CPBL (Taiwan)</button>
  <button class="tab" data-panel="itoh">Hiromi Itoh Assessment</button>
</nav>

<!-- HOME TAB -->
<section class="panel active" id="panel-home">
  <div class="kpis" id="homeKpis"></div>
  <div class="note" id="homeNote"></div>

  <div class="section">
    <div class="section-h"><h2>Metric Evaluation List \u2014 Stable Metrics for Cross-League Scouting</h2></div>
    <div class="section-body" id="metricList"></div>
  </div>

  <div class="section">
    <div class="section-h"><h2>Stability \u2014 All Leagues (Multi-Window)</h2></div>
    <div class="section-body" id="homeStab"></div>
  </div>

  <div class="cols">
    <div class="section">
      <div class="section-h"><h2>Redundancy Clusters (Asian Metrics)</h2></div>
      <div class="section-body" id="homeClusters"></div>
    </div>
    <div class="section">
      <div class="section-h"><h2>Redundant Pairs (|r| \u2265 0.75)</h2></div>
      <div class="section-body" id="homePairs"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-h"><h2>Significance \u2014 What Predicts MLB Success? (ERA+ Focus)</h2></div>
    <div class="section-body" id="homeSig"></div>
  </div>

  <div class="section">
    <div class="section-h"><h2>All Pitchers \u2014 Complete Dataset</h2></div>
    <div class="section-body" style="overflow-x:auto" id="allTable"></div>
  </div>
</section>

<!-- NPB TAB -->
<section class="panel" id="panel-npb">
  <div class="kpis" id="npbKpis"></div>
  <div class="section">
    <div class="section-h" style="background:var(--npb)"><h2>Stability \u2014 NPB \u2192 MLB (Multi-Window)</h2></div>
    <div class="section-body" id="npbStab"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--npb)"><h2>Significance \u2014 NPB Predictors</h2></div>
    <div class="section-body" id="npbSig"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--npb)"><h2>NPB Pitchers</h2></div>
    <div class="section-body" style="overflow-x:auto" id="npbTable"></div>
  </div>
</section>

<!-- KBO TAB -->
<section class="panel" id="panel-kbo">
  <div class="kpis" id="kboKpis"></div>
  <div class="section">
    <div class="section-h" style="background:var(--kbo)"><h2>Stability \u2014 KBO \u2192 MLB (Multi-Window)</h2></div>
    <div class="section-body" id="kboStab"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--kbo)"><h2>Significance \u2014 KBO Predictors</h2></div>
    <div class="section-body" id="kboSig"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--kbo)"><h2>KBO Pitchers</h2></div>
    <div class="section-body" style="overflow-x:auto" id="kboTable"></div>
  </div>
</section>

<!-- CPBL TAB -->
<section class="panel" id="panel-cpbl">
  <div class="kpis" id="cpblKpis"></div>
  <div class="section">
    <div class="section-h" style="background:var(--cpbl)"><h2>Stability \u2014 CPBL \u2192 MLB (Multi-Window)</h2></div>
    <div class="section-body" id="cpblStab"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--cpbl)"><h2>Significance \u2014 CPBL Predictors</h2></div>
    <div class="section-body" id="cpblSig"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--cpbl)"><h2>CPBL Pitchers</h2></div>
    <div class="section-body" style="overflow-x:auto" id="cpblTable"></div>
  </div>
</section>

<!-- ITOH TAB -->
<section class="panel" id="panel-itoh">
  <div class="kpis" id="itohKpis"></div>
  <div class="section">
    <div class="section-h" style="background:#37474f"><h2>Pitch Arsenal</h2></div>
    <div class="section-body" id="itohArsenal"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:#37474f"><h2>A. Likely MLB Role &amp; Performance Projection</h2></div>
    <div class="section-body" id="itohA"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:#37474f"><h2>B. Potential Adjustments for ML Success</h2></div>
    <div class="section-body" id="itohB"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:#37474f"><h2>C. Three Priority Information Requests</h2></div>
    <div class="section-body" id="itohC"></div>
  </div>
  <div class="section">
    <div class="section-h" style="background:#37474f"><h2>Sources</h2></div>
    <div class="section-body" id="itohSources"></div>
  </div>
</section>

<footer>Asian League \u2192 MLB Pitcher Transition Analysis \u00B7 Data: MLB Stats API, Baseball-Reference Register, bWAR \u00B7 Cross-league factor: Cho (2026) \u00B7 {data['meta']['n_with_both']} pitchers with both Asian &amp; MLB data</footer>
</div>

<script>
const D = {data_json};
const ML = D.meta.metric_labels;
const WINS = D.windows;

document.querySelectorAll('.tab').forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
  }};
}});

function fmt(v, d) {{ return v != null && !isNaN(v) ? Number(v).toFixed(d) : '\u2014'; }}
function fmtR(r) {{ return `<span class="rnum">${{Number(r).toFixed(3)}}</span>`; }}
function stabPill(s) {{ return s ? '<span class="pill y">STABLE</span>' : '<span class="pill n">below</span>'; }}
function sigPill(s) {{ return s ? '<span class="pill y">SIG</span>' : '<span class="pill n">n.s.</span>'; }}
function leagueBadge(l) {{ return `<span class="badge ${{l.toLowerCase()}}">${{l}}</span>`; }}
function originTag(o) {{
  if (o === 'US') return '<span class="origin-tag us">US</span>';
  return '';
}}
function stabBar(r) {{
  const abs_r = Math.abs(r);
  const pct = Math.min(abs_r * 100, 100);
  const color = abs_r >= 0.7 ? 'var(--pass)' : abs_r >= 0.4 ? 'var(--navy)' : '#ccc';
  return `<div class="bar-wrap"><div class="bar-bg"><div class="bar-fill" style="width:${{pct}}%;background:${{color}}"></div></div></div>`;
}}

function renderWindowedStab(containerId, leagueKey) {{
  const leagueData = D.stability[leagueKey];
  if (!leagueData) {{ document.getElementById(containerId).innerHTML = '<p>Insufficient data for this league.</p>'; return; }}

  const uid = containerId;
  let html = '<div class="win-tabs">';
  WINS.forEach((w, i) => {{
    const active = i === 0 ? ' active' : '';
    html += `<button class="win-tab${{active}}" data-wg="${{uid}}" data-wt="${{w.tag}}">${{w.label}}</button>`;
  }});
  html += '</div>';

  WINS.forEach((w, i) => {{
    const winData = leagueData[w.tag];
    const active = i === 0 ? ' active' : '';
    html += `<div class="win-panel${{active}}" data-wg="${{uid}}" data-wp="${{w.tag}}">`;
    if (!winData || !winData.metrics) {{
      html += '<p>Insufficient data for this window.</p>';
    }} else {{
      html += '<table><thead><tr><th>Metric</th><th>r (Pearson)</th><th>p-value</th><th>N</th><th>Status</th><th></th></tr></thead><tbody>';
      for (const [m, v] of Object.entries(winData.metrics)) {{
        const label = ML[m] || m;
        html += `<tr><td>${{label}}</td><td>${{fmtR(v.r)}}</td><td>${{v.p.toFixed(4)}}</td><td>${{v.n}}</td><td>${{stabPill(v.stable)}}</td><td style="width:120px">${{stabBar(v.r)}}</td></tr>`;
      }}
      html += '</tbody></table>';
      html += '<p style="font-size:11px;color:var(--muted);margin-top:8px">Stable = |r| \u2265 0.40 and p &lt; 0.10. Pearson r between Asian-league stat and MLB stat for the same time window.</p>';
    }}
    html += '</div>';
  }});

  document.getElementById(containerId).innerHTML = html;

  document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(btn => {{
    btn.onclick = () => {{
      document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(b => b.classList.remove('active'));
      document.querySelectorAll(`.win-panel[data-wg="${{uid}}"]`).forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.querySelector(`.win-panel[data-wg="${{uid}}"][data-wp="${{btn.dataset.wt}}"]`).classList.add('active');
    }};
  }});
}}

function renderWindowedSig(containerId, leagueKey) {{
  const leagueData = D.significance[leagueKey];
  if (!leagueData) {{ document.getElementById(containerId).innerHTML = '<p>Insufficient data.</p>'; return; }}

  const uid = containerId;
  let html = '<div class="win-tabs">';
  WINS.forEach((w, i) => {{
    const active = i === 0 ? ' active' : '';
    html += `<button class="win-tab${{active}}" data-wg="${{uid}}" data-wt="${{w.tag}}">${{w.label}}</button>`;
  }});
  html += '</div>';

  WINS.forEach((w, i) => {{
    const winData = leagueData[w.tag];
    const active = i === 0 ? ' active' : '';
    html += `<div class="win-panel${{active}}" data-wg="${{uid}}" data-wp="${{w.tag}}">`;
    if (!winData || !winData.outcomes) {{
      html += '<p>Insufficient data for this window.</p>';
    }} else {{
      for (const [outKey, outData] of Object.entries(winData.outcomes)) {{
        html += `<h3>Predicting ${{outData.label}}</h3>`;
        html += '<table><thead><tr><th>Asian Metric</th><th>r</th><th>p</th><th>N</th><th></th></tr></thead><tbody>';
        for (const d of outData.drivers.slice(0, 7)) {{
          html += `<tr><td>${{d.label}}</td><td>${{fmtR(d.r)}}</td><td>${{d.p.toFixed(4)}}</td><td>${{d.n}}</td><td>${{sigPill(d.significant)}}</td></tr>`;
        }}
        html += '</tbody></table>';
      }}
    }}
    html += '</div>';
  }});

  document.getElementById(containerId).innerHTML = html;

  document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(btn => {{
    btn.onclick = () => {{
      document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(b => b.classList.remove('active'));
      document.querySelectorAll(`.win-panel[data-wg="${{uid}}"]`).forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.querySelector(`.win-panel[data-wg="${{uid}}"][data-wp="${{btn.dataset.wt}}"]`).classList.add('active');
    }};
  }});
}}

function renderPitcherTable(containerId, league) {{
  const pitchers = league === 'ALL' ? D.pitchers : D.pitchers.filter(p => p.league === league);
  let html = '<table><thead><tr><th>Name</th><th>League</th><th>Pos</th><th>Year</th>';
  html += '<th>A-ERA</th><th>A-IP</th><th>A-K/9</th><th>A-BB/9</th><th>A-WHIP</th><th>A-K/BB</th>';
  html += '<th>M-ERA</th><th>M-IP</th><th>M-K/9</th><th>M-BB/9</th><th>M-WHIP</th><th>M-K/BB</th>';
  html += '<th>ERA+</th><th>WAR</th></tr></thead><tbody>';
  const sorted = [...pitchers].sort((a, b) => (b.m_war||0) - (a.m_war||0));
  for (const p of sorted) {{
    const ep = p.m_era_plus;
    const eraClass = ep != null ? (ep >= 110 ? 'color:var(--pass)' : ep < 90 ? 'color:var(--cut)' : '') : '';
    const otag = p.origin === 'US' ? originTag('US') : '';
    html += `<tr>
      <td><strong>${{p.name}}</strong>${{otag}}</td><td>${{leagueBadge(p.league)}}</td><td>${{p.pos||''}}</td>
      <td>${{p.transition_year||'\u2014'}}</td>
      <td class="rnum">${{fmt(p.a_era,2)}}</td><td class="rnum">${{fmt(p.a_ip,0)}}</td>
      <td class="rnum">${{fmt(p.a_k9,1)}}</td><td class="rnum">${{fmt(p.a_bb9,1)}}</td>
      <td class="rnum">${{fmt(p.a_whip,2)}}</td><td class="rnum">${{fmt(p.a_k_bb,2)}}</td>
      <td class="rnum">${{fmt(p.m_era,2)}}</td><td class="rnum">${{fmt(p.m_ip,0)}}</td>
      <td class="rnum">${{fmt(p.m_k9,1)}}</td><td class="rnum">${{fmt(p.m_bb9,1)}}</td>
      <td class="rnum">${{fmt(p.m_whip,2)}}</td><td class="rnum">${{fmt(p.m_k_bb,2)}}</td>
      <td class="rnum" style="${{eraClass}}">${{fmt(ep,0)}}</td>
      <td class="rnum">${{fmt(p.m_war,1)}}</td>
    </tr>`;
  }}
  html += '</tbody></table>';
  document.getElementById(containerId).innerHTML = html;
}}

function renderLeagueKpis(containerId, league) {{
  const all = D.pitchers.filter(p => p.league === league);
  const withMlb = all.filter(p => p.m_war != null);
  const n = all.length;
  const nm = withMlb.length;
  const nCross = all.filter(p => p.origin === 'US').length;
  const avgWar = nm ? (withMlb.reduce((s, p) => s + (p.m_war||0), 0) / nm).toFixed(1) : '\u2014';
  const avgEra = nm ? (withMlb.reduce((s, p) => s + (p.m_era||0), 0) / nm).toFixed(2) : '\u2014';
  const avgEraPlus = nm ? Math.round(withMlb.reduce((s, p) => s + (p.m_era_plus||100), 0) / nm) : '\u2014';
  document.getElementById(containerId).innerHTML = `
    <div class="kpi"><div class="v">${{n}}</div><div class="l">Pitchers (${{nCross}} crossover)</div></div>
    <div class="kpi"><div class="v">${{nm}}</div><div class="l">With MLB Data</div></div>
    <div class="kpi"><div class="v">${{avgWar}}</div><div class="l">Avg Career WAR</div></div>
    <div class="kpi"><div class="v">${{avgEra}}</div><div class="l">Avg MLB ERA</div></div>
    <div class="kpi"><div class="v">${{avgEraPlus}}</div><div class="l">Avg ERA+</div></div>`;
}}

// HOME
document.getElementById('homeKpis').innerHTML = `
  <div class="kpi"><div class="v">${{D.meta.n_pitchers}}</div><div class="l">Total Pitchers</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_with_both}}</div><div class="l">With Both Asian + MLB Stats</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_asian_born || ''}}</div><div class="l">Asian-Born</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_crossover || ''}}</div><div class="l">American Crossover</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_npb}}</div><div class="l">NPB (Japan)</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_kbo}}</div><div class="l">KBO (Korea)</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_cpbl}}</div><div class="l">CPBL (Taiwan)</div></div>
  <div class="kpi"><div class="v">${{D.meta.translation_factor}}</div><div class="l">xFIP\u2212 Translation Factor</div></div>`;

document.getElementById('homeNote').innerHTML =
  '<strong>Methodology:</strong> Multi-window Pearson r correlations between Asian-league stats and MLB stats, ' +
  'tested across four time horizons: last 1yr Asia vs first 1yr MLB, trailing 2yr Asia vs first 2yr MLB, ' +
  'trailing 3yr Asia vs first 3yr MLB, and career-to-career. ' +
  'Stability = |r| \u2265 0.40, p &lt; 0.10. Redundancy = |r| \u2265 0.75 between Asian metrics (league-agnostic). ' +
  'Significance = Asian metric predicting MLB ERA+ (primary), WAR, or longevity. ' +
  '<br><br><strong>What does p &lt; 0.10 mean?</strong> The p-value is the probability that the observed correlation arose by random chance alone (under the null hypothesis of no relationship). ' +
  'p &lt; 0.10 means there is less than a 10% probability the correlation is a statistical fluke. Lower p-values = stronger evidence of a genuine cross-league relationship.' +
  '<br><br><strong>Data sources:</strong> MLB Stats API (statsapi.mlb.com), Baseball-Reference Register, bWAR (pybaseball). ' +
  'Cross-league translation factor from Cho (2026): NPB xFIP\u2212 worsens ~9.6% in MLB. ' +
  'Dataset includes Asian-born pitchers and American pitchers who pitched in Asian leagues before (returning to) MLB.';

// Metric Evaluation List (uses career window for primary recommendation)
(function() {{
  const stabAll = D.stability['ALL'] || {{}};
  const careerData = (stabAll['career'] || {{}}).metrics || {{}};

  let allMetrics = {{}};
  for (const [wtag, wdata] of Object.entries(stabAll)) {{
    if (!wdata || !wdata.metrics) continue;
    for (const [m, v] of Object.entries(wdata.metrics)) {{
      if (!allMetrics[m]) allMetrics[m] = {{}};
      allMetrics[m][wtag] = v;
    }}
  }}

  const stableCount = (m) => Object.values(allMetrics[m] || {{}}).filter(v => v.stable).length;
  const metrics = Object.keys(allMetrics).sort((a, b) => stableCount(b) - stableCount(a));
  const stable = metrics.filter(m => stableCount(m) >= 2);
  const unstable = metrics.filter(m => stableCount(m) < 2);

  let html = '<h3>Recommended for Cross-League Evaluation (Stable Across Multiple Windows)</h3>';
  html += '<p style="font-size:12px;color:#555;margin-bottom:10px">These metrics are stable (|r| \u2265 0.40, p &lt; 0.10) in at least 2 of 4 time windows. They transfer reliably from Asian leagues to MLB.</p>';
  html += '<table><thead><tr><th>Metric</th><th>1yr</th><th>2yr</th><th>3yr</th><th>Career</th><th>Windows Stable</th></tr></thead><tbody>';
  for (const m of stable) {{
    const label = ML[m] || m;
    const wins = allMetrics[m];
    const sc = stableCount(m);
    function winCell(wtag) {{
      const v = wins[wtag];
      if (!v) return '<td>\u2014</td>';
      return `<td>${{fmtR(v.r)}} ${{stabPill(v.stable)}}</td>`;
    }}
    html += `<tr><td><strong>${{label}}</strong></td>${{winCell('1y')}}${{winCell('2y')}}${{winCell('3y')}}${{winCell('career')}}<td><span class="pill g">${{sc}}/4</span></td></tr>`;
  }}
  html += '</tbody></table>';

  if (unstable.length) {{
    html += '<h3 style="margin-top:18px">Not Recommended (Unstable Metrics)</h3>';
    html += '<p style="font-size:12px;color:#555;margin-bottom:10px">These metrics are stable in fewer than 2 windows. Do not rely on them as primary scouting indicators.</p>';
    html += '<table><thead><tr><th>Metric</th><th>1yr</th><th>2yr</th><th>3yr</th><th>Career</th><th>Windows Stable</th></tr></thead><tbody>';
    for (const m of unstable) {{
      const label = ML[m] || m;
      const wins = allMetrics[m];
      const sc = stableCount(m);
      function winCell2(wtag) {{
        const v = wins[wtag];
        if (!v) return '<td>\u2014</td>';
        return `<td>${{fmtR(v.r)}} ${{stabPill(v.stable)}}</td>`;
      }}
      html += `<tr><td>${{label}}</td>${{winCell2('1y')}}${{winCell2('2y')}}${{winCell2('3y')}}${{winCell2('career')}}<td><span class="pill n">${{sc}}/4</span></td></tr>`;
    }}
    html += '</tbody></table>';
  }}
  document.getElementById('metricList').innerHTML = html;
}})();

renderWindowedStab('homeStab', 'ALL');

// Clusters (now using plain metric names, not Asian/MLB prefix)
let cHtml = '';
for (const c of D.redundancy.clusters) {{
  cHtml += `<div class="cluster-box"><div class="cid">Cluster ${{c.id}}</div><div class="metrics">${{c.labels.join(' \u00B7 ')}}</div></div>`;
}}
if (!cHtml) cHtml = '<p>No multi-metric clusters found at threshold.</p>';
document.getElementById('homeClusters').innerHTML = cHtml;

// Pairs (now using plain labels)
let pHtml = '<table><thead><tr><th>Metric A</th><th>Metric B</th><th>r</th></tr></thead><tbody>';
for (const p of D.redundancy.pairs.slice(0, 15)) {{
  pHtml += `<tr><td>${{p.a_label}}</td><td>${{p.b_label}}</td><td class="rnum">${{p.r.toFixed(3)}}</td></tr>`;
}}
pHtml += '</tbody></table>';
pHtml += '<p style="font-size:11px;color:var(--muted);margin-top:8px">Redundancy computed on Asian-league career metrics only. Since stable metrics transfer across leagues, redundancy is inherent to the metric itself (e.g., ERA and WHIP are redundant regardless of which league).</p>';
document.getElementById('homePairs').innerHTML = pHtml;

renderWindowedSig('homeSig', 'ALL');
renderPitcherTable('allTable', 'ALL');

// LEAGUE TABS
for (const lg of ['npb', 'kbo', 'cpbl']) {{
  const LG = lg.toUpperCase();
  renderLeagueKpis(lg + 'Kpis', LG);
  renderWindowedStab(lg + 'Stab', LG);
  renderWindowedSig(lg + 'Sig', LG);
  renderPitcherTable(lg + 'Table', LG);
}}

// ITOH TAB
const itoh = D.itoh;
const c = itoh.npb_career;
const b = itoh.best_season_2025;
document.getElementById('itohKpis').innerHTML = `
  <div class="kpi"><div class="v">${{itoh.name}}</div><div class="l">${{itoh.team}} \u00B7 Age ${{itoh.age}} \u00B7 ${{itoh.throws}} / ${{itoh.bats}} \u00B7 ${{itoh.height}}</div></div>
  <div class="kpi"><div class="v">${{c.era}} ERA</div><div class="l">NPB Career (${{c.seasons}} seasons, ${{c.record}})</div></div>
  <div class="kpi"><div class="v">${{c.k}} K / ${{c.bb}} BB</div><div class="l">${{c.ip}} IP \u00B7 ${{c.cg}} CG \u00B7 ${{c.sho}} SHO</div></div>
  <div class="kpi"><div class="v">${{b.era}} ERA</div><div class="l">2025 Best (${{b.record}}, ${{b.award}})</div></div>
  <div class="kpi"><div class="v">${{b.k}}:${{b.bb}} K:BB</div><div class="l">2025: ${{b.ip}} IP, ${{b.gb_pct}}% GB, ${{b.siera}} SIERA</div></div>`;

let aHtml = '<div class="arsenal-grid">';
for (const p of itoh.arsenal) {{
  aHtml += `<div class="pitch-card">
    <span class="pname">${{p.pitch}}</span>
    <span class="pvelo">${{p.velo}}</span>
    ${{p.grade !== 'N/A' ? `<span class="pgrade">${{p.grade}}</span>` : ''}}
    <div class="pnotes">${{p.notes}}</div>
  </div>`;
}}
aHtml += '</div>';
document.getElementById('itohArsenal').innerHTML = aHtml;

let saHtml = '';
for (const item of itoh.section_a.content) {{
  saHtml += `<h3>${{item.heading}}</h3><p>${{item.text}}</p>`;
}}
document.getElementById('itohA').innerHTML = saHtml;

let sbHtml = '';
for (const adj of itoh.section_b.adjustments) {{
  sbHtml += `<h3>${{adj.adjustment}}</h3><p>${{adj.reasoning}}</p>`;
}}
document.getElementById('itohB').innerHTML = sbHtml;

let scHtml = '';
for (const req of itoh.section_c.requests) {{
  scHtml += `<h3>Priority ${{req.priority}}: ${{req.info}}</h3><p>${{req.impact}}</p>`;
}}
scHtml += `<h3>Recommended Next Step</h3><p>${{itoh.section_c.next_step}}</p>`;
document.getElementById('itohC').innerHTML = scHtml;

let srcHtml = '<ol class="source-list">';
for (let i = 0; i < itoh.sources.length; i++) {{
  srcHtml += `<li data-n="${{i+1}}">${{itoh.sources[i]}}</li>`;
}}
srcHtml += '</ol>';
document.getElementById('itohSources').innerHTML = srcHtml;
</script>
</body>
</html>"""

    out_path = OUT.parent / "asian_pitcher_mlb_analysis.html"
    out_path.write_text(html)
    print(f"Wrote {out_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
