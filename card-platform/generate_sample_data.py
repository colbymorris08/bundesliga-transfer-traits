"""Generate sample data for the Card Vault / Cause Collectibles platform.

Creates realistic mock data across all asset classes:
  - Sports Cards (graded)
  - Memorabilia (jerseys, bats, balls, helmets, etc.)
  - Art (paintings, prints, sculptures)
  - Comics (graded)
  - Watches (luxury/collectible)
  - Trading Card Games (Pokémon, MTG, Yu-Gi-Oh)

Uses LIQUIDATE / HOLD / REVIEW rating system for Cause Collectibles positioning.
"""
import json
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

ITEMS = [
    # ── Sports Cards ──
    {"id": "luka-prizm-psa10", "name": "2018-19 Panini Prizm Luka Dončić RC #280 PSA 10", "asset_class": "Sports Cards", "sport": "Basketball", "brand": "Panini Prizm", "player": "Luka Dončić", "team": "Dallas Mavericks", "year": 2018, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 2200, "trend": "up", "volatility": 0.15},
    {"id": "wemby-prizm-psa10", "name": "2023-24 Panini Prizm Victor Wembanyama RC #225 PSA 10", "asset_class": "Sports Cards", "sport": "Basketball", "brand": "Panini Prizm", "player": "Victor Wembanyama", "team": "San Antonio Spurs", "year": 2023, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 850, "trend": "up", "volatility": 0.25},
    {"id": "jordan-fleer-psa9", "name": "1986-87 Fleer Michael Jordan RC #57 PSA 9", "asset_class": "Sports Cards", "sport": "Basketball", "brand": "Fleer", "player": "Michael Jordan", "team": "Chicago Bulls", "year": 1986, "grade": "PSA 9", "era": "Vintage", "type": "Rookie Card", "base_price": 28000, "trend": "stable", "volatility": 0.08},
    {"id": "lebron-topps-psa10", "name": "2003-04 Topps LeBron James RC #221 PSA 10", "asset_class": "Sports Cards", "sport": "Basketball", "brand": "Topps", "player": "LeBron James", "team": "Cleveland Cavaliers", "year": 2003, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 42000, "trend": "up", "volatility": 0.10},
    {"id": "ohtani-bowman-psa10", "name": "2018 Bowman Chrome Shohei Ohtani RC PSA 10", "asset_class": "Sports Cards", "sport": "Baseball", "brand": "Bowman Chrome", "player": "Shohei Ohtani", "team": "Los Angeles Dodgers", "year": 2018, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 1100, "trend": "up", "volatility": 0.18},
    {"id": "trout-update-psa10", "name": "2011 Topps Update Mike Trout RC #US175 PSA 10", "asset_class": "Sports Cards", "sport": "Baseball", "brand": "Topps", "player": "Mike Trout", "team": "Los Angeles Angels", "year": 2011, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 3800, "trend": "down", "volatility": 0.12},
    {"id": "mahomes-prizm-psa10", "name": "2017 Panini Prizm Patrick Mahomes RC #269 PSA 10", "asset_class": "Sports Cards", "sport": "Football", "brand": "Panini Prizm", "player": "Patrick Mahomes", "team": "Kansas City Chiefs", "year": 2017, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 9500, "trend": "stable", "volatility": 0.12},
    {"id": "jokic-prizm-psa10", "name": "2015-16 Panini Prizm Nikola Jokić RC #335 PSA 10", "asset_class": "Sports Cards", "sport": "Basketball", "brand": "Panini Prizm", "player": "Nikola Jokić", "team": "Denver Nuggets", "year": 2015, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 4800, "trend": "up", "volatility": 0.14},
    {"id": "charizard-base-psa9", "name": "1999 Pokémon Base Set Charizard #4 PSA 9", "asset_class": "TCG", "sport": "Pokémon", "brand": "Base Set", "player": "Charizard", "team": "", "year": 1999, "grade": "PSA 9", "era": "Vintage", "type": "Holographic", "base_price": 4200, "trend": "stable", "volatility": 0.10},
    {"id": "lugia-1st-psa10", "name": "2000 Pokémon Neo Genesis Lugia 1st Ed #9 PSA 10", "asset_class": "TCG", "sport": "Pokémon", "brand": "Neo Genesis", "player": "Lugia", "team": "", "year": 2000, "grade": "PSA 10", "era": "Vintage", "type": "1st Edition", "base_price": 8500, "trend": "up", "volatility": 0.15},
    {"id": "messi-panini-psa10", "name": "2004 Panini Mega Cracks Lionel Messi RC PSA 10", "asset_class": "Sports Cards", "sport": "Soccer", "brand": "Panini", "player": "Lionel Messi", "team": "FC Barcelona", "year": 2004, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 1200000, "trend": "stable", "volatility": 0.06},
    {"id": "bellingham-topps-psa10", "name": "2020 Topps Chrome UCL Jude Bellingham RC PSA 10", "asset_class": "Sports Cards", "sport": "Soccer", "brand": "Topps Chrome", "player": "Jude Bellingham", "team": "Real Madrid", "year": 2020, "grade": "PSA 10", "era": "Modern", "type": "Rookie Card", "base_price": 3200, "trend": "up", "volatility": 0.22},

    # ── Memorabilia ──
    {"id": "jordan-jersey-uda", "name": "Michael Jordan Game-Worn Bulls Jersey (1996 Finals) UDA Authenticated", "asset_class": "Memorabilia", "sport": "Basketball", "brand": "UDA", "player": "Michael Jordan", "team": "Chicago Bulls", "year": 1996, "grade": "Authenticated", "era": "Vintage", "type": "Jersey", "base_price": 480000, "trend": "up", "volatility": 0.06},
    {"id": "ruth-bat-psa", "name": "Babe Ruth Game-Used Bat (1920s) PSA/DNA Authenticated", "asset_class": "Memorabilia", "sport": "Baseball", "brand": "PSA/DNA", "player": "Babe Ruth", "team": "New York Yankees", "year": 1925, "grade": "Authenticated", "era": "Pre-War", "type": "Bat", "base_price": 1200000, "trend": "up", "volatility": 0.04},
    {"id": "brady-helmet-fanatics", "name": "Tom Brady Game-Worn SB LI Helmet Fanatics Authentic", "asset_class": "Memorabilia", "sport": "Football", "brand": "Fanatics", "player": "Tom Brady", "team": "New England Patriots", "year": 2017, "grade": "Authenticated", "era": "Modern", "type": "Helmet", "base_price": 340000, "trend": "stable", "volatility": 0.08},
    {"id": "ohtani-ball-signed", "name": "Shohei Ohtani Signed Official MLB Baseball Fanatics Hologram", "asset_class": "Memorabilia", "sport": "Baseball", "brand": "Fanatics", "player": "Shohei Ohtani", "team": "Los Angeles Dodgers", "year": 2024, "grade": "Certified Auto", "era": "Modern", "type": "Signed Baseball", "base_price": 850, "trend": "up", "volatility": 0.20},
    {"id": "messi-jersey-match", "name": "Lionel Messi Match-Worn Argentina Jersey (2022 WC Final)", "asset_class": "Memorabilia", "sport": "Soccer", "brand": "Adidas", "player": "Lionel Messi", "team": "Argentina", "year": 2022, "grade": "Match-Worn", "era": "Modern", "type": "Jersey", "base_price": 7800000, "trend": "stable", "volatility": 0.03},
    {"id": "gretzky-stick-hof", "name": "Wayne Gretzky Game-Used Hockey Stick (802nd Goal) LOA", "asset_class": "Memorabilia", "sport": "Hockey", "brand": "LOA", "player": "Wayne Gretzky", "team": "Los Angeles Kings", "year": 1994, "grade": "Authenticated", "era": "Vintage", "type": "Stick", "base_price": 290000, "trend": "up", "volatility": 0.07},

    # ── Art ──
    {"id": "banksy-gdmj", "name": "Banksy — Girl with Balloon (2006, screenprint, ed. 150)", "asset_class": "Art", "sport": "", "brand": "Pest Control", "player": "Banksy", "team": "", "year": 2006, "grade": "COA", "era": "Contemporary", "type": "Print", "base_price": 1100000, "trend": "stable", "volatility": 0.08},
    {"id": "kaws-companion", "name": "KAWS — Companion (Resting Place) 2013, vinyl sculpture", "asset_class": "Art", "sport": "", "brand": "Medicom", "player": "KAWS", "team": "", "year": 2013, "grade": "Mint/Boxed", "era": "Contemporary", "type": "Sculpture", "base_price": 45000, "trend": "down", "volatility": 0.18},
    {"id": "warhol-campbell-print", "name": "Andy Warhol — Campbell's Soup I (1968, screenprint, ed. 250)", "asset_class": "Art", "sport": "", "brand": "Authenticated", "player": "Andy Warhol", "team": "", "year": 1968, "grade": "Provenance", "era": "Post-War", "type": "Print", "base_price": 680000, "trend": "up", "volatility": 0.06},
    {"id": "basquiat-skull-print", "name": "Jean-Michel Basquiat — Untitled (Skull) 1982 Lithograph", "asset_class": "Art", "sport": "", "brand": "Estate", "player": "Jean-Michel Basquiat", "team": "", "year": 1982, "grade": "Provenance", "era": "Contemporary", "type": "Print", "base_price": 380000, "trend": "up", "volatility": 0.10},
    {"id": "haring-radiant-baby", "name": "Keith Haring — Radiant Baby (1990, screenprint, ed. 100)", "asset_class": "Art", "sport": "", "brand": "Authenticated", "player": "Keith Haring", "team": "", "year": 1990, "grade": "COA", "era": "Contemporary", "type": "Print", "base_price": 95000, "trend": "stable", "volatility": 0.09},
    {"id": "kusama-pumpkin", "name": "Yayoi Kusama — Pumpkin (2004, screenprint, ed. 120)", "asset_class": "Art", "sport": "", "brand": "Authenticated", "player": "Yayoi Kusama", "team": "", "year": 2004, "grade": "COA", "era": "Contemporary", "type": "Print", "base_price": 210000, "trend": "up", "volatility": 0.12},

    # ── Comics ──
    {"id": "asm-300-cgc98", "name": "Amazing Spider-Man #300 (1988) CGC 9.8 — 1st Venom", "asset_class": "Comics", "sport": "", "brand": "Marvel", "player": "Venom / Spider-Man", "team": "", "year": 1988, "grade": "CGC 9.8", "era": "Copper Age", "type": "Key Issue", "base_price": 3800, "trend": "up", "volatility": 0.14},
    {"id": "batman-1-cgc30", "name": "Batman #1 (1940) CGC 3.0 — 1st Joker & Catwoman", "asset_class": "Comics", "sport": "", "brand": "DC", "player": "Batman / Joker", "team": "", "year": 1940, "grade": "CGC 3.0", "era": "Golden Age", "type": "Key Issue", "base_price": 280000, "trend": "stable", "volatility": 0.05},
    {"id": "xmen-1-cgc60", "name": "X-Men #1 (1963) CGC 6.0 — 1st X-Men", "asset_class": "Comics", "sport": "", "brand": "Marvel", "player": "X-Men", "team": "", "year": 1963, "grade": "CGC 6.0", "era": "Silver Age", "type": "Key Issue", "base_price": 48000, "trend": "up", "volatility": 0.09},

    # ── Watches ──
    {"id": "rolex-daytona-116500", "name": "Rolex Cosmograph Daytona 116500LN (White Dial, 2023)", "asset_class": "Watches", "sport": "", "brand": "Rolex", "player": "", "team": "", "year": 2023, "grade": "Unworn/Box+Papers", "era": "Modern", "type": "Chronograph", "base_price": 28000, "trend": "down", "volatility": 0.10},
    {"id": "patek-nautilus-5711", "name": "Patek Philippe Nautilus 5711/1A (Blue Dial, Discontinued)", "asset_class": "Watches", "sport": "", "brand": "Patek Philippe", "player": "", "team": "", "year": 2021, "grade": "Unworn/Box+Papers", "era": "Modern", "type": "Sport", "base_price": 135000, "trend": "down", "volatility": 0.12},
    {"id": "ap-royal-oak-15500", "name": "Audemars Piguet Royal Oak 15500ST (Blue Dial)", "asset_class": "Watches", "sport": "", "brand": "Audemars Piguet", "player": "", "team": "", "year": 2022, "grade": "Unworn/Box+Papers", "era": "Modern", "type": "Sport", "base_price": 42000, "trend": "stable", "volatility": 0.08},
]

