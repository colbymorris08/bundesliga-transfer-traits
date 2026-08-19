"""V-Dem dataset integration for richer regime classification.

V-Dem (Varieties of Democracy) provides the gold-standard variables for:
  - Regime type classification (v2x_regime: 0–3 ordinal)
  - Electoral democracy index (v2x_polyarchy: 0–1 continuous)
  - Liberal democracy index (v2x_libdem)
  - Executive turnover (v2elturnhog) — can replace hand-coded target
  - State discrimination indicators (v2xeg_eqdr, v2pepwrsoc)

Download the CSV from https://v-dem.net/data/the-v-dem-dataset/
(Country-Year: V-Dem Core, CSV format — free with email)
Place it as: data/vdem_core.csv

If V-Dem is unavailable, we approximate regime type from World Bank
governance indicators (voice/accountability as proxy for polyarchy).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

VDEM_PATH = Path(__file__).resolve().parent / "data" / "vdem_core.csv"

VDEM_VARS = [
    "country_text_id",
    "year",
    "v2x_polyarchy",      # electoral democracy index (0–1)
    "v2x_libdem",         # liberal democracy index (0–1)
    "v2x_partipdem",      # participatory democracy index
    "v2x_egaldem",        # egalitarian democracy index
    "v2x_regime",         # regimes of world (0=closed auto, 1=elec auto, 2=elec dem, 3=lib dem)
    "v2elturnhog",        # HOG turnover at election (ordinal)
    "v2elturnhos",        # HOS turnover at election
    "v2x_clpol",          # political civil liberties
    "v2x_cspart",         # civil society participation
    "v2xpe_exlsocgr",     # exclusion by social group
    "v2pepwrsoc",         # social class equality
]

REGIME_LABELS = {
    0: "Closed Autocracy",
    1: "Electoral Autocracy",
    2: "Electoral Democracy",
    3: "Liberal Democracy",
}


def load_vdem() -> pd.DataFrame | None:
    """Load V-Dem if the CSV is present."""
    if not VDEM_PATH.exists():
        return None

    print(f"  Loading V-Dem from {VDEM_PATH}")
    df = pd.read_csv(VDEM_PATH, low_memory=False)

    keep = [c for c in VDEM_VARS if c in df.columns]
    df = df[keep].copy()
    df = df.rename(columns={"country_text_id": "country"})

    if "v2x_regime" in df.columns:
        df["regime_label"] = df["v2x_regime"].map(REGIME_LABELS)
        # PITF-style: partial democracies (electoral autocracies + electoral democracies) are most unstable
        df["partial_democracy_vdem"] = df["v2x_regime"].isin([1, 2]).astype(float)

    if "v2x_polyarchy" in df.columns:
        poly = df["v2x_polyarchy"]
        # "Anocracy" zone: mid-range polyarchy (0.2–0.7) = highest instability
        df["anocracy_zone"] = ((poly >= 0.2) & (poly <= 0.7)).astype(float)

    if "v2elturnhog" in df.columns:
        # v2elturnhog: 0=no election, 1=election/no turnover, 2=turnover
        df["vdem_turnover"] = (df["v2elturnhog"] >= 2).astype(float)

    if "v2xpe_exlsocgr" in df.columns:
        df["social_exclusion"] = df["v2xpe_exlsocgr"]

    print(f"  V-Dem loaded: {len(df)} rows, {len(df.columns)} columns")
    return df


def approximate_regime_from_wb(wb_df: pd.DataFrame) -> pd.DataFrame:
    """Approximate V-Dem regime categories from World Bank governance data.

    Uses voice/accountability as a rough proxy for polyarchy.
    This is a fallback when V-Dem CSV is not available.
    """
    df = wb_df.copy()

    if "voice_accountability" in df.columns:
        va = df["voice_accountability"]
        conditions = [
            va < -1.0,                     # closed autocracy
            (va >= -1.0) & (va < 0.0),     # electoral autocracy
            (va >= 0.0) & (va < 1.0),      # electoral democracy
            va >= 1.0,                      # liberal democracy
        ]
        choices = [0, 1, 2, 3]
        df["v2x_regime_approx"] = np.select(conditions, choices, default=np.nan)
        df["partial_democracy_approx"] = df["v2x_regime_approx"].isin([1, 2]).astype(float)
        df["polyarchy_approx"] = (va - va.min()) / (va.max() - va.min())
        df["anocracy_zone_approx"] = (
            (df["polyarchy_approx"] >= 0.2) & (df["polyarchy_approx"] <= 0.7)
        ).astype(float)

    return df


def merge_vdem(base_df: pd.DataFrame) -> pd.DataFrame:
    """Try to merge V-Dem data; fall back to WB approximation."""
    vdem = load_vdem()
    if vdem is not None:
        merged = base_df.merge(vdem, on=["country", "year"], how="left")
        print(f"  V-Dem merged. Non-null polyarchy: {merged['v2x_polyarchy'].notna().sum()}")
        return merged
    else:
        print("  V-Dem CSV not found — using World Bank governance approximation")
        return approximate_regime_from_wb(base_df)
