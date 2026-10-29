#!/usr/bin/env python3
"""v3 scraper: Corrected BRef register IDs + MLB Stats API + bWAR + hand-compiled fallback."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup

CACHE = Path(__file__).resolve().parent / "cache"
CACHE.mkdir(exist_ok=True)
OUT = Path(__file__).resolve().parent

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Top-league codes only. Farm (JPEL/JPFL) and winter (JPWL) stay out.
ASIAN_TOP = [
    ("NPB", ["JPPL", "JPCL", "JPCe", "JPPa"]),
    ("KBO", ["KBO"]),
    ("CPBL", ["CPBL", "TML"]),
]


def asian_league_of(row: dict, fallback_league: str) -> str | None:
    """Return NPB, KBO, or CPBL when a register row is a top-league Asian season."""
    lg = row.get("lg_ID", "") or ""
    level = row.get("level", "") or ""
    for name, codes in ASIAN_TOP:
        if any(code in lg for code in codes):
            return name
    if fallback_league == "NPB" and "Jpn" in level:
        return "NPB"
    if fallback_league == "KBO" and "Kor" in level:
        return "KBO"
    if fallback_league == "CPBL" and ("Twn" in level or "TML" in level):
        return "CPBL"
    return None

PITCHERS = [
    # ── Asian-born: NPB → MLB ────────────────────────────────────────────
    {"name": "Hideo Nomo",          "league": "NPB", "mlb_id": 119827, "bref_reg": "nomo--001hid", "pos": "SP", "tyear": 1995, "origin": "JP"},
    {"name": "Kazuhiro Sasaki",     "league": "NPB", "mlb_id": 277408, "bref_reg": "sasaki001kaz", "pos": "RP", "tyear": 2000, "origin": "JP"},
    {"name": "Shigetoshi Hasegawa", "league": "NPB", "mlb_id": 115586, "bref_reg": "hasega001shi", "pos": "RP", "tyear": 1997, "origin": "JP"},
    {"name": "Hideki Irabu",        "league": "NPB", "mlb_id": 116400, "bref_reg": "irabu-001hid", "pos": "SP", "tyear": 1997, "origin": "JP"},
    {"name": "Masato Yoshii",       "league": "NPB", "mlb_id": 134180, "bref_reg": "yoshii001mas", "pos": "SP", "tyear": 1998, "origin": "JP"},
    {"name": "Kazuhisa Ishii",      "league": "NPB", "mlb_id": 408193, "bref_reg": "ishii-001kaz", "pos": "SP", "tyear": 2002, "origin": "JP"},
    {"name": "Daisuke Matsuzaka",   "league": "NPB", "mlb_id": 493137, "bref_reg": "matsuz001dai", "pos": "SP", "tyear": 2007, "origin": "JP"},
    {"name": "Hiroki Kuroda",       "league": "NPB", "mlb_id": 493133, "bref_reg": "kuroda001hir", "pos": "SP", "tyear": 2008, "origin": "JP"},
    {"name": "Takashi Saito",       "league": "NPB", "mlb_id": 493416, "bref_reg": "saito-001tak", "pos": "RP", "tyear": 2006, "origin": "JP"},
    {"name": "Koji Uehara",         "league": "NPB", "mlb_id": 493157, "bref_reg": "uehara001koj", "pos": "SP", "tyear": 2009, "origin": "JP"},
    {"name": "Junichi Tazawa",      "league": "NPB", "mlb_id": 547749, "bref_reg": "tazawa001jun", "pos": "RP", "tyear": 2009, "origin": "JP"},
    {"name": "Kenshin Kawakami",    "league": "NPB", "mlb_id": 499877, "bref_reg": "kawaka001ken", "pos": "SP", "tyear": 2009, "origin": "JP"},
    {"name": "Hisashi Iwakuma",     "league": "NPB", "mlb_id": 547874, "bref_reg": "iwakum001his", "pos": "SP", "tyear": 2012, "origin": "JP"},
    {"name": "Yu Darvish",          "league": "NPB", "mlb_id": 506433, "bref_reg": "darvis001yu-", "pos": "SP", "tyear": 2012, "origin": "JP"},
    {"name": "Kyuji Fujikawa",      "league": "NPB", "mlb_id": 493117, "bref_reg": "fujika001kyu", "pos": "RP", "tyear": 2013, "origin": "JP"},
    {"name": "Masahiro Tanaka",     "league": "NPB", "mlb_id": 547888, "bref_reg": "tanaka003mas", "pos": "SP", "tyear": 2014, "origin": "JP"},
    {"name": "Tsuyoshi Wada",       "league": "NPB", "mlb_id": 493159, "bref_reg": "wada--001tsu", "pos": "SP", "tyear": 2014, "origin": "JP"},
    {"name": "Kenta Maeda",         "league": "NPB", "mlb_id": 628317, "bref_reg": "maeda-001ken", "pos": "SP", "tyear": 2016, "origin": "JP"},
    {"name": "Yusei Kikuchi",       "league": "NPB", "mlb_id": 579328, "bref_reg": "kikuch000yus", "pos": "SP", "tyear": 2019, "origin": "JP"},
    {"name": "Hirokazu Sawamura",   "league": "NPB", "mlb_id": 617228, "bref_reg": "sawamu000hir", "pos": "RP", "tyear": 2021, "origin": "JP"},
    {"name": "Kodai Senga",         "league": "NPB", "mlb_id": 673540, "bref_reg": "senga-000kod", "pos": "SP", "tyear": 2023, "origin": "JP"},
    {"name": "Shintaro Fujinami",   "league": "NPB", "mlb_id": 660261, "bref_reg": "fujina000shi", "pos": "SP", "tyear": 2023, "origin": "JP"},
    {"name": "Shota Imanaga",       "league": "NPB", "mlb_id": 684007, "bref_reg": "imanag000sho", "pos": "SP", "tyear": 2024, "origin": "JP"},
    {"name": "Yuki Matsui",         "league": "NPB", "mlb_id": 673513, "bref_reg": "matsui000yuk", "pos": "RP", "tyear": 2024, "origin": "JP"},
    {"name": "Yoshinobu Yamamoto",  "league": "NPB", "mlb_id": 808967, "bref_reg": "yamamo004yos", "pos": "SP", "tyear": 2024, "origin": "JP"},
    {"name": "Tomoyuki Sugano",     "league": "NPB", "mlb_id": 608372, "bref_reg": "sugano001tom", "pos": "SP", "tyear": 2025, "origin": "JP"},
    {"name": "Hiromi Itoh",         "league": "NPB", "mlb_id": None,   "bref_reg": "itoh--002hir", "pos": "SP", "tyear": None, "origin": "JP"},
    # ── Asian-born: KBO → MLB ────────────────────────────────────────────
    {"name": "Chan Ho Park",        "league": "KBO", "mlb_id": 120221, "bref_reg": "park--001cha", "pos": "SP", "tyear": 1994, "origin": "KR"},
    {"name": "Byung-Hyun Kim",      "league": "KBO", "mlb_id": 218294, "bref_reg": "kim---001byu", "pos": "RP", "tyear": 1999, "origin": "KR"},
    {"name": "Sun-Woo Kim",         "league": "KBO", "mlb_id": 279615, "bref_reg": "kim---001sun", "pos": "SP", "tyear": 2001, "origin": "KR"},
    {"name": "Jae-Weong Seo",       "league": "KBO", "mlb_id": 150242, "bref_reg": "seo---002jae", "pos": "SP", "tyear": 2002, "origin": "KR"},
    {"name": "Hyun-Jin Ryu",        "league": "KBO", "mlb_id": 547943, "bref_reg": "ryu---000hye", "pos": "SP", "tyear": 2013, "origin": "KR"},
    {"name": "Seung-Hwan Oh",       "league": "KBO", "mlb_id": 493200, "bref_reg": "oh----000seu", "pos": "RP", "tyear": 2016, "origin": "KR"},
    {"name": "Kwang-Hyun Kim",      "league": "KBO", "mlb_id": 547942, "bref_reg": "kim---002gwa", "pos": "SP", "tyear": 2020, "origin": "KR"},
    {"name": "Hyeon-Jong Yang",     "league": "KBO", "mlb_id": 660365, "bref_reg": "yang--000hye", "pos": "SP", "tyear": 2021, "origin": "KR"},
    {"name": "Woo-Suk Go",          "league": "KBO", "mlb_id": 808970, "bref_reg": "ko----001woo", "pos": "RP", "tyear": 2026, "origin": "KR"},
    # ── Asian-born: CPBL → MLB ───────────────────────────────────────────
    {"name": "Fu-Te Ni",            "league": "CPBL", "mlb_id": 547820, "bref_reg": "ni----001fut", "pos": "RP", "tyear": 2009, "origin": "TW"},
    {"name": "Wei-Yin Chen",        "league": "NPB",  "mlb_id": 612672, "bref_reg": "chen--001wei", "pos": "SP", "tyear": 2012, "origin": "TW"},
    # ── Crossover: Americans who pitched in NPB then (returned to) MLB ──
    {"name": "Colby Lewis",         "league": "NPB", "mlb_id": 407890, "bref_reg": "lewis-001col", "pos": "SP", "tyear": 2010, "origin": "US"},
    {"name": "Ryan Vogelsong",      "league": "NPB", "mlb_id": 285064, "bref_reg": "vogels001rya", "pos": "SP", "tyear": 2011, "origin": "US"},
    {"name": "Miles Mikolas",       "league": "NPB", "mlb_id": 571945, "bref_reg": "mikola001mil", "pos": "SP", "tyear": 2018, "origin": "US"},
    {"name": "Tony Barnette",       "league": "NPB", "mlb_id": 501817, "bref_reg": "barnet002ant", "pos": "RP", "tyear": 2016, "origin": "US"},
    # ── Crossover: Americans who pitched in KBO then (returned to) MLB ──
    {"name": "Chris Flexen",        "league": "KBO", "mlb_id": 623167, "bref_reg": "flexen000chr", "pos": "SP", "tyear": 2021, "origin": "US"},
    {"name": "Merrill Kelly",       "league": "KBO", "mlb_id": 518876, "bref_reg": "kelly-003ken", "pos": "SP", "tyear": 2019, "origin": "US"},
    {"name": "Josh Lindblom",       "league": "KBO", "mlb_id": 458676, "bref_reg": "lindbl001jos", "pos": "SP", "tyear": 2020, "origin": "US"},
    {"name": "Erick Fedde",         "league": "KBO", "mlb_id": 607200, "bref_reg": "fedde-000eri", "pos": "SP", "tyear": 2024, "origin": "US"},
    # Additional NPB / KBO / CPBL pitchers who also pitched in MLB.
    # bref_reg is None when the register id was not confirmed; they stay in the
    # roster table and are left out of the correlations.
    {"name": "Satoru Komiyama",     "league": "NPB", "mlb_id": 407894, "bref_reg": "komiya001sat", "pos": "SP", "tyear": 2002, "origin": "JP"},
    {"name": "Akinori Otsuka",      "league": "NPB", "mlb_id": 430788, "bref_reg": "otsuka001aki", "pos": "RP", "tyear": 2004, "origin": "JP"},
    {"name": "Kazuhito Tadano",     "league": "NPB", "mlb_id": 430954, "bref_reg": "tadano001kaz", "pos": "SP", "tyear": 2004, "origin": "JP"},
    {"name": "Keiichi Yabu",        "league": "NPB", "mlb_id": 435158, "bref_reg": "yabu--001kei", "pos": "RP", "tyear": 2005, "origin": "JP"},
    {"name": "Shingo Takatsu",      "league": "NPB", "mlb_id": 430968, "bref_reg": "takats001shi", "pos": "RP", "tyear": 2004, "origin": "JP"},
    {"name": "Kei Igawa",           "league": "NPB", "mlb_id": 506432, "bref_reg": "igawa-001kei", "pos": "SP", "tyear": 2007, "origin": "JP"},
    {"name": "Hideki Okajima",      "league": "NPB", "mlb_id": 506606, "bref_reg": "okajim001hid", "pos": "RP", "tyear": 2007, "origin": "JP"},
    {"name": "Masumi Kuwata",       "league": "NPB", "mlb_id": 506555, "bref_reg": "kuwata001mas", "pos": "SP", "tyear": 2007, "origin": "JP"},
    # kobaya001mas is Masato Kobayashi (born 1980), a different pitcher.
    {"name": "Masahide Kobayashi",  "league": "NPB", "mlb_id": 493131, "bref_reg": None,          "pos": "RP", "tyear": 2008, "origin": "JP"},
    {"name": "Hisanori Takahashi",  "league": "NPB", "mlb_id": 538227, "bref_reg": "takaha001his", "pos": "RP", "tyear": 2010, "origin": "JP"},
    {"name": "Ryota Igarashi",      "league": "NPB", "mlb_id": 579799, "bref_reg": "igaras001ryo", "pos": "RP", "tyear": 2010, "origin": "JP"},
    {"name": "C.C. Lee",            "league": "NPB", "mlb_id": 547348, "bref_reg": "lee---001che", "pos": "RP", "tyear": 2013, "origin": "TW"},
    {"name": "Wei-Chung Wang",      "league": "CPBL", "mlb_id": 623913, "bref_reg": None,          "pos": "SP", "tyear": 2014, "origin": "TW"},
    {"name": "Yoshihisa Hirano",    "league": "NPB", "mlb_id": 673633, "bref_reg": "hirano001yos", "pos": "RP", "tyear": 2018, "origin": "JP"},
    {"name": "Kazuhisa Makita",     "league": "NPB", "mlb_id": 628318, "bref_reg": "makita000kaz", "pos": "RP", "tyear": 2018, "origin": "JP"},
    {"name": "Shun Yamaguchi",      "league": "NPB", "mlb_id": 685493, "bref_reg": "yamagu001shu", "pos": "SP", "tyear": 2020, "origin": "JP"},
    {"name": "Kohei Arihara",       "league": "NPB", "mlb_id": 685503, "bref_reg": None,          "pos": "SP", "tyear": 2021, "origin": "JP"},
    {"name": "Robert Suarez",       "league": "NPB", "mlb_id": 663158, "bref_reg": "suarez002rob", "pos": "RP", "tyear": 2022, "origin": "VE"},
    {"name": "Naoyuki Uwasawa",     "league": "NPB", "mlb_id": 683822, "bref_reg": "uwasaw000nao", "pos": "SP", "tyear": 2024, "origin": "JP"},
    {"name": "Roki Sasaki",         "league": "NPB", "mlb_id": 808963, "bref_reg": "sasaki000rok", "pos": "SP", "tyear": 2025, "origin": "JP"},
    {"name": "Shinnosuke Ogasawara","league": "NPB", "mlb_id": 829272, "bref_reg": "ogasaw000shi", "pos": "SP", "tyear": 2025, "origin": "JP"},
    {"name": "Tatsuya Imai",        "league": "NPB", "mlb_id": 837227, "bref_reg": "imai--000tat", "pos": "SP", "tyear": 2026, "origin": "JP"},
    {"name": "Chris Martin",        "league": "NPB", "mlb_id": 455119, "bref_reg": None,          "pos": "RP", "tyear": 2018, "origin": "US"},
    {"name": "Pierce Johnson",      "league": "NPB", "mlb_id": 572955, "bref_reg": "johnso001pie", "pos": "RP", "tyear": 2020, "origin": "US"},
    # martin001nic is Nick Martin, a different player.
    {"name": "Nick Martinez",       "league": "NPB", "mlb_id": 607259, "bref_reg": None,          "pos": "SP", "tyear": 2022, "origin": "US"},
    {"name": "Albert Suarez",       "league": "NPB", "mlb_id": 544150, "bref_reg": "suarez001alb", "pos": "SP", "tyear": 2024, "origin": "VE"},
    {"name": "Foster Griffin",      "league": "NPB", "mlb_id": 656492, "bref_reg": "griffi000fos", "pos": "SP", "tyear": 2026, "origin": "US"},
    {"name": "Anthony Kay",         "league": "NPB", "mlb_id": 641743, "bref_reg": "kay---000ant", "pos": "SP", "tyear": 2026, "origin": "US"},
    {"name": "Kyle Hart",           "league": "KBO", "mlb_id": 606996, "bref_reg": None,          "pos": "SP", "tyear": 2025, "origin": "US"},
    {"name": "Andrew Suarez",       "league": "KBO", "mlb_id": 605498, "bref_reg": "suarez002and", "pos": "SP", "tyear": 2023, "origin": "US"},
    {"name": "Adrian Sampson",      "league": "KBO", "mlb_id": 592716, "bref_reg": "sampso000adr", "pos": "SP", "tyear": 2021, "origin": "US"},
    {"name": "Aaron Brooks",        "league": "KBO", "mlb_id": 605156, "bref_reg": None,          "pos": "SP", "tyear": 2022, "origin": "US"},
    {"name": "Cody Ponce",          "league": "KBO", "mlb_id": 664074, "bref_reg": "ponce-000cod", "pos": "SP", "tyear": 2026, "origin": "US"},
    {"name": "Drew Anderson",       "league": "KBO", "mlb_id": 623454, "bref_reg": None,          "pos": "SP", "tyear": 2026, "origin": "US"},
    {"name": "Ryan Weiss",          "league": "KBO", "mlb_id": 680802, "bref_reg": None,          "pos": "SP", "tyear": 2026, "origin": "US"},
]

HAND_COMPILED = {
    "Hideo Nomo":          {"a_era":3.15,"a_ip":175.0,"a_k9":10.7,"a_bb9":3.8,"a_hr9":0.7,"a_whip":1.13,"a_k_bb":2.82,"a_gb_pct":None,"a_w_pct":.680,"m_era":4.24,"m_ip":1976.1,"m_k9":8.7,"m_bb9":4.1,"m_hr9":1.1,"m_whip":1.35,"m_k_bb":2.12,"m_gb_pct":38.0,"m_w_pct":.530,"m_era_plus":98,"m_war":21.4,"m_seasons":12},
    "Kazuhiro Sasaki":     {"a_era":2.02,"a_ip":60.0,"a_k9":11.2,"a_bb9":2.5,"a_hr9":0.4,"a_whip":0.87,"a_k_bb":4.48,"a_gb_pct":None,"a_w_pct":.600,"m_era":3.14,"m_ip":223.1,"m_k9":9.8,"m_bb9":3.1,"m_hr9":1.0,"m_whip":1.09,"m_k_bb":3.16,"m_gb_pct":35.0,"m_w_pct":.304,"m_era_plus":138,"m_war":7.2,"m_seasons":4},
    "Shigetoshi Hasegawa": {"a_era":3.22,"a_ip":140.0,"a_k9":6.8,"a_bb9":2.3,"a_hr9":0.8,"a_whip":1.18,"a_k_bb":2.96,"a_gb_pct":None,"a_w_pct":.550,"m_era":3.71,"m_ip":720.1,"m_k9":5.6,"m_bb9":3.3,"m_hr9":0.9,"m_whip":1.30,"m_k_bb":1.70,"m_gb_pct":45.0,"m_w_pct":.511,"m_era_plus":125,"m_war":7.8,"m_seasons":9},
    "Hideki Irabu":        {"a_era":3.55,"a_ip":155.0,"a_k9":9.2,"a_bb9":3.5,"a_hr9":0.9,"a_whip":1.22,"a_k_bb":2.63,"a_gb_pct":None,"a_w_pct":.580,"m_era":5.15,"m_ip":514.0,"m_k9":7.1,"m_bb9":3.1,"m_hr9":1.6,"m_whip":1.48,"m_k_bb":2.29,"m_gb_pct":36.0,"m_w_pct":.493,"m_era_plus":90,"m_war":2.1,"m_seasons":6},
    "Masato Yoshii":       {"a_era":3.45,"a_ip":160.0,"a_k9":6.5,"a_bb9":2.2,"a_hr9":0.9,"a_whip":1.20,"a_k_bb":2.95,"a_gb_pct":None,"a_w_pct":.520,"m_era":4.62,"m_ip":757.1,"m_k9":5.3,"m_bb9":2.6,"m_hr9":1.3,"m_whip":1.41,"m_k_bb":2.04,"m_gb_pct":40.0,"m_w_pct":.405,"m_era_plus":101,"m_war":5.7,"m_seasons":5},
    "Kazuhisa Ishii":      {"a_era":3.27,"a_ip":155.0,"a_k9":10.1,"a_bb9":3.8,"a_hr9":0.6,"a_whip":1.15,"a_k_bb":2.66,"a_gb_pct":None,"a_w_pct":.620,"m_era":4.44,"m_ip":564.0,"m_k9":6.9,"m_bb9":5.7,"m_hr9":1.1,"m_whip":1.51,"m_k_bb":1.21,"m_gb_pct":34.0,"m_w_pct":.534,"m_era_plus":90,"m_war":3.2,"m_seasons":4},
    "Daisuke Matsuzaka":   {"a_era":2.95,"a_ip":178.0,"a_k9":8.5,"a_bb9":3.1,"a_hr9":0.5,"a_whip":1.14,"a_k_bb":2.74,"a_gb_pct":42.0,"a_w_pct":.618,"m_era":4.45,"m_ip":790.2,"m_k9":8.5,"m_bb9":4.3,"m_hr9":0.9,"m_whip":1.43,"m_k_bb":1.98,"m_gb_pct":40.0,"m_w_pct":.560,"m_era_plus":97,"m_war":10.2,"m_seasons":8},
    "Hiroki Kuroda":       {"a_era":3.69,"a_ip":170.0,"a_k9":7.2,"a_bb9":2.5,"a_hr9":0.9,"a_whip":1.24,"a_k_bb":2.88,"a_gb_pct":48.0,"a_w_pct":.530,"m_era":3.45,"m_ip":1319.0,"m_k9":6.8,"m_bb9":2.3,"m_hr9":0.9,"m_whip":1.17,"m_k_bb":2.96,"m_gb_pct":49.0,"m_w_pct":.517,"m_era_plus":111,"m_war":20.5,"m_seasons":7},
    "Takashi Saito":       {"a_era":3.18,"a_ip":130.0,"a_k9":8.5,"a_bb9":2.5,"a_hr9":0.7,"a_whip":1.12,"a_k_bb":3.40,"a_gb_pct":None,"a_w_pct":.550,"m_era":2.34,"m_ip":365.2,"m_k9":10.5,"m_bb9":2.9,"m_hr9":0.5,"m_whip":0.97,"m_k_bb":3.62,"m_gb_pct":35.0,"m_w_pct":.540,"m_era_plus":186,"m_war":11.2,"m_seasons":7},
    "Koji Uehara":         {"a_era":3.01,"a_ip":150.0,"a_k9":8.8,"a_bb9":1.3,"a_hr9":0.8,"a_whip":1.01,"a_k_bb":6.77,"a_gb_pct":35.0,"a_w_pct":.600,"m_era":2.66,"m_ip":508.2,"m_k9":10.4,"m_bb9":1.8,"m_hr9":0.7,"m_whip":0.87,"m_k_bb":5.78,"m_gb_pct":32.0,"m_w_pct":.472,"m_era_plus":157,"m_war":13.5,"m_seasons":9},
    "Junichi Tazawa":      {"a_era":3.80,"a_ip":50.0,"a_k9":7.5,"a_bb9":3.0,"a_hr9":0.8,"a_whip":1.28,"a_k_bb":2.50,"a_gb_pct":None,"a_w_pct":.500,"m_era":3.68,"m_ip":478.2,"m_k9":8.3,"m_bb9":2.6,"m_hr9":1.1,"m_whip":1.20,"m_k_bb":3.19,"m_gb_pct":38.0,"m_w_pct":.535,"m_era_plus":112,"m_war":6.5,"m_seasons":9},
    "Kenshin Kawakami":    {"a_era":3.48,"a_ip":175.0,"a_k9":7.0,"a_bb9":2.0,"a_hr9":0.8,"a_whip":1.15,"a_k_bb":3.50,"a_gb_pct":42.0,"a_w_pct":.590,"m_era":4.32,"m_ip":243.2,"m_k9":6.1,"m_bb9":3.3,"m_hr9":0.9,"m_whip":1.43,"m_k_bb":1.85,"m_gb_pct":44.0,"m_w_pct":.267,"m_era_plus":94,"m_war":1.4,"m_seasons":2},
    "Hisashi Iwakuma":     {"a_era":3.25,"a_ip":165.0,"a_k9":7.4,"a_bb9":1.9,"a_hr9":0.7,"a_whip":1.10,"a_k_bb":3.89,"a_gb_pct":46.0,"a_w_pct":.580,"m_era":3.42,"m_ip":861.1,"m_k9":7.3,"m_bb9":2.0,"m_hr9":1.0,"m_whip":1.12,"m_k_bb":3.65,"m_gb_pct":45.0,"m_w_pct":.574,"m_era_plus":119,"m_war":16.9,"m_seasons":6},
    "Yu Darvish":          {"a_era":1.99,"a_ip":180.0,"a_k9":10.0,"a_bb9":2.1,"a_hr9":0.4,"a_whip":0.98,"a_k_bb":4.76,"a_gb_pct":42.0,"a_w_pct":.710,"m_era":3.47,"m_ip":1760.0,"m_k9":10.5,"m_bb9":2.9,"m_hr9":1.1,"m_whip":1.14,"m_k_bb":3.62,"m_gb_pct":41.0,"m_w_pct":.567,"m_era_plus":118,"m_war":37.2,"m_seasons":13},
    "Kyuji Fujikawa":      {"a_era":1.77,"a_ip":60.0,"a_k9":10.5,"a_bb9":2.8,"a_hr9":0.3,"a_whip":0.95,"a_k_bb":3.75,"a_gb_pct":None,"a_w_pct":.600},
    "Masahiro Tanaka":     {"a_era":2.30,"a_ip":195.0,"a_k9":8.4,"a_bb9":1.5,"a_hr9":0.5,"a_whip":0.94,"a_k_bb":5.60,"a_gb_pct":46.0,"a_w_pct":.763,"m_era":3.74,"m_ip":1054.0,"m_k9":8.6,"m_bb9":1.8,"m_hr9":1.3,"m_whip":1.13,"m_k_bb":4.78,"m_gb_pct":45.0,"m_w_pct":.590,"m_era_plus":112,"m_war":18.5,"m_seasons":7},
    "Tsuyoshi Wada":       {"a_era":3.11,"a_ip":145.0,"a_k9":8.2,"a_bb9":2.4,"a_hr9":0.6,"a_whip":1.10,"a_k_bb":3.42,"a_gb_pct":None,"a_w_pct":.560},
    "Kenta Maeda":         {"a_era":2.39,"a_ip":190.0,"a_k9":8.6,"a_bb9":1.8,"a_hr9":0.6,"a_whip":1.00,"a_k_bb":4.78,"a_gb_pct":41.0,"a_w_pct":.660,"m_era":3.80,"m_ip":834.1,"m_k9":9.8,"m_bb9":2.5,"m_hr9":1.3,"m_whip":1.13,"m_k_bb":3.92,"m_gb_pct":37.0,"m_w_pct":.553,"m_era_plus":115,"m_war":17.5,"m_seasons":8},
    "Yusei Kikuchi":       {"a_era":2.77,"a_ip":165.0,"a_k9":8.2,"a_bb9":2.4,"a_hr9":0.5,"a_whip":1.08,"a_k_bb":3.42,"a_gb_pct":48.0,"a_w_pct":.560,"m_era":4.32,"m_ip":810.0,"m_k9":9.0,"m_bb9":3.5,"m_hr9":1.3,"m_whip":1.32,"m_k_bb":2.57,"m_gb_pct":40.0,"m_w_pct":.463,"m_era_plus":96,"m_war":7.8,"m_seasons":6},
    "Hirokazu Sawamura":   {"a_era":2.67,"a_ip":65.0,"a_k9":9.5,"a_bb9":3.0,"a_hr9":0.5,"a_whip":1.05,"a_k_bb":3.17,"a_gb_pct":None,"a_w_pct":.550},
    "Kodai Senga":         {"a_era":2.59,"a_ip":155.0,"a_k9":9.8,"a_bb9":2.8,"a_hr9":0.5,"a_whip":1.05,"a_k_bb":3.50,"a_gb_pct":44.0,"a_w_pct":.620,"m_era":3.38,"m_ip":185.0,"m_k9":10.4,"m_bb9":3.2,"m_hr9":0.8,"m_whip":1.12,"m_k_bb":3.25,"m_gb_pct":42.0,"m_w_pct":.550,"m_era_plus":118,"m_war":4.8,"m_seasons":2},
    "Shintaro Fujinami":   {"a_era":3.38,"a_ip":120.0,"a_k9":8.4,"a_bb9":4.5,"a_hr9":0.6,"a_whip":1.38,"a_k_bb":1.87,"a_gb_pct":44.0,"a_w_pct":.480,"m_era":7.18,"m_ip":64.0,"m_k9":7.3,"m_bb9":6.3,"m_hr9":1.5,"m_whip":1.82,"m_k_bb":1.16,"m_gb_pct":39.0,"m_w_pct":.143,"m_era_plus":58,"m_war":-1.2,"m_seasons":1},
    "Shota Imanaga":       {"a_era":2.47,"a_ip":150.0,"a_k9":8.3,"a_bb9":1.7,"a_hr9":0.6,"a_whip":0.96,"a_k_bb":4.88,"a_gb_pct":42.0,"a_w_pct":.640},
    "Yuki Matsui":         {"a_era":2.09,"a_ip":55.0,"a_k9":12.8,"a_bb9":3.2,"a_hr9":0.3,"a_whip":0.92,"a_k_bb":4.00,"a_gb_pct":None,"a_w_pct":.600},
    "Yoshinobu Yamamoto":  {"a_era":1.82,"a_ip":168.0,"a_k9":9.4,"a_bb9":1.6,"a_hr9":0.4,"a_whip":0.84,"a_k_bb":5.88,"a_gb_pct":50.0,"a_w_pct":.720,"m_era":3.25,"m_ip":310.0,"m_k9":9.2,"m_bb9":2.3,"m_hr9":0.9,"m_whip":1.05,"m_k_bb":4.00,"m_gb_pct":47.0,"m_w_pct":.600,"m_era_plus":126,"m_war":8.2,"m_seasons":3},
    "Tomoyuki Sugano":     {"a_era":2.34,"a_ip":180.0,"a_k9":8.0,"a_bb9":1.5,"a_hr9":0.6,"a_whip":0.92,"a_k_bb":5.33,"a_gb_pct":43.0,"a_w_pct":.700,"m_era":4.95,"m_ip":120.0,"m_k9":6.5,"m_bb9":2.8,"m_hr9":1.5,"m_whip":1.35,"m_k_bb":2.32,"m_gb_pct":38.0,"m_w_pct":.400,"m_era_plus":82,"m_war":0.5,"m_seasons":2},
    "Hiromi Itoh":         {"a_era":2.92,"a_ip":168.0,"a_k9":8.2,"a_bb9":1.9,"a_hr9":0.5,"a_whip":1.00,"a_k_bb":4.32,"a_gb_pct":45.0,"a_w_pct":.650},
    "Chan Ho Park":        {"a_era":3.50,"a_ip":60.0,"a_k9":9.0,"a_bb9":3.0,"a_hr9":0.7,"a_whip":1.15,"a_k_bb":3.00,"a_gb_pct":None,"a_w_pct":.500,"m_era":4.36,"m_ip":2081.0,"m_k9":7.4,"m_bb9":3.6,"m_hr9":1.2,"m_whip":1.39,"m_k_bb":2.06,"m_gb_pct":38.0,"m_w_pct":.559,"m_era_plus":101,"m_war":18.8,"m_seasons":17},
    "Byung-Hyun Kim":      {"a_era":3.00,"a_ip":55.0,"a_k9":10.5,"a_bb9":3.5,"a_hr9":0.5,"a_whip":1.10,"a_k_bb":3.00,"a_gb_pct":None,"a_w_pct":.500,"m_era":4.42,"m_ip":799.0,"m_k9":8.7,"m_bb9":3.5,"m_hr9":1.0,"m_whip":1.35,"m_k_bb":2.49,"m_gb_pct":33.0,"m_w_pct":.474,"m_era_plus":102,"m_war":8.5,"m_seasons":9},
    "Sun-Woo Kim":         {"a_era":4.00,"a_ip":70.0,"a_k9":7.0,"a_bb9":3.5,"a_hr9":0.9,"a_whip":1.35,"a_k_bb":2.00,"a_gb_pct":None,"a_w_pct":.450,"m_era":4.89,"m_ip":336.2,"m_k9":5.7,"m_bb9":3.5,"m_hr9":1.2,"m_whip":1.47,"m_k_bb":1.63,"m_gb_pct":42.0,"m_w_pct":.357,"m_era_plus":86,"m_war":0.8,"m_seasons":5},
    "Jae-Weong Seo":       {"a_era":3.80,"a_ip":80.0,"a_k9":6.5,"a_bb9":3.2,"a_hr9":0.9,"a_whip":1.30,"a_k_bb":2.03,"a_gb_pct":None,"a_w_pct":.450,"m_era":4.62,"m_ip":503.0,"m_k9":5.6,"m_bb9":3.1,"m_hr9":1.2,"m_whip":1.44,"m_k_bb":1.81,"m_gb_pct":40.0,"m_w_pct":.415,"m_era_plus":90,"m_war":2.8,"m_seasons":5},
    "Hyun-Jin Ryu":        {"a_era":2.80,"a_ip":175.0,"a_k9":7.8,"a_bb9":2.1,"a_hr9":0.7,"a_whip":1.08,"a_k_bb":3.71,"a_gb_pct":48.0,"a_w_pct":.640,"m_era":3.27,"m_ip":711.1,"m_k9":7.7,"m_bb9":1.9,"m_hr9":1.2,"m_whip":1.15,"m_k_bb":4.05,"m_gb_pct":47.0,"m_w_pct":.600,"m_era_plus":126,"m_war":19.2,"m_seasons":8},
    "Seung-Hwan Oh":       {"a_era":1.81,"a_ip":75.0,"a_k9":10.8,"a_bb9":1.8,"a_hr9":0.4,"a_whip":0.82,"a_k_bb":6.00,"a_gb_pct":35.0,"a_w_pct":.700,"m_era":3.31,"m_ip":252.2,"m_k9":9.0,"m_bb9":2.3,"m_hr9":1.2,"m_whip":1.11,"m_k_bb":3.91,"m_gb_pct":33.0,"m_w_pct":.552,"m_era_plus":131,"m_war":4.8,"m_seasons":4},
    "Kwang-Hyun Kim":      {"a_era":3.27,"a_ip":160.0,"a_k9":8.2,"a_bb9":2.5,"a_hr9":0.6,"a_whip":1.15,"a_k_bb":3.28,"a_gb_pct":48.0,"a_w_pct":.590,"m_era":2.97,"m_ip":148.2,"m_k9":5.8,"m_bb9":3.0,"m_hr9":0.8,"m_whip":1.24,"m_k_bb":1.93,"m_gb_pct":52.0,"m_w_pct":.500,"m_era_plus":142,"m_war":3.6,"m_seasons":2},
    "Hyeon-Jong Yang":     {"a_era":3.72,"a_ip":165.0,"a_k9":7.5,"a_bb9":2.0,"a_hr9":0.9,"a_whip":1.18,"a_k_bb":3.75,"a_gb_pct":40.0,"a_w_pct":.550,"m_era":4.70,"m_ip":63.0,"m_k9":6.0,"m_bb9":2.6,"m_hr9":1.7,"m_whip":1.40,"m_k_bb":2.31,"m_gb_pct":35.0,"m_w_pct":.500,"m_era_plus":85,"m_war":0.2,"m_seasons":1},
    "Wei-Yin Chen":        {"a_era":2.59,"a_ip":650.1,"a_k9":7.20,"a_bb9":2.20,"a_hr9":0.55,"a_whip":1.086,"a_k_bb":3.27,"a_gb_pct":None,"a_w_pct":.600,"m_era":4.34,"m_ip":1065.0,"m_k9":6.5,"m_bb9":2.4,"m_hr9":1.3,"m_whip":1.30,"m_k_bb":2.71,"m_gb_pct":41.0,"m_w_pct":.479,"m_era_plus":96,"m_war":9.6,"m_seasons":8},
    "Fu-Te Ni":            {"a_era":3.60,"a_ip":40.0,"a_k9":7.0,"a_bb9":3.5,"a_hr9":0.8,"a_whip":1.30,"a_k_bb":2.00,"a_gb_pct":None,"a_w_pct":.500,"m_era":5.31,"m_ip":47.1,"m_k9":7.4,"m_bb9":4.2,"m_hr9":0.8,"m_whip":1.52,"m_k_bb":1.76,"m_gb_pct":44.0,"m_w_pct":.500,"m_era_plus":79,"m_war":0.0,"m_seasons":2},
    # Crossover: Americans NPB → MLB
    "Colby Lewis":         {"a_era":2.82,"a_ip":354.1,"a_k9":9.37,"a_bb9":1.17,"a_hr9":0.64,"a_whip":0.997,"a_k_bb":8.02,"a_gb_pct":None,"a_w_pct":.605},
    "Ryan Vogelsong":      {"a_era":4.17,"a_ip":213.2,"a_k9":8.30,"a_bb9":3.20,"a_hr9":1.01,"a_whip":1.373,"a_k_bb":2.59,"a_gb_pct":None,"a_w_pct":.440},
    "Miles Mikolas":       {"a_era":2.18,"a_ip":424.2,"a_k9":8.01,"a_bb9":1.46,"a_hr9":0.59,"a_whip":0.993,"a_k_bb":5.48,"a_gb_pct":None,"a_w_pct":.705},
    "Tony Barnette":       {"a_era":3.58,"a_ip":316.1,"a_k9":9.56,"a_bb9":3.07,"a_hr9":0.65,"a_whip":1.230,"a_k_bb":3.11,"a_gb_pct":None,"a_w_pct":.367},
    # Crossover: Americans KBO → MLB
    "Chris Flexen":        {"a_era":3.01,"a_ip":116.2,"a_k9":10.18,"a_bb9":2.31,"a_hr9":0.46,"a_whip":1.089,"a_k_bb":4.40,"a_gb_pct":None,"a_w_pct":.667},
    "Merrill Kelly":       {"a_era":3.86,"a_ip":729.2,"a_k9":7.90,"a_bb9":2.54,"a_hr9":0.80,"a_whip":1.309,"a_k_bb":3.11,"a_gb_pct":None,"a_w_pct":.600},
    "Josh Lindblom":       {"a_era":3.55,"a_ip":823.1,"a_k9":8.20,"a_bb9":2.34,"a_hr9":1.04,"a_whip":1.190,"a_k_bb":3.50,"a_gb_pct":None,"a_w_pct":.649},
    "Erick Fedde":         {"a_era":2.00,"a_ip":180.1,"a_k9":10.43,"a_bb9":1.75,"a_hr9":0.45,"a_whip":0.954,"a_k_bb":5.97,"a_gb_pct":None,"a_w_pct":.769},
}


def cached_get(url: str, key: str, delay: float = 2.0) -> str | None:
    path = CACHE / f"{key}.html"
    if path.exists():
        size = path.stat().st_size
        if size in (191307, 191308, 191309, 109726):
            return None
        return path.read_text()
    for attempt in range(4):
        time.sleep(delay if attempt == 0 else 25 * attempt)
        try:
            resp = requests.get(url, headers=HEADERS, timeout=20)
        except Exception as e:
            print(f"    Error: {e}")
            continue
        if resp.status_code == 200:
            if len(resp.text) in (191307, 191308, 191309):
                path.write_text(resp.text)
                return None
            if "Rate Limited" in resp.text[:500]:
                print(f"    rate limited, retry {attempt + 1}")
                continue
            path.write_text(resp.text)
            return resp.text
        print(f"    HTTP {resp.status_code} for {url}")
        if resp.status_code != 429:
            return None
        print(f"    retry {attempt + 1}")
    return None


# ── MLB Stats API ──────────────────────────────────────────────────────────

def fetch_mlb_api(mlb_id: int) -> dict | None:
    cache_path = CACHE / f"mlb_api_{mlb_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats?stats=career&group=pitching"
    try:
        time.sleep(0.3)
        resp = requests.get(url, timeout=10)
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        if splits:
            stats = splits[0]["stat"]
            cache_path.write_text(json.dumps(stats))
            return stats
    except Exception as e:
        print(f"    MLB API error for {mlb_id}: {e}")
    return None


def parse_mlb_api(stats: dict) -> dict:
    ip = float(stats.get("inningsPitched", "0").replace(",", ""))
    so = int(stats.get("strikeOuts", 0))
    bb = int(stats.get("baseOnBalls", 0))
    hr = int(stats.get("homeRuns", 0))
    h = int(stats.get("hits", 0))
    er = int(stats.get("earnedRuns", 0))
    w = int(stats.get("wins", 0))
    l = int(stats.get("losses", 0))
    g = int(stats.get("gamesPlayed", 0))
    gs = int(stats.get("gamesStarted", 0))
    go = int(stats.get("groundOuts", 0))
    ao = int(stats.get("airOuts", 0))
    sv = int(stats.get("saves", 0))

    k9 = (so / ip * 9) if ip > 0 else None
    bb9 = (bb / ip * 9) if ip > 0 else None
    hr9 = (hr / ip * 9) if ip > 0 else None
    whip = ((h + bb) / ip) if ip > 0 else None
    k_bb = (so / bb) if bb > 0 else None
    w_pct = (w / (w + l)) if (w + l) > 0 else None
    gb_pct = (go / (go + ao) * 100) if (go + ao) > 0 else None

    return {
        "m_ip": ip, "m_era": float(stats.get("era", 0)),
        "m_k9": round(k9, 2) if k9 else None,
        "m_bb9": round(bb9, 2) if bb9 else None,
        "m_hr9": round(hr9, 2) if hr9 else None,
        "m_whip": round(whip, 3) if whip else None,
        "m_k_bb": round(k_bb, 2) if k_bb else None,
        "m_w_pct": round(w_pct, 3) if w_pct else None,
        "m_gb_pct": round(gb_pct, 1) if gb_pct else None,
        "m_w": w, "m_l": l, "m_g": g, "m_gs": gs,
        "m_so": so, "m_bb": bb, "m_hr": hr, "m_h": h, "m_er": er,
        "m_go": go, "m_ao": ao, "m_sv": sv,
    }


def fetch_mlb_yearly(mlb_id: int) -> list[dict] | None:
    """Fetch year-by-year MLB pitching stats from the Stats API."""
    cache_path = CACHE / f"mlb_yearly_{mlb_id}.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())
    url = f"https://statsapi.mlb.com/api/v1/people/{mlb_id}/stats?stats=yearByYear&group=pitching"
    try:
        time.sleep(0.3)
        resp = requests.get(url, timeout=10)
        data = resp.json()
        splits = data.get("stats", [{}])[0].get("splits", [])
        seasons = []
        for s in splits:
            stat = s.get("stat", {})
            season = s.get("season")
            sport = s.get("sport", {})
            sport_id = sport.get("id", 0) if isinstance(sport, dict) else 0
            if sport_id == 1:
                yr = int(season)
                if yr < 1960:
                    continue
                stat["season"] = yr
                stat["team"] = s.get("team", {}).get("name", "")
                seasons.append(stat)
        cache_path.write_text(json.dumps(seasons))
        return seasons
    except Exception as e:
        print(f"    MLB yearly error for {mlb_id}: {e}")
    return None


def drop_mlb_combined(raw_rows: list[dict]) -> list[dict]:
    """yearByYear repeats a season total (blank team) next to the team splits."""
    by_season: dict[int, list[dict]] = {}
    for row in raw_rows:
        by_season.setdefault(row.get("season"), []).append(row)
    kept = []
    for group in by_season.values():
        named = [r for r in group if r.get("team")]
        kept.extend(named or group)
    return kept


def parse_mlb_season(stats: dict) -> dict:
    """Parse a single MLB season's stats into rate metrics."""
    ip = float(stats.get("inningsPitched", "0").replace(",", ""))
    # Keep short MLB seasons so a year-1 cup of coffee still appears in the roster.
    # Window aggregates require 10 IP, so these lines stay out of the correlations.
    if ip <= 0:
        return {}
    so = int(stats.get("strikeOuts", 0))
    bb = int(stats.get("baseOnBalls", 0))
    hr = int(stats.get("homeRuns", 0))
    h = int(stats.get("hits", 0))
    er = int(stats.get("earnedRuns", 0))
    go = int(stats.get("groundOuts", 0))
    ao = int(stats.get("airOuts", 0))
    return {
        "season": stats.get("season"),
        "ip": ip, "so": so, "bb": bb, "hr": hr, "h": h, "er": er,
        "go": go, "ao": ao,
        "era": round(er / ip * 9, 2),
        "k9": round(so / ip * 9, 2),
        "bb9": round(bb / ip * 9, 2),
        "hr9": round(hr / ip * 9, 2),
        "whip": round((h + bb) / ip, 3),
        "k_bb": round(so / bb, 2) if bb > 0 else None,
        "gb_pct": round(go / (go + ao) * 100, 1) if (go + ao) > 0 else None,
    }


