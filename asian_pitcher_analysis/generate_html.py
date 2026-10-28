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
.bar {{ height:6px; border-radius:3px; margin-top:3px; }}
.bar-wrap {{ display:flex; align-items:center; gap:8px; }}
.bar-bg {{ flex:1; height:6px; background:#e8eaee; border-radius:3px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:3px; }}
</style>
</head>
<body>
<div class="wrap">
<h1>Asian League → MLB Pitcher Transition Analysis</h1>
<p class="sub">Stability, redundancy, and significance analysis of CPBL / KBO / NPB pitchers who transitioned to Major League Baseball. Includes Hiromi Itoh scouting assessment.</p>

<nav class="tabs">
  <button class="tab active" data-panel="home">Home &amp; Rankings</button>
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
    <div class="section-h"><h2>Top 10 Overall Rankings — Composite Score</h2></div>
    <div class="section-body" id="rankTable"></div>
  </div>

  <div class="cols">
    <div class="section">
      <div class="section-h"><h2>Stability — All Leagues</h2></div>
      <div class="section-body" id="homeStab"></div>
    </div>
    <div class="section">
      <div class="section-h"><h2>Redundancy Clusters</h2></div>
      <div class="section-body" id="homeClusters"></div>
    </div>
  </div>

  <div class="section">
    <div class="section-h"><h2>Top Redundant Pairs (|r| ≥ 0.75)</h2></div>
    <div class="section-body" id="homePairs"></div>
  </div>

  <div class="section">
    <div class="section-h"><h2>Significance — What Predicts MLB Success?</h2></div>
    <div class="section-body" id="homeSig"></div>
  </div>
</section>

<!-- NPB TAB -->
<section class="panel" id="panel-npb">
  <div class="kpis" id="npbKpis"></div>
  <div class="cols">
    <div class="section">
      <div class="section-h" style="background:var(--npb)"><h2>Stability — NPB → MLB</h2></div>
      <div class="section-body" id="npbStab"></div>
    </div>
    <div class="section">
      <div class="section-h" style="background:var(--npb)"><h2>Significance — NPB Predictors</h2></div>
      <div class="section-body" id="npbSig"></div>
    </div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--npb)"><h2>NPB Pitchers — Complete Dataset</h2></div>
    <div class="section-body" style="overflow-x:auto" id="npbTable"></div>
  </div>
</section>

<!-- KBO TAB -->
<section class="panel" id="panel-kbo">
  <div class="kpis" id="kboKpis"></div>
  <div class="cols">
    <div class="section">
      <div class="section-h" style="background:var(--kbo)"><h2>Stability — KBO → MLB</h2></div>
      <div class="section-body" id="kboStab"></div>
    </div>
    <div class="section">
      <div class="section-h" style="background:var(--kbo)"><h2>Significance — KBO Predictors</h2></div>
      <div class="section-body" id="kboSig"></div>
    </div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--kbo)"><h2>KBO Pitchers — Complete Dataset</h2></div>
    <div class="section-body" style="overflow-x:auto" id="kboTable"></div>
  </div>
</section>

<!-- CPBL TAB -->
<section class="panel" id="panel-cpbl">
  <div class="kpis" id="cpblKpis"></div>
  <div class="cols">
    <div class="section">
      <div class="section-h" style="background:var(--cpbl)"><h2>Stability — CPBL → MLB</h2></div>
      <div class="section-body" id="cpblStab"></div>
    </div>
    <div class="section">
      <div class="section-h" style="background:var(--cpbl)"><h2>Significance — CPBL Predictors</h2></div>
      <div class="section-body" id="cpblSig"></div>
    </div>
  </div>
  <div class="section">
    <div class="section-h" style="background:var(--cpbl)"><h2>CPBL Pitchers — Complete Dataset</h2></div>
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

<footer>Asian League → MLB Pitcher Transition Analysis · Data: Baseball-Reference, FanGraphs, NPB Official, KBO, CPBL · Cross-league factor: Cho (2026)</footer>
</div>

<script>
const D = {data_json};
const ML = D.meta.metric_labels;

document.querySelectorAll('.tab').forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
  }};
}});

