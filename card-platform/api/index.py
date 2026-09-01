"""Card Vault API — Vercel serverless backend with caching.

Proxies HoodCar API, caches responses to conserve the 1K req/month free tier.
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Card Vault API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

HOODCAR_KEY = os.environ.get("HOODCAR_API_KEY", "")
HOODCAR = "https://api.hoodcar.com"

# In-memory cache (persists within a single function invocation on Vercel,
# but resets between cold starts — fine for our use case)
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 3600  # 1 hour


def _cached_get(url: str, params: dict) -> dict | None:
    key = f"{url}?{json.dumps(params, sort_keys=True)}"
    now = time.time()
    if key in _cache and now - _cache[key][0] < CACHE_TTL:
        return _cache[key][1]

    try:
        resp = httpx.get(url, headers={"x-api-key": HOODCAR_KEY}, params=params, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            _cache[key] = (now, data)
            return data
    except Exception:
        pass
    return None


def _recommendation(data: dict) -> dict:
    """Generate LIQUIDATE/HOLD/REVIEW from HoodCar response."""
    verdict = data.get("verdict", "")
    score = data.get("buy_score")
    confidence = data.get("confidence")
    value = data.get("value")
    trend = data.get("trend_30d")

    if verdict in ("Strong Buy", "Accumulate"):
        rating, reason = "HOLD", "Uptrend detected — holding may increase proceeds"
    elif verdict == "Hold":
        rating, reason = "LIQUIDATE", "Stable pricing with liquidity — sell at current FMV"
    elif verdict == "Reduce":
        rating, reason = "LIQUIDATE", "Declining value — liquidate promptly"
    elif score and score >= 70:
        rating, reason = "HOLD", f"Buy score {score}/100 suggests appreciation potential"
    elif score and score <= 40:
        rating, reason = "LIQUIDATE", f"Low market interest (score {score}) — sell now"
    elif confidence and confidence < 20:
        rating, reason = "REVIEW", f"Low confidence ({confidence}%) — manual appraisal recommended"
    else:
        rating, reason = "REVIEW", "Limited market data — recommend human appraisal"

    if trend and trend > 10:
        reason += f" (30-day trend: +{trend:.1f}%)"
    elif trend and trend < -10:
        reason += f" (30-day trend: {trend:.1f}%)"

    est = round(value * 0.87, 2) if value else None

    return {"rating": rating, "reason": reason, "est_net_proceeds": est}


@app.get("/api/health")
def health():
    return {"status": "ok", "hoodcar_configured": bool(HOODCAR_KEY)}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2), grade: str = Query("")):
    """Search cards — returns value + grade ladder for drilling down."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    query = f"{q} {grade}".strip()
    data = _cached_get(f"{HOODCAR}/v3/value", {"q": query})

    if not data or not data.get("data"):
        return JSONResponse({"error": "No results found", "query": query}, 404)

    d = data["data"]
    rec = _recommendation(d)

    grade_ladder = []
    for g in d.get("by_grade", []):
        grade_ladder.append({
            "grade": g.get("grade"),
            "value": g.get("value"),
            "low": g.get("low"),
            "high": g.get("high"),
            "sample_size": g.get("sample_size"),
        })

    return {
        "query": d.get("query", query),
        "fair_value": d.get("value"),
        "avg_price": d.get("avg"),
        "buy_score": d.get("buy_score"),
        "verdict": d.get("verdict"),
        "confidence": d.get("confidence"),
        "liquidity": d.get("liquidity"),
        "sample_size": d.get("sample_size"),
        "sales_90d": d.get("sales_90d"),
        "trend_30d": d.get("trend_30d"),
        "last_sale": d.get("last_sale"),
        "last_sale_date": d.get("last_sale_date"),
        "grade_ladder": grade_ladder,
        "recommendation": rec,
    }


@app.get("/api/movers")
async def movers():
    """Top market movers — cached aggressively."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    data = _cached_get(f"{HOODCAR}/v1/movers", {})
    if not data or not data.get("data"):
        return JSONResponse({"error": "Could not fetch movers"}, 502)

    return data["data"]


@app.get("/api/categories")
async def categories():
    """All available categories with listing counts."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    data = _cached_get(f"{HOODCAR}/v1/categories", {})
    if not data or not data.get("data"):
        return JSONResponse({"error": "Could not fetch categories"}, 502)

    return data["data"]