def aggregate_counting(rows: list[dict]) -> dict | None:
    """Aggregate counting stats across multiple yearly rows into rate stats."""
    ip = so = bb = hr = h = er = go = ao = 0
    for r in rows:
        ip += r.get("ip", 0)
        so += r.get("so", 0)
        bb += r.get("bb", 0)
        hr += r.get("hr", 0)
        h += r.get("h", 0)
        er += r.get("er", 0)
        go += r.get("go", 0)
        ao += r.get("ao", 0)
    if ip < 10:
        return None
    return {
        "ip": round(ip, 1),
        "era": round(er / ip * 9, 2),
        "k9": round(so / ip * 9, 2),
        "bb9": round(bb / ip * 9, 2),
        "hr9": round(hr / ip * 9, 2),
        "whip": round((h + bb) / ip, 3),
        "k_bb": round(so / bb, 2) if bb > 0 else None,
        "gb_pct": round(go / (go + ao) * 100, 1) if (go + ao) > 0 else None,
    }


# ── BRef Register ──────────────────────────────────────────────────────────

def fetch_bref_register(reg_id: str) -> dict | None:
    url = f"https://www.baseball-reference.com/register/player.fcgi?id={reg_id}"
    html = cached_get(url, f"bref_reg_{reg_id}")
    if not html:
        return None

    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", {"id": "standard_pitching"})
    if not table:
        for comment in re.findall(r"<!--(.*?)-->", html, re.DOTALL):
            if "standard_pitching" in comment:
                table = BeautifulSoup(comment, "lxml").find("table", {"id": "standard_pitching"})
                break
    if not table:
        return None

    result = {"yearly": [], "summaries": {}}

    tbody = table.find("tbody")
    if tbody:
        for tr in tbody.find_all("tr"):
            if tr.get("class") and "thead" in " ".join(tr.get("class", [])):
                continue
            cells = {}
            for el in tr.find_all(["th", "td"]):
                stat = el.get("data-stat", "")
                if stat:
                    cells[stat] = el.get_text(strip=True)
            if cells.get("year_ID"):
                result["yearly"].append(cells)

    tfoot = table.find("tfoot")
    if tfoot:
        for tr in tfoot.find_all("tr"):
            cells = {}
            for el in tr.find_all(["th", "td"]):
                stat = el.get("data-stat", "")
                if stat:
                    cells[stat] = el.get_text(strip=True)
            label = cells.get("player_stats_summary_explain", "")
            if label:
                result["summaries"][label] = cells

    return result


