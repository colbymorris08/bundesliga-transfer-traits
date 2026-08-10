#!/usr/bin/env python3
"""Bundesliga inbound traits — StatsBomb open data.
Stability (prior→Y1) @ r>=0.70 → redundancy for Step 2 → pizzas with avg dotted line.
"""
from __future__ import annotations

import json
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/Users/colbymorris/bundesliga-transfer-traits")
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)
CACHE = OUT / "sb_cache"
CACHE.mkdir(exist_ok=True)
# Prefer project cache; fall back to legacy /tmp cache for lineups already fetched
LEGACY_CACHE = Path("/tmp/sb-cache")
BASE = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

STABILITY_THRESHOLD = 0.70
MIN_PRIOR = 45.0   # relaxed to grow open-data cohort
MIN_Y1 = 30.0
MIN_PAIRS = 10

POS_MAP = {
    "Left Back": "Full Back", "Right Back": "Full Back",
    "Left Wing Back": "Full Back", "Right Wing Back": "Full Back",
    "Left Center Back": "Central Defender", "Right Center Back": "Central Defender",
    "Center Back": "Central Defender",
    "Left Defensive Midfield": "Central Midfielder",
    "Right Defensive Midfield": "Central Midfielder",
    "Center Defensive Midfield": "Central Midfielder",
    "Defensive Midfield": "Central Midfielder",
    "Left Center Midfield": "Central Midfielder",
    "Right Center Midfield": "Central Midfielder",
    "Center Midfield": "Central Midfielder",
    "Left Attacking Midfield": "Attacking Midfielder",
    "Right Attacking Midfield": "Attacking Midfielder",
    "Center Attacking Midfield": "Attacking Midfielder",
    "Left Wing": "Winger", "Right Wing": "Winger",
    "Left Midfield": "Winger", "Right Midfield": "Winger",
    "Center Forward": "Forward", "Secondary Striker": "Forward",
    "Striker": "Forward", "Goalkeeper": "Goalkeeper",
}

METRIC_META = {
    "passes": ("PAS", "Passing", "Pass volume"),
    "pass_progressive": ("PPC", "Passing", "Progressive passes (~10m+ toward goal)"),
    "passes_into_final_third": ("PATT", "Passing", "Passes into final third"),
    "shots": ("SH", "Attacking", "Shots"),
    "xg": ("XG", "Attacking", "Non-pen xG"),
    "xa": ("XA", "Attacking", "Expected assists"),
    "pressures": ("PRS", "Defending", "Pressures"),
    "tackles": ("TAC", "Defending", "Tackles"),
    "interceptions": ("INT", "Defending", "Interceptions"),
    "clearances": ("CLR", "Defending", "Clearances"),
    "aerials_won": ("AER", "Defending", "Aerials won"),
    "dribbles_completed": ("DRB", "Carrying", "Successful dribbles"),
    "carries": ("CRY", "Carrying", "Carries"),
    "carry_progressive": ("CFGP", "Carrying", "Progressive carries"),
    "fouls_won": ("FLW", "Other", "Fouls won"),
    "dispossessed": ("DIS", "Other", "Dispossessed (inverted)"),
}

CAT_COLOR = {
    "Defending": "#3d5a80", "Passing": "#2a6f97", "Carrying": "#52796f",
    "Attacking": "#bc4749", "Other": "#6c757d",
}


def fetch_json(path: str):
    key = path.replace("/", "__")
    cache_path = CACHE / key
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    legacy = LEGACY_CACHE / key
    if legacy.exists():
        data = json.loads(legacy.read_text())
        cache_path.write_text(json.dumps(data))
        return data
    data = json.loads(urllib.request.urlopen(f"{BASE}/{path}", timeout=60).read())
    cache_path.write_text(json.dumps(data))
    return data


def sy(name: str) -> int:
    return int(name.split("/")[0]) if "/" in name else int(name)


def parse_clock(value):
    if value is None:
        return None
    parts = str(value).split(":")
    if len(parts) == 2:
        return int(parts[0]) + int(parts[1]) / 60.0
    return float(parts[0])


def minutes_from_positions(positions):
    total = 0.0
    for pos in positions or []:
        start = parse_clock(pos.get("from", "00:00"))
        end = parse_clock(pos.get("to"))
        if start is None:
            continue
        if end is None:
            end = 95.0
        total += max(0.0, end - start)
    return total