function fmtR(r) {{ return `<span class="rnum">${{Number(r).toFixed(3)}}</span>`; }}
function stabPill(s) {{ return s ? '<span class="pill y">STABLE</span>' : '<span class="pill n">below</span>'; }}
function sigPill(s) {{ return s ? '<span class="pill y">SIG</span>' : '<span class="pill n">n.s.</span>'; }}
function leagueBadge(l) {{ return `<span class="badge ${{l.toLowerCase()}}">${{l}}</span>`; }}

function stabBar(r) {{
  const abs_r = Math.abs(r);
  const pct = Math.min(abs_r * 100, 100);
  const color = abs_r >= 0.7 ? 'var(--pass)' : abs_r >= 0.4 ? 'var(--navy)' : '#ccc';
  return `<div class="bar-wrap"><div class="bar-bg"><div class="bar-fill" style="width:${{pct}}%;background:${{color}}"></div></div></div>`;
}}

function renderStab(containerId, leagueKey) {{
  const stab = D.stability[leagueKey];
  if (!stab) {{ document.getElementById(containerId).innerHTML = '<p>Insufficient data for this league.</p>'; return; }}
  let html = '<table><thead><tr><th>Metric</th><th>ρ (Spearman)</th><th>p-value</th><th>N</th><th>Status</th><th></th></tr></thead><tbody>';
  for (const [m, v] of Object.entries(stab)) {{
    const label = ML[m] || m;
    html += `<tr><td>${{label}}</td><td>${{fmtR(v.r)}}</td><td>${{v.p.toFixed(4)}}</td><td>${{v.n}}</td><td>${{stabPill(v.stable)}}</td><td style="width:120px">${{stabBar(v.r)}}</td></tr>`;
  }}
  html += '</tbody></table>';
  html += '<p style="font-size:11px;color:var(--muted);margin-top:8px">Stable = |ρ| ≥ 0.40 and p &lt; 0.10. Spearman rank correlation, Asian league avg → MLB career.</p>';
  document.getElementById(containerId).innerHTML = html;
}}

function renderSig(containerId, leagueKey) {{
  const sig = D.significance[leagueKey];
  if (!sig) {{ document.getElementById(containerId).innerHTML = '<p>Insufficient data.</p>'; return; }}
  let html = '';
  for (const [outKey, outData] of Object.entries(sig)) {{
    html += `<h3>Predicting ${{outData.label}}</h3>`;
    html += '<table><thead><tr><th>Asian Metric</th><th>ρ</th><th>p</th><th>N</th><th></th></tr></thead><tbody>';
    for (const d of outData.drivers.slice(0, 7)) {{
      html += `<tr><td>${{d.label}}</td><td>${{fmtR(d.r)}}</td><td>${{d.p.toFixed(4)}}</td><td>${{d.n}}</td><td>${{sigPill(d.significant)}}</td></tr>`;
    }}
    html += '</tbody></table>';
  }}
  document.getElementById(containerId).innerHTML = html;
}}

function renderPitcherTable(containerId, league) {{
  const pitchers = D.pitchers.filter(p => p.league === league);
  let html = '<table><thead><tr><th>Name</th><th>Pos</th><th>Asian Yrs</th><th>MLB Yrs</th>';
  html += '<th>A-ERA</th><th>A-K/9</th><th>A-BB/9</th><th>A-WHIP</th><th>A-K/BB</th>';
  html += '<th>M-ERA</th><th>M-K/9</th><th>M-BB/9</th><th>M-WHIP</th><th>M-K/BB</th>';
  html += '<th>ERA+</th><th>WAR</th><th>Seasons</th></tr></thead><tbody>';
  const sorted = [...pitchers].sort((a, b) => b.m_war - a.m_war);
  for (const p of sorted) {{
    const eraClass = p.m_era_plus >= 110 ? 'color:var(--pass)' : p.m_era_plus < 90 ? 'color:var(--cut)' : '';
    html += `<tr>
      <td><strong>${{p.name}}</strong></td><td>${{p.pos}}</td>
      <td>${{p.asian_years}}</td><td>${{p.mlb_years}}</td>
      <td class="rnum">${{p.a_era.toFixed(2)}}</td><td class="rnum">${{p.a_k9.toFixed(1)}}</td>
      <td class="rnum">${{p.a_bb9.toFixed(1)}}</td><td class="rnum">${{p.a_whip.toFixed(2)}}</td>
      <td class="rnum">${{p.a_k_bb.toFixed(2)}}</td>
      <td class="rnum">${{p.m_era.toFixed(2)}}</td><td class="rnum">${{p.m_k9.toFixed(1)}}</td>
      <td class="rnum">${{p.m_bb9.toFixed(1)}}</td><td class="rnum">${{p.m_whip.toFixed(2)}}</td>
      <td class="rnum">${{p.m_k_bb.toFixed(2)}}</td>
      <td class="rnum" style="${{eraClass}}">${{p.m_era_plus}}</td>
      <td class="rnum">${{p.m_war.toFixed(1)}}</td><td>${{p.m_seasons}}</td>
    </tr>`;
  }}
  html += '</tbody></table>';
  document.getElementById(containerId).innerHTML = html;
}}

