#!/usr/bin/env python3
"""Generate Excel workbook with all data, analysis results, and source tracking."""
import json
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

OUT = Path(__file__).resolve().parent


def main():
    data = json.loads((OUT / "analysis_data.json").read_text())
    pitchers = data["pitchers"]
    stability = data["stability"]
    redundancy = data["redundancy"]
    significance = data["significance"]
    meta = data["meta"]

    wb = Workbook()
    hdr_font = Font(bold=True, color="FFFFFF", size=11)
    hdr_fill = PatternFill(start_color="3D5A80", end_color="3D5A80", fill_type="solid")
    npb_fill = PatternFill(start_color="FFCDD2", end_color="FFCDD2", fill_type="solid")
    kbo_fill = PatternFill(start_color="BBDEFB", end_color="BBDEFB", fill_type="solid")
    cpbl_fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
    stable_fill = PatternFill(start_color="D8F3E4", end_color="D8F3E4", fill_type="solid")
    sig_fill = PatternFill(start_color="D8F3E4", end_color="D8F3E4", fill_type="solid")
    thin_border = Border(
        bottom=Side(style="thin", color="D0D4DB"),
    )
    league_fills = {"NPB": npb_fill, "KBO": kbo_fill, "CPBL": cpbl_fill}

    def style_header(ws, ncols):
        for col in range(1, ncols + 1):
            cell = ws.cell(row=1, column=col)
            cell.font = hdr_font
            cell.fill = hdr_fill
            cell.alignment = Alignment(horizontal="center", wrap_text=True)

    def auto_width(ws):
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                try:
                    val = str(cell.value) if cell.value else ""
                    max_len = max(max_len, len(val))
                except Exception:
                    pass
            ws.column_dimensions[col_letter].width = min(max_len + 3, 25)

    # ── Sheet 1: Complete Pitcher Data ──
    ws = wb.active
    ws.title = "Pitcher Data"

    cols = [
        ("Name", "name"), ("League", "league"), ("Origin", "origin"), ("Pos", "pos"), ("Trans. Year", "transition_year"),
        ("A-ERA", "a_era"), ("A-IP", "a_ip"), ("A-K/9", "a_k9"), ("A-BB/9", "a_bb9"),
        ("A-HR/9", "a_hr9"), ("A-WHIP", "a_whip"), ("A-K/BB", "a_k_bb"), ("A-W%", "a_w_pct"),
        ("A-GB%", "a_gb_pct"),
        ("M-ERA", "m_era"), ("M-IP", "m_ip"), ("M-K/9", "m_k9"), ("M-BB/9", "m_bb9"),
        ("M-HR/9", "m_hr9"), ("M-WHIP", "m_whip"), ("M-K/BB", "m_k_bb"), ("M-W%", "m_w_pct"),
        ("M-GB%", "m_gb_pct"),
        ("ERA+", "m_era_plus"), ("WAR", "m_war"), ("M-Seasons", "m_seasons_bwar"),
        ("M-W", "m_w"), ("M-L", "m_l"), ("M-G", "m_g"), ("M-GS", "m_gs"),
        ("M-SO", "m_so"), ("M-BB", "m_bb"), ("M-SV", "m_sv"),
    ]
    for c, (label, _) in enumerate(cols, 1):
        ws.cell(row=1, column=c, value=label)
    style_header(ws, len(cols))

    for r, p in enumerate(pitchers, 2):
        for c, (_, key) in enumerate(cols, 1):
            val = p.get(key)
            if val is not None and isinstance(val, float) and val != val:
                val = None
            ws.cell(row=r, column=c, value=val)
        league = p.get("league", "")
        if league in league_fills:
            ws.cell(row=r, column=2).fill = league_fills[league]
        for c in range(1, len(cols) + 1):
            ws.cell(row=r, column=c).border = thin_border
    auto_width(ws)

    # ── Sheet 2: Stability ──
    ws2 = wb.create_sheet("Stability")
    stab_cols = ["League", "Metric", "r (Pearson)", "p-value", "N", "Stable (|r|>=0.40, p<0.10)"]
    for c, label in enumerate(stab_cols, 1):
        ws2.cell(row=1, column=c, value=label)
    style_header(ws2, len(stab_cols))

    ml = meta["metric_labels"]
    row = 2
    for league in ["ALL", "NPB", "KBO", "CPBL"]:
        stab = stability.get(league, {})
        for m, v in stab.items():
            ws2.cell(row=row, column=1, value=league)
            ws2.cell(row=row, column=2, value=ml.get(m, m))
            ws2.cell(row=row, column=3, value=v["r"])
            ws2.cell(row=row, column=4, value=v["p"])
            ws2.cell(row=row, column=5, value=v["n"])
            ws2.cell(row=row, column=6, value="YES" if v["stable"] else "no")
            if v["stable"]:
                ws2.cell(row=row, column=6).fill = stable_fill
            if league in league_fills:
                ws2.cell(row=row, column=1).fill = league_fills[league]
            for c in range(1, len(stab_cols) + 1):
                ws2.cell(row=row, column=c).border = thin_border
            row += 1
    auto_width(ws2)

    # ── Sheet 3: Significance ──
    ws3 = wb.create_sheet("Significance")
    sig_cols = ["League", "Outcome", "Asian Metric", "r (Pearson)", "p-value", "N", "Significant (p<0.10)"]
    for c, label in enumerate(sig_cols, 1):
        ws3.cell(row=1, column=c, value=label)
    style_header(ws3, len(sig_cols))

    row = 2
    for league in ["ALL", "NPB", "KBO", "CPBL"]:
        sig_data = significance.get(league, {})
        for out_key, out_data in sig_data.items():
            for d in out_data["drivers"]:
                ws3.cell(row=row, column=1, value=league)
                ws3.cell(row=row, column=2, value=out_data["label"])
                ws3.cell(row=row, column=3, value=d["label"])
                ws3.cell(row=row, column=4, value=d["r"])
                ws3.cell(row=row, column=5, value=d["p"])
                ws3.cell(row=row, column=6, value=d["n"])
                ws3.cell(row=row, column=7, value="YES" if d["significant"] else "no")
                if d["significant"]:
                    ws3.cell(row=row, column=7).fill = sig_fill
                if league in league_fills:
                    ws3.cell(row=row, column=1).fill = league_fills[league]
                for c in range(1, len(sig_cols) + 1):
                    ws3.cell(row=row, column=c).border = thin_border
                row += 1
    auto_width(ws3)

    # ── Sheet 4: Redundancy ──
    ws4 = wb.create_sheet("Redundancy")
    ws4.cell(row=1, column=1, value="REDUNDANT PAIRS (|r| >= 0.75)")
    ws4.cell(row=1, column=1).font = Font(bold=True, size=12)
    ws4.cell(row=2, column=1, value="Metric A")
    ws4.cell(row=2, column=2, value="Metric B")
    ws4.cell(row=2, column=3, value="r (Pearson)")
    style_header(ws4, 3)
    ws4.cell(row=1, column=1).font = Font(bold=True, size=12)

    for r, pair in enumerate(redundancy["pairs"], 3):
        a_base = pair["a"].replace("a_", "Asian ").replace("m_", "MLB ")
        b_base = pair["b"].replace("a_", "Asian ").replace("m_", "MLB ")
        ws4.cell(row=r, column=1, value=a_base)
        ws4.cell(row=r, column=2, value=b_base)
        ws4.cell(row=r, column=3, value=pair["r"])

    row = len(redundancy["pairs"]) + 5
    ws4.cell(row=row, column=1, value="CLUSTERS (distance threshold 0.40)")
    ws4.cell(row=row, column=1).font = Font(bold=True, size=12)
    for cl in redundancy["clusters"]:
        row += 1
        labels = [m.replace("a_", "Asian ").replace("m_", "MLB ") for m in cl["metrics"]]
        ws4.cell(row=row, column=1, value=f"Cluster {cl['id']}")
        ws4.cell(row=row, column=1).font = Font(bold=True)
        ws4.cell(row=row, column=2, value=" | ".join(labels))
    auto_width(ws4)

    # ── Sheet 5: Data Sources ──
    ws5 = wb.create_sheet("Sources")
    ws5.cell(row=1, column=1, value="Data Source")
    ws5.cell(row=1, column=2, value="Description")
    ws5.cell(row=1, column=3, value="Coverage")
    style_header(ws5, 3)

    sources = [
        ("MLB Stats API", "statsapi.mlb.com — career pitching stats (IP, ERA, K, BB, HR, GO/AO, saves)", f"{meta['n_pitchers'] - 1} pitchers"),
        ("Baseball-Reference Register", "standard_pitching tfoot summary rows — Asian league career stats", f"{meta['n_pitchers'] - 2} pitchers"),
        ("bWAR dataset (pybaseball)", "bwar_pitch() — career WAR and ERA+ for MLB seasons", f"{meta['n_pitchers'] - 1} pitchers"),
        ("Hand-compiled fallback", "Research-verified stats for pitchers without API coverage", "Fills remaining gaps"),
        ("Cho (2026)", "Cross-League Equivalencies: xFIP− translation factor = 1.096", "NPB → MLB"),
    ]
    for r, (src, desc, cov) in enumerate(sources, 2):
        ws5.cell(row=r, column=1, value=src)
        ws5.cell(row=r, column=2, value=desc)
        ws5.cell(row=r, column=3, value=cov)
        for c in range(1, 4):
            ws5.cell(row=r, column=c).border = thin_border

    row = len(sources) + 3
    ws5.cell(row=row, column=1, value="METHODOLOGY")
    ws5.cell(row=row, column=1).font = Font(bold=True, size=12)
    methods = [
        "Stability: Pearson r between Asian-league career stat and MLB career stat (same metric)",
        "Threshold: |r| >= 0.40 and p < 0.10 to qualify as 'stable'",
        "p < 0.10 means < 10% probability the correlation arose by chance (null = no relationship)",
        "Redundancy: Pairwise Pearson correlation matrix; pairs at |r| >= 0.75; agglomerative clustering at distance 0.40",
        "Significance: Pearson r between Asian-league metric and MLB outcome (ERA+, WAR, seasons); p < 0.10",
        f"Total pitchers: {meta['n_pitchers']} (NPB={meta['n_npb']}, KBO={meta['n_kbo']}, CPBL={meta['n_cpbl']})",
        f"Asian-born: {meta.get('n_asian_born', 'N/A')}, American crossover: {meta.get('n_crossover', 'N/A')}",
        f"Pitchers with both Asian + MLB data: {meta['n_with_both']}",
    ]
    for i, m in enumerate(methods):
        ws5.cell(row=row + 1 + i, column=1, value=m)
    auto_width(ws5)

    outpath = OUT.parent / "asian_pitcher_mlb_analysis.xlsx"
    wb.save(outpath)
    print(f"Wrote {outpath} ({outpath.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