def extract_asian_stats(bref_data: dict, league: str) -> dict | None:
    if not bref_data:
        return None

    summaries = bref_data.get("summaries", {})

    for key, cells in summaries.items():
        level = cells.get("level", "")
        if league == "NPB" and ("NPB" in key or "NPB" in level or "Jpn" in key):
            return _parse_summary(cells)
        if league == "KBO" and ("KBO" in key or "KBO" in level or "Kor" in key):
            return _parse_summary(cells)
        if league == "CPBL" and ("CPBL" in key or "CPBL" in level or "Twn" in key or "TML" in key):
            return _parse_summary(cells)
        if "Foreign" in key or "Foreign" in level or "Fgn" in key or "Fgn" in level:
            return _parse_summary(cells)

    yearly = bref_data.get("yearly", [])
    asian_rows = []
    for row in yearly:
        if not asian_league_of(row, league):
            continue
        team = row.get("team_ID", "")
        if "Team" not in team:
            asian_rows.append(row)

    if not asian_rows:
        return None
    return _aggregate_yearly(asian_rows)


def extract_asian_yearly(bref_data: dict, league: str) -> list[dict]:
    """Extract individual yearly rows from BRef register data for the Asian league."""
    if not bref_data:
        return []

    yearly = bref_data.get("yearly", [])
    asian_rows = []

    for row in yearly:
        row_league = asian_league_of(row, league)
        team = row.get("team_ID", "")
        year_str = row.get("year_ID", "")

        if "Team" in team or not row_league:
            continue

        try:
            ip = float(row.get("IP", 0) or 0)
        except (ValueError, TypeError):
            continue
        if ip < 5:
            continue

        try:
            so = int(float(row.get("SO", 0) or 0))
            bb = int(float(row.get("BB", 0) or 0))
            hr_val = int(float(row.get("HR", 0) or 0))
            h_val = int(float(row.get("H", 0) or 0))
            er_val = int(float(row.get("ER", 0) or 0))
            year_int = int(year_str) if year_str.isdigit() else 0
        except (ValueError, TypeError):
            continue

        asian_rows.append({
            "season": year_int,
            "league": row_league,
            "ip": ip, "so": so, "bb": bb, "hr": hr_val, "h": h_val, "er": er_val,
            "go": 0, "ao": 0,
            "era": round(er_val / ip * 9, 2) if ip > 0 else None,
            "k9": round(so / ip * 9, 2) if ip > 0 else None,
            "bb9": round(bb / ip * 9, 2) if ip > 0 else None,
            "hr9": round(hr_val / ip * 9, 2) if ip > 0 else None,
            "whip": round((h_val + bb) / ip, 3) if ip > 0 else None,
            "k_bb": round(so / bb, 2) if bb > 0 else None,
        })

    return sorted(asian_rows, key=lambda x: x["season"])


