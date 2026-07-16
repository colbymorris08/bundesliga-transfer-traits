#!/usr/bin/env python3
"""Sequential FBref feeder scrape + merge with Big5 cache → broad stability."""
from __future__ import annotations

import json
import re
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from lxml import html

ROOT = Path("/Users/colbymorris/bundesliga-transfer-traits")
OUT = ROOT / "results"
CACHE = OUT / "fbref_broad_cache"
HTML_DIR = Path("/Users/colbymorris/soccerdata/data/FBref")
R_CACHE = OUT / "fbref_cache"
CACHE.mkdir(parents=True, exist_ok=True)

SEASONS = ["1718", "1819", "1920", "2021", "2122", "2223", "2324", "2425"]
# Map soccerdata season code → end year
def end_year(code: str) -> int:
    return 2000 + int(code[2:4])

FEEDERS = [
    "GER-2.Bundesliga",
    "AUT-Bundesliga",
    "NED-Eredivisie",
    "ENG-Championship",
    "BEL-Pro League",
    "POR-Primeira Liga",
    "TUR-Super Lig",
    "SUI-Super League",
    "DEN-Superliga",
    "SCO-Premiership",
    "FRA-Ligue 2",
    "ITA-Serie B",
    "ESP-Segunda",
    "POL-Ekstraklasa",
    "CZE-First League",
    "CRO-Football League",
    "GRE-Super League",
    "USA-MLS",
    "MEX-Liga MX",
    "SWE-Allsvenskan",
    "NOR-Eliteserien",
]

MIN_PRIOR = 450.0
MIN_Y1 = 450.0
STABILITY_GATE = 0.40
REDUNDANCY_GATE = 0.70
MIN_PAIRS = 25


def parse_player_html(path: Path) -> pd.DataFrame | None:
    text = path.read_text(errors="ignore")
    comments = re.findall(r"<!--(.*?)-->", text, flags=re.S)
    blobs = [text] + comments
    best = None
    for blob in blobs:
        try:
            t = html.fromstring(blob)
        except Exception:
            continue
        for table in t.xpath("//table[contains(@id,'stats_standard')]"):
            headers = [th.text_content().strip() for th in table.xpath(".//thead/tr[last()]/th")]
            if len(headers) < 8:
                continue
            rows = []
            for tr in table.xpath(".//tbody/tr"):
                cls = tr.get("class") or ""
                if "thead" in cls:
                    continue
                cells = [td.text_content().strip() for td in tr.xpath("./th|./td")]
                if len(cells) < 5:
                    continue
                n = len(headers)
                rows.append(cells[:n] + [""] * max(0, n - len(cells)))
            if rows and (best is None or len(rows) > len(best[1])):
                best = (headers, rows)
    if not best:
        return None
    headers, rows = best
    # uniquify headers
    seen = {}
    uniq = []
    for h in headers:
        if h not in seen:
            seen[h] = 0
            uniq.append(h)
        else:
            seen[h] += 1
            uniq.append(f"{h}_{seen[h]}")
    return pd.DataFrame(rows, columns=uniq)


def scrape_one(league: str, season: str) -> Path | None:
    """Use soccerdata to fetch HTML into its cache; return path if present."""
    import soccerdata as sd

    safe = league.replace(" ", "_")
    # soccerdata cache naming
    # players_{league}_{season}_standard.html
    expected = HTML_DIR / f"players_{league}_{season}_standard.html"
    if expected.exists() and expected.stat().st_size > 10000:
        return expected

    print(f"SCRAPE {league} {season}", flush=True)
    try:
        fb = sd.FBref(leagues=league, seasons=season)
        _ = fb.read_player_season_stats(stat_type="standard")
    except Exception as e:
        print(f"  scrape error: {e}", flush=True)
        traceback.print_exc()
        return expected if expected.exists() else None

    return expected if expected.exists() else None


