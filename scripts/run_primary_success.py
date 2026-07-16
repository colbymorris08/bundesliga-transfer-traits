#!/usr/bin/env python3
"""Phase-2 success: pre-specified primary traits × overall cohort only.

Design choices for better-powered, honest inference:
  - Bigger N via lower minute gate on Big-5 cache (see run_fbref_stability.R)
  - No league×trait slicing (burns n)
  - 5 primary traits only + Benjamini–Hochberg FDR

Requires: results/fbref_primary_trait_panel.csv (from R rebuild)
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"

PRIMARY = [
    "Lost_Aerial",
    "Final_Third",
    "Sh_Blocks",
    "Def_Pen_Touches",
    "Won_percent_Aerial",
]

LABELS = {
    "Lost_Aerial": "Lost Aerial (inverted — fewer losses = higher)",
    "Final_Third": "Final Third passes",
    "Sh_Blocks": "Shot Blocks",
    "Def_Pen_Touches": "Defensive penalty-area touches",
    "Won_percent_Aerial": "Aerial win %",
}


def bh_adjust(pvals: list[float]) -> list[float]:
    """Benjamini–Hochberg FDR q-values."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    q = ranked * n / (np.arange(1, n + 1))
    # enforce monotonicity from the back
    q_rev = np.minimum.accumulate(q[::-1])[::-1]
    out = np.empty(n)
    out[order] = np.clip(q_rev, 0, 1)
    return [round(float(x), 4) for x in out]


def main():
    panel_path = OUT / "fbref_primary_trait_panel.csv"
    if not panel_path.exists():
        raise SystemExit(
            f"Missing {panel_path}. Re-run: Rscript scripts/run_fbref_stability.R"
        )
    df = pd.read_csv(panel_path)
    n = len(df)
    rows = []
    for trait in PRIMARY:
        col = f"{trait}_prior"
        if col not in df.columns:
            continue
        # percentile of prior rate within cohort (simple rank — enough for Spearman)
        prior = df[col]
        prior_pct = prior.rank(pct=True) * 100
        ok = prior_pct.notna() & df["y1_minutes"].notna()
        nn = int(ok.sum())
        if nn < 20:
            r, p = np.nan, np.nan
        else:
            r, p = stats.spearmanr(prior_pct[ok], df.loc[ok, "y1_minutes"])
        rows.append({
            "trait": trait,
            "label": LABELS.get(trait, trait),
            "n": nn,
            "spearman_r": round(float(r), 4) if r == r else None,
            "p_value": round(float(p), 4) if p == p else None,
        })

    out = pd.DataFrame(rows)
    out["q_value_bh"] = bh_adjust([r["p_value"] if r["p_value"] is not None else 1.0 for r in rows])
    out["significant_fdr_05"] = out["q_value_bh"] < 0.05
    out = out.sort_values("p_value")
    out.to_csv(OUT / "primary_success_traits.csv", index=False)

    # League means (descriptive only — not sliced trait tests)
    league = (
        df.groupby("prior_comp", dropna=False)
        .agg(n=("y1_minutes", "size"), mean_y1_minutes=("y1_minutes", "mean"), median_y1_minutes=("y1_minutes", "median"))
        .reset_index()
        .sort_values("mean_y1_minutes", ascending=False)
    )
    league["mean_y1_minutes"] = league["mean_y1_minutes"].round(1)
    league["median_y1_minutes"] = league["median_y1_minutes"].round(1)
    league.to_csv(OUT / "primary_success_league_means.csv", index=False)

    summary = {
        "design": {
            "cohort_n": int(n),
            "tests": "5 pre-specified traits × Y1 minutes (overall only)",
            "multiple_testing": "Benjamini–Hochberg FDR on the 5 p-values",
            "not_done": "No league×trait Spearman grid (underpowered)",
        },
        "traits": out.to_dict("records"),
        "league_means_head": league.head(8).to_dict("records"),
        "headline": _headline(out, n),
    }
    (OUT / "primary_success_summary.json").write_text(json.dumps(summary, indent=2))

    md = [
        "# Primary success analysis (powered design)",
        "",
        f"**N = {n}** inbound pairs · **5 pre-specified traits** · overall cohort only · BH FDR",
        "",
        "| Trait | ρ | p | q (BH) | sig FDR 0.05 | n |",
        "|---|---:|---:|---:|:---:|---:|",
    ]
    for _, r in out.iterrows():
        md.append(
            f"| {r['label']} | {r['spearman_r']} | {r['p_value']} | {r['q_value_bh']} | "
            f"{'yes' if r['significant_fdr_05'] else 'no'} | {int(r['n'])} |"
        )
    md += [
        "",
        "## League means (descriptive only)",
        "",
        "| Prior competition | n | Mean Y1 min | Median Y1 min |",
        "|---|---:|---:|---:|",
    ]
    for _, r in league.head(10).iterrows():
        md.append(f"| {r['prior_comp']} | {int(r['n'])} | {r['mean_y1_minutes']} | {r['median_y1_minutes']} |")
    md += ["", f"**Headline:** {summary['headline']}", ""]
    (OUT / "PRIMARY_SUCCESS.md").write_text("\n".join(md))
    print("\n".join(md))


def _headline(out: pd.DataFrame, n: int) -> str:
    sig = out[out["significant_fdr_05"]]
    if len(sig):
        tops = ", ".join(f"{r.label} (ρ={r.spearman_r}, q={r.q_value_bh})" for r in sig.itertuples())
        return f"N={n}: FDR-significant — {tops}"
    best = out.iloc[0]
    return f"N={n}: none FDR-significant at 0.05; strongest {best.label} ρ={best.spearman_r} p={best.p_value} q={best.q_value_bh}"


if __name__ == "__main__":
    main()