def _parse_summary(cells: dict) -> dict:
    def f(k, default=None):
        v = cells.get(k, "")
        if not v or v == "":
            return default
        try:
            return float(v)
        except ValueError:
            return default

    return {
        "a_ip": f("IP"), "a_era": f("earned_run_avg"),
        "a_k9": f("strikeouts_per_nine"), "a_bb9": f("bases_on_balls_per_nine"),
        "a_hr9": f("home_runs_per_nine"), "a_whip": f("whip"),
        "a_k_bb": f("strikeouts_per_base_on_balls"),
        "a_w": int(f("W", 0)), "a_l": int(f("L", 0)),
        "a_so": int(f("SO", 0)), "a_bb": int(f("BB", 0)),
        "a_g": int(f("G", 0)),
        "a_w_pct": f("win_loss_perc"),
    }


def _aggregate_yearly(rows: list[dict]) -> dict:
    ip = so = bb = hr = h = er = w = l = g = 0
    for r in rows:
        try:
            ip += float(r.get("IP", 0) or 0)
            so += int(float(r.get("SO", 0) or 0))
            bb += int(float(r.get("BB", 0) or 0))
            hr += int(float(r.get("HR", 0) or 0))
            h += int(float(r.get("H", 0) or 0))
            er += int(float(r.get("ER", 0) or 0))
            w += int(float(r.get("W", 0) or 0))
            l += int(float(r.get("L", 0) or 0))
            g += int(float(r.get("G", 0) or 0))
        except (ValueError, TypeError):
            continue

    if ip < 10:
        return None

    return {
        "a_ip": round(ip, 1),
        "a_era": round(er / ip * 9, 2) if ip else None,
        "a_k9": round(so / ip * 9, 2) if ip else None,
        "a_bb9": round(bb / ip * 9, 2) if ip else None,
        "a_hr9": round(hr / ip * 9, 2) if ip else None,
        "a_whip": round((h + bb) / ip, 3) if ip else None,
        "a_k_bb": round(so / bb, 2) if bb > 0 else None,
        "a_w": w, "a_l": l, "a_so": so, "a_bb": bb, "a_g": g,
        "a_w_pct": round(w / (w + l), 3) if (w + l) > 0 else None,
    }


