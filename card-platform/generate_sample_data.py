"""Generate sample card data for the explorer demo.

Creates realistic mock data based on real market patterns for
popular cards across sports, Pokémon, and collectibles.
"""
import json
import random
import math
from datetime import datetime, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)

CARDS = [
    {"id": "luka-prizm-psa10", "name": "2018-19 Panini Prizm Luka Dončić RC #280 PSA 10", "sport": "Basketball", "brand": "Panini Prizm", "player": "Luka Dončić", "year": 2018, "grade": "PSA 10", "base_price": 2200, "trend": "up", "volatility": 0.15},
    {"id": "wemby-prizm-psa10", "name": "2023-24 Panini Prizm Victor Wembanyama RC #225 PSA 10", "sport": "Basketball", "brand": "Panini Prizm", "player": "Victor Wembanyama", "year": 2023, "grade": "PSA 10", "base_price": 850, "trend": "up", "volatility": 0.25},
    {"id": "jordan-fleer-psa9", "name": "1986-87 Fleer Michael Jordan RC #57 PSA 9", "sport": "Basketball", "brand": "Fleer", "player": "Michael Jordan", "year": 1986, "grade": "PSA 9", "base_price": 28000, "trend": "stable", "volatility": 0.08},
    {"id": "lebron-topps-psa10", "name": "2003-04 Topps LeBron James RC #221 PSA 10", "sport": "Basketball", "brand": "Topps", "player": "LeBron James", "year": 2003, "grade": "PSA 10", "base_price": 42000, "trend": "up", "volatility": 0.10},
    {"id": "ohtani-bowman-psa10", "name": "2018 Bowman Chrome Shohei Ohtani RC PSA 10", "sport": "Baseball", "brand": "Bowman Chrome", "player": "Shohei Ohtani", "year": 2018, "grade": "PSA 10", "base_price": 1100, "trend": "up", "volatility": 0.18},
    {"id": "trout-update-psa10", "name": "2011 Topps Update Mike Trout RC #US175 PSA 10", "sport": "Baseball", "brand": "Topps", "player": "Mike Trout", "year": 2011, "grade": "PSA 10", "base_price": 3800, "trend": "down", "volatility": 0.12},
    {"id": "soto-topps-psa10", "name": "2018 Topps Update Juan Soto RC #US300 PSA 10", "sport": "Baseball", "brand": "Topps", "player": "Juan Soto", "year": 2018, "grade": "PSA 10", "base_price": 520, "trend": "up", "volatility": 0.20},
    {"id": "mahomes-prizm-psa10", "name": "2017 Panini Prizm Patrick Mahomes RC #269 PSA 10", "sport": "Football", "brand": "Panini Prizm", "player": "Patrick Mahomes", "year": 2017, "grade": "PSA 10", "base_price": 9500, "trend": "stable", "volatility": 0.12},
    {"id": "stroud-prizm-psa10", "name": "2023 Panini Prizm C.J. Stroud RC PSA 10", "sport": "Football", "brand": "Panini Prizm", "player": "C.J. Stroud", "year": 2023, "grade": "PSA 10", "base_price": 280, "trend": "up", "volatility": 0.30},
    {"id": "caleb-prizm-psa10", "name": "2024 Panini Prizm Caleb Williams RC PSA 10", "sport": "Football", "brand": "Panini Prizm", "player": "Caleb Williams", "year": 2024, "grade": "PSA 10", "base_price": 180, "trend": "down", "volatility": 0.35},
    {"id": "charizard-base-psa9", "name": "1999 Pokémon Base Set Charizard #4 PSA 9", "sport": "Pokémon", "brand": "Base Set", "player": "Charizard", "year": 1999, "grade": "PSA 9", "base_price": 4200, "trend": "stable", "volatility": 0.10},
    {"id": "pikachu-illustrator", "name": "1998 Pokémon Illustrator Pikachu PSA 7", "sport": "Pokémon", "brand": "Promo", "player": "Pikachu", "year": 1998, "grade": "PSA 7", "base_price": 900000, "trend": "up", "volatility": 0.05},
    {"id": "lugia-1st-psa10", "name": "2000 Pokémon Neo Genesis Lugia 1st Ed #9 PSA 10", "sport": "Pokémon", "brand": "Neo Genesis", "player": "Lugia", "year": 2000, "grade": "PSA 10", "base_price": 8500, "trend": "up", "volatility": 0.15},
    {"id": "messi-topps-psa10", "name": "2004 Panini Mega Cracks Lionel Messi RC PSA 10", "sport": "Soccer", "brand": "Panini", "player": "Lionel Messi", "year": 2004, "grade": "PSA 10", "base_price": 1200000, "trend": "stable", "volatility": 0.06},
    {"id": "bellingham-topps-psa10", "name": "2020 Topps Chrome UCL Jude Bellingham RC PSA 10", "sport": "Soccer", "brand": "Topps Chrome", "player": "Jude Bellingham", "year": 2020, "grade": "PSA 10", "base_price": 3200, "trend": "up", "volatility": 0.22},
    {"id": "jokic-prizm-psa10", "name": "2015-16 Panini Prizm Nikola Jokić RC #335 PSA 10", "sport": "Basketball", "brand": "Panini Prizm", "player": "Nikola Jokić", "year": 2015, "grade": "PSA 10", "base_price": 4800, "trend": "up", "volatility": 0.14},
    {"id": "acuna-bowman-psa10", "name": "2017 Bowman Chrome Ronald Acuña Jr. RC PSA 10", "sport": "Baseball", "brand": "Bowman Chrome", "player": "Ronald Acuña Jr.", "year": 2017, "grade": "PSA 10", "base_price": 380, "trend": "down", "volatility": 0.20},
    {"id": "cj-optic-psa10", "name": "2023 Donruss Optic C.J. Stroud RC PSA 10", "sport": "Football", "brand": "Donruss Optic", "player": "C.J. Stroud", "year": 2023, "grade": "PSA 10", "base_price": 190, "trend": "up", "volatility": 0.28},
    {"id": "pokemon-evolving-skies", "name": "Pokémon SWSH Evolving Skies Booster Box (Sealed)", "sport": "Pokémon", "brand": "Evolving Skies", "player": "Sealed Product", "year": 2021, "grade": "Sealed", "base_price": 320, "trend": "up", "volatility": 0.12},
    {"id": "bowman-2024-box", "name": "2024 Bowman Baseball Hobby Box (Sealed)", "sport": "Baseball", "brand": "Bowman", "player": "Sealed Product", "year": 2024, "grade": "Sealed", "base_price": 290, "trend": "stable", "volatility": 0.08},
]


