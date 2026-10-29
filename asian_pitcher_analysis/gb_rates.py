#!/usr/bin/env python3
"""Measured ground-ball rates for the Asian-to-MLB comparison.

MLB GB% is Baseball Savant's batted-ball rate: ground balls divided by
batted balls, weighted by batted-ball events. The MLB Stats API pitching
line only has ground outs and air outs, which is a different rate, so it
is not used.

NPB GB% is the ゴロ率 on NPB Data Store (baseball-data-store.com) for a
season whose page title matches that year. The site currently publishes
2025 and 2026. Official npb.jp lines do not publish ground-ball rate.
A page that redirects to a different year is ignored.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from scrape_v3 import PITCHERS

CACHE = Path(__file__).resolve().parent / "cache"
SAVANT_YEARS = range(2015, 2027)
NPB_YEARS = (2025, 2026)
HEADERS = {"User-Agent": "Mozilla/5.0 (research; asian-pitcher-gb)"}

# English roster name -> Japanese name as NPB Data Store prints it.
NPB_JA = {
    "Daisuke Matsuzaka": "松坂 大輔",
    "Hiroki Kuroda": "黒田 博樹",
    "Takashi Saito": "斎藤 隆",
    "Koji Uehara": "上原 浩治",
    "Kenshin Kawakami": "川上 憲伸",
    "Hisashi Iwakuma": "岩隈 久志",
    "Yu Darvish": "ダルビッシュ 有",
    "Kyuji Fujikawa": "藤川 球児",
    "Masahiro Tanaka": "田中 将大",
    "Tsuyoshi Wada": "和田 毅",
    "Kenta Maeda": "前田 健太",
    "Yusei Kikuchi": "菊池 雄星",
    "Hirokazu Sawamura": "澤村 拓一",
    "Kodai Senga": "千賀 滉大",
    "Shintaro Fujinami": "藤浪 晋太郎",
    "Shota Imanaga": "今永 昇太",
    "Yuki Matsui": "松井 裕樹",
    "Yoshinobu Yamamoto": "山本 由伸",
    "Tomoyuki Sugano": "菅野 智之",
    "Hiromi Itoh": "伊藤 大海",
    "Wei-Yin Chen": "チェン ウェイイン",
    "Kei Igawa": "井川 慶",
    "Hideki Okajima": "岡島 秀樹",
    "Masumi Kuwata": "桑田 真澄",
    "Masahide Kobayashi": "小林 雅英",
    "Hisanori Takahashi": "高橋 尚成",
    "Ryota Igarashi": "五十嵐 亮太",
    "Yoshihisa Hirano": "平野 佳寿",
    "Kazuhisa Makita": "牧田 和久",
    "Shun Yamaguchi": "山口 俊",
    "Kohei Arihara": "有原 航平",
    "Naoyuki Uwasawa": "上沢 直之",
    "Roki Sasaki": "佐々木 朗希",
    "Shinnosuke Ogasawara": "小笠原 慎之介",
    "Tatsuya Imai": ["今井 達也", "今井達也"],
    "Kazuo Fukumori": "福盛 和男",
    "Yasuhiko Yabuta": "藪田 安彦",
    "Ken Takahashi": "高橋 建",
    "Yoshinori Tateyama": "建山 義紀",
    "Shohei Ohtani": "大谷 翔平",
    "Sang-Hoon Lee": "李 尚勲",
    "Dae-Sung Koo": "具 臺晟",
    "Chang-Yong Lim": "林 昌勇",
    "Yariel Rodriguez": "ヤリエル ロドリゲス",
    "Reed Garrett": "リード ギャレット",
    "Robert Suarez": "ロバート スアレス",
    "Albert Suarez": "アルバート スアレス",
    "Chris Martin": "クリス マーティン",
    "Pierce Johnson": "ピアース ジョンソン",
    "Nick Martinez": "ニック マルティネス",
    "Foster Griffin": ["グリフィン", "フォスター グリフィン"],
    "Anthony Kay": ["ケイ", "アンソニー ケイ"],
    "Colby Lewis": "コルビー ルイス",
    "Ryan Vogelsong": "ライアン ボーゲルソン",
    "Miles Mikolas": "マイルス マイコラス",
    "Tony Barnette": "トニー バーネット",
}


def _savant_cache(year: int) -> Path:
    return CACHE / f"savant_bbe_{year}.csv"


def fetch_savant_year(year: int) -> dict[int, tuple[float, float]]:
    """Return {mlb_id: (batted_balls, gb_rate)} for one season."""
    import csv
    import io

    path = _savant_cache(year)
    if path.exists() and path.stat().st_size > 1000:
        text = path.read_text()
    else:
        url = (
            "https://baseballsavant.mlb.com/leaderboard/batted-ball"
            f"?type=pitcher&year={year}&min=0&csv=true"
        )
        resp = requests.get(url, headers=HEADERS, timeout=40)
        resp.raise_for_status()
        text = resp.content.decode("utf-8-sig")
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        time.sleep(0.3)
    out = {}
    for row in csv.DictReader(io.StringIO(text)):
        try:
            pid = int(row["id"])
            bbe = float(row["bbe"] or 0)
            rate = float(row["gb_rate"]) if row.get("gb_rate") not in (None, "") else None
        except (TypeError, ValueError, KeyError):
            continue
        if rate is None or bbe <= 0:
            continue
        out[pid] = (bbe, rate)
    return out


def load_savant() -> dict[int, dict[int, tuple[float, float]]]:
    """year -> mlb_id -> (bbe, gb_rate as a fraction)."""
    book = {}
    for year in SAVANT_YEARS:
        try:
            book[year] = fetch_savant_year(year)
        except Exception as exc:
            print(f"  Savant {year} skipped: {exc}")
            book[year] = {}
        print(f"  Savant {year}: {len(book[year])} pitchers")
    return book


def _npb_cache() -> Path:
    return CACHE / "npb_gb.json"


def fetch_npb_season(ja_name: str, year: int) -> float | None:
    """Return GB% for one NPB season, or None when that year's page is absent."""
    from urllib.parse import quote

    url = f"https://baseball-data-store.com/player/{quote(ja_name)}/pitch_by_pitch?year={year}"
    resp = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
    if resp.status_code != 200:
        return None
    title_m = re.search(r"<title>(.*?)</title>", resp.text)
    title = title_m.group(1) if title_m else ""
    if "被投球" in title or f"{year}年" not in title:
        return None
    family = ja_name.split()[0]
    if family not in title:
        return None
    match = re.search(
        r'percentile-row__label"[^>]*>\s*GB%\s*</span>.*?percentile-row__value">\s*([\d.]+)%',
        resp.text,
        re.S,
    )
    if not match:
        return None
    return round(float(match.group(1)), 1)


