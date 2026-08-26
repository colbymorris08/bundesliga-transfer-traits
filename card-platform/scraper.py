"""eBay sold-listings scraper for trading card price data.

Fetches completed/sold listings from eBay's public search to build
historical price series for sports cards, Pokémon, and collectibles.

Usage:
    python3 scraper.py "2018 Luka Doncic Prizm PSA 10"
    python3 scraper.py "Charizard Base Set PSA 9" --pages 3
"""
from __future__ import annotations

import json
import re
import time
import random
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode, quote_plus

import requests
from bs4 import BeautifulSoup

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

EBAY_SEARCH_URL = "https://www.ebay.com/sch/i.html"


def build_sold_url(query: str, page: int = 1, category: int = 0) -> str:
    params = {
        "_nkw": query,
        "_sacat": category,
        "LH_Sold": "1",
        "LH_Complete": "1",
        "_pgn": page,
        "_ipg": 60,
    }
    return f"{EBAY_SEARCH_URL}?{urlencode(params)}"


def parse_price(text: str) -> float | None:
    text = text.replace(",", "").strip()
    match = re.search(r"\$?([\d]+\.?\d*)", text)
    if match:
        return float(match.group(1))
    return None


def parse_date(text: str) -> str | None:
    text = text.strip().lower()
    patterns = [
        (r"(\w+ \d{1,2}, \d{4})", "%b %d, %Y"),
        (r"(\d{1,2} \w+ \d{4})", "%d %b %Y"),
    ]
    for pattern, fmt in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return datetime.strptime(match.group(1), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def scrape_sold_page(query: str, page: int = 1) -> list[dict]:
    url = build_sold_url(query, page)
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    try:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  Request failed: {e}")
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    items = []

    for card in soup.select("li.s-item"):
        title_el = card.select_one(".s-item__title")
        price_el = card.select_one(".s-item__price")
        date_el = card.select_one(".s-item__title--tag, .s-item__ended-date, .POSITIVE")
        link_el = card.select_one("a.s-item__link")

        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        if title.lower().startswith("shop on ebay"):
            continue

        price = parse_price(price_el.get_text(strip=True))
        if price is None or price < 0.5:
            continue

        sold_date = None
        if date_el:
            sold_date = parse_date(date_el.get_text())

        link = link_el["href"] if link_el else None

        items.append({
            "title": title,
            "price": price,
            "sold_date": sold_date,
            "url": link,
            "query": query,
            "scraped_at": datetime.now().isoformat(),
        })

    return items


def scrape_card(query: str, pages: int = 2, delay: float = 3.0) -> list[dict]:
    """Scrape multiple pages of sold listings for a card."""
    all_items = []
    print(f"Scraping: {query}")

    for page in range(1, pages + 1):
        print(f"  Page {page}...", end="", flush=True)
        items = scrape_sold_page(query, page)
        print(f" {len(items)} items")
        all_items.extend(items)

        if page < pages:
            wait = delay + random.uniform(1, 3)
            time.sleep(wait)

    return all_items


def compute_stats(items: list[dict]) -> dict:
    """Compute price statistics from scraped items."""
    prices = [i["price"] for i in items if i["price"]]
    if not prices:
        return {}

    prices_sorted = sorted(prices)
    n = len(prices_sorted)

    return {
        "count": n,
        "avg": round(sum(prices) / n, 2),
        "median": round(prices_sorted[n // 2], 2),
        "low": round(prices_sorted[0], 2),
        "high": round(prices_sorted[-1], 2),
        "p25": round(prices_sorted[n // 4], 2),
        "p75": round(prices_sorted[3 * n // 4], 2),
    }


def generate_rating(items: list[dict]) -> dict:
    """Generate buy/hold/sell rating based on price trend."""
    dated = [i for i in items if i.get("sold_date")]
    if len(dated) < 4:
        return {"rating": "HOLD", "confidence": "low", "reason": "Insufficient data"}

    dated.sort(key=lambda x: x["sold_date"])
    mid = len(dated) // 2
    recent = [i["price"] for i in dated[mid:]]
    older = [i["price"] for i in dated[:mid]]

    avg_recent = sum(recent) / len(recent)
    avg_older = sum(older) / len(older)

    if avg_older == 0:
        return {"rating": "HOLD", "confidence": "low", "reason": "No baseline"}

    pct_change = (avg_recent - avg_older) / avg_older * 100

    if pct_change > 15:
        rating = "STRONG BUY"
        reason = f"Price trending up {pct_change:.1f}% over sample period"
    elif pct_change > 5:
        rating = "BUY"
        reason = f"Moderate uptrend +{pct_change:.1f}%"
    elif pct_change > -5:
        rating = "HOLD"
        reason = f"Stable pricing ({pct_change:+.1f}%)"
    elif pct_change > -15:
        rating = "SELL"
        reason = f"Declining {pct_change:.1f}%"
    else:
        rating = "STRONG SELL"
        reason = f"Sharp decline {pct_change:.1f}%"

    confidence = "high" if len(dated) > 15 else "medium" if len(dated) > 8 else "low"

    return {"rating": rating, "confidence": confidence, "reason": reason, "pct_change": round(pct_change, 1)}


def save_results(query: str, items: list[dict], stats: dict, rating: dict):
    """Save scrape results to JSON."""
    slug = re.sub(r"[^a-z0-9]+", "_", query.lower()).strip("_")
    path = DATA_DIR / f"{slug}.json"
    payload = {
        "query": query,
        "scraped_at": datetime.now().isoformat(),
        "stats": stats,
        "rating": rating,
        "items": items,
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  Saved to {path}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Scrape eBay sold listings for trading cards")
    parser.add_argument("query", help="Search query (e.g. '2018 Luka Doncic Prizm PSA 10')")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages to scrape (default 2)")
    parser.add_argument("--delay", type=float, default=4.0, help="Delay between pages in seconds")
    args = parser.parse_args()

    items = scrape_card(args.query, pages=args.pages, delay=args.delay)
    if not items:
        print("No items found.")
        return

    stats = compute_stats(items)
    rating = generate_rating(items)

    print(f"\n  Results: {stats.get('count', 0)} sales")
    print(f"  Avg: ${stats.get('avg', 0):.2f} | Median: ${stats.get('median', 0):.2f}")
    print(f"  Range: ${stats.get('low', 0):.2f} – ${stats.get('high', 0):.2f}")
    print(f"  Rating: {rating['rating']} ({rating['confidence']} confidence)")
    print(f"  Reason: {rating.get('reason', '')}")

    save_results(args.query, items, stats, rating)


if __name__ == "__main__":
    main()
