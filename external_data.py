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
    """Load ACLED aggregated country-year data."""
    path = DATA / "acled_aggregated.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)
    df = df.rename(columns={"country_name": "country_raw", "year": "year"})

    # Map ACLED country names to ISO3
    name_to_iso = {v: k for k, v in {
        "AFG": "Afghanistan", "ALB": "Albania", "DZA": "Algeria", "AGO": "Angola",
        "ARG": "Argentina", "ARM": "Armenia", "AUS": "Australia", "AUT": "Austria",
        "AZE": "Azerbaijan", "BHR": "Bahrain", "BGD": "Bangladesh", "BLR": "Belarus",
        "BEL": "Belgium", "BEN": "Benin", "BOL": "Bolivia", "BIH": "Bosnia and Herzegovina",
        "BWA": "Botswana", "BRA": "Brazil", "BFA": "Burkina Faso", "BDI": "Burundi",
        "KHM": "Cambodia", "CMR": "Cameroon", "CAN": "Canada", "CAF": "Central African Republic",
        "TCD": "Chad", "CHL": "Chile", "CHN": "China", "COL": "Colombia",
        "COD": "Democratic Republic of Congo", "COG": "Republic of Congo",
        "CRI": "Costa Rica", "CIV": "Ivory Coast", "HRV": "Croatia", "CUB": "Cuba",
        "CZE": "Czech Republic", "DNK": "Denmark", "DOM": "Dominican Republic",
        "ECU": "Ecuador", "EGY": "Egypt", "SLV": "El Salvador", "ERI": "Eritrea",
        "EST": "Estonia", "ETH": "Ethiopia", "FIN": "Finland", "FRA": "France",
        "DEU": "Germany", "GHA": "Ghana", "GRC": "Greece", "GTM": "Guatemala",
        "GIN": "Guinea", "GNB": "Guinea-Bissau", "HTI": "Haiti", "HND": "Honduras",
        "HUN": "Hungary", "IND": "India", "IDN": "Indonesia", "IRN": "Iran",
        "IRQ": "Iraq", "IRL": "Ireland", "ISR": "Israel", "ITA": "Italy",
        "JAM": "Jamaica", "JPN": "Japan", "JOR": "Jordan", "KAZ": "Kazakhstan",
        "KEN": "Kenya", "KWT": "Kuwait", "KGZ": "Kyrgyzstan", "LAO": "Laos",
        "LVA": "Latvia", "LBN": "Lebanon", "LSO": "Lesotho", "LBR": "Liberia",
        "LBY": "Libya", "LTU": "Lithuania", "MKD": "Macedonia", "MDG": "Madagascar",
        "MWI": "Malawi", "MYS": "Malaysia", "MLI": "Mali", "MRT": "Mauritania",
        "MUS": "Mauritius", "MEX": "Mexico", "MDA": "Moldova", "MNG": "Mongolia",
        "MNE": "Montenegro", "MAR": "Morocco", "MOZ": "Mozambique", "MMR": "Myanmar",
        "NAM": "Namibia", "NPL": "Nepal", "NLD": "Netherlands", "NZL": "New Zealand",
        "NIC": "Nicaragua", "NER": "Niger", "NGA": "Nigeria", "NOR": "Norway",
        "OMN": "Oman", "PAK": "Pakistan", "PSE": "Palestine", "PAN": "Panama",
        "PNG": "Papua New Guinea", "PRY": "Paraguay", "PER": "Peru", "PHL": "Philippines",
        "POL": "Poland", "PRT": "Portugal", "QAT": "Qatar", "ROU": "Romania",
        "RUS": "Russia", "RWA": "Rwanda", "SAU": "Saudi Arabia", "SEN": "Senegal",
        "SRB": "Serbia", "SLE": "Sierra Leone", "SGP": "Singapore", "SVK": "Slovakia",
        "SVN": "Slovenia", "SOM": "Somalia", "ZAF": "South Africa", "SSD": "South Sudan",
        "KOR": "South Korea", "ESP": "Spain", "LKA": "Sri Lanka", "SDN": "Sudan",
        "SWZ": "Eswatini", "SWE": "Sweden", "CHE": "Switzerland", "SYR": "Syria",
        "TJK": "Tajikistan", "TZA": "Tanzania", "THA": "Thailand", "TLS": "Timor-Leste",
        "TGO": "Togo", "TTO": "Trinidad and Tobago", "TUN": "Tunisia", "TUR": "Turkey",
        "TKM": "Turkmenistan", "UGA": "Uganda", "UKR": "Ukraine", "ARE": "United Arab Emirates",
        "GBR": "United Kingdom", "USA": "United States of America", "URY": "Uruguay",
        "UZB": "Uzbekistan", "VEN": "Venezuela", "VNM": "Vietnam", "YEM": "Yemen",
        "ZMB": "Zambia", "ZWE": "Zimbabwe",
    }.items()}

    df["country"] = df["country_raw"].map(name_to_iso)
    df = df.dropna(subset=["country"])
    df = df.drop(columns=["country_raw"])

    return df


