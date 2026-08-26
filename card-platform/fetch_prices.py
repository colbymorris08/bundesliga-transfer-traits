"""Multi-source card pricing data fetcher.

Integrates all available data sources for the Card Vault platform.
Each source is optional — the system uses whatever APIs are configured.

TIER 1 (Primary — implemented):
  - HoodCar API: Fair Value, Buy Score, Verdict, sold comps, market index
  - 130Point: eBay sold comps + Goldin + Heritage + MySlabs + Fanatics
  - PriceCharting: Grade ladder pricing, historical charts [PAID — placeholder]

TIER 2 (Specialty — placeholder for future):
  - CardSight AI: AI-matched pricing, source-transparent
  - SportsCardsPro: Grade-by-grade pricing + monthly trends
  - PriceDepth: Institutional oracle feeds
  - CardLadder: CL Value + confidence + population

TIER 3 (Market Intelligence — reference):
  - PSA Pop Reports: Population/scarcity data
  - Goldin Auctions: High-end auction results
  - Market Movers: Portfolio tracking
"""
from __future__ import annotations

import json
import os
import time
import random
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# ─── HOODCAR API (Tier 1 — Free: 1,000 req/mo) ────────────────────────────

HOODCAR_API_KEY = os.environ.get("HOODCAR_API_KEY", "")
HOODCAR_BASE = "https://api.hoodcar.com"