def load_npb_gb(names: list[str]) -> dict[str, dict[str, float]]:
    """name -> {year_str: gb_pct}. Cached. Only seasons the page actually titles."""
    path = _npb_cache()
    cached: dict[str, dict[str, float]] = {}
    if path.exists():
        cached = json.loads(path.read_text())
    changed = False
    for name in names:
        variants = NPB_JA.get(name)
        if not variants:
            continue
        if isinstance(variants, str):
            variants = [variants]
        have = cached.setdefault(name, {})
        for year in NPB_YEARS:
            key = str(year)
            if key in have:
                continue
            pct = None
            for ja in variants:
                try:
                    pct = fetch_npb_season(ja, year)
                except Exception as exc:
                    print(f"  NPB GB {name} {year} skipped: {exc}")
                    pct = None
                time.sleep(0.25)
                if pct is not None:
                    break
            have[key] = pct
            changed = True
            print(f"  NPB {name} {year}: {pct}")
    if changed:
        CACHE.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(cached, ensure_ascii=False, indent=2))
    return cached


def _rows(value) -> list[dict]:
    if isinstance(value, list):
        return value
    return []


def _weighted(rows: list[dict], weight_key: str) -> float | None:
    """IP- or BBE-weighted GB%. Incomplete windows stay blank."""
    if not rows:
        return None
    weight = 0.0
    total = 0.0
    for row in rows:
        pct = row.get("gb_pct")
        w = row.get(weight_key)
        if pct is None or w is None:
            return None
        w = float(w)
        if w <= 0:
            return None
        weight += w
        total += float(pct) * w
    if weight <= 0:
        return None
    return round(total / weight, 1)


def _savant_gb(savant: dict, mlb_id: int, years: list[int] | None) -> float | None:
    """BBE-weighted Savant GB%. years=None uses every season on file for the id."""
    chosen = years if years is not None else list(savant)
    weight = 0.0
    total = 0.0
    saw = False
    for year in chosen:
        hit = savant.get(year, {}).get(mlb_id)
        if years is not None and hit is None:
            return None
        if not hit:
            continue
        bbe, rate = hit
        weight += bbe
        total += rate * bbe
        saw = True
    if not saw or weight <= 0:
        return None
    return round(total / weight * 100, 1)


def apply_measured_gb(df: pd.DataFrame) -> None:
    """Replace ground-out rates and hand estimates with measured GB%."""
    for col in list(df.columns):
        if "gb_pct" in col:
            df[col] = np.nan

    id_by_name = {p["name"]: p["mlb_id"] for p in PITCHERS}
    print("Loading Savant ground-ball rates")
    savant = load_savant()
    npb_names = [n for n in df["name"] if n in NPB_JA]
    print("Loading NPB Data Store ground-ball rates")
    npb = load_npb_gb(npb_names)

    for i in df.index:
        name = df.at[i, "name"]
        tyear = df.at[i, "transition_year"]
        asian = _rows(df.at[i, "asian_yearly"]) if "asian_yearly" in df.columns else []
        mlb_rows = _rows(df.at[i, "mlb_yearly"]) if "mlb_yearly" in df.columns else []
        for row in asian + mlb_rows:
            row.pop("gb_pct", None)
            row.pop("bbe", None)

        published = npb.get(name, {})
        for row in asian:
            pct = published.get(str(int(row["season"])))
            if pct is not None:
                row["gb_pct"] = pct

        mlb_id = id_by_name.get(name)
        if mlb_id:
            for row in mlb_rows:
                hit = savant.get(int(row["season"]), {}).get(int(mlb_id))
                if hit:
                    row["bbe"] = hit[0]
                    row["gb_pct"] = round(hit[1] * 100, 1)
            df.at[i, "m_gb_pct"] = _savant_gb(savant, int(mlb_id), None)

        if pd.isna(tyear):
            continue
        ty = int(tyear)
        pre = [r for r in asian if int(r["season"]) <= ty]
        df.at[i, "a_gb_pct"] = _weighted(pre, "ip")
        for n in (1, 2, 3):
            window = [r for r in asian if ty - n <= int(r["season"]) < ty]
            df.at[i, f"a{n}y_gb_pct"] = _weighted(window, "ip")
            years = sorted({int(r["season"]) for r in mlb_rows if int(r["season"]) >= ty})
            if not years or not mlb_id:
                continue
            start = years[0]
            span = [y for y in years if start <= y < start + n]
            df.at[i, f"m{n}y_gb_pct"] = _savant_gb(savant, int(mlb_id), span)