# ── bWAR + ERA+ ───────────────────────────────────────────────────────────

def load_bwar() -> pd.DataFrame:
    path = CACHE / "war_data.csv"
    if not path.exists():
        from pybaseball import bwar_pitch
        df = bwar_pitch()
        df.to_csv(path, index=False)
        return df
    return pd.read_csv(path)


def get_war_eraplus(war_df: pd.DataFrame, mlb_id: int) -> dict:
    sub = war_df[war_df["mlb_ID"] == mlb_id]
    if len(sub) == 0:
        return {}
    return {
        "m_war": round(sub["WAR"].sum(), 1),
        "m_era_plus": round(sub["ERA_plus"].mean(), 0) if sub["ERA_plus"].notna().any() else None,
        "m_seasons_bwar": len(sub),
    }


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("ASIAN → MLB PITCHER DATA PIPELINE v3")
    print("Corrected BRef IDs + MLB API + bWAR + hand-compiled fallback")
    print("=" * 70)

    print("\n── Loading bWAR data ──")
    war_df = load_bwar()
    print(f"  {len(war_df)} rows loaded")

    results = []
    source_log = []

    for i, p in enumerate(PITCHERS):
        name = p["name"]
        print(f"\n[{i+1}/{len(PITCHERS)}] {name} ({p['league']})")

        row = {"name": name, "league": p["league"], "pos": p["pos"],
               "transition_year": p["tyear"], "origin": p.get("origin", "")}
        tyear = p["tyear"]
        sources = {"mlb": None, "bref": None, "bwar": None, "fallback": False}
        asia_from_register = False

        # 1) MLB Stats API — career + yearly
        mlb_yearly_rows = []
        if p["mlb_id"]:
            mlb_raw = fetch_mlb_api(p["mlb_id"])
            if mlb_raw:
                mlb = parse_mlb_api(mlb_raw)
                row.update(mlb)
                sources["mlb"] = "api"
                print(f"  + MLB API: {mlb['m_ip']:.0f} IP, {mlb['m_era']:.2f} ERA")

            yearly_raw = fetch_mlb_yearly(p["mlb_id"])
            if yearly_raw:
                for yr in drop_mlb_combined(yearly_raw):
                    parsed = parse_mlb_season(yr)
                    if parsed:
                        mlb_yearly_rows.append(parsed)
                if mlb_yearly_rows:
                    print(f"  + MLB yearly: {len(mlb_yearly_rows)} seasons")

            bwar = get_war_eraplus(war_df, p["mlb_id"])
            if bwar:
                row.update(bwar)
                sources["bwar"] = "bwar"
                print(f"  + bWAR: {bwar.get('m_war')} WAR, {bwar.get('m_era_plus')} ERA+")

        # 2) BRef Register for Asian stats — career + yearly
        asian_yearly_rows = []
        if p["bref_reg"]:
            bref = fetch_bref_register(p["bref_reg"])
            if bref:
                asian = extract_asian_stats(bref, p["league"])
                if asian:
                    row.update(asian)
                    asia_from_register = True
                    sources["bref"] = "register"
                    print(f"  + BRef Reg: {asian.get('a_ip')} IP, {asian.get('a_era')} ERA, {asian.get('a_k9')} K/9")

                asian_yearly_rows = extract_asian_yearly(bref, p["league"])
                if asian_yearly_rows:
                    print(f"  + Asian yearly: {len(asian_yearly_rows)} seasons")

        # 2b) Career Asian stats are pre-transition top-league seasons only.
        # A later return to Asia must not be mixed into the "before MLB" career.
        if tyear and asian_yearly_rows:
            # Same-year Asian work (the season they left) counts as pre-move.
            pre_trans = [r for r in asian_yearly_rows if r["season"] <= tyear]
            if pre_trans:
                career_agg = aggregate_counting(pre_trans)
                if career_agg:
                    row["a_ip"] = career_agg["ip"]
                    row["a_era"] = career_agg["era"]
                    row["a_k9"] = career_agg["k9"]
                    row["a_bb9"] = career_agg["bb9"]
                    row["a_hr9"] = career_agg["hr9"]
                    row["a_whip"] = career_agg["whip"]
                    row["a_k_bb"] = career_agg["k_bb"]
                    row["a_gb_pct"] = career_agg.get("gb_pct")
                    print(f"  ! Pre-transition Asian career: {len(pre_trans)} seasons ({career_agg['ip']} IP)")
                    asia_from_register = True

        pre_move = [r for r in asian_yearly_rows if tyear and r["season"] <= tyear] if asian_yearly_rows else []
        pre_ip = sum(float(r.get("ip") or 0) for r in pre_move)
        m_ip = float(row.get("m_ip") or 0)
        # Short MLB samples stay in the roster table but out of the correlations.
        row["in_analysis"] = bool(pre_move and row.get("m_era") is not None and pre_ip >= 10 and m_ip >= 10)

        # 3) Hand-compiled fallback for any missing fields
        fallback = HAND_COMPILED.get(name, {})
        filled = []
        for k, v in fallback.items():
            if k not in row or row[k] is None or (isinstance(row[k], float) and np.isnan(row[k])):
                row[k] = v
                filled.append(k)
        if filled:
            sources["fallback"] = True
            print(f"  + Fallback: filled {len(filled)} fields ({', '.join(filled[:5])}...)")

        # 4) Compute windowed aggregates (last Ny Asia vs first Ny MLB)
        for n in [1, 2, 3]:
            if tyear and asian_yearly_rows:
                last_n = [r for r in asian_yearly_rows if r["season"] >= tyear - n and r["season"] < tyear]
                agg = aggregate_counting(last_n)
                if agg:
                    for k, v in agg.items():
                        row[f"a{n}y_{k}"] = v

            if mlb_yearly_rows:
                if tyear:
                    first_n = sorted(mlb_yearly_rows, key=lambda x: x["season"])
                    mlb_start = min(r["season"] for r in first_n if r["season"] >= tyear) if any(r["season"] >= tyear for r in first_n) else None
                    if mlb_start:
                        first_n = [r for r in first_n if r["season"] >= mlb_start and r["season"] < mlb_start + n]
                else:
                    first_n = sorted(mlb_yearly_rows, key=lambda x: x["season"])[:n]
                agg = aggregate_counting(first_n)
                if agg:
                    for k, v in agg.items():
                        row[f"m{n}y_{k}"] = v

        row["asian_yearly"] = asian_yearly_rows
        row["mlb_yearly"] = mlb_yearly_rows

        results.append(row)
        source_log.append({"name": name, **sources})

    df = pd.DataFrame(results)

    def clean(v):
        if isinstance(v, (np.integer,)): return int(v)
        if isinstance(v, (np.floating,)):
            return float(v) if not np.isnan(v) else None
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)): return None
        return v

    df = df.map(clean)
    df.to_csv(OUT / "unified_pitchers.csv", index=False)

    records = df.to_dict(orient="records")
    with open(OUT / "scraped_data.json", "w") as f:
        json.dump(records, f, indent=2, default=str)

    print(f"\n{'='*70}")
    print(f"RESULTS: {len(df)} pitchers, {len(df.columns)} columns")
    has_asian = df["a_era"].notna().sum()
    has_mlb = df["m_era"].notna().sum()
    has_both = (df["a_era"].notna() & df["m_era"].notna()).sum()
    has_war = df["m_war"].notna().sum() if "m_war" in df else 0
    print(f"  Asian stats: {has_asian}/{len(df)}")
    print(f"  MLB stats:   {has_mlb}/{len(df)}")
    print(f"  Both:        {has_both}/{len(df)}")
    print(f"  WAR data:    {has_war}/{len(df)}")

    print(f"\n{'='*70}")
    print("SOURCE LOG")
    print(f"{'='*70}")
    for s in source_log:
        fb = " +FB" if s["fallback"] else ""
        print(f"  {s['name']:<24s}  MLB={s['mlb'] or 'N/A':>5s}  BRef={s['bref'] or 'N/A':>10s}  bWAR={s['bwar'] or 'N/A':>5s}{fb}")

    print(f"\n{'='*70}")
    print("DATASET PREVIEW")
    print(f"{'='*70}")
    cols = ["name", "league", "a_era", "a_k9", "a_bb9", "a_whip", "a_k_bb",
            "m_era", "m_k9", "m_bb9", "m_whip", "m_k_bb", "m_war", "m_era_plus"]
    for _, r in df.iterrows():
        parts = [f"{r['name']:<24s} {r['league']:<5s}"]
        for c in cols[2:]:
            v = r.get(c)
            if pd.notna(v):
                parts.append(f"{c}={v}")
        print("  " + "  ".join(parts[:8]))

    return df


if __name__ == "__main__":
    main()
