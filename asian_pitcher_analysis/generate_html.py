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
:root {{
  --ink:#1c1c1c; --muted:#5a5f6a; --line:#d0d4db; --bg:#f4f5f7; --card:#fff;
  --npb:#c62828; --kbo:#1565c0; --cpbl:#2e7d32; --all:#37474f;
  --pass:#2d6a4f; --cut:#9a3412; --navy:#3d5a80;
}}
*{{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  font-family:"IBM Plex Sans","Segoe UI",system-ui,sans-serif;
  background:radial-gradient(ellipse 80% 50% at 8% -10%,#dbe4f0,transparent 55%),var(--bg);
  color:var(--ink); line-height:1.5;
}}
.wrap {{ max-width:1080px; margin:0 auto; padding:32px 24px 72px; }}
h1 {{
  font-family:"IBM Plex Serif",Georgia,serif;
  font-size:clamp(22px,3.5vw,30px); letter-spacing:-.02em;
}}
.sub {{ color:var(--muted); font-size:14px; margin-top:8px; max-width:880px; line-height:1.6; }}

/* ── tabs ── */
.tabs {{ display:flex; gap:0; border-bottom:2px solid var(--ink); margin:28px 0 0; flex-wrap:wrap; }}
.tab {{
  font:600 13px/1 inherit; padding:11px 18px; border:none; background:transparent;
  cursor:pointer; color:#888; border-bottom:3px solid transparent; margin-bottom:-2px;
  transition:color .15s, border-color .15s;
}}
.tab:hover {{ color:var(--ink); }}
.tab.active {{ color:var(--ink); border-bottom-color:var(--navy); }}
.panel {{ display:none; padding-top:24px; }} .panel.active {{ display:block; }}

/* ── cards & sections ── */
.section {{
  background:var(--card); border:1px solid var(--line); border-radius:10px;
  margin-bottom:20px; overflow:hidden;
}}
.section-h {{ padding:12px 18px; background:var(--ink); color:#fff; }}
.section-h h2 {{ font-size:13px; letter-spacing:.06em; text-transform:uppercase; }}
.section-body {{ padding:20px; }}
.section-body p {{ font-size:13.5px; color:#444; margin-bottom:10px; line-height:1.6; }}
.section-body h3 {{ font-size:14px; margin:16px 0 6px; color:var(--navy); }}
.section-body h3:first-child {{ margin-top:0; }}

/* ── explainer boxes ── */
.explain {{
  background:#f8f9fb; border:1px solid var(--line); border-radius:8px;
  padding:18px 20px; margin-bottom:20px; font-size:13.5px; color:#333; line-height:1.65;
}}
.explain strong {{ color:var(--ink); }}
.explain code {{
  background:#e8ecf2; padding:1px 5px; border-radius:3px; font-size:12px;
  font-family:"IBM Plex Mono",monospace;
}}
.formula {{
  display:block; background:#fff; border:1px solid var(--line); border-radius:6px;
  padding:12px 16px; margin:12px 0; font-family:"IBM Plex Mono",monospace;
  font-size:13px; color:var(--navy); line-height:1.7;
}}

/* ── tables ── */
table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
th,td {{ padding:8px 10px; text-align:left; border-bottom:1px solid #eceff3; }}
th {{
  font-size:10px; text-transform:uppercase; letter-spacing:.04em;
  color:var(--muted); background:#fafbfc; position:sticky; top:0; z-index:1;
}}
tr:hover td {{ background:#f0f4fa; }}
.rnum {{ font-variant-numeric:tabular-nums; font-weight:700; }}

/* ── pills ── */
.pill {{
  display:inline-block; padding:2px 8px; border-radius:999px;
  font-size:10px; font-weight:700; white-space:nowrap;
}}
.pill.y {{ background:#d8f3e4; color:var(--pass); }}
.pill.n {{ background:#f3e8e2; color:var(--cut); }}
.pill.g {{ background:#e8eef6; color:var(--navy); }}

/* ── bars ── */
.bar-wrap {{ display:flex; align-items:center; gap:8px; }}
.bar-bg {{ flex:1; height:7px; background:#e8eaee; border-radius:3px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:3px; transition:width .3s; }}

/* ── cluster boxes ── */
.cluster-box {{
  background:#f8f9fb; border:1px solid var(--line); border-radius:8px;
  padding:14px 16px; margin:8px 0;
}}
.cluster-box .cid {{ font-weight:700; color:var(--navy); font-size:13px; margin-bottom:4px; }}
.cluster-box .metrics {{ font-size:12.5px; color:#555; }}
.cluster-box .metrics .metric-pill {{
  display:inline-block; background:#e8eef6; color:var(--navy); padding:3px 10px;
  border-radius:4px; font-weight:600; font-size:12px; margin:2px 4px 2px 0;
}}

/* ── pair row highlight ── */
.pair-row {{ transition: background .15s; }}
.pair-row:hover td {{ background:#fff3e0; }}

/* ── correlation matrix ── */
.corr-grid {{
  display:grid; gap:2px; margin:16px 0;
}}
.corr-cell {{
  display:flex; align-items:center; justify-content:center;
  font-size:11px; font-weight:700; border-radius:4px; aspect-ratio:1;
  min-height:38px;
}}
.corr-label {{
  display:flex; align-items:center; justify-content:center;
  font-size:11px; font-weight:600; color:var(--muted);
}}

/* ── window sub-tabs ── */
.win-tabs {{ display:flex; gap:4px; margin:8px 0 14px; flex-wrap:wrap; }}
.win-tab {{
  font:600 11px inherit; padding:6px 12px; border:1px solid var(--line);
  border-radius:4px; background:#fff; cursor:pointer; color:var(--muted);
  transition:all .15s;
}}
.win-tab:hover {{ border-color:var(--navy); color:var(--navy); }}
.win-tab.active {{ background:var(--navy); color:#fff; border-color:var(--navy); }}
.win-panel {{ display:none; }} .win-panel.active {{ display:block; }}

/* ── KPI row ── */
.kpis {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; margin-bottom:20px; }}
.kpi {{ background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 14px; }}
.kpi .v {{ font-size:20px; font-weight:700; color:var(--navy); }}
.kpi .l {{ font-size:11px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin-top:2px; }}

footer {{ margin-top:28px; font-size:11px; color:#999; text-align:center; }}

@media(max-width:700px) {{
  .wrap {{ padding:16px 12px 48px; }}
  table {{ font-size:11px; }}
  th,td {{ padding:6px 6px; }}
}}
</style>
</head>
<body>
<div class="wrap">

<h1>Asian League \u2192 MLB Pitcher Transition Analysis</h1>
<p class="sub">
  {data['meta']['n_pitchers']} pitchers who crossed between Asian professional leagues
  (NPB\u2009/\u2009KBO\u2009/\u2009CPBL) and Major League Baseball \u2014
  {data['meta'].get('n_asian_born','')} Asian-born,
  {data['meta'].get('n_crossover','')} American crossover.
</p>

<nav class="tabs">
  <button class="tab active" data-panel="stability">Stability &amp; Metrics</button>
  <button class="tab" data-panel="redundancy">Redundancy Clusters</button>
</nav>

<!-- ═══════════════════════════════════════════════════════════════
     TAB 1 — STABILITY & METRICS
     ═══════════════════════════════════════════════════════════════ -->
<section class="panel active" id="panel-stability">

  <!-- KPIs -->
  <div class="kpis">
    <div class="kpi"><div class="v">{data['meta']['n_pitchers']}</div><div class="l">Pitchers</div></div>
    <div class="kpi"><div class="v">{data['meta']['n_with_both']}</div><div class="l">Asian + MLB Stats</div></div>
    <div class="kpi"><div class="v">{data['meta']['n_npb']}</div><div class="l">NPB (Japan)</div></div>
    <div class="kpi"><div class="v">{data['meta']['n_kbo']}</div><div class="l">KBO (Korea)</div></div>
    <div class="kpi"><div class="v">{data['meta']['n_cpbl']}</div><div class="l">CPBL (Taiwan)</div></div>
    <div class="kpi"><div class="v">{data['meta']['translation_factor']}</div><div class="l">xFIP\u2212 Factor</div></div>
  </div>

  <!-- EXPLANATION -->
  <div class="section">
    <div class="section-h"><h2>How the Calculation Works</h2></div>
    <div class="section-body">

      <h3>Goal</h3>
      <p>
        Determine which pitching metrics are <strong>stable</strong> (reliably transfer)
        when a pitcher moves from an Asian professional league to MLB.
        A stable metric means that a pitcher\u2019s Asian-league number meaningfully
        predicts his MLB number for the same statistic.
      </p>

      <h3>Pearson r Correlation</h3>
      <p>
        For each metric, we compute the <strong>Pearson r</strong> between every pitcher\u2019s
        Asian-league value and his MLB value for that same metric. Pearson r measures the
        strength and direction of the linear relationship between two continuous variables.
      </p>
      <div class="formula">
        r = \u03A3 (x\u1D62 \u2212 x\u0305)(y\u1D62 \u2212 \u0233) / \u221A[\u03A3(x\u1D62 \u2212 x\u0305)\u00B2 \u00B7 \u03A3(y\u1D62 \u2212 \u0233)\u00B2]<br>
        where x = Asian metric, y = MLB metric for the same stat
      </div>
      <p>
        The result ranges from \u22121 to +1. A value of +0.60 means
        pitchers with higher Asian values also tend to have higher MLB values;
        \u22120.60 would mean the opposite. Values near 0 indicate no linear relationship.
      </p>

      <h3>Multi-Window Approach</h3>
      <p>
        Instead of a single career-vs-career comparison, we test across <strong>four time windows</strong>
        to see whether stability holds at different horizons:
      </p>
      <div class="formula">
        Window 1: Last 1 year in Asia \u2192 First 1 year in MLB<br>
        Window 2: Last 2 years in Asia \u2192 First 2 years in MLB<br>
        Window 3: Last 3 years in Asia \u2192 First 3 years in MLB<br>
        Window 4: Full career in Asia \u2192 Full career in MLB
      </div>
      <p>
        Shorter windows capture recent form; longer windows smooth out variance.
        A metric that is stable across <em>all</em> windows is the most trustworthy
        for cross-league scouting.
      </p>

      <h3>Stability Thresholds</h3>
      <p>
        A metric is marked <strong>STABLE</strong> in a given window when both conditions are met:
      </p>
      <div class="formula">
        |r| \u2265 0.40 &nbsp;&nbsp;(at least moderate correlation strength)<br>
        p &lt; 0.10 &nbsp;&nbsp;(less than 10% probability the result is due to chance)
      </div>
      <p>
        The p-value comes from a two-tailed t-test on the Pearson correlation coefficient.
        A lower p-value means stronger evidence that the metric genuinely transfers across leagues.
      </p>

      <h3>Data Sources</h3>
      <p>
        <strong>MLB Stats API</strong> (statsapi.mlb.com) for career and year-by-year MLB pitching stats.
        <strong>Baseball-Reference Register</strong> for Asian-league career and yearly data.
        <strong>bWAR dataset</strong> (via pybaseball) for WAR and ERA+.
        Cross-league translation factor of {data['meta']['translation_factor']} xFIP\u2212 from Cho (2026).
        Career Asian stats are filtered to <em>pre-transition years only</em> \u2014
        if a pitcher returned to Asia after MLB, those later seasons are excluded.
      </p>
    </div>
  </div>

  <!-- METRIC ROWS WITH STABILITY SCORES -->
  <div class="section">
    <div class="section-h"><h2>Metric Stability Scores \u2014 All Leagues Combined</h2></div>
    <div class="section-body" id="metricTable"></div>
  </div>

  <!-- FULL STABILITY TABLES BY WINDOW -->
  <div class="section">
    <div class="section-h"><h2>Detailed Stability by Window</h2></div>
    <div class="section-body" id="stabDetail"></div>
  </div>

</section>

<!-- ═══════════════════════════════════════════════════════════════
     TAB 2 — REDUNDANCY CLUSTERS
     ═══════════════════════════════════════════════════════════════ -->
<section class="panel" id="panel-redundancy">

  <!-- EXPLANATION -->
  <div class="section">
    <div class="section-h"><h2>How Redundancy Is Calculated</h2></div>
    <div class="section-body">

      <h3>Goal</h3>
      <p>
        Identify which pitching metrics measure essentially the <strong>same thing</strong>,
        so a scout doesn\u2019t double-count overlapping information.
        If two metrics are highly correlated among pitchers\u2019 Asian-league stats,
        they carry redundant signal for cross-league evaluation.
      </p>

      <h3>Pairwise Pearson r on Asian Metrics</h3>
      <p>
        We compute Pearson r between every pair of Asian-league career metrics
        (ERA, K/9, BB/9, HR/9, WHIP, K/BB, GB%).
        This uses the same Pearson formula as stability, but both variables come
        from the Asian side \u2014 we\u2019re measuring how metrics relate to <em>each other</em>,
        not how they transfer to MLB.
      </p>

      <h3>Redundancy Threshold</h3>
      <div class="formula">
        A pair is flagged as <strong>redundant</strong> when |r| \u2265 0.75
      </div>
      <p>
        This means that 75%+ of one metric\u2019s pitcher-to-pitcher variance is
        linearly explained by the other. Using both in a scouting model would
        over-weight that dimension.
      </p>

      <h3>Agglomerative Clustering</h3>
      <p>
        To group redundant metrics into clusters, we use <strong>agglomerative
        hierarchical clustering</strong> with average linkage on a distance matrix
        derived from the correlation matrix:
      </p>
      <div class="formula">
        distance = 1 \u2212 |r|<br>
        Clustering threshold = 0.40 (i.e., metrics with |r| \u2265 0.60 tend to cluster)
      </div>
      <p>
        Each cluster contains metrics that are interchangeable for evaluation purposes.
        A scout should pick <strong>one representative metric per cluster</strong>
        rather than using all of them.
      </p>
    </div>
  </div>

  <!-- REDUNDANT PAIRS TABLE -->
  <div class="section">
    <div class="section-h"><h2>Redundant Pairs (|r| \u2265 0.75)</h2></div>
    <div class="section-body" id="pairsTable"></div>
  </div>

  <!-- CLUSTER BOXES -->
  <div class="section">
    <div class="section-h"><h2>Metric Clusters</h2></div>
    <div class="section-body" id="clusterBoxes"></div>
  </div>

  <!-- CORRELATION HEATMAP -->
  <div class="section">
    <div class="section-h"><h2>Full Pairwise Correlation Matrix (Asian Metrics)</h2></div>
    <div class="section-body" id="corrMatrix"></div>
  </div>

</section>

<footer>
  Asian League \u2192 MLB Pitcher Transition Analysis \u00B7
  Data: MLB Stats API, Baseball-Reference Register, bWAR \u00B7
  Cross-league factor: Cho (2026) \u00B7
  {data['meta']['n_with_both']} pitchers with both Asian &amp; MLB data
</footer>

</div>

<script>
const D = {data_json};
const ML = D.meta.metric_labels;
const WINS = D.windows;

/* ── tab switching ── */
document.querySelectorAll('.tab').forEach(btn => {{
  btn.onclick = () => {{
    document.querySelectorAll('.tab').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.panel).classList.add('active');
  }};
}});

/* ── helpers ── */
function fmt(v,d){{ return v!=null && !isNaN(v) ? Number(v).toFixed(d) : '\u2014'; }}
function fmtR(r){{ return `<span class="rnum">${{Number(r).toFixed(3)}}</span>`; }}
function stabPill(s){{ return s ? '<span class="pill y">STABLE</span>' : '<span class="pill n">below</span>'; }}
function stabBar(r){{
  const a=Math.abs(r), pct=Math.min(a*100,100);
  const c = a>=0.7?'var(--pass)':a>=0.4?'var(--navy)':'#ccc';
  return `<div class="bar-wrap"><div class="bar-bg"><div class="bar-fill" style="width:${{pct}}%;background:${{c}}"></div></div></div>`;
}}
function corrColor(r){{
  const a=Math.abs(r);
  if(a>=0.75) return r>0?'#c62828':'#1565c0';
  if(a>=0.50) return r>0?'#ef5350':'#42a5f5';
  if(a>=0.25) return r>0?'#ef9a9a':'#90caf9';
  return '#e0e0e0';
}}

/* ═══════════════════════════════════════════════════
   TAB 1: METRIC STABILITY SCORES
   ═══════════════════════════════════════════════════ */
(function(){{
  const stabAll = D.stability['ALL'] || {{}};

  const allMetrics = {{}};
  for (const [wtag, wdata] of Object.entries(stabAll)) {{
    if (!wdata || !wdata.metrics) continue;
    for (const [m, v] of Object.entries(wdata.metrics)) {{
      if (!allMetrics[m]) allMetrics[m] = {{}};
      allMetrics[m][wtag] = v;
    }}
  }}

  const stableCount = m => Object.values(allMetrics[m]||{{}}).filter(v=>v.stable).length;
  const totalWindows = m => Object.keys(allMetrics[m]||{{}}).length;
  const metrics = Object.keys(allMetrics).sort((a,b)=>stableCount(b)-stableCount(a));

  let html = '<p style="margin-bottom:14px">Each row shows one pitching metric and its Pearson r correlation between the Asian-league value and MLB value, tested across four time windows. Metrics are ranked by how many windows they are stable in.</p>';

  html += '<table><thead><tr>';
  html += '<th>Metric</th><th style="text-align:center">1yr</th><th style="text-align:center">2yr</th><th style="text-align:center">3yr</th><th style="text-align:center">Career</th><th style="text-align:center">Score</th><th>Verdict</th>';
  html += '</tr></thead><tbody>';

  for (const m of metrics) {{
    const label = ML[m] || m;
    const sc = stableCount(m);
    const tot = totalWindows(m);
    const verdict = sc >= 3 ? '<span class="pill y">USE</span>'
                  : sc >= 2 ? '<span class="pill g">MAYBE</span>'
                  : '<span class="pill n">AVOID</span>';

    function winCell(wtag) {{
      const v = (allMetrics[m]||{{}})[wtag];
      if (!v) return '<td style="text-align:center;color:#ccc">\u2014</td>';
      const bg = v.stable ? 'background:#edf7f0' : '';
      return `<td style="text-align:center;${{bg}}">${{fmtR(v.r)}}<br><span style="font-size:10px;color:var(--muted)">p=${{v.p.toFixed(3)}}</span><br>${{stabPill(v.stable)}}</td>`;
    }}

    html += `<tr>`;
    html += `<td><strong>${{label}}</strong></td>`;
    html += winCell('1y') + winCell('2y') + winCell('3y') + winCell('career');
    html += `<td style="text-align:center"><span class="pill g" style="font-size:13px">${{sc}}/${{tot}}</span></td>`;
    html += `<td>${{verdict}}</td>`;
    html += `</tr>`;
  }}
  html += '</tbody></table>';

  html += '<p style="font-size:11.5px;color:var(--muted);margin-top:12px"><strong>USE</strong> = stable in 3+ windows, highly reliable for cross-league scouting. <strong>MAYBE</strong> = stable in 2 windows, use with caution. <strong>AVOID</strong> = stable in 0\u20131 windows, does not transfer reliably.</p>';

  document.getElementById('metricTable').innerHTML = html;
}})();

/* ═══════════════════════════════════════════════════
   TAB 1: DETAILED STABILITY BY WINDOW
   ═══════════════════════════════════════════════════ */
(function(){{
  const stabAll = D.stability['ALL'] || {{}};
  const uid = 'stabDet';

  let html = '<div class="win-tabs">';
  WINS.forEach((w,i) => {{
    html += `<button class="win-tab${{i===0?' active':''}}" data-wg="${{uid}}" data-wt="${{w.tag}}">${{w.label}}</button>`;
  }});
  html += '</div>';

  WINS.forEach((w,i) => {{
    const wd = stabAll[w.tag];
    html += `<div class="win-panel${{i===0?' active':''}}" data-wg="${{uid}}" data-wp="${{w.tag}}">`;
    if(!wd||!wd.metrics){{
      html += '<p>Insufficient data for this window.</p>';
    }} else {{
      html += `<p style="font-size:12px;color:var(--muted);margin-bottom:10px">${{wd.label}} \u2014 ${{Object.values(wd.metrics)[0]?.n || '?'}} pitchers with data in this window.</p>`;
      html += '<table><thead><tr><th>Metric</th><th>Pearson r</th><th>p-value</th><th>N</th><th>Status</th><th style="width:140px">Strength</th></tr></thead><tbody>';
      const sorted = Object.entries(wd.metrics).sort((a,b)=>Math.abs(b[1].r)-Math.abs(a[1].r));
      for(const [m,v] of sorted){{
        html += `<tr><td>${{ML[m]||m}}</td><td>${{fmtR(v.r)}}</td><td>${{v.p.toFixed(4)}}</td><td>${{v.n}}</td><td>${{stabPill(v.stable)}}</td><td>${{stabBar(v.r)}}</td></tr>`;
      }}
      html += '</tbody></table>';
    }}
    html += '</div>';
  }});

  document.getElementById('stabDetail').innerHTML = html;

  document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(btn=>{{
    btn.onclick=()=>{{
      document.querySelectorAll(`.win-tab[data-wg="${{uid}}"]`).forEach(b=>b.classList.remove('active'));
      document.querySelectorAll(`.win-panel[data-wg="${{uid}}"]`).forEach(p=>p.classList.remove('active'));
      btn.classList.add('active');
      document.querySelector(`.win-panel[data-wg="${{uid}}"][data-wp="${{btn.dataset.wt}}"]`).classList.add('active');
    }};
  }});
}})();

/* ═══════════════════════════════════════════════════
   TAB 2: REDUNDANT PAIRS
   ═══════════════════════════════════════════════════ */
(function(){{
  const pairs = D.redundancy.pairs || [];

  let html = '';
  if(pairs.length===0){{
    html = '<p>No metric pairs exceed the |r| \u2265 0.75 redundancy threshold.</p>';
  }} else {{
    html += '<p style="margin-bottom:12px">These pairs of Asian-league pitching metrics are so highly correlated that they carry essentially the same information. Using both in a scouting evaluation double-counts that dimension.</p>';
    html += '<table><thead><tr><th>Metric A</th><th>Metric B</th><th>Pearson r</th><th style="width:160px">Strength</th><th>Interpretation</th></tr></thead><tbody>';
    for(const p of pairs){{
      const a = Math.abs(p.r);
      const interp = a>=0.85 ? 'Very high redundancy \u2014 near-identical signal'
                   : a>=0.75 ? 'High redundancy \u2014 overlapping signal'
                   : 'Moderate correlation';
      const dir = p.r > 0 ? 'positive' : 'inverse';
      html += `<tr class="pair-row">`;
      html += `<td><strong>${{p.a_label}}</strong></td>`;
      html += `<td><strong>${{p.b_label}}</strong></td>`;
      html += `<td>${{fmtR(p.r)}} <span style="font-size:10px;color:var(--muted)">(${{dir}})</span></td>`;
      html += `<td>${{stabBar(p.r)}}</td>`;
      html += `<td style="font-size:12px;color:#555">${{interp}}</td>`;
      html += `</tr>`;
    }}
    html += '</tbody></table>';
  }}

  document.getElementById('pairsTable').innerHTML = html;
}})();

/* ═══════════════════════════════════════════════════
   TAB 2: CLUSTER BOXES
   ═══════════════════════════════════════════════════ */
(function(){{
  const clusters = D.redundancy.clusters || [];
  let html = '<p style="margin-bottom:12px">Metrics grouped into clusters share overlapping signal. Pick <strong>one representative per cluster</strong> for scouting instead of using all.</p>';

  if(clusters.length===0){{
    html += '<p>No multi-metric clusters at the current threshold.</p>';
  }} else {{
    for(const c of clusters){{
      html += `<div class="cluster-box">`;
      html += `<div class="cid">Cluster ${{c.id + 1}}</div>`;
      html += `<div class="metrics">`;
      for(const lab of c.labels){{
        html += `<span class="metric-pill">${{lab}}</span>`;
      }}
      html += `</div>`;
      html += `<p style="font-size:12px;color:var(--muted);margin-top:6px">${{c.labels.length}} metrics that measure similar underlying pitcher traits.</p>`;
      html += `</div>`;
    }}
  }}

  document.getElementById('clusterBoxes').innerHTML = html;
}})();

/* ═══════════════════════════════════════════════════
   TAB 2: CORRELATION HEATMAP
   ═══════════════════════════════════════════════════ */
(function(){{
  const pitchers = D.pitchers.filter(p => p.a_era != null);
  const metricKeys = ['era','k9','bb9','hr9','whip','k_bb'];
  const n = metricKeys.length;

  function getVals(key){{ return pitchers.map(p => p['a_'+key]).filter(v => v!=null && !isNaN(v)); }}
  function pearson(xs,ys){{
    const paired = [];
    for(let i=0;i<xs.length&&i<ys.length;i++){{
      if(xs[i]!=null&&ys[i]!=null&&!isNaN(xs[i])&&!isNaN(ys[i])) paired.push([xs[i],ys[i]]);
    }}
    if(paired.length<5) return null;
    const nx=paired.length;
    const mx=paired.reduce((s,p)=>s+p[0],0)/nx;
    const my=paired.reduce((s,p)=>s+p[1],0)/nx;
    let num=0,dx=0,dy=0;
    for(const [x,y] of paired){{ num+=(x-mx)*(y-my); dx+=(x-mx)**2; dy+=(y-my)**2; }}
    return dx&&dy ? num/Math.sqrt(dx*dy) : null;
  }}

  const valArrays = {{}};
  for(const k of metricKeys) {{
    valArrays[k] = pitchers.map(p => p['a_'+k]);
  }}

  const corrMat = [];
  for(let i=0;i<n;i++){{
    corrMat[i]=[];
    for(let j=0;j<n;j++){{
      corrMat[i][j] = i===j ? 1.0 : pearson(valArrays[metricKeys[i]], valArrays[metricKeys[j]]);
    }}
  }}

  const cols = n + 1;
  let html = `<p style="margin-bottom:10px">Pairwise Pearson r between Asian-league metrics. Red = positive, blue = negative. Cells with |r| \u2265 0.75 are redundant.</p>`;
  html += `<div class="corr-grid" style="grid-template-columns:60px repeat(${{n}},1fr); max-width:${{n*70+60}}px;">`;

  html += '<div class="corr-label"></div>';
  for(const k of metricKeys) html += `<div class="corr-label">${{ML[k]||k}}</div>`;

  for(let i=0;i<n;i++){{
    html += `<div class="corr-label">${{ML[metricKeys[i]]||metricKeys[i]}}</div>`;
    for(let j=0;j<n;j++){{
      const r = corrMat[i][j];
      if(r==null){{
        html += '<div class="corr-cell" style="background:#f5f5f5;color:#bbb">\u2014</div>';
      }} else {{
        const a = Math.abs(r);
        const bg = corrColor(r);
        const alpha = i===j ? 0.3 : Math.max(0.15, a*0.8);
        const textColor = a>=0.5 ? '#fff' : '#333';
        const border = a>=0.75 && i!==j ? 'outline:2px solid '+bg+';outline-offset:-2px;' : '';
        html += `<div class="corr-cell" style="background:${{bg}};opacity:${{alpha.toFixed(2)}};color:${{textColor}};${{border}}">${{r.toFixed(2)}}</div>`;
      }}
    }}
  }}
  html += '</div>';

  html += '<p style="font-size:11px;color:var(--muted);margin-top:8px">Red shades = positive correlation, blue shades = negative. Bold-outlined cells exceed the |r| \u2265 0.75 redundancy threshold.</p>';

  document.getElementById('corrMatrix').innerHTML = html;
}})();

</script>
</body>
</html>"""

    out_path = OUT.parent / "asian_pitcher_mlb_analysis.html"
    out_path.write_text(html)
    print(f"Wrote {out_path} ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
