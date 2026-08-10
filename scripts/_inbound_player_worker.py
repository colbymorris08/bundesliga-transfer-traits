#!/usr/bin/env python3
"""Fetch one FBref player page via seleniumbase UC; print path on success.

Usage: _inbound_player_worker.py PLAYER_URL OUT_HTML
Exit 0 if HTML looks like a real player page; 2 on CF/empty; 1 on error.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: PLAYER_URL OUT_HTML", file=sys.stderr)
        return 2
    url, out = sys.argv[1], Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)

    import seleniumbase as sb

    driver = sb.Driver(uc=True, headless=True)
    try:
        driver.get(url)
        # allow CF / lazy tables
        time.sleep(8)
        html = driver.page_source or ""
        # retry once if challenge page
        if "Just a moment" in html or "cf-browser-verification" in html.lower():
            time.sleep(12)
            driver.get(url)
            time.sleep(8)
            html = driver.page_source or ""
        out.write_text(html, encoding="utf-8")
        ok = len(html) > 20000 and ("stats_" in html or "Standard Stats" in html)
        print(f"bytes={len(html)} ok={int(ok)}", flush=True)
        return 0 if ok else 2
    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
