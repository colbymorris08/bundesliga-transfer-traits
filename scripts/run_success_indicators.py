#!/usr/bin/env python3
"""Which prior traits and source leagues are most indicative of BL Year-1 success?

Outcomes (BL success proxies):
  - y1_minutes: Bundesliga Year-1 minutes played
  - y1_minutes_pct: percentile of y1_minutes within cohort
  - stable_trait_score: mean Y1 percentile on Step-2 shortlist traits

Methods:
  - Trait: Spearman r (prior trait vs outcome); rank traits by |r|
  - League: cohort mean outcomes by prior league; FBref also reports median

Outputs under results/ — see SUCCESS_INDICATORS.md
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)


def percentile_of(value, peer_series: pd.Series) -> float:
    peer = peer_series.dropna().astype(float)
    if value is None or (isinstance(value, float) and np.isnan(value)) or len(peer) < 5:
        return np.nan
    return float((peer <= float(value)).mean() * 100.0)


def spearman_row(prior: pd.Series, outcome: pd.Series) -> dict:
    ok = prior.notna() & outcome.notna()
    n = int(ok.sum())
    if n < 8:
        return {"n": n, "spearman_r": np.nan, "p_value": np.nan}
    r, p = stats.spearmanr(prior[ok], outcome[ok])
    return {"n": n, "spearman_r": round(float(r), 4), "p_value": round(float(p), 4)}


def run_statsbomb() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    sb_path = OUT / "statsbomb_step2_decisions.json"
    if sb_path.exists():
        sb_dec = json.loads(sb_path.read_text())
        shortlist = sb_dec["auto_shortlist"]
    else:
        sb_dec = json.loads((ROOT / "decisions" / "step2_decisions.json").read_text())
        shortlist = sb_dec["statsbomb"]["final_shortlist"]

    cohort = pd.read_csv(OUT / "cohort.csv")
    prior = pd.read_csv(OUT / "prior_p90.csv").set_index("player_id")
    y1 = pd.read_csv(OUT / "y1_p90.csv").set_index("player_id")
    peer = pd.read_csv(OUT / "peer_p90.csv")
    rankings = pd.read_csv(OUT / "player_rankings_stable_traits.csv")

    # primary source per player
    def primary_source(row):
        d = eval(row["prior_leagues"]) if isinstance(row["prior_leagues"], str) else row["prior_leagues"]
        if not d:
            return None
        return max(d.items(), key=lambda x: x[1])[0]

    cohort["primary_source"] = cohort.apply(primary_source, axis=1)
    mins_map = dict(zip(rankings["player_id"], rankings["y1_minutes"]))
    score_map = dict(zip(rankings["player_id"], rankings["stable_trait_score"]))
    cohort["y1_minutes"] = cohort["player_id"].map(mins_map)
    cohort["stable_trait_score"] = cohort["player_id"].map(score_map)
    cohort["y1_minutes_pct"] = cohort["y1_minutes"].rank(pct=True) * 100

    trait_rows = []
    for m in shortlist:
        if m not in prior.columns:
            continue
        prior_vals = cohort["player_id"].map(prior[m])
        prior_pct = pd.Series(
            [percentile_of(v, peer[m]) if m in peer.columns else np.nan for v in prior_vals],
            index=cohort.index,
        )
        for outcome_name, outcome in [
            ("y1_minutes", cohort["y1_minutes"]),
            ("y1_minutes_pct", cohort["y1_minutes_pct"]),
            ("stable_trait_score", cohort["stable_trait_score"]),
        ]:
            s = spearman_row(prior_pct, outcome)
            meta = pd.read_csv(OUT / "stability_all_metrics.csv")
            row_meta = meta[meta["metric"] == m]
            trait_rows.append({
                "source": "statsbomb",
                "metric": m,
                "abbrev": row_meta["abbrev"].iloc[0] if len(row_meta) else m[:4].upper(),
                "label": row_meta["label"].iloc[0] if len(row_meta) else m,
                "category": row_meta["category"].iloc[0] if len(row_meta) else "",
                "outcome": outcome_name,
                **s,
                "interpretation": "Higher prior percentile → higher BL success" if s.get("spearman_r", 0) and s["spearman_r"] > 0 else "See sign",
            })

    trait_df = pd.DataFrame(trait_rows).sort_values(["outcome", "spearman_r"], ascending=[True, False], key=lambda c: c.abs() if c.name == "spearman_r" else c)

    league_rows = []
    for league, sub in cohort.groupby("primary_source"):
        league_rows.append({
            "source": "statsbomb",
            "prior_league": league,
            "n_players": len(sub),
            "mean_y1_minutes": round(float(sub["y1_minutes"].mean()), 1),
            "median_y1_minutes": round(float(sub["y1_minutes"].median()), 1),
            "mean_stable_trait_score": round(float(sub["stable_trait_score"].mean()), 2),
            "mean_y1_minutes_pct": round(float(sub["y1_minutes_pct"].mean()), 1),
        })
    league_df = pd.DataFrame(league_rows).sort_values("mean_stable_trait_score", ascending=False)

    summary = {
        "source": "statsbomb",
        "cohort_n": len(cohort),
        "outcomes": ["y1_minutes", "y1_minutes_pct", "stable_trait_score"],
        "method": "Spearman correlation: prior-season trait percentile vs BL success proxy",
        "top_traits_y1_minutes": trait_df[trait_df.outcome == "y1_minutes"].head(5)[["abbrev", "spearman_r", "p_value"]].to_dict("records"),
        "top_leagues": league_df.head(5)[["prior_league", "n_players", "mean_y1_minutes", "mean_stable_trait_score"]].to_dict("records"),
    }
    return trait_df, league_df, pd.DataFrame(), summary


def _scalar(x):
    """Unbox R/jsonlite list-wrapped scalars."""
    if isinstance(x, list):
        return x[0] if x else None
    return x


def run_fbref() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    fb = json.loads((OUT / "fbref_explorer_players.json").read_text())
    shortlist = fb["shortlist"]
    players = fb["players"]

    rows = []
    for p in players:
        pid = _scalar(p["id"])
        name = _scalar(p["name"])
        league = _scalar((p.get("sources") or ["Unknown"])[0])
        y1_min = p.get("y1_minutes")
        score = p.get("score")
        for m in p.get("metrics") or []:
            rows.append({
                "player_id": pid,
                "name": name,
                "prior_league": league,
                "y1_minutes": y1_min,
                "stable_trait_score": score,
                "metric": _scalar(m["key"]),
                "abbrev": _scalar(m.get("abbrev")),
                "label": _scalar(m.get("label")),
                "category": _scalar(m.get("category")),
                "prior_pct": m.get("prior"),
                "y1_pct": m.get("player"),
            })

    long_df = pd.DataFrame(rows)
    player_mins = long_df.drop_duplicates("player_id")[["player_id", "y1_minutes"]].copy()
    player_mins["y1_minutes_pct"] = player_mins["y1_minutes"].rank(pct=True) * 100
    long_df = long_df.merge(player_mins[["player_id", "y1_minutes_pct"]], on="player_id", how="left")

    trait_rows = []
    for m in shortlist:
        sub = long_df[long_df["metric"] == m]
        if sub.empty:
            continue
        for outcome_name, col in [
            ("y1_minutes", "y1_minutes"),
            ("y1_minutes_pct", "y1_minutes_pct"),
            ("stable_trait_score", "stable_trait_score"),
        ]:
            s = spearman_row(sub["prior_pct"], sub[col])
            info = sub.iloc[0]
            trait_rows.append({
                "source": "fbref",
                "metric": m,
                "abbrev": info["abbrev"],
                "label": info["label"],
                "category": info["category"],
                "outcome": outcome_name,
                **s,
            })

    trait_df = pd.DataFrame(trait_rows).sort_values(["outcome", "spearman_r"], ascending=[True, False], key=lambda c: c.abs() if c.name == "spearman_r" else c)

    player_df = long_df.drop_duplicates("player_id")
    league_rows = []
    for league, sub in player_df.groupby("prior_league"):
        league_rows.append({
            "source": "fbref",
            "prior_league": league,
            "n_players": len(sub),
            "mean_y1_minutes": round(float(sub["y1_minutes"].mean()), 1),
            "median_y1_minutes": round(float(sub["y1_minutes"].median()), 1),
            "mean_stable_trait_score": round(float(sub["stable_trait_score"].mean()), 2),
            "mean_y1_minutes_pct": round(float(sub["y1_minutes_pct"].mean()), 1),
        })
    league_df = pd.DataFrame(league_rows).sort_values("mean_y1_minutes", ascending=False)

    # League × trait: which feeder league best predicts Y1 minutes for each trait?
    league_trait_rows = []
    for m in shortlist:
        sub = long_df[long_df["metric"] == m]
        if sub.empty:
            continue
        info = sub.iloc[0]
        best = None
        for league, g in sub.groupby("prior_league"):
            if len(g) < 8:
                continue
            r, p = stats.spearmanr(g["prior_pct"], g["y1_minutes"])
            if not np.isfinite(r):
                continue
            row = {
                "metric": m,
                "abbrev": info["abbrev"],
                "label": info["label"],
                "category": info["category"],
                "prior_league": league,
                "n": len(g),
                "spearman_r": round(float(r), 4),
                "p_value": round(float(p), 4),
            }
            league_trait_rows.append(row)
            if best is None or r > best["spearman_r"]:
                best = row
        if best:
            best = dict(best)
            best["is_best_league_for_trait"] = True

    league_trait_df = pd.DataFrame(league_trait_rows)
    if not league_trait_df.empty:
        # mark best per trait
        league_trait_df["is_best_league_for_trait"] = False
        for m in shortlist:
            sub = league_trait_df[league_trait_df["metric"] == m]
            if sub.empty:
                continue
            pos = sub[sub["spearman_r"] == sub["spearman_r"].max()]
            league_trait_df.loc[pos.index, "is_best_league_for_trait"] = True

    summary = {
        "source": "fbref",
        "cohort_n": len(player_df),
        "outcomes": ["y1_minutes", "y1_minutes_pct", "stable_trait_score"],
        "method": "Spearman correlation: prior-season trait percentile vs BL success proxy",
        "top_traits_y1_minutes": trait_df[trait_df.outcome == "y1_minutes"].head(5)[["abbrev", "spearman_r", "p_value"]].to_dict("records"),
        "top_leagues": league_df[["prior_league", "n_players", "mean_y1_minutes", "mean_stable_trait_score"]].to_dict("records"),
        "league_trait_best": league_trait_df[league_trait_df.get("is_best_league_for_trait", False) == True].to_dict("records") if not league_trait_df.empty else [],
    }
    return trait_df, league_df, league_trait_df, summary


def write_md(sb_trait, sb_league, sb_sum, fb_trait, fb_league, fb_league_trait, fb_sum) -> None:
    lines = [
        "# Success indicators — traits & leagues vs Bundesliga Year-1",
        "",
        "## Method (Phase 2 · descriptive prediction)",
        "",
        "After stability/redundancy, we ask: **which prior traits and feeder leagues line up with BL success?**",
        "",
        "**BL success proxies (outcomes):**",
        "- `y1_minutes` — Year-1 Bundesliga minutes (playing-time success)",
        "- `y1_minutes_pct` — percentile of Y1 minutes within inbound cohort",
        "- `stable_trait_score` — mean Y1 percentile on Step-2 shortlist traits",
        "",
        "**Trait test:** Spearman ρ between **prior-season trait percentile** (vs BL position peers) and each outcome.",
        "",
        "**League test:** Mean/median outcomes by **prior league** (Big 5 for FBref; primary prior comp for StatsBomb).",
        "",
        "This is **associative / indicative** — not a validated forecast model. Small-N leagues are directional only.",
        "",
        "---",
        "",
        "## StatsBomb (N={})".format(sb_sum["cohort_n"]),
        "",
        "### Top prior traits → Y1 minutes",
        "",
        "| Abbrev | ρ | p | n |",
        "|---|---:|---:|---:|",
    ]
    for _, r in sb_trait[sb_trait.outcome == "y1_minutes"].head(8).iterrows():
        lines.append(f"| {r['abbrev']} | {r['spearman_r']:.3f} | {r['p_value']:.3f} | {int(r['n'])} |")

    lines += ["", "### Source leagues → BL success", "", "| League | N | Mean Y1 min | Mean trait score |", "|---|---:|---:|---:|"]
    for _, r in sb_league.iterrows():
        lines.append(f"| {r['prior_league']} | {int(r['n_players'])} | {r['mean_y1_minutes']} | {r['mean_stable_trait_score']} |")

    lines += [
        "",
        "---",
        "",
        "## FBref Big 5 (N={})".format(fb_sum["cohort_n"]),
        "",
        "### Top prior traits → Y1 minutes",
        "",
        "| Abbrev | Label | ρ | p | n |",
        "|---|---|---:|---:|---:|",
    ]
    for _, r in fb_trait[fb_trait.outcome == "y1_minutes"].head(10).iterrows():
        lines.append(f"| {r['abbrev']} | {r['label']} | {r['spearman_r']:.3f} | {r['p_value']:.3f} | {int(r['n'])} |")

    lines += ["", "### Source leagues → BL success", "", "| League | N | Mean Y1 min | Median Y1 min | Mean trait score |", "|---|---:|---:|---:|---:|"]
    for _, r in fb_league.iterrows():
        lines.append(
            f"| {r['prior_league']} | {int(r['n_players'])} | {r['mean_y1_minutes']} | {r['median_y1_minutes']} | {r['mean_stable_trait_score']} |"
        )

    if not fb_league_trait.empty:
        lines += [
            "",
            "### Which league is most predictive per trait? (FBref)",
            "",
            "Within each Big-5 feeder, Spearman ρ(prior trait percentile → Y1 minutes). **Best league** = highest ρ for that trait.",
            "",
            "| Trait | Best league | ρ | p | n |",
            "|---|---|---:|---:|---:|",
        ]
        best = fb_league_trait[fb_league_trait["is_best_league_for_trait"] == True].sort_values("spearman_r", ascending=False)
        for _, r in best.head(15).iterrows():
            lines.append(
                f"| {r['abbrev']} — {r['label']} | {r['prior_league']} | {r['spearman_r']:.3f} | {r['p_value']:.3f} | {int(r['n'])} |"
            )

    (OUT / "SUCCESS_INDICATORS.md").write_text("\n".join(lines) + "\n")


def main():
    sb_trait, sb_league, _, sb_sum = run_statsbomb()
    fb_trait, fb_league, fb_league_trait, fb_sum = run_fbref()

    sb_trait.to_csv(OUT / "success_trait_indicators_statsbomb.csv", index=False)
    sb_league.to_csv(OUT / "success_league_indicators_statsbomb.csv", index=False)
    fb_trait.to_csv(OUT / "success_trait_indicators_fbref.csv", index=False)
    fb_league.to_csv(OUT / "success_league_indicators_fbref.csv", index=False)
    if not fb_league_trait.empty:
        fb_league_trait.to_csv(OUT / "success_league_trait_fbref.csv", index=False)

    payload = {"statsbomb": sb_sum, "fbref": fb_sum}
    (OUT / "success_indicators_summary.json").write_text(json.dumps(payload, indent=2))

    write_md(sb_trait, sb_league, sb_sum, fb_trait, fb_league, fb_league_trait, fb_sum)

    print("StatsBomb top traits (y1_minutes):")
    print(sb_trait[sb_trait.outcome == "y1_minutes"].head(5).to_string(index=False))
    print("\nFBref top traits (y1_minutes):")
    print(fb_trait[fb_trait.outcome == "y1_minutes"].head(5).to_string(index=False))
    print("\nFBref leagues:")
    print(fb_league.to_string(index=False))


if __name__ == "__main__":
    main()