CHARACTERISTICS = {
    "Sports Cards": ["Rookie Card", "Auto", "Patch", "Parallel", "Insert", "Base", "Holographic", "1st Edition", "Numbered"],
    "Memorabilia": ["Jersey", "Bat", "Ball", "Helmet", "Stick", "Signed Baseball", "Signed Photo", "Ring", "Trophy", "Glove"],
    "Art": ["Print", "Painting", "Sculpture", "Photography", "Mixed Media", "Drawing"],
    "Comics": ["Key Issue", "1st Appearance", "Origin Story", "Variant Cover", "Newsstand"],
    "Watches": ["Chronograph", "Sport", "Dress", "Dive", "Pilot", "Field"],
    "TCG": ["Holographic", "1st Edition", "Full Art", "Secret Rare", "Sealed Product"],
}


def generate_price_history(item: dict, days: int = 365) -> list[dict]:
    history = []
    price = item["base_price"]
    vol = item["volatility"]
    trend_map = {"up": 0.0004, "down": -0.0003, "stable": 0.0001}
    daily_drift = trend_map[item["trend"]]
    start = datetime.now() - timedelta(days=days)
    for day in range(days):
        date = start + timedelta(days=day)
        if random.random() < 0.3:
            noise = random.gauss(0, vol * price * 0.02)
            seasonal = math.sin(day / 365 * 2 * math.pi) * price * 0.03
            price = price * (1 + daily_drift) + noise + seasonal * 0.01
            price = max(price * 0.5, price)
            history.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    return history


