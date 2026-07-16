#!/usr/bin/env python3
"""Regression explaining why feeder leagues differ on BL Year-1 success (FBref N=117).

Models (player-level):
  M1: y1_minutes ~ prior_league dummies + prior_minutes (+ position bucket)
  M2: stable_trait_score ~ prior_league dummies + prior_minutes
  M3: y1_minutes ~ prior_league + key prior trait percentiles (mediation-style)

Reference league: Serie A (lowest mean Y1 minutes in descriptive table).

Outputs: results/feeder_regression_*.csv, FEEDER_REGRESSION.md, feeder_regression_summary.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
REF_LEAGUE = "Serie A"

KEY_TRAITS = [
    "Final_Third",
    "Def_Pen_Touches",
    "Lost_Aerial",
    "Sh_Blocks",
    "PrgDist_Total",
    "xG_Per",
]


def _scalar(x):
    if isinstance(x, list):
        return x[0] if x else None
    return x


def load_fbref_players() -> pd.DataFrame:
    fb = json.loads((OUT / "fbref_explorer_players.json").read_text())
    rows = []
    for p in fb["players"]:
        league = _scalar((p.get("sources") or ["Unknown"])[0])
        rows.append({
            "player_id": _scalar(p["id"]),
            "name": _scalar(p["name"]),
            "position": _scalar(p.get("position")),
            "prior_league": league,
            "prior_minutes": p.get("prior_minutes"),
            "y1_minutes": p.get("y1_minutes"),
            "stable_trait_score": p.get("score"),
        })
    base = pd.DataFrame(rows)

    # wide trait priors
    trait_rows = []
    for p in fb["players"]:
        pid = _scalar(p["id"])
        for m in p.get("metrics") or []:
            key = _scalar(m["key"])
            trait_rows.append({
                "player_id": pid,
                "metric": key,
                "prior_pct": m.get("prior"),
            })
    traits = pd.DataFrame(trait_rows)
    wide = traits.pivot_table(index="player_id", columns="metric", values="prior_pct", aggfunc="first")
    wide.columns = [f"prior_{c}" for c in wide.columns]
    df = base.merge(wide, left_on="player_id", right_index=True, how="left")
    return df


def pos_bucket(p) -> str:
    p = str(p or "").upper()
    if "GK" in p:
        return "GK"
    if any(x in p for x in ["DF", "CB", "FB", "WB", "LB", "RB", "DEF"]):
        return "DF"
    if any(x in p for x in ["MF", "CM", "DM", "AM", "MID"]):
        return "MF"
    if any(x in p for x in ["FW", "ST", "CF", "LW", "RW", "ATT", "WING"]):
        return "FW"
    return "Other"


def fit_ols(y: pd.Series, X: pd.DataFrame):
    X = sm.add_constant(X.astype(float))
    ok = y.notna() & X.notna().all(axis=1)
    model = sm.OLS(y[ok], X[ok]).fit()
    return model


def league_dummies(df: pd.DataFrame, ref: str = REF_LEAGUE) -> pd.DataFrame:
    d = pd.get_dummies(df["prior_league"], prefix="lg", dtype=float)
    ref_col = f"lg_{ref}"
    if ref_col in d.columns:
        d = d.drop(columns=[ref_col])
    return d


def model_table(model, prefix: str = "lg_") -> pd.DataFrame:
    rows = []
    for name, coef in model.params.items():
        if name == "const":
            continue
        se = model.bse[name]
        p = model.pvalues[name]
        rows.append({
            "term": name.replace("lg_", "").replace("prior_", "").replace("_", " "),
            "coef": round(float(coef), 2),
            "se": round(float(se), 2),
            "p_value": round(float(p), 4),
            "significant_05": bool(p < 0.05),
        })
    return pd.DataFrame(rows)


def main():
    df = load_fbref_players()
    df["pos_bucket"] = df["position"].map(pos_bucket)
    df["y1_minutes_pct"] = df["y1_minutes"].rank(pct=True) * 100

    # --- M1: Y1 minutes ~ league + prior minutes + position ---
    X1 = pd.concat([league_dummies(df), df[["prior_minutes"]], pd.get_dummies(df["pos_bucket"], prefix="pos", dtype=float)], axis=1)
    m1 = fit_ols(df["y1_minutes"], X1)

    # --- M2: stable trait score ~ league + prior minutes ---
    X2 = pd.concat([league_dummies(df), df[["prior_minutes"]]], axis=1)
    m2 = fit_ols(df["stable_trait_score"], X2)

    # --- M3: Y1 minutes ~ league + key trait priors ---
    trait_cols = [f"prior_{t}" for t in KEY_TRAITS if f"prior_{t}" in df.columns]
    X3 = pd.concat([league_dummies(df), df[trait_cols], df[["prior_minutes"]]], axis=1)
    m3 = fit_ols(df["y1_minutes"], X3)

    # --- M4: holdout sanity (80/20) predict y1_minutes from league + traits ---
    rng = np.random.default_rng(42)
    idx = np.arange(len(df))
    rng.shuffle(idx)
    split = int(0.8 * len(df))
    train, test = idx[:split], idx[split:]
    X4 = pd.concat([league_dummies(df), df[trait_cols], df[["prior_minutes"]]], axis=1)
    X4 = sm.add_constant(X4.astype(float))
    ok = df["y1_minutes"].notna() & X4.notna().all(axis=1)
    train_ok = ok.iloc[train] if hasattr(ok, "iloc") else ok[train]
    m4_train = sm.OLS(df["y1_minutes"].iloc[train][train_ok], X4.iloc[train][train_ok]).fit()
    test_ok = ok.iloc[test]
    y_pred = m4_train.predict(X4.iloc[test][test_ok])
    y_true = df["y1_minutes"].iloc[test][test_ok]
    holdout_r = float(np.corrcoef(y_pred, y_true)[0, 1]) if len(y_true) > 3 else np.nan

    # Save coefficient tables
    t1 = model_table(m1)
    t1["model"] = "M1_y1_minutes_league"
    t2 = model_table(m2)
    t2["model"] = "M2_trait_score_league"
    t3 = model_table(m3)
    t3["model"] = "M3_y1_minutes_league_plus_traits"
    coef_all = pd.concat([t1, t2, t3], ignore_index=True)
    coef_all.to_csv(OUT / "feeder_regression_coefficients.csv", index=False)

    league_coefs = t1[t1["term"].isin(["Ligue 1", "Premier League", "La Liga"])].copy()
    league_coefs.to_csv(OUT / "feeder_regression_league_effects.csv", index=False)

    summary = {
        "reference_league": REF_LEAGUE,
        "cohort_n": int(len(df)),
        "models": {
            "M1_y1_minutes": {
                "formula": f"y1_minutes ~ prior_league (ref={REF_LEAGUE}) + prior_minutes + position",
                "r_squared": round(float(m1.rsquared), 3),
                "adj_r_squared": round(float(m1.rsquared_adj), 3),
                "n": int(m1.nobs),
                "league_effects_minutes": league_coefs.to_dict("records"),
                "interpretation": "Positive coef = more Y1 minutes vs Serie A baseline, holding minutes & position.",
            },
            "M2_trait_score": {
                "formula": f"stable_trait_score ~ prior_league (ref={REF_LEAGUE}) + prior_minutes",
                "r_squared": round(float(m2.rsquared), 3),
                "adj_r_squared": round(float(m2.rsquared_adj), 3),
                "n": int(m2.nobs),
            },
            "M3_mediation": {
                "formula": f"y1_minutes ~ prior_league + prior traits ({', '.join(KEY_TRAITS[:4])}...) + prior_minutes",
                "r_squared": round(float(m3.rsquared), 3),
                "adj_r_squared": round(float(m3.rsquared_adj), 3),
                "n": int(m3.nobs),
                "interpretation": "If league coefs shrink vs M1, traits partially explain feeder-league gaps.",
            },
            "M4_holdout": {
                "formula": "80/20 split · predict y1_minutes from league + traits",
                "holdout_r": round(holdout_r, 3) if holdout_r == holdout_r else None,
                "note": "Exploratory next-phase check — not a production forecast.",
            },
        },
        "headline": _headline(league_coefs, t1, t3),
    }
    (OUT / "feeder_regression_summary.json").write_text(json.dumps(summary, indent=2))

    md = _write_md(summary, m1, m2, m3, league_coefs, t3, holdout_r)
    (OUT / "FEEDER_REGRESSION.md").write_text(md)

    print(md)
    print("\nWrote", OUT / "feeder_regression_summary.json")


def _headline(league_coefs, t1, t3) -> str:
    parts = []
    sig = league_coefs[league_coefs["significant_05"]]
    if len(sig):
        top = sig.sort_values("coef", ascending=False).iloc[0]
        parts.append(f"{top['term']} +{top['coef']:.0f} Y1 minutes vs {REF_LEAGUE} (p={top['p_value']:.3f})")
    # M1 vs M3 league coef change for Ligue 1
    l1_m1 = t1[t1["term"] == "Ligue 1"]
    l1_m3 = t3[t3["term"] == "Ligue 1"]
    if len(l1_m1) and len(l1_m3):
        shrink = l1_m1.iloc[0]["coef"] - l1_m3.iloc[0]["coef"]
        if abs(shrink) > 20:
            parts.append(f"Ligue 1 advantage partly explained by prior trait profile (coef shrinks {shrink:.0f} min when traits added)")
    return "; ".join(parts) if parts else "League differences modest after controls."


def _write_md(summary, m1, m2, m3, league_coefs, t3, holdout_r) -> str:
    lines = [
        "# Feeder league regression — why some leagues look “best”",
        "",
        "## Next phase (this analysis)",
        "",
        "Descriptive “best feeder” rankings are not enough — we run **OLS regression** to estimate",
        f"how much each Big-5 league adds on BL outcomes vs **{REF_LEAGUE}** (reference), controlling for",
        "prior minutes and (where available) position and prior trait percentiles.",
        "",
        "This is the bridge to full prediction: same features could enter train/test ML later.",
        "",
        f"**Headline:** {summary['headline']}",
        "",
        "---",
        "",
        "## M1 · Y1 minutes ~ feeder league + controls",
        "",
        f"- R² = {m1.rsquared:.3f} · adj R² = {m1.rsquared_adj:.3f} · n = {int(m1.nobs)}",
        "",
        "| League (vs Serie A) | Δ Y1 minutes | p |",
        "|---|---:|---:|",
    ]
    for _, r in league_coefs.iterrows():
        sig = "*" if r["significant_05"] else ""
        lines.append(f"| {r['term']}{sig} | {r['coef']:+.0f} | {r['p_value']:.3f} |")

    lines += [
        "",
        "Positive = more Year-1 minutes than Serie A arrivals, holding prior minutes & position.",
        "",
        "## M2 · Stable-trait score ~ feeder league",
        "",
        f"- R² = {m2.rsquared:.3f} · adj R² = {m2.rsquared_adj:.3f}",
        "",
        "## M3 · Do prior traits explain the league gap?",
        "",
        f"- R² = {m3.rsquared:.3f} · adj R² = {m3.rsquared_adj:.3f}",
        "",
        "Key prior trait coefficients (standardized direction):",
        "",
        "| Prior trait pct | Δ Y1 minutes | p |",
        "|---|---:|---:|",
    ]
    trait_terms = t3[~t3["term"].isin(["Ligue 1", "Premier League", "La Liga", "prior minutes"])]
    for _, r in trait_terms.head(8).iterrows():
        lines.append(f"| {r['term']} | {r['coef']:+.0f} | {r['p_value']:.3f} |")

    lines += [
        "",
        "If league dummy coefficients **shrink** from M1 → M3, those traits partially mediate feeder-league differences.",
        "",
        "## M4 · Holdout check (exploratory)",
        "",
        f"- 80/20 split · holdout correlation(pred, actual Y1 minutes) = **{holdout_r:.3f}**" if holdout_r == holdout_r else "- Holdout not computed",
        "",
        "Not a validated forecast — shows feasibility of Phase-3 ML.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
