#!/usr/bin/env python3
"""Rebuild final shortlists → pizzas/explorer → success p-values."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
DEC = ROOT / "decisions"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

from run_fbref_stability_expanded import (  # noqa: E402
    INVERT,
    is_already_rate,
    load_big5_wide,
    load_feeder_slim_rows,
    load_player_cache_rows,
)
from run_analysis import METRIC_META, CAT_COLOR  # noqa: E402


def percentile_of(value, peer_series: pd.Series) -> float:
    peer = peer_series.dropna().astype(float)
    if value is None or (isinstance(value, float) and np.isnan(value)) or len(peer) < 5:
        return np.nan
    return float((peer <= float(value)).mean() * 100.0)


def rate_val(row, metric: str, minutes: float) -> float:
    if metric not in row.index or pd.isna(row.get(metric, np.nan)):
        return np.nan
    v = float(row[metric])
    if not is_already_rate(metric):
        if not (np.isfinite(minutes) and minutes > 0 and np.isfinite(v)):
            return np.nan
        v = v / minutes * 90.0
    if metric in INVERT or re.search(r"^Mis_|^Dis_|^Err|Lost_|Tkld_", metric):
        v = -v
    return v


def rebuild_statsbomb_pizzas(shortlist: list[str]) -> dict:
    cohort = pd.read_csv(OUT / "cohort.csv")
    prior = pd.read_csv(OUT / "prior_p90.csv")
    y1 = pd.read_csv(OUT / "y1_p90.csv")
    peer = pd.read_csv(OUT / "peer_p90.csv")
    stab = pd.read_csv(OUT / "stability_all_metrics.csv").set_index("metric")

    prior_i = prior.set_index("player_id")
    y1_i = y1.set_index("player_id")

    score_rows = []
    players = []
    for _, r in cohort.iterrows():
        pid = int(r["player_id"])
        if pid not in y1_i.index or pid not in prior_i.index:
            continue
        yrow = y1_i.loc[pid]
        prow = prior_i.loc[pid]
        pcts = []
        metrics = []
        for m in shortlist:
            if m not in yrow.index:
                continue
            val = float(yrow[m])
            prior_val = float(prow[m])
            pct = percentile_of(val, peer[m]) if m in peer.columns else np.nan
            prior_pct = percentile_of(prior_val, peer[m]) if m in peer.columns else np.nan
            if pct == pct:
                pcts.append(pct)
            abb, cat, hint = METRIC_META[m]
            sr = stab.loc[m, "stability_r"] if m in stab.index else None
            metrics.append({
                "key": m,
                "abbrev": abb,
                "label": hint,
                "category": cat,
                "stability_r": None if sr is None or (isinstance(sr, float) and np.isnan(sr)) else round(float(sr), 4),
                "prior": None if prior_pct != prior_pct else round(prior_pct, 1),
                "player": None if pct != pct else round(pct, 1),
                "avg": 50.0,
                "top": 90.0,
            })
        score = float(np.nanmean(pcts)) if pcts else np.nan
        leagues = r["prior_leagues"]
        if isinstance(leagues, str):
            leagues = eval(leagues)
        primary = list(leagues.keys())[0] if leagues else None
        score_rows.append({
            "player_id": pid,
            "name": r["name"],
            "arrival_season": r["arrival_season"],
            "position": r["position"],
            "prior_minutes": r["prior_minutes"],
            "y1_minutes": r["y1_minutes"],
            "primary_source": primary,
            "n_pizza_metrics": len(pcts),
            "stable_trait_score": None if score != score else round(score, 2),
        })
        players.append({
            "id": pid,
            "name": r["name"],
            "position": r["position"],
            "arrival": r["arrival_season"],
            "sources": list(leagues.keys())[:3] if leagues else [],
            "national_team": None,
            "prior_minutes": r["prior_minutes"],
            "y1_minutes": r["y1_minutes"],
            "score": None if score != score else round(score, 2),
            "metrics": metrics,
        })

    scores = pd.DataFrame(score_rows).sort_values("stable_trait_score", ascending=False)
    scores.to_csv(OUT / "player_rankings_stable_traits.csv", index=False)

    payload = {
        "source": "StatsBomb open data",
        "cohort_n": len(cohort),
        "stability_gate": 0.40,
        "redundancy_gate": 0.85,
        "shortlist": shortlist,
        "n_shortlist": len(shortlist),
        "note": "Final shortlist: stability r≥0.40; redundancy |r|≥0.85 (passes retained).",
        "players_top15": scores.head(15).to_dict("records"),
    }
    (OUT / "analysis_payload.json").write_text(json.dumps(payload, indent=2))
    return {
        "source_id": "statsbomb",
        "source_label": "StatsBomb Open Data",
        "cohort_n": int(len(cohort)),
        "n_metrics": len(shortlist),
        "note": f"{len(shortlist)} traits · stability r≥0.40 · redundancy |r|≥0.85 (passes kept).",
        "players": players,
        "shortlist": shortlist,
    }


def rebuild_fbref_explorer(shortlist: list[str], stab_meta: pd.DataFrame) -> dict:
    pairs = pd.read_csv(OUT / "fbref_inbound_pairs.csv")
    print("  loading Big5 / feeder / player caches for explorer…")
    wide = load_big5_wide()
    feeder = load_feeder_slim_rows()
    players_cache = load_player_cache_rows()

    y1_map = {}
    for _, p in pairs.iterrows():
        sub = wide[
            (wide["player_id"] == p.player_id)
            & (wide["season_end"] == p.y1_season)
            & (wide["is_bl"])
        ]
        if sub.empty:
            sub = wide[(wide["player_id"] == p.player_id) & (wide["season_end"] == p.y1_season)]
        if sub.empty:
            continue
        y1_map[p.player_id] = sub.sort_values("minutes", ascending=False).iloc[0]

    def lookup_prior(p):
        pid, season, src = p.player_id, p.prior_season, p.prior_source
        if src == "big5":
            sub = wide[(wide.player_id == pid) & (wide.season_end == season) & (~wide.is_bl)]
            if len(sub):
                return sub.sort_values("minutes", ascending=False).iloc[0]
        nk = str(p.player).strip().lower()
        if len(feeder):
            sub = feeder[(feeder.name_key == nk) & (feeder.season_end == season)]
            if len(sub):
                return sub.sort_values("minutes", ascending=False).iloc[0]
        if len(players_cache):
            sub = players_cache[(players_cache.name_key == nk) & (players_cache.season_end == season)]
            if len(sub):
                return sub.sort_values("minutes", ascending=False).iloc[0]
        return None

    # Collect raw values first to build peer distributions
    rows = []
    for _, p in pairs.iterrows():
        if p.player_id not in y1_map:
            continue
        prow = lookup_prior(p)
        if prow is None:
            continue
        yrow = y1_map[p.player_id]
        item = {
            "player_id": p.player_id,
            "name": p.player,
            "prior_comp": p.prior_comp,
            "prior_source": p.prior_source,
            "prior_minutes": float(p.prior_minutes),
            "y1_minutes": float(p.y1_minutes),
            "y1_season": int(p.y1_season),
            "pos": p.pos if "pos" in p else "",
        }
        for m in shortlist:
            item[f"{m}_prior"] = rate_val(prow, m, float(p.prior_minutes))
            item[f"{m}_y1"] = rate_val(yrow, m, float(p.y1_minutes))
        rows.append(item)
    panel = pd.DataFrame(rows)
    print(f"  explorer panel players={len(panel)}")

    # Peer = all Y1 values in this inbound cohort
    peer = {m: panel[f"{m}_y1"] for m in shortlist}

    stab_i = stab_meta.set_index("metric")
    players_out = []
    for _, r in panel.iterrows():
        metrics = []
        pcts = []
        for m in shortlist:
            yv = r[f"{m}_y1"]
            pv = r[f"{m}_prior"]
            pct = percentile_of(yv, peer[m])
            prior_pct = percentile_of(pv, peer[m])  # prior on same BL Y1 scale (approx)
            if pct == pct:
                pcts.append(pct)
            meta = stab_i.loc[m] if m in stab_i.index else None
            metrics.append({
                "key": m,
                "abbrev": meta["abbrev"] if meta is not None else m[:5].upper(),
                "label": meta["label"] if meta is not None else m,
                "category": meta["category"] if meta is not None else "Other",
                "stability_r": round(float(meta["stability_r"]), 4) if meta is not None else None,
                "prior": None if prior_pct != prior_pct else round(prior_pct, 1),
                "player": None if pct != pct else round(pct, 1),
                "avg": 50.0,
                "top": 90.0,
            })
        score = float(np.nanmean(pcts)) if pcts else np.nan
        players_out.append({
            "id": r["player_id"],
            "name": r["name"],
            "position": r["pos"] or "Other",
            "arrival": str(r["y1_season"]),
            "sources": [str(r["prior_comp"])],
            "national_team": None,
            "prior_minutes": r["prior_minutes"],
            "y1_minutes": r["y1_minutes"],
            "score": None if score != score else round(score, 2),
            "metrics": metrics,
        })

    players_out.sort(key=lambda x: (x["score"] is not None, x["score"] or -1), reverse=True)
    payload = {
        "source": "FBref",
        "cohort_n": len(players_out),
        "n_leagues": 19,
        "shortlist": shortlist,
        "players": players_out,
    }
    (OUT / "fbref_explorer_players.json").write_text(json.dumps(payload))
    return {
        "source_id": "fbref",
        "source_label": "FBref (19 leagues)",
        "cohort_n": len(players_out),
        "n_metrics": len(shortlist),
        "note": (
            f"{len(shortlist)} traits · category gates Att/Pass/Other≥0.60 Def/Carry≥0.50 · "
            "redundancy |r|≥0.95."
        ),
        "players": players_out,
        "shortlist": shortlist,
    }


def sync_decisions(fb_short: list[str], sb_short: list[str], fb_dec: dict, sb_dec: dict) -> None:
    DEC.mkdir(exist_ok=True)
    stab = pd.read_csv(OUT / "fbref_stability_all_metrics.csv").set_index("metric")
    labels = []
    for m in fb_short:
        if m in stab.index:
            labels.append({
                "metric": m,
                "abbrev": stab.loc[m, "abbrev"],
                "label": stab.loc[m, "label"],
                "category": stab.loc[m, "category"],
                "stability_r": round(float(stab.loc[m, "stability_r"]), 4),
                "n_pairs": int(stab.loc[m, "n_pairs"]),
            })
    (DEC / "step2_fbref.json").write_text(json.dumps({
        "source": "FBref",
        "stability_gates": fb_dec["gates"],
        "redundancy_threshold": fb_dec["redundancy_gate"],
        "cohort_n": int(pd.read_csv(OUT / "fbref_inbound_pairs.csv").shape[0]),
        "n_passers": fb_dec["n_gated"],
        "shortlist": fb_short,
        "shortlist_labels": labels,
        "force_keep": fb_dec.get("force_keep", []),
        "dropped": fb_dec.get("dropped", []),
    }, indent=2))

    (DEC / "step2_decisions.json").write_text(json.dumps({
        "project": "bundesliga-transfer-traits",
        "statsbomb": {
            "cohort_n": sb_dec.get("n_passed_stability") and int(pd.read_csv(OUT / "cohort.csv").shape[0]),
            "stability_threshold": sb_dec["stability_gate"],
            "redundancy_threshold": sb_dec["redundancy_gate"],
            "final_shortlist": sb_short,
            "dropped": sb_dec.get("dropped", []),
            "note": sb_dec.get("note", ""),
        },
        "fbref": {
            "final_shortlist": fb_short,
            "gates": fb_dec["gates"],
            "redundancy_threshold": fb_dec["redundancy_gate"],
        },
    }, indent=2))


def patch_success_script() -> None:
    path = ROOT / "scripts" / "run_success_indicators.py"
    text = path.read_text()
    old = 'sb_dec = json.loads((ROOT / "decisions" / "step2_decisions.json").read_text())\n    shortlist = sb_dec["statsbomb"]["final_shortlist"]'
    new = (
        'sb_path = OUT / "statsbomb_step2_decisions.json"\n'
        '    if sb_path.exists():\n'
        '        sb_dec = json.loads(sb_path.read_text())\n'
        '        shortlist = sb_dec["auto_shortlist"]\n'
        '    else:\n'
        '        sb_dec = json.loads((ROOT / "decisions" / "step2_decisions.json").read_text())\n'
        '        shortlist = sb_dec["statsbomb"]["final_shortlist"]'
    )
    if old in text:
        path.write_text(text.replace(old, new))
        print("  patched run_success_indicators.py to read final SB shortlist")


def rebuild_explorer_html(sb_src: dict, fb_src: dict) -> None:
    path = ROOT / "interactive_player_explorer.html"
    html = path.read_text()
    sources = {"statsbomb": sb_src, "fbref": fb_src}
    payload = json.dumps(sources, separators=(",", ":"))
    # Replace const SOURCES = {...};
    m = re.search(r"const SOURCES = \{", html)
    if not m:
        raise SystemExit("SOURCES block not found in explorer HTML")
    start = m.start()
    # find matching end at `};` before next const
    i = m.end() - 1
    depth = 0
    end = None
    for j in range(i, len(html)):
        ch = html[j]
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = j + 1
                if html[end:end + 1] == ";":
                    end += 1
                break
    if end is None:
        raise SystemExit("could not find end of SOURCES")
    html = html[:start] + "const SOURCES = " + payload + ";" + html[end:]

    # Update hardcoded N labels in copy
    html = html.replace("StatsBomb (N=60)", f"StatsBomb (N={sb_src['cohort_n']})")
    html = html.replace("FBref (N=117)", f"FBref (N={fb_src['cohort_n']})")
    html = html.replace("FBref Big 5, N=117", f"FBref, N={fb_src['cohort_n']}")
    html = re.sub(
        r"Toggle <strong>StatsBomb</strong> \(N=\d+ · \d+ traits\) ↔ <strong>FBref</strong> \(N=\d+ · \d+ traits\)\.",
        f"Toggle <strong>StatsBomb</strong> (N={sb_src['cohort_n']} · {sb_src['n_metrics']} traits) ↔ "
        f"<strong>FBref</strong> (N={fb_src['cohort_n']} · {fb_src['n_metrics']} traits).",
        html,
    )
    path.write_text(html)
    print(f"  wrote {path.name} ({path.stat().st_size // 1024}KB)")


def main() -> None:
    fb_dec = json.loads((OUT / "fbref_step2_decisions.json").read_text())
    sb_dec = json.loads((OUT / "statsbomb_step2_decisions.json").read_text())
    fb_short = fb_dec["auto_shortlist"]
    sb_short = sb_dec["auto_shortlist"]
    stab_meta = pd.read_csv(OUT / "fbref_stability_all_metrics.csv")

    print("1) Sync decisions…")
    sync_decisions(fb_short, sb_short, fb_dec, sb_dec)

    print("2) Rebuild StatsBomb pizzas / rankings…")
    sb_src = rebuild_statsbomb_pizzas(sb_short)

    print("3) Rebuild FBref explorer players…")
    fb_src = rebuild_fbref_explorer(fb_short, stab_meta)

    print("4) Rebuild interactive explorer HTML…")
    rebuild_explorer_html(sb_src, fb_src)

    print("5) Patch + run success indicators…")
    patch_success_script()
    # inline success run to avoid import issues
    from run_success_indicators import main as success_main  # noqa: E402
    success_main()

    summary = {
        "fbref_n": fb_src["cohort_n"],
        "fbref_shortlist_n": len(fb_short),
        "statsbomb_n": sb_src["cohort_n"],
        "statsbomb_shortlist_n": len(sb_short),
        "fbref_shortlist": fb_short,
        "statsbomb_shortlist": sb_short,
    }
    (OUT / "final_deliverable_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    print("DONE finalize")


if __name__ == "__main__":
    main()