def load_r_big5_standard() -> pd.DataFrame:
    frames = []
    for path in sorted(R_CACHE.glob("standard_*.csv")):
        year = int(path.stem.split("_")[1])
        df = pd.read_csv(path)
        df["season_end"] = year
        df["source"] = "big5_dump"
        # league key
        comp = df["Comp"].astype(str)
        lk = pd.Series(["Other"] * len(df))
        lk = lk.mask(comp.str.contains("Premier League", case=False), "ENG-Premier League")
        lk = lk.mask(comp.eq("La Liga") | comp.str.contains("La Liga", case=False), "ESP-La Liga")
        lk = lk.mask(comp.str.contains("Serie A", case=False), "ITA-Serie A")
        lk = lk.mask(comp.str.contains("Ligue 1", case=False), "FRA-Ligue 1")
        lk = lk.mask(comp.str.contains("Bundesliga", case=False), "GER-Bundesliga")
        df["league_key"] = lk

        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    out["player"] = out["Player"].astype(str)
    out["squad"] = out["Squad"].astype(str)
    out["minutes"] = pd.to_numeric(out["Min_Playing"], errors="coerce")
    out["player_id"] = out["Url"].fillna("name:" + out["player"]).astype(str)
    # metrics
    for c in ["Gls_Per", "Ast_Per", "xG_Per", "npxG_Per", "xAG_Per",
              "PrgC_Progression", "PrgP_Progression", "PrgR_Progression",
              "Gls", "Ast", "xG_Expected", "npxG_Expected"]:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors="coerce")
    return out


def normalize_feeder_df(df: pd.DataFrame, league: str, season: str) -> pd.DataFrame:
    # Map FBref table columns to our names
    col = {c: c for c in df.columns}
    # Minutes
    min_col = "Min" if "Min" in df.columns else None
    out = pd.DataFrame({
        "player": df["Player"].astype(str),
        "squad": df["Squad"].astype(str) if "Squad" in df.columns else "unknown",
        "minutes": pd.to_numeric(df[min_col], errors="coerce") if min_col else np.nan,
        "league_key": league,
        "season_end": end_year(season),
        "source": "feeder_scrape",
        "player_id": "name:" + df["Player"].astype(str).str.strip().str.lower(),
    })
    # Per-90 already in table often duplicated - FBref has Gls both counting and per90 as duplicate header
    # After uniquify, second Gls becomes Gls_1 which is often per90 section
    # Prefer columns from Per 90 section if present
    mapping = {
        "Gls_Per": ["Gls_1", "Gls"],
        "Ast_Per": ["Ast_1", "Ast"],
        "xG_Per": ["xG_1", "xG"],
        "npxG_Per": ["npxG_1", "npxG"],
        "xAG_Per": ["xAG_1", "xAG"],
        "PrgC_Progression": ["PrgC", "PrgC_1"],
        "PrgP_Progression": ["PrgP", "PrgP_1"],
        "PrgR_Progression": ["PrgR", "PrgR_1"],
    }
    for dest, cands in mapping.items():
        for c in cands:
            if c in df.columns:
                out[dest] = pd.to_numeric(df[c], errors="coerce")
                break
    # If Prg* look like season counts (median large), convert to per90
    for c in ["PrgC_Progression", "PrgP_Progression", "PrgR_Progression"]:
        if c in out.columns:
            med = out[c].median(skipna=True)
            if pd.notna(med) and med > 5:
                out[c] = out[c] / out["minutes"] * 90
    return out