@app.get("/api/floor")
async def floor(category: str = Query("basketball")):
    """Market floor snapshot for a category."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    data = _cached_get(f"{HOODCAR}/v1/floor", {"category": category})
    if not data or not data.get("data"):
        return JSONResponse({"error": "Could not fetch floor"}, 502)

    return data["data"]


@app.get("/api/index")
async def index(category: str = Query("basketball")):
    """Market index time series for a category."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    data = _cached_get(f"{HOODCAR}/v1/index", {"category": category})
    if not data or not data.get("data"):
        return JSONResponse({"error": "Could not fetch index"}, 502)

    return data["data"]


@app.get("/api/cert")
async def cert_lookup(cert: str = Query(..., min_length=4)):
    """PSA cert number lookup → card details → auto-valuation via HoodCar.

    Flow: cert number → PSA API (card info + grade) → HoodCar (FMV + recommendation)
    This is the Cause Collectibles donation intake: donor enters cert, system does the rest.
    """
    cert = cert.strip()

    # Step 1: Look up cert on PSA
    psa_data = None
    psa_error = None
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                f"https://api.psacard.com/publicapi/cert/GetByCertNumber/{cert}",
                headers={"Accept": "application/json"},
            )
            if resp.status_code == 200:
                body = resp.json()
                if isinstance(body, str) and "quota" in body.lower():
                    psa_error = "PSA API daily limit reached (100/day). Try again tomorrow."
                elif isinstance(body, dict) and body.get("PSACert"):
                    psa_data = body
                else:
                    psa_error = "PSA returned unexpected data format"
            else:
                psa_error = f"PSA API returned status {resp.status_code}"
        except Exception as e:
            psa_error = f"Could not connect to PSA: {str(e)}"

    if not psa_data:
        return JSONResponse({
            "error": psa_error or "Could not verify this cert number with PSA",
            "cert": cert,
            "hint": "Check the number on the slab label and try again. PSA allows 100 lookups per day.",
        }, 503 if "limit" in (psa_error or "") else 404)

    psa = psa_data["PSACert"]
    card_info = {
        "cert_number": psa.get("CertNumber", cert),
        "year": psa.get("Year", ""),
        "brand": psa.get("Brand", ""),
        "category": psa.get("Category", ""),
        "card_number": psa.get("CardNumber", ""),
        "player": psa.get("Subject", ""),
        "grade": psa.get("CardGrade", ""),
        "grade_description": psa.get("GradeDescription", ""),
        "label_type": psa.get("LabelType", ""),
        "spec_number": psa.get("SpecNumber", ""),
    }

    # Build search query from PSA data
    search_parts = [card_info["player"], card_info["brand"], card_info["year"]]
    search_query = " ".join(p for p in search_parts if p).strip()
    grade_str = ""
    if card_info["grade"]:
        grade_str = f"PSA {card_info['grade']}"

    # Step 2: Get valuation from HoodCar
    valuation = None
    if HOODCAR_KEY and search_query:
        q = f"{search_query} {grade_str}".strip()
        hc_data = _cached_get(f"{HOODCAR}/v3/value", {"q": q})
        if hc_data and hc_data.get("data"):
            d = hc_data["data"]
            rec = _recommendation(d)

            # Find the 3 most recent comp prices from grade ladder
            grade_ladder = []
            for g in d.get("by_grade", []):
                grade_ladder.append({
                    "grade": g.get("grade"),
                    "value": g.get("value"),
                    "low": g.get("low"),
                    "high": g.get("high"),
                    "sample_size": g.get("sample_size"),
                })

            valuation = {
                "fair_value": d.get("value"),
                "avg_price": d.get("avg"),
                "buy_score": d.get("buy_score"),
                "verdict": d.get("verdict"),
                "confidence": d.get("confidence"),
                "liquidity": d.get("liquidity"),
                "sample_size": d.get("sample_size"),
                "sales_90d": d.get("sales_90d"),
                "trend_30d": d.get("trend_30d"),
                "last_sale": d.get("last_sale"),
                "last_sale_date": d.get("last_sale_date"),
                "grade_ladder": grade_ladder,
                "recommendation": rec,
                "search_query": q,
            }

    return {
        "cert": cert,
        "psa": card_info,
        "description": f"{card_info['year']} {card_info['brand']} {card_info['player']} #{card_info['card_number']} PSA {card_info['grade']}".strip(),
        "valuation": valuation,
    }
