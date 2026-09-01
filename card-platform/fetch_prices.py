"""Unified search-driven pricing engine across all asset classes.

Routes queries to the appropriate data source(s) based on asset class,
aggregates results, and returns a standardized valuation + recommendation.

Asset classes and their primary data sources:
  Sports Cards   → HoodCar API (live), 130Point (comps), Goldin (auctions)
  Memorabilia    → Goldin Auctions, Heritage Auctions, eBay sold
  Art            → LiveArt API, Art Market API, AuctionAsk
  Comics         → HoodCar (graded), GPAnalysis (reference), eBay sold
  Watches        → WatchCharts API, Chrono24
  TCG            → HoodCar (graded Pokémon), PriceCharting, eBay sold

Every source is optional — the engine uses whatever API keys are configured
and gracefully falls back when a source is unavailable.
"""
from __future__ import annotations

import json
import os
import re
import time
import random
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── API KEYS (set via environment or GitHub Secrets) ───────────────────────

HOODCAR_API_KEY = os.environ.get("HOODCAR_API_KEY", "")
LIVEART_API_KEY = os.environ.get("LIVEART_API_KEY", "")
WATCHCHARTS_API_KEY = os.environ.get("WATCHCHARTS_API_KEY", "")
PRICECHARTING_API_KEY = os.environ.get("PRICECHARTING_API_KEY", "")

HOODCAR_BASE = "https://api.hoodcar.com"
LIVEART_BASE = "https://api.liveart.ai"
WATCHCHARTS_BASE = "https://watchcharts.com/api"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def _headers_hoodcar():
    return {"x-api-key": HOODCAR_API_KEY}


def _api_get(url, headers=None, params=None, timeout=15):
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  API error ({url}): {e}")
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  SPORTS CARDS — HoodCar + 130Point + Goldin
# ═══════════════════════════════════════════════════════════════════════════

def search_cards(query: str, grade: str = "") -> dict:
    """Search sports cards via HoodCar API."""
    results = {"source": "hoodcar", "items": []}
    if not HOODCAR_API_KEY:
        return results

    q = f"{query} {grade}".strip()
    data = _api_get(f"{HOODCAR_BASE}/v3/value", _headers_hoodcar(), {"q": q})
    if data and data.get("data"):
        d = data["data"]
        results["items"].append({
            "name": q,
            "fair_value": d.get("value"),
            "buy_score": d.get("buy_score"),
            "verdict": d.get("verdict"),
            "confidence": d.get("confidence"),
            "liquidity": d.get("liquidity"),
            "last_sale": d.get("last_sale"),
            "grade_ladder": d.get("grade_ladder", []),
            "source": "HoodCar",
        })
    return results


def get_card_market_data() -> dict:
    """Get market overview: index, movers, floor."""
    overview = {}
    if not HOODCAR_API_KEY:
        return overview

    for endpoint in ["movers"]:
        data = _api_get(f"{HOODCAR_BASE}/v1/{endpoint}", _headers_hoodcar())
        if data and data.get("data"):
            overview[endpoint] = data["data"]

    for cat in ["basketball", "football", "baseball", "pokemon"]:
        data = _api_get(f"{HOODCAR_BASE}/v1/index", _headers_hoodcar(), {"category": cat})
        if data and data.get("data"):
            overview[f"index_{cat}"] = data["data"]

        data = _api_get(f"{HOODCAR_BASE}/v1/floor", _headers_hoodcar(), {"category": cat})
        if data and data.get("data"):
            overview[f"floor_{cat}"] = data["data"]

    return overview


# ═══════════════════════════════════════════════════════════════════════════
#  MEMORABILIA — eBay sold comps (Goldin/Heritage via future integration)
# ═══════════════════════════════════════════════════════════════════════════