def generate_predictions(item: dict, current_price: float) -> list[dict]:
    ac = item["asset_class"]
    if ac in ("Sports Cards", "Memorabilia"):
        scenarios = [
            {"label": "MVP / Championship / HoF", "multiplier": 1.6, "probability": 0.15},
            {"label": "Strong Season / Milestone", "multiplier": 1.25, "probability": 0.30},
            {"label": "Steady Demand", "multiplier": 1.05, "probability": 0.35},
            {"label": "Injury / Decline", "multiplier": 0.70, "probability": 0.15},
            {"label": "Scandal / Delisting", "multiplier": 0.40, "probability": 0.05},
        ]
    elif ac == "Art":
        scenarios = [
            {"label": "Major Exhibition / Museum Acquisition", "multiplier": 1.5, "probability": 0.10},
            {"label": "Auction Record / Collector Demand", "multiplier": 1.20, "probability": 0.25},
            {"label": "Stable Market", "multiplier": 1.05, "probability": 0.40},
            {"label": "Market Correction / Oversupply", "multiplier": 0.80, "probability": 0.20},
            {"label": "Provenance Issue / Attribution Dispute", "multiplier": 0.50, "probability": 0.05},
        ]
    elif ac == "Comics":
        scenarios = [
            {"label": "MCU / Film Announcement", "multiplier": 1.5, "probability": 0.15},
            {"label": "Collector Resurgence", "multiplier": 1.20, "probability": 0.30},
            {"label": "Steady Key Demand", "multiplier": 1.05, "probability": 0.35},
            {"label": "Spec Bubble Pop", "multiplier": 0.75, "probability": 0.15},
            {"label": "Reprint / Oversaturation", "multiplier": 0.55, "probability": 0.05},
        ]
    elif ac == "Watches":
        scenarios = [
            {"label": "Discontinuation / Waitlist Spike", "multiplier": 1.35, "probability": 0.15},
            {"label": "Steady Luxury Demand", "multiplier": 1.10, "probability": 0.35},
            {"label": "Market Plateau", "multiplier": 0.95, "probability": 0.30},
            {"label": "Grey Market Correction", "multiplier": 0.75, "probability": 0.15},
            {"label": "Counterfeit Scandal / Recall", "multiplier": 0.55, "probability": 0.05},
        ]
    else:
        scenarios = [
            {"label": "Scarcity / Hype Cycle", "multiplier": 1.4, "probability": 0.20},
            {"label": "Steady Collector Demand", "multiplier": 1.10, "probability": 0.45},
            {"label": "Market Correction", "multiplier": 0.85, "probability": 0.25},
            {"label": "Reprint / Oversaturation", "multiplier": 0.60, "probability": 0.10},
        ]

    branches = []
    for s in scenarios:
        target = current_price * s["multiplier"]
        points = []
        p = current_price
        for month in range(1, 13):
            p += (target - p) * 0.15 + random.gauss(0, current_price * 0.02)
            points.append({"month": month, "price": round(p, 2)})
        branches.append({"label": s["label"], "probability": s["probability"], "target_price": round(target, 2), "path": points})
    return branches


