#!/usr/bin/env python3
"""FBref stability: prior → BL Y1 from season tables across the study leagues.

Y1 always comes from Big5 Bundesliga cache.
Prior = latest eligible season before first BL among:
  Big5 non-BL (richest) > feeder slim > player-page cache.

Study window: first BL season end-year >= MIN_BL_SEASON (default 2021).
Reports pass counts at r >= 0.40 / 0.50 / 0.70 so we can pick the gate
before redundancy.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results"
BIG5 = OUT / "fbref_cache"
SLIM = OUT / "fbref_inbound_feeder_slim"
PLAYER = OUT / "fbref_inbound_player_cache"

SEASONS = range(2018, 2026)
STAT_TYPES = ["standard", "shooting", "passing", "possession", "defense", "misc"]
MIN_PRIOR = 300.0
MIN_Y1 = 300.0
MIN_BL_SEASON = 2021
MIN_PAIRS = 25
GATES = (0.40, 0.50, 0.70)

META_BIG5 = {
    "Season_End_Year", "Squad", "Comp", "Player", "Nation", "Pos", "Age", "Born",
    "Url", "Rk", "Matches", "Player_Href", "MP_Playing", "Starts_Playing",
    "Min_Playing", "Mins_Per_90_Playing", "Mins_Per_90", "Min", ".stat_type",
}

INVERT = {
    "Mis_Performance", "Dis_Performance", "Err", "Fls", "Lost_Aerial",
    "Lost_Challenges", "Tkld_Take", "Mis_Carries", "Dis_Carries",
}

# soccerdata / player-page column → Big5 stability metric name
FEEDER_ALIASES: dict[str, list[str]] = {
    "Gls_Per": ["Per 90 Minutes_Gls", "Gls_Per"],
    "Ast_Per": ["Per 90 Minutes_Ast", "Ast_Per"],
    "G_minus_PK_Per": ["Per 90 Minutes_G-PK"],
    "Gls": ["Performance_Gls", "Gls", "Standard_Gls"],
    "Ast": ["Performance_Ast", "Ast"],
    "Gls_Standard": ["Standard_Gls", "Performance_Gls"],
    "Sh_Standard": ["Standard_Sh"],
    "SoT_Standard": ["Standard_SoT"],
    "SoT_percent_Standard": ["Standard_SoT%"],
    "Sh_per_90_Standard": ["Standard_Sh/90"],
    "SoT_per_90_Standard": ["Standard_SoT/90"],
    "G_per_Sh_Standard": ["Standard_G/Sh"],
    "G_per_SoT_Standard": ["Standard_G/SoT"],
    "PK_Standard": ["Standard_PK", "Performance_PK"],
    "PKatt_Standard": ["Standard_PKatt", "Performance_PKatt"],
    "Cmp_Total": ["Total_Cmp"],
    "Att_Total": ["Total_Att"],
    "Cmp_percent_Total": ["Total_Cmp%"],
    "TotDist_Total": ["Total_TotDist"],
    "PrgDist_Total": ["Total_PrgDist"],
    "Cmp_Short": ["Short_Cmp"],
    "Att_Short": ["Short_Att"],
    "Cmp_percent_Short": ["Short_Cmp%"],
    "Cmp_Medium": ["Medium_Cmp"],
    "Att_Medium": ["Medium_Att"],
    "Cmp_percent_Medium": ["Medium_Cmp%"],
    "Cmp_Long": ["Long_Cmp"],
    "Att_Long": ["Long_Att"],
    "Cmp_percent_Long": ["Long_Cmp%"],
    "KP": ["KP"],
    "Final_Third": ["1/3", "Final Third", "Final_Third"],
    "PPA": ["PPA"],
    "CrsPA": ["CrsPA"],
    "Touches_Touches": ["Touches_Touches"],
    "Def_Pen_Touches": ["Touches_Def Pen", "Def Pen_Touches", "Def_Pen_Touches"],
    "Def_3rd_Touches": ["Touches_Def 3rd", "Def 3rd_Touches", "Def_3rd_Touches"],
    "Mid_3rd_Touches": ["Touches_Mid 3rd", "Mid 3rd_Touches", "Mid_3rd_Touches"],
    "Att_3rd_Touches": ["Touches_Att 3rd", "Att 3rd_Touches", "Att_3rd_Touches"],
    "Att_Pen_Touches": ["Touches_Att Pen", "Att Pen_Touches", "Att_Pen_Touches"],
    "Live_Touches": ["Touches_Live", "Live_Touches"],
    "Att_Take": ["Take-Ons_Att", "Att_Take"],
    "Succ_Take": ["Take-Ons_Succ", "Succ_Take"],
    "Succ_percent_Take": ["Take-Ons_Succ%", "Succ_percent_Take"],
    "Tkld_Take": ["Take-Ons_Tkld", "Tkld_Take"],
    "Tkld_percent_Take": ["Take-Ons_Tkld%", "Tkld_percent_Take"],
    "Carries_Carries": ["Carries_Carries"],
    "TotDist_Carries": ["Carries_TotDist", "TotDist_Carries"],
    "PrgDist_Carries": ["Carries_PrgDist", "PrgDist_Carries"],
    "Final_Third_Carries": ["Carries_1/3", "Final_Third_Carries"],
    "CPA_Carries": ["Carries_CPA", "CPA_Carries"],
    "Mis_Carries": ["Carries_Mis", "Mis_Carries"],
    "Dis_Carries": ["Carries_Dis", "Dis_Carries"],
    "Rec_Receiving": ["Rec", "Rec_Receiving"],
    "Tkl_Tackles": ["Tackles_Tkl", "Tkl_Tackles"],
    "TklW_Tackles": ["Tackles_TklW", "TklW_Tackles"],
    "Def_3rd_Tackles": ["Tackles_Def 3rd", "Def 3rd_Tackles", "Def_3rd_Tackles"],
    "Mid_3rd_Tackles": ["Tackles_Mid 3rd", "Mid 3rd_Tackles", "Mid_3rd_Tackles"],
    "Att_3rd_Tackles": ["Tackles_Att 3rd", "Att 3rd_Tackles", "Att_3rd_Tackles"],
    "Tkl_Challenges": ["Challenges_Tkl", "Tkl_Challenges"],
    "Att_Challenges": ["Challenges_Att", "Att_Challenges"],
    "Tkl_percent_Challenges": ["Challenges_Tkl%", "Tkl_percent_Challenges"],
    "Lost_Challenges": ["Challenges_Lost", "Lost_Challenges"],
    "Blocks_Blocks": ["Blocks_Blocks"],
    "Sh_Blocks": ["Blocks_Sh", "Sh_Blocks"],
    "Pass_Blocks": ["Blocks_Pass", "Pass_Blocks"],
    "Int": ["Int", "Performance_Int"],
    "Tkl_plus_Int": ["Tkl+Int"],
    "Clr": ["Clr"],
    "Err": ["Err"],
    "Fls": ["Performance_Fls", "Fls"],
    "Fld": ["Performance_Fld", "Fld"],
    "Off": ["Performance_Off", "Off"],
    "Crs": ["Performance_Crs", "Crs"],
    "TklW": ["Performance_TklW", "TklW"],
    "PKwon": ["Performance_PKwon", "PKwon"],
    "PKcon": ["Performance_PKcon", "PKcon"],
    "OG": ["Performance_OG", "OG"],
    "CrdY": ["Performance_CrdY", "CrdY"],
    "CrdR": ["Performance_CrdR", "CrdR"],
}


def clean_metric_name(col: str) -> str:
    nm = str(col).replace(" ", "_")
    nm = nm.replace("%", "_pct").replace("+", "_plus_").replace("/", "_per_")
    nm = nm.replace("-", "_minus_")
    nm = re.sub(r"_+", "_", nm).strip("_")
    return nm


def numify(s: pd.Series) -> pd.Series:
    return pd.to_numeric(
        s.astype(str).str.replace(",", "", regex=False), errors="coerce"
    )


def is_bl_comp(comp: str) -> bool:
    c = str(comp)
    if "2." in c and "Bundesliga" in c:
        return False
    if re.search(r"\b2\.?\s*Bundesliga\b", c, re.I):
        return False
    return bool(re.search(r"Bundesliga", c, re.I)) and "Jr." not in c


def end_year_from_season_code(code: str) -> int | None:
    m = re.search(r"(\d{2})(\d{2})$", str(code).replace("-", ""))
    if m:
        return 2000 + int(m.group(2))
    m = re.match(r"(\d{4})", str(code))
    if m:
        y = int(m.group(1))
        return y if y > 1900 else None
    return None


def season_str_to_end_year(s: str) -> int | None:
    s = str(s).strip()
    if re.match(r"^\d{4}$", s):
        return int(s)
    m = re.match(r"^(\d{4})-(\d{2,4})$", s)
    if m:
        y2 = m.group(2)
        return int(y2) if len(y2) == 4 else 2000 + int(y2)
    return end_year_from_season_code(s)


def pick_col(cols: list[str], aliases: list[str]) -> str | None:
    colset = set(cols)
    for a in aliases:
        if a in colset:
            return a
    lower = {c.lower(): c for c in cols}
    for a in aliases:
        if a.lower() in lower:
            return lower[a.lower()]
    return None


def get_minutes_big5(df: pd.DataFrame) -> pd.Series:
    for c in ["Min_Playing", "Min", "Playing Time_Min"]:
        if c in df.columns:
            return numify(df[c])
    if "Mins_Per_90_Playing" in df.columns:
        return numify(df["Mins_Per_90_Playing"]) * 90
    if "Mins_Per_90" in df.columns:
        return numify(df["Mins_Per_90"]) * 90
    return pd.Series(np.nan, index=df.index)


def load_big5_wide() -> pd.DataFrame:
    pieces: list[pd.DataFrame] = []
    for st in STAT_TYPES:
        for yr in SEASONS:
            path = BIG5 / f"{st}_{yr}.csv"
            if not path.exists():
                continue
            df = pd.read_csv(path, low_memory=False)
            df[".stat_type"] = st
            pieces.append(df)
    if not pieces:
        raise SystemExit(f"No Big5 cache under {BIG5}")

    tabs = []
    for df in pieces:
        minutes = get_minutes_big5(df)
        out = pd.DataFrame(
            {
                "season_end": df["Season_End_Year"],
                "player": df["Player"].astype(str),
                "squad": df["Squad"].astype(str),
                "comp": df["Comp"].astype(str),
                "pos": df["Pos"].astype(str) if "Pos" in df.columns else "",
                "url": df["Url"].astype(str) if "Url" in df.columns else "",
                "minutes": minutes,
                ".stat_type": df[".stat_type"],
            }
        )
        used = set()
        for col in df.columns:
            if col in META_BIG5:
                continue
            v = numify(df[col])
            if v.notna().sum() == 0:
                continue
            nm = clean_metric_name(col)
            # R: space→underscore before other cleanups for names like "Def Pen_Touches"
            nm = str(col).replace(" ", "_")
            nm = nm.replace("%", "_percent").replace("+", "_plus_").replace("/", "_per_")
            nm = nm.replace("-", "_minus_")
            nm = re.sub(r"_+", "_", nm).strip("_")
            if nm in used or nm in out.columns:
                nm = f"{df['.stat_type'].iloc[0]}__{nm}"
            used.add(nm)
            out[nm] = v
        tabs.append(out)

    base = pd.concat([t for t in tabs if (t[".stat_type"] == "standard").all()], ignore_index=True)
    wide = base.drop(columns=[".stat_type"])
    keys = ["season_end", "player", "squad", "comp"]

    for st in STAT_TYPES:
        if st == "standard":
            continue
        add = pd.concat([t for t in tabs if (t[".stat_type"] == st).all()], ignore_index=True)
        if add.empty:
            continue
        add = add.drop(columns=[".stat_type", "minutes", "pos", "url"], errors="ignore")
        add = add.groupby(keys, as_index=False).first()
        new_cols = [c for c in add.columns if c not in wide.columns]
        overlap = [c for c in add.columns if c in wide.columns and c not in keys]
        if overlap:
            tmp = wide.merge(add[keys + overlap], on=keys, how="left", suffixes=("", "__new"))
            for col in overlap:
                newc = f"{col}__new"
                if newc in tmp.columns:
                    tmp[col] = tmp[col].combine_first(tmp[newc])
                    tmp.drop(columns=[newc], inplace=True)
            wide = tmp
        if new_cols:
            wide = wide.merge(add[keys + new_cols], on=keys, how="left")

    wide["player_id"] = np.where(
        wide["url"].fillna("").str.len() > 0,
        wide["url"],
        "name:" + wide["player"],
    )
    wide["name_key"] = wide["player"].str.strip().str.lower()
    wide["is_bl"] = wide["comp"].map(is_bl_comp)
    wide = wide[wide["minutes"].fillna(0) > 0].copy()
    return wide


def map_feeder_metrics(df: pd.DataFrame) -> pd.DataFrame:
    out = {}
    cols = list(df.columns)
    for metric, aliases in FEEDER_ALIASES.items():
        c = pick_col(cols, aliases)
        if c is not None:
            out[metric] = numify(df[c])
    return pd.DataFrame(out, index=df.index)


def load_feeder_slim_rows() -> pd.DataFrame:
    """One row per player-league-season with mapped metrics + minutes."""
    by_key: dict[tuple, dict] = {}
    for pq in sorted(SLIM.glob("*.parquet")):
        parts = pq.stem.split("_")
        if len(parts) < 3:
            continue
        season_code = parts[-2]
        season_end = end_year_from_season_code(season_code)
        if season_end is None:
            continue
        league = "_".join(parts[:-2])
        df = pd.read_parquet(pq)
        if "Player" not in df.columns:
            continue
        minutes = None
        for c in ["Playing Time_Min", "Min", "Playing Time Min"]:
            if c in df.columns:
                minutes = numify(df[c])
                break
        if minutes is None and "90s" in df.columns:
            minutes = numify(df["90s"]) * 90
        if minutes is None:
            minutes = pd.Series(np.nan, index=df.index)

        mapped = map_feeder_metrics(df)
        for i in df.index:
            player = str(df.at[i, "Player"])
            nk = player.strip().lower()
            squad = str(df.at[i, "Squad"]) if "Squad" in df.columns else ""
            key = (nk, season_end, league)
            row = by_key.setdefault(
                key,
                {
                    "name_key": nk,
                    "player": player,
                    "season_end": season_end,
                    "comp": league.replace("_", " "),
                    "squad": squad,
                    "minutes": float(minutes.at[i]) if pd.notna(minutes.at[i]) else np.nan,
                    "source": "feeder_slim",
                    "url": "",
                    "pos": str(df.at[i, "Pos"]) if "Pos" in df.columns else "",
                },
            )
            # keep max minutes across stat files
            m = float(minutes.at[i]) if pd.notna(minutes.at[i]) else np.nan
            if pd.notna(m) and (not pd.notna(row["minutes"]) or m > row["minutes"]):
                row["minutes"] = m
                row["squad"] = squad
            for col in mapped.columns:
                val = mapped.at[i, col]
                if pd.notna(val):
                    row[col] = float(val)
    if not by_key:
        return pd.DataFrame()
    return pd.DataFrame(list(by_key.values()))


def load_player_cache_rows() -> pd.DataFrame:
    rows = []
    for pq in sorted(PLAYER.glob("*.parquet")):
        try:
            df = pd.read_parquet(pq)
        except Exception:
            continue
        if df.empty:
            continue
        # Drop header junk rows
        if "Comp" in df.columns:
            df = df[df["Comp"].astype(str).str.lower() != "comp"].copy()
        if "Season" not in df.columns:
            continue
        df["season_end"] = df["Season"].map(season_str_to_end_year)
        df = df[df["season_end"].notna()].copy()
        if df.empty:
            continue
        player = str(df["player"].iloc[0]) if "player" in df.columns else pq.stem
        url = str(df["player_url"].iloc[0]) if "player_url" in df.columns else ""
        nk = player.strip().lower()

        # collapse duplicate season rows (multiple stat tables) by season+squad+comp
        for (season_end, squad, comp), sub in df.groupby(
            ["season_end", "Squad", "Comp"], dropna=False
        ):
            if is_bl_comp(str(comp)):
                continue  # priors only
            minutes = np.nan
            for c in ["Playing Time_Min", "Min", "Domestic Leagues_Min"]:
                if c in sub.columns:
                    minutes = numify(sub[c]).max()
                    break
            if not pd.notna(minutes) and "90s" in sub.columns:
                minutes = float(numify(sub["90s"]).max() * 90)
            mapped = map_feeder_metrics(sub)
            # take first non-null per metric across stacked tables
            metric_vals = {}
            for col in mapped.columns:
                v = mapped[col].dropna()
                if len(v):
                    metric_vals[col] = float(v.iloc[0])
            row = {
                "name_key": nk,
                "player": player,
                "season_end": int(season_end),
                "comp": str(comp),
                "squad": str(squad),
                "minutes": float(minutes) if pd.notna(minutes) else np.nan,
                "source": "player_page",
                "url": url,
                "pos": "",
                **metric_vals,
            }
            rows.append(row)
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows)


def prefer_metrics(bases: list[str]) -> list[str]:
    drop: set[str] = set()
    base_set = set(bases)
    for b in bases:
        if b.endswith("_Per"):
            raw = b[: -len("_Per")]
            if raw in base_set:
                drop.add(raw)
        if b.endswith("_Expected") and f"{b[: -len('_Expected')]}_Per" in base_set:
            drop.add(b)
        if "per_90" in b.lower():
            raw = re.sub(r"_?per_90_?", "", b, flags=re.I)
            if raw in base_set:
                drop.add(raw)
    return [b for b in bases if b not in drop]


def is_already_rate(nm: str) -> bool:
    return bool(
        re.search(r"_Per$|_pct|per_90|Per90|_percent", nm, re.I)
        or re.search(r"Cmp_percent|Succ_percent|SoT_percent|Won_percent|Tkl_percent", nm)
    )


def categorize(m: str) -> str:
    if re.search(r"Tkl|Int|Blocks|Clr|Err|Chall|Def|Aerial|Sh_Blocks|Pass_Blocks|Recov|Fls", m, re.I):
        return "Defending"
    if re.search(r"Pass|PrgP|Cmp|Prog|Final|KP|xA|xAG|TB|Sw|Crs|CK|PrgDist_Total|TotDist_Total", m, re.I):
        return "Passing"
    if re.search(r"Carr|PrgC|PrgR|Take|Drb|Mis|Dis|Touch|Att_Pen|CPA|Prog", m, re.I):
        return "Carrying"
    if re.search(r"Gls|Ast|xG|npxG|Sh|SoT|SCA|GCA|Shot|PK", m, re.I):
        return "Attacking"
    return "Other"


def abbrevize(m: str) -> str:
    a = re.sub(
        r"_Expected|_Per|_Playing|_Progression|_Performance|_Standard|_Total|"
        r"_Carries|_Touches|_Take|_Tackles|_Challenges|_Blocks|_Aerial|_Types",
        "",
        m,
    )
    a = a.replace("_", "")
    return a[:5].upper()


def nice_label(m: str) -> str:
    m = m.replace("_", " ")
    m = m.replace(" percent", "%").replace(" plus ", "+").replace(" per ", "/")
    return m


def source_rank(src: str) -> int:
    return {"big5": 0, "feeder_slim": 1, "player_page": 2}.get(src, 9)


def main() -> None:
    print("Loading Big5 wide…")
    wide = load_big5_wide()
    print(f"  big5 rows={len(wide)} cols={wide.shape[1]}")

    first_bl = (
        wide[wide["is_bl"]]
        .groupby("player_id", as_index=False)
        .agg(first_bl_season=("season_end", "min"), player_name=("player", "first"), name_key=("name_key", "first"))
    )
    first_bl = first_bl[first_bl["first_bl_season"] >= MIN_BL_SEASON]

    y1 = (
        wide[wide["is_bl"]]
        .merge(first_bl, on="player_id")
        .query("season_end == first_bl_season and minutes >= @MIN_Y1")
        .sort_values("minutes", ascending=False)
        .groupby("player_id", as_index=False)
        .first()
    )
    print(f"  Y1 eligible (BL>={MIN_BL_SEASON}, min>={MIN_Y1}): {len(y1)}")

    # Big5 priors
    big5_prior = (
        wide[~wide["is_bl"]]
        .merge(first_bl[["player_id", "first_bl_season"]], on="player_id")
        .query("season_end < first_bl_season and minutes >= @MIN_PRIOR")
        .copy()
    )
    big5_prior["source"] = "big5"

    print("Loading feeder slim…")
    feeder = load_feeder_slim_rows()
    print(f"  feeder rows={len(feeder)}")
    print("Loading player-page cache…")
    players = load_player_cache_rows()
    print(f"  player-page rows={len(players)}")

    # Align prior frames to a common column set for stacking
    meta_cols = [
        "player_id", "name_key", "player", "season_end", "comp", "squad",
        "minutes", "source", "url", "pos", "first_bl_season",
    ]

    # Attach player_id / first_bl to feeder & player via name_key
    name_to_id = (
        first_bl[["name_key", "player_id", "first_bl_season"]]
        .drop_duplicates("name_key")
    )

    def attach_ids(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        out = df.merge(name_to_id, on="name_key", how="inner")
        out = out[out["season_end"] < out["first_bl_season"]]
        out = out[out["minutes"].fillna(0) >= MIN_PRIOR]
        return out

    feeder_p = attach_ids(feeder)
    player_p = attach_ids(players)
    print(f"  feeder priors matching Y1 roster: {len(feeder_p)}")
    print(f"  player-page priors matching Y1 roster: {len(player_p)}")

    # Metric columns on Y1 (Big5 names)
    y1_meta = {
        "season_end", "player", "squad", "comp", "pos", "url", "minutes",
        "player_id", "is_bl", "first_bl_season", "player_name", "name_key",
        "source",
    }
    y1_metrics = [c for c in y1.columns if c not in y1_meta]

    # Build candidate prior pool
    prior_parts = []
    b5 = big5_prior.copy()
    b5_keep = [c for c in b5.columns if c in set(meta_cols) | set(y1_metrics) or c in meta_cols]
    # ensure meta
    for c in ["source"]:
        if c not in b5.columns:
            b5[c] = "big5"
    prior_parts.append(b5)

    for part in (feeder_p, player_p):
        if part.empty:
            continue
        # only keep metrics that exist on Y1
        keep = [c for c in part.columns if c in y1_metrics or c in {
            "player_id", "name_key", "player", "season_end", "comp", "squad",
            "minutes", "source", "url", "pos", "first_bl_season",
        }]
        prior_parts.append(part[keep])

    priors = pd.concat(prior_parts, ignore_index=True, sort=False)
    # Prefer latest season; within season prefer richer source, then more minutes
    priors["_src_rank"] = priors["source"].map(source_rank)
    priors = priors.sort_values(
        ["player_id", "season_end", "_src_rank", "minutes"],
        ascending=[True, False, True, False],
    )
    prior = priors.groupby("player_id", as_index=False).first()
    prior = prior.drop(columns=["_src_rank"], errors="ignore")

    # Rename prior cols up front so merge suffixes are unambiguous
    prior_renamed = prior.rename(
        columns={c: f"{c}_prior" for c in prior.columns if c != "player_id"}
    )
    y1_renamed = y1.rename(
        columns={c: f"{c}_y1" for c in y1.columns if c != "player_id"}
    )
    pairs = y1_renamed.merge(prior_renamed, on="player_id")
    print(f"PAIRS={len(pairs)}")
    print(pairs["source_prior"].value_counts().to_string())

    # Metric bases present on both sides
    y1_bases = [c[: -len("_y1")] for c in pairs.columns if c.endswith("_y1")]
    pr_bases = [c[: -len("_prior")] for c in pairs.columns if c.endswith("_prior")]
    meta_bases = {
        "season_end", "player", "squad", "comp", "pos", "url", "minutes",
        "player_id", "is_bl", "first_bl_season", "player_name", "name_key",
        "source",
    }
    metric_bases = prefer_metrics(
        sorted(set(y1_bases) & set(pr_bases) - meta_bases)
    )
    print(f"metrics after prefer={len(metric_bases)}")

    def make_val(suffix: str, base: str) -> np.ndarray:
        v = pairs[f"{base}_{suffix}"].to_numpy(dtype=float)
        mins = pairs[f"minutes_{suffix}"].to_numpy(dtype=float)
        if is_already_rate(base):
            return v
        out = np.full_like(v, np.nan, dtype=float)
        ok = np.isfinite(mins) & (mins > 0) & np.isfinite(v)
        out[ok] = v[ok] / mins[ok] * 90.0
        return out

    rows = []
    for base in metric_bases:
        x = make_val("prior", base)
        y = make_val("y1", base)
        if base in INVERT or re.search(r"^Mis_|^Dis_|^Err|Lost_|Tkld_", base):
            x = -x
            y = -y
        ok = np.isfinite(x) & np.isfinite(y)
        n = int(ok.sum())
        if n < MIN_PAIRS:
            continue
        if np.nanstd(x[ok]) < 1e-8 or np.nanstd(y[ok]) < 1e-8:
            continue
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        if not np.isfinite(r):
            continue
        rows.append(
            {
                "metric": base,
                "n_pairs": n,
                "stability_r": r,
                "passes_0_40": r >= 0.40,
                "passes_0_50": r >= 0.50,
                "passes_0_70": r >= 0.70,
                "category": categorize(base),
                "abbrev": abbrevize(base),
                "label": nice_label(base),
            }
        )

    stab = pd.DataFrame(rows).sort_values("stability_r", ascending=False)
    for g in GATES:
        col = f"passes_{str(g).replace('.', '_')}"
        # already have passes_0_40 etc
        pass

    pairs_out = pd.DataFrame(
        {
            "player_id": pairs["player_id"],
            "player": pairs["player_y1"],
            "prior_season": pairs["season_end_prior"],
            "prior_comp": pairs["comp_prior"],
            "prior_squad": pairs["squad_prior"],
            "prior_minutes": pairs["minutes_prior"],
            "prior_source": pairs["source_prior"],
            "y1_season": pairs["season_end_y1"],
            "y1_squad": pairs["squad_y1"],
            "y1_minutes": pairs["minutes_y1"],
            "pos": pairs["pos_y1"],
        }
    )

    OUT.mkdir(parents=True, exist_ok=True)
    stab.to_csv(OUT / "fbref_stability_all_metrics.csv", index=False)
    stab[stab["passes_0_40"]].to_csv(OUT / "fbref_stability_passed_r040.csv", index=False)
    stab[stab["passes_0_50"]].to_csv(OUT / "fbref_stability_passed_r050.csv", index=False)
    stab[stab["passes_0_70"]].to_csv(OUT / "fbref_stability_passed_r070.csv", index=False)
    pairs_out.to_csv(OUT / "fbref_inbound_pairs.csv", index=False)

    summary = {
        "source": "FBref season tables from 19 leagues",
        "min_bl_season": MIN_BL_SEASON,
        "min_prior_minutes": MIN_PRIOR,
        "min_y1_minutes": MIN_Y1,
        "n_pairs": int(len(pairs)),
        "n_pairs_by_prior_source": pairs_out["prior_source"].value_counts().to_dict(),
        "n_metrics_tested": int(len(stab)),
        "n_pass_0_40": int(stab["passes_0_40"].sum()),
        "n_pass_0_50": int(stab["passes_0_50"].sum()),
        "n_pass_0_70": int(stab["passes_0_70"].sum()),
        "top_20": stab.head(20)[["metric", "stability_r", "n_pairs", "category"]].to_dict("records"),
    }
    (OUT / "fbref_cohort_summary.json").write_text(json.dumps(summary, indent=2))

    md = [
        "# FBref stability — Bundesliga inbound (expanded)",
        "",
        f"**Source:** {summary['source']}",
        f"**First BL seasons:** ≥ {MIN_BL_SEASON}",
        f"**Minutes:** prior ≥ {int(MIN_PRIOR)} · BL Y1 ≥ {int(MIN_Y1)}",
        f"**Paired inbound N:** **{len(pairs)}**",
        f"**Prior sources:** {summary['n_pairs_by_prior_source']}",
        f"**Metrics tested:** {len(stab)}",
        f"**Passed r ≥ 0.40:** **{summary['n_pass_0_40']}**",
        f"**Passed r ≥ 0.50:** **{summary['n_pass_0_50']}**",
        f"**Passed r ≥ 0.70:** **{summary['n_pass_0_70']}**",
        "",
        "## Gate comparison (pick before redundancy)",
        "",
        "| Gate | Metrics passing |",
        "|---|---:|",
        f"| r ≥ 0.40 | {summary['n_pass_0_40']} |",
        f"| r ≥ 0.50 | {summary['n_pass_0_50']} |",
        f"| r ≥ 0.70 | {summary['n_pass_0_70']} |",
        "",
        "## Top 25 by stability r",
        "",
        "| Abbrev | Metric | Category | r | N | ≥.40 | ≥.50 | ≥.70 |",
        "|---|---|---|---:|---:|:---:|:---:|:---:|",
    ]
    for _, row in stab.head(25).iterrows():
        md.append(
            f"| {row.abbrev} | {row.label} | {row.category} | {row.stability_r:.3f} | "
            f"{int(row.n_pairs)} | {'Y' if row.passes_0_40 else ''} | "
            f"{'Y' if row.passes_0_50 else ''} | {'Y' if row.passes_0_70 else ''} |"
        )
    md += [
        "",
        "## All metrics at r ≥ 0.50",
        "",
        "| Abbrev | Metric | Category | r | N |",
        "|---|---|---|---:|---:|",
    ]
    for _, row in stab[stab["passes_0_50"]].iterrows():
        md.append(
            f"| {row.abbrev} | {row.label} | {row.category} | "
            f"{row.stability_r:.3f} | {int(row.n_pairs)} |"
        )
    (OUT / "FBREF_RESULTS.md").write_text("\n".join(md) + "\n")

    print("\n=== SUMMARY ===")
    print(json.dumps({k: summary[k] for k in summary if k != "top_20"}, indent=2))
    print("\nTop 15:")
    print(stab.head(15)[["metric", "stability_r", "n_pairs", "passes_0_40", "passes_0_50", "passes_0_70"]].to_string(index=False))
    print("\nDONE → results/fbref_stability_*.csv, FBREF_RESULTS.md")


if __name__ == "__main__":
    main()