def primary_position(pos_minutes: dict) -> str:
    return max(pos_minutes, key=pos_minutes.get) if pos_minutes else "Unknown"


def progressive(loc_start, loc_end):
    if not loc_start or not loc_end or len(loc_start) < 2 or len(loc_end) < 2:
        return False
    return (loc_end[0] - loc_start[0]) >= 10.0


def empty_bag():
    return {k: 0.0 for k in METRIC_META}


def accumulate_events(events, bags, needed):
    shot_xg_by_key_pass = {}
    for ev in events:
        if ev.get("type", {}).get("name") != "Shot":
            continue
        if ev.get("shot", {}).get("type", {}).get("name") == "Penalty":
            continue
        xg = ev.get("shot", {}).get("statsbomb_xg") or 0.0
        kp = ev.get("shot", {}).get("key_pass_id")
        if kp:
            shot_xg_by_key_pass[kp] = xg

    for ev in events:
        player = ev.get("player") or {}
        pid = player.get("id")
        if pid is None or pid not in needed:
            continue
        bag = bags.get(pid)
        if bag is None:
            continue
        tname = (ev.get("type") or {}).get("name")

        if tname == "Pass":
            bag["passes"] += 1
            loc = ev.get("location")
            end = ev.get("pass", {}).get("end_location")
            if progressive(loc, end):
                bag["pass_progressive"] += 1
            if end and len(end) >= 1 and end[0] >= 80:
                bag["passes_into_final_third"] += 1
            if ev.get("id") in shot_xg_by_key_pass:
                bag["xa"] += shot_xg_by_key_pass[ev["id"]]
        elif tname == "Shot":
            if ev.get("shot", {}).get("type", {}).get("name") == "Penalty":
                continue
            bag["shots"] += 1
            bag["xg"] += ev.get("shot", {}).get("statsbomb_xg") or 0.0
        elif tname == "Pressure":
            bag["pressures"] += 1
        elif tname == "Duel":
            duel = ev.get("duel", {})
            dtype = (duel.get("type") or {}).get("name") or ""
            if dtype == "Tackle":
                bag["tackles"] += 1
            if dtype == "Aerial Won" or (dtype.startswith("Aerial") and (duel.get("outcome") or {}).get("name") in ("Won", "Success In Play", "Success Out")):
                bag["aerials_won"] += 1
        elif tname == "Interception":
            bag["interceptions"] += 1
        elif tname == "Clearance":
            bag["clearances"] += 1
            if ev.get("clearance", {}).get("aerial_won"):
                bag["aerials_won"] += 1
        elif tname == "Dribble":
            if (ev.get("dribble") or {}).get("outcome", {}).get("name") == "Complete":
                bag["dribbles_completed"] += 1
        elif tname == "Carry":
            bag["carries"] += 1
            loc = ev.get("location")
            end = (ev.get("carry") or {}).get("end_location")
            if progressive(loc, end):
                bag["carry_progressive"] += 1
        elif tname == "Foul Won":
            bag["fouls_won"] += 1
        elif tname in ("Miscontrol", "Dispossessed"):
            bag["dispossessed"] += 1


def load_comp_season(comp_id, season_id):
    matches = fetch_json(f"matches/{comp_id}/{season_id}.json")
    players = defaultdict(lambda: {
        "minutes": 0.0, "pos_minutes": defaultdict(float),
        "name": None, "match_ids": set(),
    })
    for match in matches:
        mid = match["match_id"]
        try:
            lineups = fetch_json(f"lineups/{mid}.json")
        except Exception:
            continue
        for side in lineups:
            for bucket in ("lineup", "substitutes"):
                for p in side.get(bucket, []):
                    pid = p["player_id"]
                    mins = minutes_from_positions(p.get("positions"))
                    if mins <= 0:
                        continue
                    players[pid]["minutes"] += mins
                    players[pid]["name"] = p.get("player_name") or players[pid]["name"]
                    players[pid]["match_ids"].add(mid)
                    for pos in p.get("positions", []):
                        grp = POS_MAP.get(pos.get("position"), "Other")
                        seg = minutes_from_positions([pos])
                        if seg > 0:
                            players[pid]["pos_minutes"][grp] += seg
    return players, matches