def search_memorabilia(query: str) -> dict:
    """Search memorabilia via eBay sold listings + HoodCar (for graded items)."""
    results = {"source": "multi", "items": []}

    if HOODCAR_API_KEY:
        data = _api_get(f"{HOODCAR_BASE}/v3/value", _headers_hoodcar(), {"q": query})
        if data and data.get("data") and data["data"].get("value"):
            d = data["data"]
            results["items"].append({
                "name": query,
                "fair_value": d.get("value"),
                "buy_score": d.get("buy_score"),
                "verdict": d.get("verdict"),
                "confidence": d.get("confidence"),
                "source": "HoodCar",
            })

    # eBay sold comps (fallback — works from home IP, may get 403 from cloud)
    ebay_results = _scrape_ebay_sold(query, limit=10)
    if ebay_results:
        prices = [r["price"] for r in ebay_results if r.get("price")]
        if prices:
            results["items"].append({
                "name": query,
                "fair_value": round(sum(prices) / len(prices), 2),
                "median": round(sorted(prices)[len(prices) // 2], 2),
                "low": round(min(prices), 2),
                "high": round(max(prices), 2),
                "comp_count": len(prices),
                "comps": ebay_results[:5],
                "source": "eBay Sold",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  ART — LiveArt API + fallback eBay
# ═══════════════════════════════════════════════════════════════════════════

def search_art(query: str) -> dict:
    """Search art via LiveArt API or fallback to eBay auction comps."""
    results = {"source": "liveart", "items": []}

    if LIVEART_API_KEY:
        data = _api_get(
            f"{LIVEART_BASE}/v1/artworks",
            {"Authorization": f"Bearer {LIVEART_API_KEY}"},
            {"q": query, "limit": 5},
        )
        if data and data.get("items"):
            for item in data["items"]:
                results["items"].append({
                    "name": item.get("title", query),
                    "artist": item.get("artist_name"),
                    "fair_value": item.get("current_estimated_price"),
                    "estimate_low": item.get("current_estimated_price_min"),
                    "estimate_high": item.get("current_estimated_price_max"),
                    "momentum": item.get("price_momentum_12mo"),
                    "medium": item.get("medium"),
                    "year": item.get("year"),
                    "source": "LiveArt",
                })
            return results

    # Fallback: eBay fine art sold comps
    ebay_results = _scrape_ebay_sold(f"{query} art print", limit=10)
    if ebay_results:
        prices = [r["price"] for r in ebay_results if r.get("price")]
        if prices:
            results["items"].append({
                "name": query,
                "fair_value": round(sum(prices) / len(prices), 2),
                "comp_count": len(prices),
                "source": "eBay Sold",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  COMICS — HoodCar (graded) + eBay sold
# ═══════════════════════════════════════════════════════════════════════════

def search_comics(query: str, grade: str = "") -> dict:
    """Search comics via HoodCar (graded) or eBay."""
    results = {"source": "multi", "items": []}
    q = f"{query} {grade}".strip()

    if HOODCAR_API_KEY:
        data = _api_get(f"{HOODCAR_BASE}/v3/value", _headers_hoodcar(), {"q": q})
        if data and data.get("data") and data["data"].get("value"):
            d = data["data"]
            results["items"].append({
                "name": q,
                "fair_value": d.get("value"),
                "buy_score": d.get("buy_score"),
                "verdict": d.get("verdict"),
                "source": "HoodCar",
            })

    ebay_results = _scrape_ebay_sold(q, limit=10)
    if ebay_results:
        prices = [r["price"] for r in ebay_results if r.get("price")]
        if prices:
            results["items"].append({
                "name": q,
                "fair_value": round(sum(prices) / len(prices), 2),
                "comp_count": len(prices),
                "source": "eBay Sold",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  WATCHES — WatchCharts API + Chrono24 fallback
# ═══════════════════════════════════════════════════════════════════════════

def search_watches(query: str) -> dict:
    """Search watches via WatchCharts API."""
    results = {"source": "watchcharts", "items": []}

    if WATCHCHARTS_API_KEY:
        data = _api_get(
            f"{WATCHCHARTS_BASE}/v1/search",
            {"x-api-key": WATCHCHARTS_API_KEY},
            {"q": query},
        )
        if data and data.get("data"):
            for w in data["data"][:5]:
                results["items"].append({
                    "name": f"{w.get('brand','')} {w.get('model','')} {w.get('reference','')}".strip(),
                    "fair_value": w.get("market_price"),
                    "brand": w.get("brand"),
                    "reference": w.get("reference"),
                    "uuid": w.get("uuid"),
                    "source": "WatchCharts",
                })
            return results

    # Fallback: eBay luxury watch sold comps
    ebay_results = _scrape_ebay_sold(query, limit=10)
    if ebay_results:
        prices = [r["price"] for r in ebay_results if r.get("price")]
        if prices:
            results["items"].append({
                "name": query,
                "fair_value": round(sum(prices) / len(prices), 2),
                "comp_count": len(prices),
                "source": "eBay Sold",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  TCG (Pokémon, MTG, Yu-Gi-Oh) — HoodCar + PriceCharting
# ═══════════════════════════════════════════════════════════════════════════

def search_tcg(query: str, grade: str = "") -> dict:
    """Search TCG cards via HoodCar or PriceCharting."""
    results = {"source": "multi", "items": []}
    q = f"{query} {grade}".strip()

    if HOODCAR_API_KEY:
        data = _api_get(f"{HOODCAR_BASE}/v3/value", _headers_hoodcar(), {"q": q})
        if data and data.get("data") and data["data"].get("value"):
            d = data["data"]
            results["items"].append({
                "name": q,
                "fair_value": d.get("value"),
                "buy_score": d.get("buy_score"),
                "verdict": d.get("verdict"),
                "source": "HoodCar",
            })

    if PRICECHARTING_API_KEY:
        data = _api_get(
            "https://www.pricecharting.com/api/products",
            params={"t": PRICECHARTING_API_KEY, "q": query, "type": "prices"},
        )
        if data and isinstance(data, dict):
            results["items"].append({
                "name": query,
                "pricecharting_data": data,
                "source": "PriceCharting",
            })

    return results


# ═══════════════════════════════════════════════════════════════════════════
#  EBAY SOLD SCRAPER (shared fallback for all asset classes)
# ═══════════════════════════════════════════════════════════════════════════

def _scrape_ebay_sold(query: str, limit: int = 10) -> list[dict]:
    """Scrape eBay completed/sold listings. May return empty from cloud IPs."""
    url = f"https://www.ebay.com/sch/i.html?{urlencode({'_nkw': query, 'LH_Sold': '1', 'LH_Complete': '1', '_ipg': 60})}"
    try:
        resp = requests.get(url, headers={"User-Agent": random.choice(USER_AGENTS)}, timeout=15)
        if resp.status_code != 200:
            return []
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []
    for card in soup.select("li.s-item")[:limit]:
        title_el = card.select_one(".s-item__title")
        price_el = card.select_one(".s-item__price")
        if not title_el or not price_el:
            continue
        title = title_el.get_text(strip=True)
        if title.lower().startswith("shop on ebay"):
            continue
        price_text = price_el.get_text(strip=True).replace(",", "")
        match = re.search(r"\$?([\d]+\.?\d*)", price_text)
        if match:
            items.append({"title": title, "price": float(match.group(1)), "source": "eBay"})
    return items


# ═══════════════════════════════════════════════════════════════════════════
#  UNIFIED SEARCH — routes to the right source(s)
# ═══════════════════════════════════════════════════════════════════════════

ASSET_CLASS_ROUTERS = {
    "cards": search_cards,
    "memorabilia": search_memorabilia,
    "art": search_art,
    "comics": search_comics,
    "watches": search_watches,
    "tcg": search_tcg,
}


def detect_asset_class(query: str) -> str:
    """Auto-detect asset class from query keywords."""
    q = query.lower()
    words = set(re.split(r"[\s\-/,]+", q))

    # Art (check before memorabilia to avoid 'ball' in 'balloon' false positive)
    art_kw = {"banksy", "warhol", "basquiat", "kaws", "haring", "kusama", "hirst",
              "richter", "monet", "picasso", "pollock", "rothko", "dali",
              "screenprint", "lithograph", "painting", "sculpture", "etching",
              "oil", "acrylic", "watercolor", "gouache", "giclée", "serigraph"}
    if words & art_kw or "oil on" in q or "art print" in q or "mixed media" in q:
        return "art"

    if any(w in q for w in ["psa", "bgs", "sgc", "prizm", "topps", "bowman", "panini", "rookie", " rc ", "fleer", "donruss", "optic", "select", "mosaic"]):
        return "cards"

    memo_kw = {"jersey", "game-worn", "game-used", "helmet", "autograph", "uda",
               "bat", "glove", "stick", "ring", "trophy", "cleats", "warm-up"}
    if words & memo_kw or "signed" in q or "game worn" in q or "game used" in q or "match worn" in q:
        return "memorabilia"

    if any(w in q for w in ["cgc", "marvel", "dc", "spider-man", "batman", "x-men", "comic", "key issue", "detective comics", "action comics"]):
        return "comics"

    if any(w in q for w in ["rolex", "patek", "audemars", "omega", "cartier", "breitling", "tudor", "iwc",
                            "daytona", "nautilus", "royal oak", "submariner", "speedmaster", "aquanaut"]):
        return "watches"

    if any(w in q for w in ["pokemon", "pokémon", "charizard", "pikachu", "mtg", "magic the gathering",
                            "yu-gi-oh", "yugioh", "one piece tcg", "lorcana", "digimon"]):
        return "tcg"

    return "cards"


def generate_recommendation(item: dict, asset_class: str) -> dict:
    """Generate LIQUIDATE / HOLD / REVIEW recommendation."""
    fv = item.get("fair_value")
    score = item.get("buy_score")
    confidence = item.get("confidence")
    momentum = item.get("momentum")
    comp_count = item.get("comp_count", 0)

    if fv is None:
        return {"rating": "REVIEW", "reason": "No fair value data available — manual appraisal required"}

    # HoodCar verdict mapping
    verdict = item.get("verdict", "")
    if verdict in ("Strong Buy", "Accumulate"):
        rating = "HOLD"
        reason = f"Uptrend detected — holding may increase proceeds"
    elif verdict == "Hold":
        rating = "LIQUIDATE"
        reason = f"Stable pricing with liquidity — safe to sell at FMV"
    elif verdict in ("Reduce",):
        rating = "LIQUIDATE"
        reason = f"Declining value — liquidate promptly to preserve proceeds"
    elif score and score >= 70:
        rating = "HOLD"
        reason = f"Buy score {score}/100 suggests appreciation potential"
    elif score and score <= 40:
        rating = "LIQUIDATE"
        reason = f"Low buy score ({score}/100) — market moving away from this item"
    elif confidence and confidence < 30:
        rating = "REVIEW"
        reason = f"Low confidence ({confidence}%) — manual appraisal recommended"
    elif comp_count and comp_count >= 5:
        rating = "LIQUIDATE"
        reason = f"Sufficient comps ({comp_count} sales) — price well-established"
    else:
        rating = "REVIEW"
        reason = "Limited market data — recommend human appraisal"

    net_fee_pct = 0.87 if asset_class in ("cards", "tcg", "comics") else 0.82
    est_proceeds = round(fv * net_fee_pct, 2) if fv else None

    return {
        "rating": rating,
        "reason": reason,
        "est_net_proceeds": est_proceeds,
    }


def unified_search(query: str, asset_class: str = "auto", grade: str = "") -> dict:
    """Main entry point: search any collectible, get valuation + recommendation."""
    if asset_class == "auto":
        asset_class = detect_asset_class(query)

    router = ASSET_CLASS_ROUTERS.get(asset_class, search_cards)

    print(f"  Searching [{asset_class}]: {query} {grade}")
    if asset_class in ("cards", "comics", "tcg"):
        raw = router(query, grade)
    else:
        raw = router(query)

    result = {
        "query": query,
        "grade": grade,
        "asset_class": asset_class,
        "fetched_at": datetime.now().isoformat(),
        "sources_used": [],
        "items": [],
    }

    for item in raw.get("items", []):
        rec = generate_recommendation(item, asset_class)
        item["recommendation"] = rec
        result["items"].append(item)
        result["sources_used"].append(item.get("source", "unknown"))

    return result


# ─── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Unified collectible pricing search")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--grade", default="", help="Grade (e.g. 'PSA 10', 'CGC 9.8')")
    parser.add_argument("--asset", default="auto", choices=["auto", "cards", "memorabilia", "art", "comics", "watches", "tcg"], help="Asset class")
    parser.add_argument("--market", action="store_true", help="Fetch market overview (cards only)")
    parser.add_argument("--key", help="HoodCar API key")
    args = parser.parse_args()

    if args.key:
        HOODCAR_API_KEY = args.key

    if args.market:
        print("Fetching market overview...")
        data = get_card_market_data()
        out = DATA_DIR / "market_overview.json"
        with open(out, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {out}")
    elif args.query:
        result = unified_search(args.query, args.asset, args.grade)
        print(json.dumps(result, indent=2, default=str))

        slug = re.sub(r"[^a-z0-9]+", "_", args.query.lower())[:40]
        out = DATA_DIR / f"{slug}.json"
        with open(out, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\nSaved to {out}")
    else:
        parser.print_help()