def load_fsi() -> pd.DataFrame | None:
    """Load Fragile States Index combined data."""
    path = DATA / "fsi_combined.csv"
    if not path.exists():
        return None

    df = pd.read_csv(path)
    if "Country" not in df.columns or "Total" not in df.columns:
        return None

    # Map FSI country names to ISO3
    fsi_name_map = {
        "United States": "USA", "United Kingdom": "GBR", "France": "FRA",
        "Germany": "DEU", "Italy": "ITA", "Spain": "ESP", "Japan": "JPN",
        "Canada": "CAN", "Australia": "AUS", "Brazil": "BRA", "Mexico": "MEX",
        "India": "IND", "China": "CHN", "Russia": "RUS", "South Korea": "KOR",
        "South Africa": "ZAF", "Turkey": "TUR", "Argentina": "ARG", "Colombia": "COL",
        "Chile": "CHL", "Peru": "PER", "Venezuela": "VEN", "Ecuador": "ECU",
        "Bolivia": "BOL", "Paraguay": "PRY", "Uruguay": "URY", "Costa Rica": "CRI",
        "Panama": "PAN", "Nicaragua": "NIC", "El Salvador": "SLV", "Guatemala": "GTM",
        "Honduras": "HND", "Dominican Republic": "DOM", "Jamaica": "JAM",
        "Trinidad and Tobago": "TTO", "Cuba": "CUB", "Haiti": "HTI",
        "Iran": "IRN", "Iraq": "IRQ", "Israel": "ISR", "Jordan": "JOR",
        "Lebanon": "LBN", "Egypt": "EGY", "Saudi Arabia": "SAU", "Syria": "SYR",
        "Yemen": "YEM", "Libya": "LBY", "Tunisia": "TUN", "Morocco": "MAR",
        "Algeria": "DZA", "Nigeria": "NGA", "Kenya": "KEN", "Ghana": "GHA",
        "Senegal": "SEN", "Ethiopia": "ETH", "Tanzania": "TZA",
        "Congo Democratic Republic": "COD", "Cameroon": "CMR", "Mali": "MLI",
        "Burkina Faso": "BFA", "Niger": "NER", "Chad": "TCD",
        "Cote d'Ivoire": "CIV", "Ivory Coast": "CIV",
        "Mozambique": "MOZ", "Botswana": "BWA", "Mauritius": "MUS",
        "Poland": "POL", "Czech Republic": "CZE", "Hungary": "HUN",
        "Greece": "GRC", "Portugal": "PRT", "Austria": "AUT",
        "Belgium": "BEL", "Netherlands": "NLD", "Switzerland": "CHE",
        "Sweden": "SWE", "Norway": "NOR", "Denmark": "DNK", "Ireland": "IRL",
        "New Zealand": "NZL", "Indonesia": "IDN", "Philippines": "PHL",
        "Thailand": "THA", "Malaysia": "MYS",
        "Pakistan": "PAK", "Afghanistan": "AFG", "Bangladesh": "BGD",
        "Myanmar": "MMR", "Sri Lanka": "LKA", "Nepal": "NPL",
        "Ukraine": "UKR", "Georgia": "GEO", "Serbia": "SRB",
    }

    df["country"] = df["Country"].map(fsi_name_map)
    df = df.dropna(subset=["country"])
    df = df.rename(columns={"Year": "year", "Total": "fsi_total", "Rank": "fsi_rank"})

    # Keep key sub-indicators
    col_map = {
        "C1: Security Apparatus": "fsi_security",
        "C2: Factionalized Elites": "fsi_factionalized_elites",
        "C3: Group Grievance": "fsi_group_grievance",
        "E1: Economy": "fsi_economy",
        "E2: Economic Inequality": "fsi_inequality",
        "P1: State Legitimacy": "fsi_legitimacy",
        "P2: Public Services": "fsi_public_services",
        "P3: Human Rights": "fsi_human_rights",
        "X1: External Intervention": "fsi_external_intervention",
    }
    for old, new in col_map.items():
        if old in df.columns:
            df[new] = pd.to_numeric(df[old], errors="coerce")

    keep = ["country", "year", "fsi_total", "fsi_rank"] + [v for v in col_map.values() if v in df.columns]
    return df[keep]


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

    # ACLED
    acled = load_acled()
    if acled is not None:
        df = df.merge(acled, on=["country", "year"], how="left")
        n = df["acled_polviolence_events"].notna().sum()
        print(f"  ACLED merged: {n} non-null conflict observations")
    else:
        print("  ACLED: not found (place data/acled_aggregated.csv)")

    # FSI
    fsi = load_fsi()
    if fsi is not None:
        df = df.merge(fsi, on=["country", "year"], how="left")
        n = df["fsi_total"].notna().sum()
        print(f"  FSI merged: {n} non-null fragility scores")
    else:
        print("  FSI: not found (place data/fsi_combined.csv)")

    return df