def bag_to_p90(bag, minutes):
    if minutes < 1:
        return {k: np.nan for k in bag}
    scale = 90.0 / minutes
    out = {k: bag[k] * scale for k in bag}
    out["dispossessed"] = -out["dispossessed"]
    return out


def percentile_of(value, peer_series):
    peer = peer_series.dropna()
    if len(peer) < 5 or value != value:
        return np.nan
    return float((peer <= value).mean() * 100.0)


def main():
    print("Loading competitions…")
    comps = fetch_json("competitions.json")
    available = {
        (c["competition_name"], c["season_name"]): (
            c["competition_id"], c["season_id"], c.get("competition_gender", "male")
        )
        for c in comps
    }

    hist_lineups = {}
    hist_matches = {}
    # Use ALL male open-data competitions / seasons (max prior coverage for BL inbounds)
    for (cname, sname), (cid, sid, gender) in sorted(available.items()):
        if str(gender).lower() not in ("male", "m"):
            continue
        print(f"  lineups {cname} {sname}", flush=True)
        try:
            players, matches = load_comp_season(cid, sid)
        except Exception as e:
            print(f"    SKIP {cname} {sname}: {e}", flush=True)
            continue
        hist_lineups[(cname, sname)] = players
        hist_matches[(cname, sname)] = matches
        print(f"    players={len(players)} matches={len(matches)}")

    bundes_seasons = sorted([s for (c, s) in hist_lineups if c == "1. Bundesliga"], key=sy)
    timeline = defaultdict(list)
    for (comp, season), players in hist_lineups.items():
        for pid, pdata in players.items():
            timeline[pid].append({
                "comp": comp, "season": season, "year": sy(season),
                "minutes": pdata["minutes"],
            })

    cohort_rows = []
    for dest_season in bundes_seasons:
        dest_players = hist_lineups[("1. Bundesliga", dest_season)]
        dest_year = sy(dest_season)
        for pid, pdata in dest_players.items():
            if any(e["comp"] == "1. Bundesliga" and e["year"] < dest_year and e["minutes"] > 0 for e in timeline[pid]):
                continue
            prior_ext = [e for e in timeline[pid] if e["comp"] != "1. Bundesliga" and e["year"] < dest_year]
            prior_mins = sum(e["minutes"] for e in prior_ext)
            if prior_mins < MIN_PRIOR or pdata["minutes"] < MIN_Y1:
                continue
            by_league = defaultdict(float)
            for e in prior_ext:
                by_league[e["comp"]] += e["minutes"]
            cohort_rows.append({
                "player_id": pid,
                "name": pdata["name"],
                "arrival_season": dest_season,
                "position": primary_position(pdata["pos_minutes"]),
                "prior_minutes": round(prior_mins, 1),
                "y1_minutes": round(pdata["minutes"], 1),
                "prior_leagues": dict(sorted(by_league.items(), key=lambda x: -x[1])),
            })

    cohort_df = pd.DataFrame(cohort_rows)
    print(f"\nCohort N={len(cohort_df)} (≥{MIN_PRIOR} prior, ≥{MIN_Y1} Y1)")
    cohort_df.to_csv(OUT / "cohort.csv", index=False)

    player_prior_matches = defaultdict(set)
    player_bl_matches = defaultdict(set)
    needed_event_matches = set()

    for row in cohort_rows:
        pid = row["player_id"]
        dest = row["arrival_season"]
        dest_year = sy(dest)
        for (comp, season), players in hist_lineups.items():
            if pid not in players:
                continue
            if comp == "1. Bundesliga" and season == dest:
                for mid in players[pid]["match_ids"]:
                    player_bl_matches[pid].add(mid)
                    needed_event_matches.add(mid)
            elif comp != "1. Bundesliga" and sy(season) < dest_year:
                for mid in players[pid]["match_ids"]:
                    player_prior_matches[pid].add(mid)
                    needed_event_matches.add(mid)

    bl_peer_players = set()
    bl_match_ids = set()
    bl_minutes_all = {}
    for season in bundes_seasons:
        for m in hist_matches[("1. Bundesliga", season)]:
            bl_match_ids.add(m["match_id"])
            needed_event_matches.add(m["match_id"])
        for pid, pdata in hist_lineups[("1. Bundesliga", season)].items():
            bl_minutes_all[pid] = bl_minutes_all.get(pid, 0.0) + pdata["minutes"]
            if pdata["minutes"] >= MIN_Y1:
                bl_peer_players.add(pid)

    print(f"Event matches to process: {len(needed_event_matches)}")

    prior_bags = {int(r["player_id"]): empty_bag() for r in cohort_rows}
    bl_bags = {int(pid): empty_bag() for pid in (set(cohort_df["player_id"]) | bl_peer_players)}

    n_ok = n_fail = 0
    for i, mid in enumerate(sorted(needed_event_matches), 1):
        if i % 40 == 0 or i == 1:
            print(f"  events {i}/{len(needed_event_matches)} ok={n_ok} fail={n_fail}", flush=True)
        try:
            events = fetch_json(f"events/{mid}.json")
            n_ok += 1
        except Exception as e:
            n_fail += 1
            if n_fail <= 5:
                print(f"    event fail {mid}: {e}", flush=True)
            continue
        if mid in bl_match_ids:
            accumulate_events(events, bl_bags, set(bl_bags.keys()))
        prior_pids = {int(pid) for pid, mids in player_prior_matches.items() if mid in mids}
        if prior_pids:
            accumulate_events(events, prior_bags, prior_pids)

    print(f"  events done ok={n_ok} fail={n_fail}", flush=True)
    # smoke check
    sample_pid = int(cohort_rows[0]["player_id"])
    print(f"  sample prior bag {sample_pid}: {prior_bags[sample_pid]}", flush=True)
    print(f"  sample y1 bag {sample_pid}: {bl_bags.get(sample_pid)}", flush=True)

    prior_minutes = {r["player_id"]: r["prior_minutes"] for r in cohort_rows}
    y1_minutes = {r["player_id"]: r["y1_minutes"] for r in cohort_rows}

    prior_df = pd.DataFrame([
        {"player_id": r["player_id"], **bag_to_p90(prior_bags[r["player_id"]], prior_minutes[r["player_id"]])}
        for r in cohort_rows
    ])
    y1_df = pd.DataFrame([
        {"player_id": r["player_id"], **bag_to_p90(bl_bags[r["player_id"]], y1_minutes[r["player_id"]])}
        for r in cohort_rows
    ])
    peer_df = pd.DataFrame([
        {"player_id": pid, **bag_to_p90(bl_bags[pid], bl_minutes_all[pid])}
        for pid in bl_peer_players if bl_minutes_all.get(pid, 0) >= MIN_Y1 and pid in bl_bags
    ])

    prior_df.to_csv(OUT / "prior_p90.csv", index=False)
    y1_df.to_csv(OUT / "y1_p90.csv", index=False)
    peer_df.to_csv(OUT / "peer_p90.csv", index=False)

    metrics = list(METRIC_META.keys())
    merged = prior_df.merge(y1_df, on="player_id", suffixes=("_prior", "_y1"))
    stability_rows = []
    for m in metrics:
        a = merged[f"{m}_prior"]
        b = merged[f"{m}_y1"]
        mask = a.notna() & b.notna() & np.isfinite(a) & np.isfinite(b)
        n = int(mask.sum())
        r = float(np.corrcoef(a[mask], b[mask])[0, 1]) if n >= MIN_PAIRS else np.nan
        # skip constant vectors (all-zero bags → undefined corr)
        if n >= MIN_PAIRS and (float(np.nanstd(a[mask])) < 1e-12 or float(np.nanstd(b[mask])) < 1e-12):
            r = np.nan
        stability_rows.append({
            "metric": m,
            "abbrev": METRIC_META[m][0],
            "category": METRIC_META[m][1],
            "label": METRIC_META[m][2],
            "n_pairs": n,
            "stability_r": None if r != r else round(r, 4),
            "passes_0_40": bool(r == r and r >= 0.40),
            "passes_0_50": bool(r == r and r >= 0.50),
            "passes_0_70": bool(r == r and r >= STABILITY_THRESHOLD),
        })

    stab = pd.DataFrame(stability_rows).sort_values("stability_r", ascending=False, na_position="last")
    stab.to_csv(OUT / "stability_all_metrics.csv", index=False)
    passed = stab[stab["passes_0_70"]].copy()
    passed.to_csv(OUT / "stability_passed_r070.csv", index=False)
    print(f"\n=== STABILITY r>={STABILITY_THRESHOLD}: {len(passed)} / {len(stab)} metrics pass ===")
    print(stab[["metric", "stability_r", "n_pairs", "passes_0_70"]].to_string(index=False))

    red_metrics = list(passed["metric"])
    pairs = []
    shortlist = []
    if len(red_metrics) >= 2:
        mat = y1_df.set_index("player_id")[red_metrics]
        corr = mat.corr(method="pearson")
        corr.to_csv(OUT / "redundancy_corr_passed_metrics.csv")
        for i, m1 in enumerate(red_metrics):
            for m2 in red_metrics[i + 1:]:
                rv = float(corr.loc[m1, m2])
                if abs(rv) >= 0.70:
                    pairs.append({"metric_a": m1, "metric_b": m2, "r": round(rv, 4)})
        pd.DataFrame(pairs).to_csv(OUT / "redundancy_high_pairs_step2.csv", index=False)
        order = list(passed.sort_values("stability_r", ascending=False)["metric"])
        kept = []
        for m in order:
            if all(abs(float(corr.loc[m, k])) < 0.70 for k in kept):
                kept.append(m)
        shortlist = kept
        pd.DataFrame({
            "metric": kept,
            "note": "AUTO SUGGESTION only — your Step 2 is to choose among stable metrics after reviewing redundancy pairs",
        }).to_csv(OUT / "redundancy_auto_shortlist_suggestion.csv", index=False)
        print(f"Redundancy high pairs (|r|≥0.70): {len(pairs)}")
        print(f"Auto shortlist suggestion (for pizzas until you choose): {shortlist}")
    elif len(red_metrics) == 1:
        shortlist = red_metrics
    else:
        print("WARNING: 0 metrics passed 0.70 — exploratory top-6 by r for pizza placeholders")
        shortlist = list(stab.dropna(subset=["stability_r"]).head(6)["metric"])

    pizza_metrics = shortlist
    pizza_note = (
        f"{len(passed)} metrics passed stability r>={STABILITY_THRESHOLD}. "
        f"Pizzas use auto shortlist suggestion ({len(pizza_metrics)} metrics). "
        "Step 2: pick final set from redundancy_high_pairs_step2.csv."
        if len(passed) else
        "No metrics cleared 0.70 — pizzas are exploratory on top-6 by stability."
    )

    score_rows = []
    detail = []
    for r in cohort_rows:
        pid = r["player_id"]
        y1row = y1_df.loc[y1_df["player_id"] == pid].iloc[0]
        priorow = prior_df.loc[prior_df["player_id"] == pid].iloc[0]
        pcts = []
        metric_detail = []
        for m in pizza_metrics:
            val = y1row[m]
            prior_val = priorow[m]
            pct = percentile_of(val, peer_df[m])
            prior_pct = percentile_of(prior_val, peer_df[m])
            if pct == pct:
                pcts.append(pct)
            abb, cat, hint = METRIC_META[m]
            stab_r = stab.loc[stab["metric"] == m, "stability_r"]
            metric_detail.append({
                "key": m, "abbrev": abb, "cat": cat, "hint": hint,
                "color": CAT_COLOR[cat],
                "player": None if pct != pct else round(pct, 1),
                "prior": None if prior_pct != prior_pct else round(prior_pct, 1),
                "avg": 50.0,
                "top": 90.0,
                "raw_y1": None if val != val else round(float(val), 3),
                "raw_prior": None if prior_val != prior_val else round(float(prior_val), 3),
                "stability": None if stab_r.empty or stab_r.iloc[0] is None else float(stab_r.iloc[0]),
            })
        score = float(np.nanmean(pcts)) if pcts else np.nan
        score_rows.append({
            "player_id": pid,
            "name": r["name"],
            "arrival_season": r["arrival_season"],
            "position": r["position"],
            "prior_minutes": r["prior_minutes"],
            "y1_minutes": r["y1_minutes"],
            "primary_source": (list(r["prior_leagues"].keys())[0] if r["prior_leagues"] else None),
            "n_pizza_metrics": len(pcts),
            "stable_trait_score": None if score != score else round(score, 2),
        })
        detail.append({
            "id": pid,
            "name": r["name"],
            "position": r["position"],
            "arrival": r["arrival_season"],
            "sources": list(r["prior_leagues"].keys())[:3],
            "prior_min": r["prior_minutes"],
            "y1_min": r["y1_minutes"],
            "score": None if score != score else round(score, 1),
            "metrics": metric_detail,
        })

    scores = pd.DataFrame(score_rows).sort_values("stable_trait_score", ascending=False)
    scores.to_csv(OUT / "player_rankings_stable_traits.csv", index=False)
    print("\nTop targets by mean Y1 percentile on shortlist metrics:")
    print(scores.head(15)[["name", "position", "stable_trait_score", "primary_source"]].to_string(index=False))

    # Source league board
    league_rows = []
    for league in sorted({k for r in cohort_rows for k in r["prior_leagues"]}):
        sub = scores[scores["primary_source"] == league]
        if sub.empty:
            continue
        league_rows.append({
            "source_league": league,
            "n_players": int(len(sub)),
            "mean_stable_trait_score": round(float(sub["stable_trait_score"].mean()), 2),
            "median_y1_minutes": round(float(sub["y1_minutes"].median()), 1),
        })
    league_df = pd.DataFrame(league_rows).sort_values("mean_stable_trait_score", ascending=False)
    league_df.to_csv(OUT / "source_league_scorecard.csv", index=False)

    summary = {
        "stability_threshold": STABILITY_THRESHOLD,
        "n_metrics_tested": int(len(stab)),
        "n_metrics_passed_0_70": int(len(passed)),
        "passed_metrics": passed.to_dict(orient="records"),
        "all_stability": stab.replace({np.nan: None}).to_dict(orient="records"),
        "redundancy_high_pairs": pairs,
        "auto_shortlist_suggestion": pizza_metrics,
        "pizza_note": pizza_note,
        "cohort_n": int(len(cohort_df)),
        "step2_instruction": (
            "Review redundancy_high_pairs_step2.csv among metrics that passed r>=0.70. "
            "Choose which metric to keep from each redundant pair/cluster; rebuild pizzas from your final list."
        ),
        "players": sorted(detail, key=lambda x: (x["position"], -(x["score"] or 0))),
        "top_targets": scores.head(20).replace({np.nan: None}).to_dict(orient="records"),
        "source_leagues": league_df.to_dict(orient="records"),
    }
    (OUT / "analysis_payload.json").write_text(json.dumps(summary, indent=2))

    md = []
    md.append("# Analysis results — Bundesliga inbound traits\n")
    md.append(f"**Stability threshold:** r ≥ **{STABILITY_THRESHOLD}**\n")
    md.append(f"**Metrics tested:** {len(stab)}  \n")
    md.append(f"**Metrics passing threshold:** **{len(passed)}**  \n")
    md.append(f"**Cohort N:** {len(cohort_df)} (prior≥{MIN_PRIOR} min, BL Y1≥{MIN_Y1} min; StatsBomb open data)\n")
    md.append("\n## Metrics that passed stability (r≥0.70)\n\n")
    if len(passed):
        md.append("| Metric | r | n pairs | Category |\n|---|---:|---:|---|\n")
        for _, row in passed.iterrows():
            md.append(f"| {row['metric']} | {row['stability_r']} | {row['n_pairs']} | {row['category']} |\n")
    else:
        md.append("_None cleared 0.70 on this open-data sample._\n")
    md.append("\n## Step 2 (your selection)\n\n")
    md.append("Among the passed metrics, review `results/redundancy_high_pairs_step2.csv` ")
    md.append("(|r|≥0.70 pairs). Pick which metric(s) to push through to the final pizza scout card.\n")
    md.append(f"\nAuto shortlist suggestion used for current pizzas: `{pizza_metrics}`\n")
    md.append("\n## Top target players (mean BL Y1 percentile on shortlist)\n\n")
    md.append("| Rank | Player | Pos | Score | Source |\n|---:|---|---|---:|---|\n")
    for i, (_, row) in enumerate(scores.head(15).iterrows(), 1):
        md.append(f"| {i} | {row['name']} | {row['position']} | {row['stable_trait_score']} | {row['primary_source']} |\n")
    (OUT / "RESULTS.md").write_text("".join(md))
    print(f"\nWrote {OUT}")


if __name__ == "__main__":
    main()
