# Bundesliga Transfer Traits (Cal Berkeley · 1 credit)

Independent-study package for **Conrad**: portable traits and source-league priorities for players transferring **into the 1. Bundesliga**.

## Design (two-tier)

| Tier | Role | Data | N |
|------|------|------|---|
| **1 Wide** | Outcomes for all inbound / first Bundesliga seasons | **FBref** | **≥500** |
| **2 Deep** | Trait portability + leagues to prioritize | **FBref** prior→Y1 (scale); **StatsBomb Open Data** deep dive | Open data ~**94–120**; FBref target **500+** pairs |

**Destination only:** Bundesliga. Transfermarkt is browsable but **not scraped** (ToS ban bots).

## Files

| File | Description |
|------|-------------|
| [`CONRAD_PROPOSAL.docx`](CONRAD_PROPOSAL.docx) | **Word proposal** — edit this in Microsoft Word / Pages / Google Docs |
| `CONRAD_PROPOSAL.md` | Same proposal in Markdown |
| `interactive_player_explorer.html` | Player dropdown by position + pizza chart |
| `methodology_results_brief.html` | Short method / results brief (6 sections) |
| `cohort_data.json` | Open-data Tier-2 stress-test cohort |

Open the HTML files in a browser (double-click or `open *.html`).

## Editing the Word proposal

Edit `CONRAD_PROPOSAL.docx` in **Microsoft Word** (or Pages / Google Docs), then commit and push. If Word says read-only, close other copies, delete any `~$*.docx` lock file in this folder, and reopen.

## Attribution

FBref / Sports Reference (planned Tier 1–2) · StatsBomb Open Data (deep dive / explorer mock).


## Editing the Word proposal

**Edit this file:** `CONRAD_PROPOSAL.txt` (plain text / Markdown — easy in any editor).

When you are done editing, tell Cursor (or run locally): convert `CONRAD_PROPOSAL.txt` → `CONRAD_PROPOSAL.docx` and push to GitHub.

Do not fight with Word login for drafts; the `.txt` is the working copy.

