#!/usr/bin/env python3
"""Add top tabs, stat glossary, and correlation guidance to explorer."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPLORER = ROOT / "interactive_player_explorer.html"

# Plain-English definitions for shortlisted traits (FBref 26 + StatsBomb 11)
STAT_DEFINITIONS: dict[str, dict] = {
    # FBref Step-2 shortlist
    "Def_Pen_Touches": {
        "abbrev": "DEFPE", "label": "Def Pen Touches", "category": "Defending", "source": "FBref",
        "definition": "Touches inside your own penalty box per 90 — receiving, clearing, and playing under pressure in the defensive third.",
    },
    "PrgC_Progression": {
        "abbrev": "PRGC", "label": "PrgC Progression", "category": "Passing", "source": "FBref",
        "definition": "Progressive carries per 90 — ball carries that advance at least ~10 yards toward the opponent goal.",
    },
    "PrgDist_Total": {
        "abbrev": "PRGDI", "label": "PrgDist Total", "category": "Passing", "source": "FBref",
        "definition": "Total yards gained on progressive carries per 90 — how far a player moves the ball forward while carrying.",
    },
    "xG_Per": {
        "abbrev": "XG", "label": "xG Per", "category": "Attacking", "source": "FBref",
        "definition": "Expected goals per 90 — shot volume and quality combined (non-penalty xG in most FBref tables).",
    },
    "PrgR_Receiving": {
        "abbrev": "PRGRR", "label": "PrgR Receiving", "category": "Carrying", "source": "FBref",
        "definition": "Progressive passes received per 90 — how often a player gets the ball via forward-moving passes.",
    },
    "KP": {
        "abbrev": "KP", "label": "Key Passes", "category": "Passing", "source": "FBref",
        "definition": "Passes that directly lead to a shot per 90.",
    },
    "Att_3rd_Touches": {
        "abbrev": "ATT3R", "label": "Att 3rd Touches", "category": "Carrying", "source": "FBref",
        "definition": "Touches in the attacking third per 90 — involvement high up the pitch.",
    },
    "Clr": {
        "abbrev": "CLR", "label": "Clearances", "category": "Defending", "source": "FBref",
        "definition": "Clearances per 90 — removing danger from the defensive area (headed or kicked).",
    },
    "Gls_Standard": {
        "abbrev": "GLS", "label": "Goals (standard)", "category": "Attacking", "source": "FBref",
        "definition": "Goals per 90 from FBref standard stats (includes open play and set pieces; penalty handling per table).",
    },
    "Succ_Take": {
        "abbrev": "SUCC", "label": "Succ Take-ons", "category": "Carrying", "source": "FBref",
        "definition": "Successful take-ons (dribbles past an opponent) per 90.",
    },
    "Tkld_Take": {
        "abbrev": "TKLD", "label": "Tkld Take-ons", "category": "Defending", "source": "FBref",
        "definition": "Times tackled during take-on attempts per 90 — how often dribble attempts get stopped.",
    },
    "Won_Aerial": {
        "abbrev": "WON", "label": "Aerials Won", "category": "Defending", "source": "FBref",
        "definition": "Aerial duels won per 90.",
    },
    "Final_Third": {
        "abbrev": "FINTH", "label": "Final Third Passes", "category": "Passing", "source": "FBref",
        "definition": "Passes completed into the final third per 90 — progressive passing into attacking areas.",
    },
    "Att_Short": {
        "abbrev": "ATTSH", "label": "Short Pass Att", "category": "Attacking", "source": "FBref",
        "definition": "Short pass attempts (<15 yards) per 90.",
    },
    "Sh_Blocks": {
        "abbrev": "SHBLK", "label": "Shot Blocks", "category": "Defending", "source": "FBref",
        "definition": "Shots blocked per 90 — defensive actions stopping an opponent shot.",
    },
    "Cmp_percent_Medium": {
        "abbrev": "CMPME", "label": "Medium Pass %", "category": "Passing", "source": "FBref",
        "definition": "Completion rate on medium-length passes (roughly 15–30 yards).",
    },
    "Mis_Carries": {
        "abbrev": "MIS", "label": "Miscontrolled Carries", "category": "Carrying", "source": "FBref",
        "definition": "Miscontrolled carries per 90 — ball control errors while carrying.",
    },
    "CrsPA": {
        "abbrev": "CRSPA", "label": "Crosses into PA", "category": "Passing", "source": "FBref",
        "definition": "Crosses into the penalty area per 90.",
    },
    "Int": {
        "abbrev": "INT", "label": "Interceptions", "category": "Defending", "source": "FBref",
        "definition": "Interceptions per 90 — reading play to cut out passes.",
    },
    "Lost_Aerial": {
        "abbrev": "LOST", "label": "Aerials Lost", "category": "Defending", "source": "FBref",
        "definition": "Aerial duels lost per 90.",
    },
    "Crs": {
        "abbrev": "CRS", "label": "Crosses", "category": "Passing", "source": "FBref",
        "definition": "Crosses attempted per 90.",
    },
    "Fld": {
        "abbrev": "FLD", "label": "Fouls Drawn", "category": "Other", "source": "FBref",
        "definition": "Fouls drawn per 90 — winning free kicks through contact.",
    },
    "Won_percent_Aerial": {
        "abbrev": "WONAER", "label": "Aerial Win %", "category": "Defending", "source": "FBref",
        "definition": "Share of aerial duels won.",
    },
    "Def_3rd_Tackles": {
        "abbrev": "DEF3T", "label": "Def 3rd Tackles", "category": "Defending", "source": "FBref",
        "definition": "Tackles in the defensive third per 90.",
    },
    "Tkl_percent_Challenges": {
        "abbrev": "TKLPCT", "label": "Tackle Success %", "category": "Defending", "source": "FBref",
        "definition": "Share of tackle/challenge attempts won.",
    },
    "Recov": {
        "abbrev": "RECOV", "label": "Recoveries", "category": "Defending", "source": "FBref",
        "definition": "Ball recoveries per 90 — regaining possession from loose balls.",
    },
    # StatsBomb event metrics
    "dispossessed": {
        "abbrev": "DIS", "label": "Dispossessed (inverted)", "category": "Other", "source": "StatsBomb",
        "definition": "Times dispossessed per 90, inverted so higher = better ball security (fewer dispossessions).",
    },
    "pass_progressive": {
        "abbrev": "PPC", "label": "Progressive Passes", "category": "Passing", "source": "StatsBomb",
        "definition": "Passes that advance the ball ~10+ meters toward the opponent goal per 90.",
    },
    "pressures": {
        "abbrev": "PRS", "label": "Pressures", "category": "Defending", "source": "StatsBomb",
        "definition": "Pressures applied per 90 — closing down opponents within ~5 yards.",
    },
    "passes": {
        "abbrev": "PAS", "label": "Pass Volume", "category": "Passing", "source": "StatsBomb",
        "definition": "Total passes attempted per 90.",
    },
    "tackles": {
        "abbrev": "TAC", "label": "Tackles", "category": "Defending", "source": "StatsBomb",
        "definition": "Tackles per 90.",
    },
    "clearances": {
        "abbrev": "CLR", "label": "Clearances", "category": "Defending", "source": "StatsBomb",
        "definition": "Clearances per 90.",
    },
    "dribbles_completed": {
        "abbrev": "DRB", "label": "Successful Dribbles", "category": "Carrying", "source": "StatsBomb",
        "definition": "Successful dribbles per 90.",
    },
    "passes_into_final_third": {
        "abbrev": "PATT", "label": "Passes into Final Third", "category": "Passing", "source": "StatsBomb",
        "definition": "Passes into the final third per 90.",
    },
    "carries": {
        "abbrev": "CRY", "label": "Carries", "category": "Carrying", "source": "StatsBomb",
        "definition": "Ball carries per 90.",
    },
    "shots": {
        "abbrev": "SH", "label": "Shots", "category": "Attacking", "source": "StatsBomb",
        "definition": "Shots per 90.",
    },
    "xg": {
        "abbrev": "XG", "label": "Non-pen xG", "category": "Attacking", "source": "StatsBomb",
        "definition": "Non-penalty expected goals per 90.",
    },
}

OUTCOME_DEFINITIONS = [
    {"term": "Y1 minutes", "definition": "Bundesliga minutes played in the player's first BL season in our cohort."},
    {"term": "Y1 minutes percentile", "definition": "Where that player's Y1 minutes rank vs all cohort peers (0–100)."},
    {"term": "Stable-trait score", "definition": "Mean of BL Y1 percentiles on Step-2 shortlist traits vs position peers — profile fit, not stability r."},
    {"term": "Prior percentile (PRE)", "definition": "Where the player's prior-season rate ranks vs BL position peers (0–100). AVG=50, TOP≈90."},
    {"term": "Spearman ρ (rho)", "definition": "Rank correlation between prior trait percentile and a success outcome. |ρ|>0.3 is moderate; |ρ|<0.15 is very weak."},
    {"term": "Stability r", "definition": "Pearson r between prior-season and BL Y1 rates — measures trait portability, not predictive power alone."},
]


def patch_css(html: str) -> str:
    nav_css = """
  .top-nav{display:flex;gap:0;border-bottom:2px solid #1c1c1c;margin-bottom:20px}
  .top-nav .tab{font:600 14px system-ui;padding:12px 20px;background:transparent;border:none;border-bottom:3px solid transparent;margin-bottom:-2px;cursor:pointer;color:#555}
  .top-nav .tab:hover{color:#1c1c1c;background:#eef3f8}
  .top-nav .tab.active{color:#1c1c1c;border-bottom-color:#3d5a80;background:#fff}
  .rho-weak{color:#888}
  .rho-mod{color:#3d5a80;font-weight:600}
  .rho-strong{color:#1b7a45;font-weight:700}
  .glossary-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
  @media(max-width:900px){.glossary-grid{grid-template-columns:1fr}}
  .glossary-item{padding:8px 0;border-bottom:1px solid #ececec}
  .glossary-item:last-child{border-bottom:none}
  .glossary-item .abbr{font-weight:700;font-size:13px}
  .glossary-item .meta{font-size:11px;color:#666;margin:2px 0 4px}
  .glossary-item .def{font-size:12px;color:#444;line-height:1.45}
  .glossary-cat{margin-top:12px}
  .glossary-cat h4{font-size:12px;text-transform:uppercase;letter-spacing:.04em;color:#3d5a80;margin:0 0 6px}
  .corr-note{background:#fff8e6;border:1px solid #e6d9a8;border-radius:6px;padding:12px 14px;font-size:13px;color:#444;margin-top:10px;line-height:1.5}
"""
    if ".top-nav" not in html:
        html = html.replace("  footer{margin-top:16px;font-size:11px;color:#777}\n</style>", f"  footer{{margin-top:16px;font-size:11px;color:#777}}\n{nav_css}</style>")
    return html


def patch_html_structure(html: str) -> str:
    if 'class="top-nav"' not in html:
        html = html.replace(
            '<div class="wrap">\n\n<!-- ========== LANDING ========== -->',
            '<div class="wrap">\n<nav class="top-nav" aria-label="Main views">\n'
            '  <button type="button" class="tab active" data-view="landing">Success summary</button>\n'
            '  <button type="button" class="tab" data-view="explorer">Player examples</button>\n'
            '</nav>\n\n<!-- ========== LANDING ========== -->',
        )

    # Remove bottom CTA
    html = re.sub(
        r'\n  <div class="cta-row">.*?</div>\n  <footer>',
        '\n  <footer>',
        html,
        count=1,
        flags=re.DOTALL,
    )

    # Remove back button from explorer header
    html = html.replace(
        '    <button type="button" class="btn btn-ghost" id="btn-back" style="margin-bottom:10px;padding:8px 14px">← Back to success summary</button>\n',
        '',
    )

    # Add correlation note + glossary placeholder before footer on landing
    if 'id="corr-note"' not in html:
        html = html.replace(
            '  <div class="card">\n    <table id="league-trait-table">',
            '  <div class="card">\n    <table id="league-trait-table">',
        )
        insert_after_table = """
  <div class="corr-note" id="corr-note">
    <strong>Reading ρ:</strong> This table picks the <em>relatively</em> best feeder per trait — not a strong predictor for every row.
    Many ρ values are <strong>near zero</strong> (e.g. 0.03–0.06) with <strong>p &gt; 0.05</strong>, meaning no reliable link at that league’s sample size
    (La Liga n≈11, Serie A n≈24, Premier League n≈30, Ligue 1 n≈52). Only a few cells are meaningfully non-zero
    (e.g. Def Pen Touches in Ligue 1 ρ≈0.37, p≈0.007). Weak ρ = “weakest signal wins,” not “this trait forecasts minutes.”
  </div>
"""
        html = html.replace(
            '    </table>\n  </div>\n\n\n  <h2>Regression',
            f'    </table>\n  </div>\n{insert_after_table}\n  <h2>Regression',
        )

    if 'id="glossary-panel"' not in html:
        glossary_block = """
  <h2>Stat dictionary (glossary)</h2>
  <p class="sub" style="margin-top:0">Definitions for every shortlisted trait in the player explorer, plus outcome terms used on this page.</p>
  <div class="grid2">
    <div class="card">
      <h3>Outcomes &amp; methods</h3>
      <div id="glossary-outcomes"></div>
    </div>
    <div class="card">
      <h3>How to read percentiles</h3>
      <p style="font-size:13px;color:#444;line-height:1.5;margin-top:4px">
        <strong>PRE</strong> and <strong>Y1</strong> cells are percentiles 0–100 vs Bundesliga position peers in the cohort.
        <strong>50 = average</strong>, <strong>90 ≈ top decile</strong>. Stability <strong>r</strong> (on explorer metrics) is prior→Y1 rate correlation from Step 1 — separate from success-indicator ρ.
      </p>
    </div>
  </div>
  <div class="card" style="margin-top:14px">
    <h3>Shortlisted traits</h3>
    <div class="glossary-grid" id="glossary-panel"></div>
  </div>
"""
        html = html.replace(
            '\n  <footer>Bundesliga Transfer Traits',
            glossary_block + '\n  <footer>Bundesliga Transfer Traits',
        )

    return html


def patch_js(html: str) -> str:
    glossary_js = json.dumps(
        {"stats": STAT_DEFINITIONS, "outcomes": OUTCOME_DEFINITIONS},
        separators=(",", ":"),
    )

    if "const GLOSSARY" not in html:
        html = html.replace(
            "const viewLanding = document.getElementById('view-landing');",
            f"const GLOSSARY = {glossary_js};\n\nconst viewLanding = document.getElementById('view-landing');",
        )

    old_nav = """document.getElementById('btn-explore').onclick = ()=>{
  viewLanding.classList.add('hide');
  viewExplorer.classList.remove('hide');
  window.scrollTo(0,0);
};
document.getElementById('btn-back').onclick = ()=>{
  viewExplorer.classList.add('hide');
  viewLanding.classList.remove('hide');
  window.scrollTo(0,0);
};"""

    new_nav = """function switchView(view){
  const landing = view === 'landing';
  viewLanding.classList.toggle('hide', !landing);
  viewExplorer.classList.toggle('hide', landing);
  document.querySelectorAll('.top-nav .tab').forEach(t=>{
    t.classList.toggle('active', t.dataset.view === view);
  });
  history.replaceState(null, '', landing ? location.pathname : '#explore');
  window.scrollTo(0,0);
}
document.querySelectorAll('.top-nav .tab').forEach(t=>{
  t.onclick = ()=> switchView(t.dataset.view);
});
if (location.hash === '#explore') switchView('explorer');
else switchView('landing');"""

    if "function switchView" not in html:
        if old_nav in html:
            html = html.replace(old_nav, new_nav)
        else:
            html = html.replace(
                "const viewLanding = document.getElementById('view-landing');",
                "const viewLanding = document.getElementById('view-landing');\n" + new_nav,
            )

    # Remove old hash handler at bottom
    html = html.replace("\nif(location.hash==='#explore') document.getElementById('btn-explore').click();", "")

    # Enhance renderLanding with rho styling + glossary
    old_render_end = """  tbody.innerHTML = rows.map(r=>`<tr>
    <td>${r.category}</td>
    <td>${r.abbrev} — ${r.label}</td>
    <td><strong>${r.prior_league}</strong></td>
    <td>${(+r.spearman_r).toFixed(2)}</td>
    <td>${(+r.p_value).toFixed(3)}</td>
    <td>${r.n}</td>
  </tr>`).join('');"""

    new_render_end = """  const rhoClass = r => {
    const a = Math.abs(+r.spearman_r);
    if (a >= 0.3) return 'rho-strong';
    if (a >= 0.15) return 'rho-mod';
    return 'rho-weak';
  };
  tbody.innerHTML = rows.map(r=>`<tr>
    <td>${r.category}</td>
    <td>${r.abbrev} — ${r.label}</td>
    <td><strong>${r.prior_league}</strong></td>
    <td class="${rhoClass(r)}">${(+r.spearman_r).toFixed(2)}</td>
    <td class="${rhoClass(r)}">${(+r.p_value).toFixed(3)}${+r.p_value<0.05?'*':''}</td>
    <td>${r.n}</td>
  </tr>`).join('');"""

    if "const rhoClass" not in html and old_render_end in html:
        html = html.replace(old_render_end, new_render_end)

    glossary_render = """
  // Glossary
  const outEl = document.getElementById('glossary-outcomes');
  if (outEl && GLOSSARY) {
    outEl.innerHTML = GLOSSARY.outcomes.map(o=>`<div class="glossary-item"><div class="abbr">${o.term}</div><div class="def">${o.definition}</div></div>`).join('');
    const stats = Object.values(GLOSSARY.stats);
    const cats = ['Attacking','Passing','Carrying','Defending','Other'];
    const byCat = {};
    stats.forEach(s=>{ (byCat[s.category]=byCat[s.category]||[]).push(s); });
    document.getElementById('glossary-panel').innerHTML = cats.filter(c=>byCat[c]).map(c=>`
      <div class="glossary-cat"><h4>${c}</h4>
        ${byCat[c].map(s=>`<div class="glossary-item"><div class="abbr">${s.abbrev} — ${s.label}</div><div class="meta">${s.source}</div><div class="def">${s.definition}</div></div>`).join('')}
      </div>`).join('');
  }"""

    if "glossary-outcomes" not in html.split("function renderLanding")[1].split("renderLanding();")[0]:
        html = html.replace("}\nrenderLanding();", glossary_render + "\n}\nrenderLanding();")

    # Use glossary in explainer tooltip
    old_explain = """function showExplain(p,i,e){
  const m=p.metrics[i];
  const ex=document.getElementById('explainer'); ex.style.display='block';
  ex.querySelector('.t').textContent=m.abbrev+' — '+(m.label||m.key);
  ex.querySelector('.b').textContent='PRE '+fmt(m.prior)+' · Y1 '+fmt(m.player)+' · AVG '+fmt(m.avg)+' · TOP '+fmt(m.top);
  ex.querySelector('.s').textContent=m.stability_r!=null?'Stability r='+m.stability_r.toFixed(2):'';
  ex.style.left=Math.min(e.clientX+12,window.innerWidth-320)+'px';
  ex.style.top=Math.min(e.clientY+12,window.innerHeight-120)+'px';
}"""

    new_explain = """function statDef(m){
  if (!GLOSSARY) return '';
  const g = GLOSSARY.stats[m.key];
  return g ? g.definition : (m.label||'');
}
function showExplain(p,i,e){
  const m=p.metrics[i];
  const ex=document.getElementById('explainer'); ex.style.display='block';
  ex.querySelector('.t').textContent=m.abbrev+' — '+(m.label||m.key);
  ex.querySelector('.b').textContent=statDef(m);
  ex.querySelector('.s').textContent='PRE '+fmt(m.prior)+' · Y1 '+fmt(m.player)+' · AVG '+fmt(m.avg)+' · TOP '+fmt(m.top)
    +(m.stability_r!=null?' · Stability r='+m.stability_r.toFixed(2):'');
  ex.style.left=Math.min(e.clientX+12,window.innerWidth-320)+'px';
  ex.style.top=Math.min(e.clientY+12,window.innerHeight-140)+'px';
}"""

    if "function statDef" not in html:
        html = html.replace(old_explain, new_explain)

    return html


def main():
    html = EXPLORER.read_text()
    html = patch_css(html)
    html = patch_html_structure(html)
    html = patch_js(html)
    EXPLORER.write_text(html)
    print(f"Patched {EXPLORER}")


if __name__ == "__main__":
    main()
