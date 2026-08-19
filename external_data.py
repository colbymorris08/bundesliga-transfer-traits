"""Integration module for external datasets: Polity5, MEPV, ACLED, FSI.

Loads available external data from data/ directory and merges into the
main country-year panel. Each source is optional — the model runs with
whatever is available.

Data sources and how to obtain them:
  - Polity5: auto-downloaded from systemicpeace.org (included)
  - MEPV: auto-downloaded from systemicpeace.org (included)
  - ACLED: requires free registration at acleddata.com (export CSV → data/acled.csv)
  - FSI: download Excel files from fragilestatesindex.org/excel (→ data/fsi_YYYY.xlsx)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path(__file__).resolve().parent / "data"

ISO3_MAP = {
    "AFG": "AFG", "ALB": "ALB", "ALG": "DZA", "ANG": "AGO", "ARG": "ARG",
    "AUL": "AUS", "AUS": "AUT", "AZE": "AZE", "BNG": "BGD", "BLR": "BLR",
    "BEL": "BEL", "BEN": "BEN", "BHU": "BTN", "BOL": "BOL", "BOS": "BIH",
    "BOT": "BWA", "BRA": "BRA", "BFO": "BFA", "BUI": "BDI", "CAM": "KHM",
    "CAO": "CMR", "CAN": "CAN", "CEN": "CAF", "CHA": "TCD", "CHL": "CHL",
    "CHN": "CHN", "COL": "COL", "COM": "COM", "CON": "COG", "COS": "CRI",
    "CRO": "HRV", "CUB": "CUB", "CYP": "CYP", "CZR": "CZE", "DEN": "DNK",
    "DJI": "DJI", "DOM": "DOM", "DRC": "COD", "ECU": "ECU", "EGY": "EGY",
    "SAL": "SLV", "EQG": "GNQ", "ERI": "ERI", "EST": "EST", "ETH": "ETH",
    "FIN": "FIN", "FRA": "FRA", "GAB": "GAB", "GAM": "GMB", "GRG": "GEO",
    "GER": "DEU", "GHA": "GHA", "GRC": "GRC", "GUA": "GTM", "GUI": "GIN",
    "GNB": "GNB", "GUY": "GUY", "HAI": "HTI", "HON": "HND", "HUN": "HUN",
    "IND": "IND", "INS": "IDN", "IRN": "IRN", "IRQ": "IRQ", "IRE": "IRL",
    "ISR": "ISR", "ITA": "ITA", "JAM": "JAM", "JPN": "JPN", "JOR": "JOR",
    "KAZ": "KAZ", "KEN": "KEN", "KUW": "KWT", "KYR": "KGZ", "LAO": "LAO",
    "LAT": "LVA", "LEB": "LBN", "LES": "LSO", "LBR": "LBR", "LIB": "LBY",
    "LIT": "LTU", "MAC": "MKD", "MAG": "MDG", "MAW": "MWI", "MAL": "MYS",
    "MLI": "MLI", "MAA": "MRT", "MAS": "MUS", "MEX": "MEX", "MOL": "MDA",
    "MON": "MNG", "MOR": "MAR", "MZM": "MOZ", "MYA": "MMR", "NAM": "NAM",
    "NEP": "NPL", "NTH": "NLD", "NEW": "NZL", "NIC": "NIC", "NIR": "NER",
    "NIG": "NGA", "NOR": "NOR", "OMA": "OMN", "PAK": "PAK", "PAN": "PAN",
    "PAR": "PRY", "PER": "PER", "PHI": "PHL", "POL": "POL", "POR": "PRT",
    "QAT": "QAT", "ROM": "ROU", "RUS": "RUS", "RWA": "RWA", "SAU": "SAU",
    "SEN": "SEN", "SER": "SRB", "SIE": "SLE", "SIN": "SGP", "SLO": "SVK",
    "SLV": "SVN", "SOM": "SOM", "SAF": "ZAF", "KOR": "KOR", "SPN": "ESP",
    "SRI": "LKA", "SUD": "SDN", "SWA": "SWZ", "SWD": "SWE", "SWZ": "CHE",
    "SYR": "SYR", "TAJ": "TJK", "TAZ": "TZA", "THI": "THA", "TIM": "TLS",
    "TOG": "TGO", "TRI": "TTO", "TUN": "TUN", "TUR": "TUR", "TKM": "TKM",
    "UGA": "UGA", "UKR": "UKR", "UAE": "ARE", "UKG": "GBR", "USA": "USA",
    "URU": "URY", "UZB": "UZB", "VEN": "VEN", "VIE": "VNM", "YEM": "YEM",
    "ZAM": "ZMB", "ZIM": "ZWE", "SSD": "SSD", "MNE": "MNE", "KOS": "XKX",
}


def load_polity5() -> pd.DataFrame | None:
    """Load Polity5 regime data."""
    path = DATA / "polity5.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)
    df["country"] = df["country_code"].map(ISO3_MAP)
    df = df.dropna(subset=["country"])
    df = df[["country", "year", "polity2", "democ", "autoc", "durable"]].copy()

    # Polity2 ranges from -10 (full autocracy) to +10 (full democracy)
    # Anocracy: -5 to +5 (PITF's key risk zone)
    df["anocracy_polity"] = ((df["polity2"] >= -5) & (df["polity2"] <= 5)).astype(float)
    df["democracy_score"] = df["polity2"]
    df["regime_durability"] = df["durable"]

    return df[["country", "year", "democracy_score", "anocracy_polity", "regime_durability"]]


def load_mepv() -> pd.DataFrame | None:
    """Load Major Episodes of Political Violence."""
    path = DATA / "mepv.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)
    df["country"] = df["country_code"].map(ISO3_MAP)
    df = df.dropna(subset=["country"])

    df["total_conflict_magnitude"] = df["actotal"].fillna(0)
    df["civil_conflict"] = (df["civviol"].fillna(0) + df["civwar"].fillna(0))
    df["ethnic_conflict"] = (df["ethviol"].fillna(0) + df["ethwar"].fillna(0))
    df["international_conflict"] = (df["intviol"].fillna(0) + df["intwar"].fillna(0))
    df["any_conflict"] = (df["total_conflict_magnitude"] > 0).astype(float)

    return df[["country", "year", "total_conflict_magnitude", "civil_conflict",
               "ethnic_conflict", "international_conflict", "any_conflict"]]


def load_acled() -> pd.DataFrame | None:
    """Load ACLED conflict events (aggregated to country-year).

    User must download from acleddata.com and save as data/acled.csv.
    Expected columns: country, year, event_type, fatalities (or similar).
    """
    path = DATA / "acled.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path, low_memory=False)
    if "country" not in df.columns or "year" not in df.columns:
        print("  ACLED: unexpected column format, skipping")
        return None

    agg = df.groupby(["country", "year"]).agg(
        acled_events=("event_type", "count"),
        acled_fatalities=("fatalities", "sum"),
    ).reset_index()

    return agg


def load_fsi() -> pd.DataFrame | None:
    """Load Fragile States Index data.

    User must download Excel files from fragilestatesindex.org/excel
    and place as data/fsi_YYYY.xlsx (one per year).
    """
    fsi_files = sorted(DATA.glob("fsi_*.xlsx"))
    if not fsi_files:
        return None

    frames = []
    for f in fsi_files:
        try:
            year = int(f.stem.split("_")[1])
            df = pd.read_excel(f)
            df["year"] = year
            frames.append(df)
        except Exception:
            continue

    if not frames:
        return None

    combined = pd.concat(frames, ignore_index=True)
    if "Total" in combined.columns and "Country" in combined.columns:
        combined = combined.rename(columns={"Total": "fsi_total", "Country": "country_name"})

    return combined


def merge_external_data(base_df: pd.DataFrame) -> pd.DataFrame:
    """Load all available external datasets and merge into the base panel."""
    df = base_df.copy()

    # Polity5
    polity = load_polity5()
    if polity is not None:
        df = df.merge(polity, on=["country", "year"], how="left")
        n = df["democracy_score"].notna().sum()
        print(f"  Polity5 merged: {n} non-null democracy scores")
    else:
        print("  Polity5: not found (run download or place data/polity5.csv)")

    # MEPV (Major Episodes of Political Violence)
    mepv = load_mepv()
    if mepv is not None:
        df = df.merge(mepv, on=["country", "year"], how="left")
        n = df["total_conflict_magnitude"].notna().sum()
        print(f"  MEPV merged: {n} non-null conflict observations")
    else:
        print("  MEPV: not found (run download or place data/mepv.csv)")

    # ACLED (optional)
    acled = load_acled()
    if acled is not None:
        df = df.merge(acled, on=["country", "year"], how="left")
        print(f"  ACLED merged: {df['acled_events'].notna().sum()} non-null")
    else:
        print("  ACLED: not found (register at acleddata.com, export CSV → data/acled.csv)")

    # FSI (optional)
    fsi = load_fsi()
    if fsi is not None:
        print(f"  FSI loaded: {len(fsi)} rows")
    else:
        print("  FSI: not found (download from fragilestatesindex.org/excel → data/fsi_YYYY.xlsx)")

    return df