function renderLeagueKpis(containerId, league) {{
  const pitchers = D.pitchers.filter(p => p.league === league);
  const n = pitchers.length;
  const avgWar = (pitchers.reduce((s, p) => s + p.m_war, 0) / n).toFixed(1);
  const avgEra = (pitchers.reduce((s, p) => s + p.m_era, 0) / n).toFixed(2);
  const avgSzn = (pitchers.reduce((s, p) => s + p.m_seasons, 0) / n).toFixed(1);
  const avgEraPlus = Math.round(pitchers.reduce((s, p) => s + p.m_era_plus, 0) / n);
  document.getElementById(containerId).innerHTML = `
    <div class="kpi"><div class="v">${{n}}</div><div class="l">Pitchers</div></div>
    <div class="kpi"><div class="v">${{avgWar}}</div><div class="l">Avg Career WAR</div></div>
    <div class="kpi"><div class="v">${{avgEra}}</div><div class="l">Avg MLB ERA</div></div>
    <div class="kpi"><div class="v">${{avgEraPlus}}</div><div class="l">Avg ERA+</div></div>
    <div class="kpi"><div class="v">${{avgSzn}}</div><div class="l">Avg MLB Seasons</div></div>`;
}}

// HOME
document.getElementById('homeKpis').innerHTML = `
  <div class="kpi"><div class="v">${{D.meta.n_pitchers}}</div><div class="l">Total Pitchers</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_npb}}</div><div class="l">NPB (Japan)</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_kbo}}</div><div class="l">KBO (Korea)</div></div>
  <div class="kpi"><div class="v">${{D.meta.n_cpbl}}</div><div class="l">CPBL (Taiwan)</div></div>
  <div class="kpi"><div class="v">${{D.meta.translation_factor}}</div><div class="l">xFIP− Translation Factor</div></div>`;

document.getElementById('homeNote').innerHTML =
  '<strong>Methodology:</strong> Spearman rank correlations between Asian-league career/peak stats and MLB career stats. ' +
  'Stability = ρ ≥ 0.40, p &lt; 0.10. Redundancy = |ρ| ≥ 0.75 between metrics. ' +
  'Significance = Asian metric predicting MLB ERA+, WAR, or longevity. ' +
  'Translation factor from Cho (2026): NPB xFIP− worsens ~9.6% in MLB. ' +
  'Composite ranking = 35% WAR + 25% ERA+ + 20% IP + 10% Seasons + 10% K/BB.';

// Rankings
let rankHtml = '<table><thead><tr><th>#</th><th>Name</th><th>League</th><th>Pos</th><th>Composite</th><th>WAR</th><th>ERA+</th><th>IP</th><th>Seasons</th><th>MLB Years</th></tr></thead><tbody>';
for (const r of D.rankings.slice(0, 10)) {{
  rankHtml += `<tr>
    <td class="rnum">${{r.rank}}</td><td><strong>${{r.name}}</strong></td>
    <td>${{leagueBadge(r.league)}}</td><td>${{r.pos}}</td>
    <td class="rnum">${{r.composite}}</td><td class="rnum">${{r.war.toFixed(1)}}</td>
    <td class="rnum">${{r.era_plus}}</td><td class="rnum">${{r.ip.toFixed(0)}}</td>
    <td>${{r.seasons}}</td><td>${{r.mlb_years}}</td>
  </tr>`;
}}
rankHtml += '</tbody></table>';
document.getElementById('rankTable').innerHTML = rankHtml;