def main():
    # 1) Big5 base
    big5 = load_r_big5_standard()
    print("big5 rows", len(big5), "BL rows", (big5.league_key == "GER-Bundesliga").sum())

    # 2) Scrape feeders sequentially
    feeder_frames = []
    for league in FEEDERS:
        for season in SEASONS:
            pq = CACHE / f"{league.replace(' ','_').replace('.','')}_{season}_standard.parquet"
            if pq.exists():
                feeder_frames.append(pd.read_parquet(pq))
                print("cache hit", pq.name)
                continue
            path = scrape_one(league, season)
            if path is None:
                print("  miss", league, season)
                time.sleep(2)
                continue
            parsed = parse_player_html(path)
            if parsed is None or len(parsed) < 10:
                print("  parse fail", path)
                continue
            norm = normalize_feeder_df(parsed, league, season)
            norm.to_parquet(pq, index=False)
            feeder_frames.append(norm)
            print(f"  ok {league} {season}: {len(norm)}")
            time.sleep(2)

    # 3) Combine
    keep_cols = [
        "player", "squad", "minutes", "league_key", "season_end", "source", "player_id",
        "Gls_Per", "Ast_Per", "xG_Per", "npxG_Per", "xAG_Per",
        "PrgC_Progression", "PrgP_Progression", "PrgR_Progression",
    ]
    base = big5[[c for c in keep_cols if c in big5.columns]].copy()
    if feeder_frames:
        feed = pd.concat(feeder_frames, ignore_index=True)
        feed = feed[[c for c in keep_cols if c in feed.columns]]
        all_df = pd.concat([base, feed], ignore_index=True)
    else:
        all_df = base
        print("WARNING: no feeder frames yet — Big5 only")

    all_df = all_df[all_df["minutes"].fillna(0) > 0].copy()
    all_df["is_bl"] = all_df["league_key"].eq("GER-Bundesliga")

    # Harmonize player_id: prefer url for big5, name for feeders — also add name key for matching
    all_df["name_key"] = all_df["player"].str.strip().str.lower()

    # First BL by name_key (more inclusive across sources)
    bl = all_df[all_df["is_bl"]]
    first_bl = (
        bl.groupby("name_key", as_index=False)
        .agg(first_bl_season=("season_end", "min"), player=("player", "first"))
    )
    print("BL players", len(first_bl))

    y1 = bl.merge(first_bl, on="name_key")
    y1 = y1[(y1["season_end"] == y1["first_bl_season"]) & (y1["minutes"] >= MIN_Y1)]
    y1 = y1.sort_values("minutes").groupby("name_key", as_index=False).tail(1)

    prior = all_df[~all_df["is_bl"]].merge(first_bl, on="name_key")
    prior = prior[(prior["season_end"] < prior["first_bl_season"]) & (prior["minutes"] >= MIN_PRIOR)]
    prior = prior.sort_values(["name_key", "season_end", "minutes"]).groupby("name_key", as_index=False).tail(1)

    pairs = y1.merge(prior, on="name_key", suffixes=("_y1", "_prior"))
    print("PAIRS", len(pairs))
    print(pairs["league_key_prior"].value_counts().head(25))

    metrics = [
        "Gls_Per", "Ast_Per", "xG_Per", "npxG_Per", "xAG_Per",
        "PrgC_Progression", "PrgP_Progression", "PrgR_Progression",
    ]
    rows = []
    for m in metrics:
        xc, yc = f"{m}_prior", f"{m}_y1"
        if xc not in pairs.columns or yc not in pairs.columns:
            continue
        x = pd.to_numeric(pairs[xc], errors="coerce")
        y = pd.to_numeric(pairs[yc], errors="coerce")
        ok = x.notna() & y.notna()
        n = int(ok.sum())
        if n < MIN_PAIRS:
            continue
        if x[ok].std() < 1e-8 or y[ok].std() < 1e-8:
            continue
        r = float(np.corrcoef(x[ok], y[ok])[0, 1])
        if not np.isfinite(r):
            continue
        rows.append({
            "metric": m, "n_pairs": n, "stability_r": r,
            "passes_0_40": r >= STABILITY_GATE, "passes_0_70": r >= 0.70,
            "category": "Attacking" if any(k in m for k in ["Gls","Ast","xG","npxG","xAG"]) else "Carrying" if "PrgC" in m or "PrgR" in m else "Passing",
            "abbrev": m[:5].upper(), "label": m,
        })

    stab = pd.DataFrame(rows).sort_values("stability_r", ascending=False)
    print(stab)

    # redundancy
    passed = stab[stab["passes_0_40"]]
    red = []
    mets = passed["metric"].tolist()
    for i, a in enumerate(mets):
        for b in mets[:i]:
            ya = pd.to_numeric(pairs[f"{a}_y1"], errors="coerce")
            yb = pd.to_numeric(pairs[f"{b}_y1"], errors="coerce")
            ok = ya.notna() & yb.notna()
            if ok.sum() < MIN_PAIRS:
                continue
            r = float(np.corrcoef(ya[ok], yb[ok])[0, 1])
            if abs(r) >= REDUNDANCY_GATE:
                red.append({"metric_a": b, "metric_b": a, "r": r})
    red_df = pd.DataFrame(red).sort_values("r", key=lambda s: s.abs(), ascending=False) if red else pd.DataFrame(columns=["metric_a","metric_b","r"])

    auto = mets[:]
    if len(red_df):
        drop = set()
        rmap = dict(zip(passed["metric"], passed["stability_r"]))
        for _, row in red_df.iterrows():
            a, b = row["metric_a"], row["metric_b"]
            if a in drop or b in drop:
                continue
            if rmap.get(a, 0) >= rmap.get(b, 0):
                drop.add(b)
            else:
                drop.add(a)
        auto = [m for m in auto if m not in drop]

    # write
    stab.to_csv(OUT / "fbref_stability_all_metrics.csv", index=False)
    passed.to_csv(OUT / "fbref_stability_passed_r040.csv", index=False)
    stab[stab["passes_0_70"]].to_csv(OUT / "fbref_stability_passed_r070.csv", index=False)
    red_df.to_csv(OUT / "fbref_redundancy_high_pairs_step2.csv", index=False)
    pd.DataFrame({"metric": auto, "note": "AUTO"}).to_csv(OUT / "fbref_redundancy_auto_shortlist_suggestion.csv", index=False)
    pairs_out = pd.DataFrame({
        "player": pairs["player_y1"],
        "prior_season": pairs["season_end_prior"],
        "prior_league": pairs["league_key_prior"],
        "prior_squad": pairs["squad_prior"],
        "prior_minutes": pairs["minutes_prior"],
        "y1_season": pairs["season_end_y1"],
        "y1_squad": pairs["squad_y1"],
        "y1_minutes": pairs["minutes_y1"],
    })
    pairs_out.to_csv(OUT / "fbref_inbound_pairs.csv", index=False)

    summary = {
        "source": "FBref Big5 dump + soccerdata feeder leagues (broad)",
        "n_pairs": int(len(pairs)),
        "n_metrics_tested": int(len(stab)),
        "n_pass_0_40": int(passed.shape[0]),
        "n_pass_0_70": int(stab["passes_0_70"].sum()) if len(stab) else 0,
        "n_redundancy_pairs": int(len(red_df)),
        "auto_shortlist_n": int(len(auto)),
        "auto_shortlist": auto,
        "prior_league_counts": pairs["league_key_prior"].value_counts().to_dict(),
        "statsbomb_analysis_n": 60,
        "min_prior_minutes": MIN_PRIOR,
        "min_y1_minutes": MIN_Y1,
        "feeder_frames": int(len(feeder_frames)),
    }
    (OUT / "fbref_cohort_summary.json").write_text(json.dumps(summary, indent=2))

    md = [
        "# FBref stability — broad inbound",
        "",
        f"**StatsBomb analysis cohort:** **60** players",
        f"**FBref paired inbound N:** **{len(pairs)}**",
        f"**Pass r≥0.40:** {int(passed.shape[0])} / {len(stab)} tested (standard-metric overlap)",
        "",
        "## Prior leagues",
        "",
    ]
    for k, v in pairs["league_key_prior"].value_counts().items():
        md.append(f"- {k}: {v}")
    md += ["", "## Stability", "", "| Metric | r | N |", "|---|---:|---:|"]
    for _, r in stab.iterrows():
        md.append(f"| {r['metric']} | {r['stability_r']:.3f} | {r['n_pairs']} |")
    (OUT / "FBREF_RESULTS.md").write_text("\n".join(md) + "\n")
    print("DONE", summary)


if __name__ == "__main__":
    main()