def hoodcar_value(query: str, grade: str = "") -> dict | None:
    """Get Fair Value, Buy Score, Verdict from HoodCar /v3/value."""
    if not HOODCAR_API_KEY:
        return None

    params = {"q": query}
    if grade:
        params["grade"] = grade

    try:
        resp = requests.get(
            f"{HOODCAR_BASE}/v3/value",
            headers={"x-api-key": HOODCAR_API_KEY},
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("data")
    except Exception as e:
        print(f"  HoodCar error: {e}")
        return None


def hoodcar_sold(query: str, grade: str = "") -> dict | None:
    """Get aggregated sold-comp stats from HoodCar /v1/sold."""
    if not HOODCAR_API_KEY:
        return None

    params = {"q": query}
    if grade:
        params["grade"] = grade

    try:
        resp = requests.get(
            f"{HOODCAR_BASE}/v1/sold",
            headers={"x-api-key": HOODCAR_API_KEY},
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except Exception as e:
        print(f"  HoodCar sold error: {e}")
        return None


def hoodcar_index(category: str = "basketball") -> dict | None:
    """Get daily price index time series from HoodCar /v1/index."""
    if not HOODCAR_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{HOODCAR_BASE}/v1/index",
            headers={"x-api-key": HOODCAR_API_KEY},
            params={"category": category},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except Exception as e:
        print(f"  HoodCar index error: {e}")
        return None


def hoodcar_movers() -> dict | None:
    """Get top movers by recent price change from HoodCar /v1/movers."""
    if not HOODCAR_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{HOODCAR_BASE}/v1/movers",
            headers={"x-api-key": HOODCAR_API_KEY},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except Exception as e:
        print(f"  HoodCar movers error: {e}")
        return None


def hoodcar_floor(category: str = "basketball") -> dict | None:
    """Get current floor snapshot from HoodCar /v1/floor."""
    if not HOODCAR_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{HOODCAR_BASE}/v1/floor",
            headers={"x-api-key": HOODCAR_API_KEY},
            params={"category": category},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("data")
    except Exception as e:
        print(f"  HoodCar floor error: {e}")
        return None


# ─── 130POINT (Tier 1 — Free, scrape-based) ────────────────────────────────

_130POINT_BASE = "https://www.130point.com/sales/"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
]


def fetch_130point(query: str) -> list[dict]:
    """Scrape 130Point sold comps for a card query."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": "https://www.130point.com/",
    })

    # Warm up session with homepage cookies
    try:
        session.get("https://www.130point.com/", timeout=10)
    except Exception:
        pass

    time.sleep(1)

    try:
        resp = session.get(_130POINT_BASE, params={"q": query}, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"  130Point error: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for row in soup.select(".sale-item, .search-result-item, tr[data-price]"):
        try:
            title_el = row.select_one(".title, .item-title, td:nth-child(1)")
            price_el = row.select_one(".price, .sold-price, td:nth-child(2)")
            date_el = row.select_one(".date, .sold-date, td:nth-child(3)")

            if not title_el or not price_el:
                continue

            price_text = price_el.get_text(strip=True).replace("$", "").replace(",", "")
            price = float(price_text) if price_text else None

            items.append({
                "title": title_el.get_text(strip=True),
                "price": price,
                "date": date_el.get_text(strip=True) if date_el else None,
                "source": "130point",
            })
        except (ValueError, TypeError):
            continue

    return items


# ─── PRICECHARTING (Tier 1 — Paid $9.99/mo, placeholder) ──────────────────

PRICECHARTING_API_KEY = os.environ.get("PRICECHARTING_API_KEY", "")
PRICECHARTING_BASE = "https://www.pricecharting.com/api"


def pricecharting_search(query: str) -> dict | None:
    """Search PriceCharting for a card. Requires paid API key."""
    if not PRICECHARTING_API_KEY:
        return None

    try:
        resp = requests.get(
            f"{PRICECHARTING_BASE}/products",
            params={"t": PRICECHARTING_API_KEY, "q": query, "type": "prices"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  PriceCharting error: {e}")
        return None


# ─── UNIFIED FETCH ─────────────────────────────────────────────────────────

def fetch_card_data(query: str, grade: str = "PSA 10") -> dict:
    """Fetch card data from all available sources and merge."""
    result = {
        "query": query,
        "grade": grade,
        "fetched_at": datetime.now().isoformat(),
        "sources": {},
    }

    # HoodCar (primary)
    hc = hoodcar_value(f"{query} {grade}")
    if hc:
        result["sources"]["hoodcar"] = hc
        result["fair_value"] = hc.get("value")
        result["buy_score"] = hc.get("buy_score")
        result["verdict"] = hc.get("verdict")
        result["confidence"] = hc.get("confidence")
        result["liquidity"] = hc.get("liquidity")
        print(f"  HoodCar: ${hc.get('value')} | Score: {hc.get('buy_score')} | {hc.get('verdict')}")

    # 130Point (sold comps)
    comps = fetch_130point(f"{query} {grade}")
    if comps:
        result["sources"]["130point"] = comps[:20]
        prices = [c["price"] for c in comps if c.get("price")]
        if prices:
            result["comp_avg"] = round(sum(prices) / len(prices), 2)
            result["comp_median"] = round(sorted(prices)[len(prices) // 2], 2)
            result["comp_count"] = len(prices)
            print(f"  130Point: {len(prices)} comps, avg ${result['comp_avg']}")

    # PriceCharting (if available)
    pc = pricecharting_search(query)
    if pc:
        result["sources"]["pricecharting"] = pc
        print(f"  PriceCharting: data retrieved")

    # HoodCar sold comps
    sold = hoodcar_sold(f"{query} {grade}")
    if sold:
        result["sources"]["hoodcar_sold"] = sold
        print(f"  HoodCar sold: {sold}")

    return result


def fetch_market_overview() -> dict:
    """Get market-wide data: index, movers, floor by category."""
    overview = {"fetched_at": datetime.now().isoformat()}

    categories = ["basketball", "football", "baseball", "pokemon"]
    for cat in categories:
        idx = hoodcar_index(cat)
        if idx:
            overview[f"index_{cat}"] = idx

        floor = hoodcar_floor(cat)
        if floor:
            overview[f"floor_{cat}"] = floor

    movers = hoodcar_movers()
    if movers:
        overview["movers"] = movers

    return overview


# ─── CLI ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch card pricing from all sources")
    parser.add_argument("query", nargs="?", help="Card search query")
    parser.add_argument("--grade", default="PSA 10", help="Grade (default: PSA 10)")
    parser.add_argument("--market", action="store_true", help="Fetch market overview instead")
    parser.add_argument("--key", help="HoodCar API key (or set HOODCAR_API_KEY env var)")
    args = parser.parse_args()

    if args.key:
        HOODCAR_API_KEY = args.key

    if not HOODCAR_API_KEY:
        print("Set HOODCAR_API_KEY env var or pass --key")
        print("Get your free key at: https://hoodcar.com/get-key")

    if args.market:
        print("Fetching market overview...")
        data = fetch_market_overview()
        out_path = DATA_DIR / "market_overview.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {out_path}")
    elif args.query:
        print(f"Fetching: {args.query} [{args.grade}]")
        data = fetch_card_data(args.query, args.grade)
        slug = args.query.lower().replace(" ", "_")[:40]
        out_path = DATA_DIR / f"{slug}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)
        print(f"\nSaved to {out_path}")
        print(json.dumps({k: v for k, v in data.items() if k != "sources"}, indent=2))
    else:
        parser.print_help()