def generate_price_history(card: dict, days: int = 365) -> list[dict]:
    """Generate realistic price history with trends and noise."""
    history = []
    price = card["base_price"]
    vol = card["volatility"]
    trend_map = {"up": 0.0004, "down": -0.0003, "stable": 0.0001}
    daily_drift = trend_map[card["trend"]]

    start = datetime.now() - timedelta(days=days)

    for day in range(days):
        date = start + timedelta(days=day)
        if random.random() < 0.3:
            noise = random.gauss(0, vol * price * 0.02)
            seasonal = math.sin(day / 365 * 2 * math.pi) * price * 0.03
            price = price * (1 + daily_drift) + noise + seasonal * 0.01
            price = max(price * 0.5, price)
            history.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 2),
            })

    return history


def generate_predictions(card: dict, current_price: float) -> list[dict]:
    """Generate branching future predictions based on player scenarios."""
    scenarios = []
    if card["sport"] in ("Basketball", "Baseball", "Football", "Soccer"):
        scenarios = [
            {"label": "MVP / Championship", "multiplier": 1.6, "probability": 0.15},
            {"label": "All-Star Season", "multiplier": 1.25, "probability": 0.30},
            {"label": "Steady Performance", "multiplier": 1.05, "probability": 0.35},
            {"label": "Injury / Decline", "multiplier": 0.70, "probability": 0.15},
            {"label": "Major Scandal/Bust", "multiplier": 0.40, "probability": 0.05},
        ]
    else:
        scenarios = [
            {"label": "New Set Hype / Reprint Scarcity", "multiplier": 1.4, "probability": 0.20},
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
        branches.append({
            "label": s["label"],
            "probability": s["probability"],
            "target_price": round(target, 2),
            "path": points,
        })

    return branches


def generate_rating(card: dict, history: list) -> dict:
    if len(history) < 10:
        return {"rating": "HOLD", "score": 50, "confidence": "low"}

    recent = [h["price"] for h in history[-20:]]
    older = [h["price"] for h in history[-60:-20]] or recent
    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)
    pct = (avg_recent - avg_older) / avg_older * 100 if avg_older else 0

    if pct > 15:
        return {"rating": "STRONG BUY", "score": 85, "confidence": "high", "change": round(pct, 1)}
    elif pct > 5:
        return {"rating": "BUY", "score": 70, "confidence": "medium", "change": round(pct, 1)}
    elif pct > -5:
        return {"rating": "HOLD", "score": 50, "confidence": "medium", "change": round(pct, 1)}
    elif pct > -15:
        return {"rating": "SELL", "score": 30, "confidence": "medium", "change": round(pct, 1)}
    else:
        return {"rating": "STRONG SELL", "score": 15, "confidence": "high", "change": round(pct, 1)}


def main():
    all_cards = []
    for card in CARDS:
        history = generate_price_history(card)
        current_price = history[-1]["price"] if history else card["base_price"]
        predictions = generate_predictions(card, current_price)
        rating = generate_rating(card, history)

        all_cards.append({
            **card,
            "current_price": round(current_price, 2),
            "history": history,
            "predictions": predictions,
            "rating": rating,
        })
        print(f"  {card['name'][:50]}... ${current_price:.0f} [{rating['rating']}]")

    payload = {"cards": all_cards, "generated_at": datetime.now().isoformat()}
    with open(OUT / "cards.json", "w") as f:
        json.dump(payload, f, separators=(",", ":"))

    print(f"\nGenerated {len(all_cards)} cards → data/cards.json")


if __name__ == "__main__":
    main()
