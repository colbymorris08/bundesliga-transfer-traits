"""Regional subset analysis — MENA, Latin America, and great-power competition.

Runs the model on regional subsets to identify region-specific dynamics:
  1. MENA + Persian sphere — ties to Iran/Afghanistan intelligence priority
  2. Latin America — great-power competition (China/Russia influence)
  3. Comparison of predictive power across regions
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, brier_score_loss

OUT = Path(__file__).resolve().parent / "output"

REGIONS: dict[str, dict] = {
    "MENA + Persian Sphere": {
        "countries": [
            "TUR", "ISR", "IRN", "IRQ", "SYR", "LBN", "JOR", "EGY",
            "SAU", "ARE", "KWT", "QAT", "BHR", "OMN", "YEM", "LBY",
            "TUN", "DZA", "MAR", "AFG", "TJK", "PSE",
        ],
        "description": (
            "Middle East, North Africa, and Persian-speaking states. "
            "Covers Iran hard-target zone, Gulf monarchies, Arab Spring "
            "states, and the Afghan/Central Asian corridor."
        ),
    },
    "Latin America": {
        "countries": [
            "MEX", "BRA", "ARG", "CHL", "COL", "PER", "VEN", "ECU",
            "BOL", "URY", "PRY", "CRI", "PAN", "NIC", "SLV", "GTM",
            "HND", "CUB", "DOM", "JAM", "TTO",
        ],
        "description": (
            "Western Hemisphere south of the US. Includes both stable "
            "democracies (Chile, Uruguay, Costa Rica) and authoritarian "
            "backsliders (Venezuela, Nicaragua). Key theater for Chinese "
            "economic expansion and Russian influence operations."
        ),
    },
    "Sub-Saharan Africa": {
        "countries": [
            "NGA", "KEN", "GHA", "SEN", "ZAF", "BWA", "MUS",
            "ETH", "TZA", "UGA", "RWA", "COD", "CMR", "CIV",
            "MLI", "BFA", "NER",
        ],
        "description": (
            "Sub-Saharan Africa. Includes both democratic success stories "
            "(Ghana, Senegal, Botswana) and coup-prone Sahel states. "
            "Increasingly contested by China, Russia (Wagner/Africa Corps), "
            "and Turkey."
        ),
    },
    "Asia-Pacific": {
        "countries": [
            "JPN", "KOR", "IND", "IDN", "PHL", "THA", "MYS",
            "AUS", "NZL",
        ],
        "description": (
            "Indo-Pacific democracies. Ranges from consolidated democracies "
            "(Japan, Australia) to democratic backsliders (Philippines under "
            "Duterte, Thailand's cycle of coups)."
        ),
    },
}

GREAT_POWER_COMPETITION = {
    "Chinese Economic Penetration (Latin America)": {
        "description": (
            "Countries where China has become a top-3 trading partner or "
            "major infrastructure investor, potentially shifting political "
            "alignment away from the US."
        ),
        "countries_high": ["BRA", "CHL", "PER", "ARG", "VEN", "ECU", "BOL", "CUB", "NIC"],
        "countries_moderate": ["COL", "MEX", "URY", "CRI", "PAN", "DOM"],
    },
    "Russian Influence (Latin America)": {
        "description": (
            "Countries with active Russian military, intelligence, or "
            "diplomatic influence operations."
        ),
        "countries_high": ["VEN", "NIC", "CUB"],
        "countries_moderate": ["MEX", "ARG", "BRA"],
    },
    "Iranian Proxy Network (MENA)": {
        "description": (
            "States where Iran maintains proxy militias or significant "
            "political influence through Shia networks."
        ),
        "countries_high": ["IRQ", "LBN", "SYR", "YEM", "PSE"],
        "countries_moderate": ["BHR", "KWT", "AFG"],
    },
}


def run_regional_analysis(full_df: pd.DataFrame, target: str = "party_shift") -> dict:
    """Run model on each region and compare performance."""
    exclude = {"country", "year", target}
    feature_cols = [
        c for c in full_df.columns
        if c not in exclude and full_df[c].dtype in ("float64", "int64", "float32")
    ]

    results = {}
    report_lines = []

    report_lines.append("=" * 70)
    report_lines.append("REGIONAL SUBSET ANALYSIS")
    report_lines.append("=" * 70)

    for region_name, info in REGIONS.items():
        countries = info["countries"]
        subset = full_df[full_df["country"].isin(countries)].copy()

        if len(subset) < 50 or subset[target].sum() < 5:
            report_lines.append(f"\n  {region_name}: insufficient data (n={len(subset)}, events={subset[target].sum()})")
            continue

        sub_features = [c for c in feature_cols if subset[c].notna().sum() > len(subset) * 0.3]
        if not sub_features:
            continue

        sub_clean = subset.dropna(subset=sub_features)
        if len(sub_clean) < 30:
            continue

        X = sub_clean[sub_features].values
        y = sub_clean[target].values
        years = sub_clean["year"].values

        cutoff = 2010
        train = years < cutoff
        test = years >= cutoff

        if sum(test) < 10 or y[test].sum() < 2:
            report_lines.append(f"\n  {region_name}: insufficient test data")
            continue

        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_train = scaler.fit_transform(X[train])
        X_test = scaler.transform(X[test])

        rf = RandomForestClassifier(
            n_estimators=150, max_depth=5, min_samples_leaf=5,
            class_weight="balanced", random_state=42
        )
        rf.fit(X_train, y[train])
        probs = rf.predict_proba(X_test)[:, 1]
        auc_score = roc_auc_score(y[test], probs)
        brier = brier_score_loss(y[test], probs)

        n_countries = sub_clean["country"].nunique()
        event_rate = y.mean()

        results[region_name] = {
            "auc_roc": auc_score,
            "brier": brier,
            "n_obs": len(sub_clean),
            "n_test": int(sum(test)),
            "n_countries": n_countries,
            "event_rate": event_rate,
        }

        report_lines.append(f"\n  {region_name}")
        report_lines.append(f"    {info['description'][:80]}...")
        report_lines.append(f"    Countries: {n_countries}, Obs: {len(sub_clean)}, Test: {sum(test)}")
        report_lines.append(f"    Event rate: {event_rate:.3f}")
        report_lines.append(f"    ROC-AUC: {auc_score:.3f}  |  Brier: {brier:.3f}")

        # Top features for this region
        feat_imp = pd.DataFrame({
            "feature": sub_features,
            "importance": rf.feature_importances_,
        }).sort_values("importance", ascending=False)
        report_lines.append(f"    Top 5 drivers: {', '.join(feat_imp.head(5)['feature'].tolist())}")

        # Country-level recent predictions
        test_df = sub_clean[test].copy()
        test_df["prob"] = probs
        latest = test_df.sort_values("year").groupby("country").tail(1)
        latest = latest[["country", "year", target, "prob"]].sort_values("prob", ascending=False)
        report_lines.append(f"    Highest risk (latest year):")
        for _, row in latest.head(5).iterrows():
            actual = "SHIFT" if row[target] == 1 else "held"
            report_lines.append(f"      {row['country']} ({int(row['year'])}): {row['prob']:.3f} [{actual}]")

    # Great power competition overlay
    report_lines.append("\n" + "=" * 70)
    report_lines.append("GREAT-POWER COMPETITION OVERLAY")
    report_lines.append("=" * 70)

    for gp_name, gp_info in GREAT_POWER_COMPETITION.items():
        report_lines.append(f"\n  {gp_name}")
        report_lines.append(f"  {gp_info['description'][:100]}")
        high = gp_info["countries_high"]
        mod = gp_info.get("countries_moderate", [])

        high_df = full_df[full_df["country"].isin(high)]
        if len(high_df) > 0 and target in high_df.columns:
            rate = high_df[target].mean()
            report_lines.append(f"    High-influence ({', '.join(high)}): turnover rate {rate:.3f}")

        if mod:
            mod_df = full_df[full_df["country"].isin(mod)]
            if len(mod_df) > 0:
                rate_m = mod_df[target].mean()
                report_lines.append(f"    Moderate-influence ({', '.join(mod)}): turnover rate {rate_m:.3f}")

    report_text = "\n".join(report_lines)
    print(report_text)

    with open(OUT / "regional_analysis.txt", "w") as f:
        f.write(report_text)

    # Save results table
    if results:
        res_df = pd.DataFrame(results).T
        res_df.index.name = "region"
        res_df.to_csv(OUT / "regional_results.csv")

    return results