renderStab('homeStab', 'ALL');

// Clusters
let cHtml = '';
for (const c of D.redundancy.clusters) {{
  const labels = c.metrics.map(m => {{
    const clean = m.replace('a_','Asian ').replace('m_','MLB ');
    const base = m.replace(/^[am]_/, '');
    return ML[base] ? `${{m.startsWith('a_') ? 'Asian' : 'MLB'}} ${{ML[base]}}` : clean;
  }});
  cHtml += `<div class="cluster-box"><div class="cid">Cluster ${{c.id}}</div><div class="metrics">${{labels.join(' · ')}}</div></div>`;
}}
if (!cHtml) cHtml = '<p>No multi-metric clusters found at threshold.</p>';
document.getElementById('homeClusters').innerHTML = cHtml;

// Pairs
let pHtml = '<table><thead><tr><th>Metric A</th><th>Metric B</th><th>ρ</th></tr></thead><tbody>';
for (const p of D.redundancy.pairs.slice(0, 15)) {{
  const la = (ML[p.a.replace(/^[am]_/,'')] || p.a);
  const lb = (ML[p.b.replace(/^[am]_/,'')] || p.b);
  const pa = p.a.startsWith('a_') ? 'Asian' : 'MLB';
  const pb = p.b.startsWith('a_') ? 'Asian' : 'MLB';
  pHtml += `<tr><td>${{pa}} ${{la}}</td><td>${{pb}} ${{lb}}</td><td class="rnum">${{p.r.toFixed(3)}}</td></tr>`;
}}
pHtml += '</tbody></table>';
document.getElementById('homePairs').innerHTML = pHtml;

renderSig('homeSig', 'ALL');

// LEAGUE TABS
for (const lg of ['npb', 'kbo', 'cpbl']) {{
  const LG = lg.toUpperCase();
  renderLeagueKpis(lg + 'Kpis', LG);
  renderStab(lg + 'Stab', LG);
  renderSig(lg + 'Sig', LG);
  renderPitcherTable(lg + 'Table', LG);
}}

// ITOH TAB
const itoh = D.itoh;
const c = itoh.npb_career;
const b = itoh.best_season_2025;
document.getElementById('itohKpis').innerHTML = `
  <div class="kpi"><div class="v">${{itoh.name}}</div><div class="l">${{itoh.team}} · Age ${{itoh.age}} · ${{itoh.throws}} / ${{itoh.bats}} · ${{itoh.height}}</div></div>
  <div class="kpi"><div class="v">${{c.era}} ERA</div><div class="l">NPB Career (${{c.seasons}} seasons, ${{c.record}})</div></div>
  <div class="kpi"><div class="v">${{c.k}} K / ${{c.bb}} BB</div><div class="l">${{c.ip}} IP · ${{c.cg}} CG · ${{c.sho}} SHO</div></div>
  <div class="kpi"><div class="v">${{b.era}} ERA</div><div class="l">2025 Best (${{b.record}}, ${{b.award}})</div></div>
  <div class="kpi"><div class="v">${{b.k}}:${{b.bb}} K:BB</div><div class="l">2025: ${{b.ip}} IP, ${{b.gb_pct}}% GB, ${{b.siera}} SIERA</div></div>`;

// Arsenal
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

// Section A
let saHtml = '';
for (const item of itoh.section_a.content) {{
  saHtml += `<h3>${{item.heading}}</h3><p>${{item.text}}</p>`;
}}
document.getElementById('itohA').innerHTML = saHtml;

// Section B
let sbHtml = '';
for (const adj of itoh.section_b.adjustments) {{
  sbHtml += `<h3>${{adj.adjustment}}</h3><p>${{adj.reasoning}}</p>`;
}}
document.getElementById('itohB').innerHTML = sbHtml;

// Section C
let scHtml = '';
for (const req of itoh.section_c.requests) {{
  scHtml += `<h3>Priority ${{req.priority}}: ${{req.info}}</h3><p>${{req.impact}}</p>`;
}}
scHtml += `<h3>Recommended Next Step</h3><p>${{itoh.section_c.next_step}}</p>`;
document.getElementById('itohC').innerHTML = scHtml;

// Sources
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
