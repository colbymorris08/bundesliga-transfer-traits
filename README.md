# Bundesliga Transfer Traits (Cal Berkeley)

Which traits travel into the **Bundesliga**, and which source leagues to prioritize?

## Pipeline

**Stability** (all prior→Bundesliga stats) → **redundancy** → **pizza charts** from the kept set.

| Tier | Role | Data | N |
|------|------|------|---|
| **1 Wide** | Outcomes for inbound / first Bundesliga seasons | FBref | ≥500 |
| **2 Deep** | Portability + pizzas | FBref pairs; StatsBomb deep dive | FBref →500+ pairs; open data ~94–120 |

Inbound players from **FBref season records** (not Transfermarkt scrape).

## Files

| File | Description |
|------|-------------|
| [`projectproposal.docx`](projectproposal.docx) | Proposal (Word) |
| [`projectproposal.txt`](projectproposal.txt) | **Editable source** — edit this, then regenerate `projectproposal.docx` |
| [`bundesliga_transfer_traits.pptx`](bundesliga_transfer_traits.pptx) | PPT template (NYRB deck structure, new fonts/wording) |
| [`mock_pizza_bundesliga.png`](mock_pizza_bundesliga.png) | Mock pizza chart image |
| [`interactive_player_explorer.html`](interactive_player_explorer.html) | Player dropdown by position + pizza |
| [`methodology_results_brief.html`](methodology_results_brief.html) | Short method / results brief |
| [`cohort_data.json`](cohort_data.json) | Open-data stress-test cohort |

## Edit → Word → GitHub

1. Edit `projectproposal.txt` and save  
2. Ask to push (or: `pandoc projectproposal.txt -o projectproposal.docx` then `git add` / commit / push)

Attribution: FBref / Sports Reference · StatsBomb Open Data (deep dive).