def generate_rating(item: dict, history: list) -> dict:
    """LIQUIDATE / HOLD / REVIEW rating system for Cause Collectibles."""
    if len(history) < 10:
        return {"rating": "REVIEW", "score": 50, "confidence": "low", "change": 0, "reason": "Insufficient data — manual appraisal recommended"}

    recent = [h["price"] for h in history[-20:]]
    older = [h["price"] for h in history[-60:-20]] or recent
    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    pct = (avg_recent - avg_older) / avg_older * 100 if avg_older else 0

    # Liquidity proxy from volume
    volume = len(history)
    is_liquid = volume > 80

    if pct < -5 and is_liquid:
        rating, score = "LIQUIDATE", 85
        reason = f"Declining {pct:.1f}% with sufficient liquidity — sell now to maximize proceeds"
    elif pct < -5:
        rating, score = "REVIEW", 45
        reason = f"Declining {pct:.1f}% but low liquidity — manual channel assessment needed"
    elif pct > 10 and is_liquid:
        rating, score = "HOLD", 75
        reason = f"Strong uptrend +{pct:.1f}% — holding likely increases nonprofit proceeds"
    elif pct > 5:
        rating, score = "HOLD", 65
        reason = f"Moderate uptrend +{pct:.1f}% — consider holding 30-60 days"
    elif is_liquid:
        rating, score = "LIQUIDATE", 70
        reason = f"Stable pricing ({pct:+.1f}%) with good liquidity — safe to sell"
    else:
        rating, score = "REVIEW", 55
        reason = f"Stable pricing ({pct:+.1f}%) but limited comps — manual review recommended"

    confidence = "high" if volume > 80 else "medium" if volume > 40 else "low"
    est_proceeds_now = avg_recent * 0.87
    est_proceeds_30d = avg_recent * (1 + pct / 100 * 0.5) * 0.87

    return {
        "rating": rating,
        "score": score,
        "confidence": confidence,
        "change": round(pct, 1),
        "reason": reason,
        "est_net_proceeds": round(est_proceeds_now, 2),
        "est_30d_proceeds": round(est_proceeds_30d, 2),
    }


def main():
    all_items = []
    for item in ITEMS:
        history = generate_price_history(item)
        current_price = history[-1]["price"] if history else item["base_price"]
        predictions = generate_predictions(item, current_price)
        rating = generate_rating(item, history)

        all_items.append({
            **item,
            "current_price": round(current_price, 2),
            "history": history,
            "predictions": predictions,
            "rating": rating,
        })
        print(f"  [{item['asset_class'][:5]}] {item['name'][:50]}... ${current_price:,.0f} [{rating['rating']}]")

    payload = {
        "items": all_items,
        "characteristics": CHARACTERISTICS,
        "asset_classes": list(set(i["asset_class"] for i in ITEMS)),
        "generated_at": datetime.now().isoformat(),
    }
    with open(OUT / "cards.json", "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"\nGenerated {len(all_items)} items across {len(payload['asset_classes'])} asset classes → data/cards.json")


if __name__ == "__main__":
    main()
