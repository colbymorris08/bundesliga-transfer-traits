"""Card Vault API — Vercel serverless backend.

Proxies HoodCar API calls so the frontend never exposes the API key.
Also serves pre-fetched trending/movers data for the landing page.
"""
from __future__ import annotations

import os
import json
import re
from pathlib import Path

import httpx
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI(title="Card Vault API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

HOODCAR_KEY = os.environ.get("HOODCAR_API_KEY", "")
HOODCAR = "https://api.hoodcar.com"


def hc_headers():
    return {"x-api-key": HOODCAR_KEY}


@app.get("/api/health")
def health():
    return {"status": "ok", "hoodcar_configured": bool(HOODCAR_KEY)}


@app.get("/api/search")
async def search(q: str = Query(..., min_length=2), grade: str = Query("")):
    """Search for any card/collectible via HoodCar."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    query = f"{q} {grade}".strip()
    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{HOODCAR}/v3/value", headers=hc_headers(), params={"q": query})

    if resp.status_code != 200:
        return JSONResponse({"error": "HoodCar API error", "status": resp.status_code}, 502)

    data = resp.json().get("data", {})

    verdict = data.get("verdict", "")
    if verdict in ("Strong Buy", "Accumulate"):
        rating = "HOLD"
        reason = "Uptrend detected — holding may increase proceeds"
    elif verdict in ("Hold",):
        rating = "LIQUIDATE"
        reason = "Stable pricing with liquidity — sell at current FMV"
    elif verdict in ("Reduce",):
        rating = "LIQUIDATE"
        reason = "Declining value — liquidate promptly"
    else:
        score = data.get("buy_score")
        if score and score >= 70:
            rating = "HOLD"
            reason = f"Buy score {score}/100 suggests appreciation"
        elif score and score <= 40:
            rating = "LIQUIDATE"
            reason = f"Low market interest (score {score}) — sell now"
        else:
            rating = "REVIEW"
            reason = "Insufficient signal — manual appraisal recommended"

    fv = data.get("value")
    return {
        "query": query,
        "fair_value": fv,
        "buy_score": data.get("buy_score"),
        "verdict": verdict,
        "confidence": data.get("confidence"),
        "liquidity": data.get("liquidity"),
        "last_sale": data.get("last_sale"),
        "grade_ladder": data.get("grade_ladder", []),
        "matched_cards": data.get("matched_cards", []),
        "recommendation": {
            "rating": rating,
            "reason": reason,
            "est_net_proceeds": round(fv * 0.87, 2) if fv else None,
        },
    }


@app.get("/api/movers")
async def movers():
    """Get top market movers from HoodCar."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{HOODCAR}/v1/movers", headers=hc_headers())

    if resp.status_code != 200:
        return JSONResponse({"error": "HoodCar API error"}, 502)

    return resp.json().get("data", {})


@app.get("/api/index")
async def index(category: str = Query("basketball")):
    """Get market index time series."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{HOODCAR}/v1/index", headers=hc_headers(), params={"category": category})

    if resp.status_code != 200:
        return JSONResponse({"error": "HoodCar API error"}, 502)

    return resp.json().get("data", {})


@app.get("/api/floor")
async def floor(category: str = Query("basketball")):
    """Get market floor snapshot."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{HOODCAR}/v1/floor", headers=hc_headers(), params={"category": category})

    if resp.status_code != 200:
        return JSONResponse({"error": "HoodCar API error"}, 502)

    return resp.json().get("data", {})


@app.get("/api/sold")
async def sold(q: str = Query(..., min_length=2)):
    """Get sold comp stats."""
    if not HOODCAR_KEY:
        return JSONResponse({"error": "API key not configured"}, 503)

    async with httpx.AsyncClient(timeout=12) as client:
        resp = await client.get(f"{HOODCAR}/v1/sold", headers=hc_headers(), params={"q": q})

    if resp.status_code != 200:
        return JSONResponse({"error": "HoodCar API error"}, 502)

    return resp.json().get("data", {})
