---
name: paper-select
description: >-
  Pick the single most important RECENT paper to read today from IEEE Xplore,
  tuned to the user's research field and reference labs as declared in config.yaml.
  Drives an authenticated, dedicated-profile Chrome/Edge (remote debugging,
  institution-IP access) to search Xplore newest-first, filters by topic + year
  window, skips anything already in index.md, and returns one paper's arnumber with
  a short rationale. Use when the user asks "find me a good recent paper on X",
  "what's the latest from <lab>", or when a daily-research-report workflow needs
  today's main paper chosen. Outputs a pick, not a download.
---

# paper-select

Chooses today's paper and returns one arnumber + why. It does not download or
summarize — that's `ieee-pdf-fetch` and `paper-deep-review`.

## Config
Read `config.yaml`: `research.reference_labs`, `research.search_keywords`,
`research.interests`, `report.selection_priority` (reference_labs_first |
recency_first | mixed), `report.year_window` (prefer / min), `browser.*`,
`paths.project_root`, `sources`.

## Step 0 — Ensure the authenticated browser
IEEE search + download need the dedicated-profile browser with remote debugging
(Chrome 136+ blocks debugging on the default profile, so a dedicated
`--user-data-dir` is used; it runs as its own instance and doesn't disturb the
user's normal browser). On an institution network the entitlement is IP-based — no
login.
1. `python scripts/launch_browser.py` → prints `ALREADY_UP …` or launches and
   prints the `/json/version` JSON. (Reads port/profile from config.yaml.)
2. `python scripts/cdp_check_access.py` → expect `ACCESS_OK: True` and your
   institution under `instName`. If False, tell the user to get on the institution
   network/VPN — selection can proceed but downloads may fail.

## Step 1 — Inputs
- **Field**: from the skill argument if given, else `research` in config.
- **Reading queue**: `research_profile/open-questions.md` section B. If the user
  queued something specific (often yesterday's "next to read"), prefer it today —
  this closes the loop.
- **Dedup**: read `index.md`. Never pick anything already there.

## Step 2 — Search Xplore (newest first)
`python scripts/cdp_ieee_search.py "QUERY" 30` (set `PYTHONIOENCODING=utf-8`).
The query is **plain text** (not field-command syntax — `("Authors":"…")` returns
0); put author surnames + topic words in the query and filter the returned author
lists yourself. Run a few queries built from `reference_labs` + `search_keywords`
(and any reading-queue item).

## Step 3 — Filter & rank
- **Year window**: prefer `year_window.prefer`, then descend; reject earlier than
  `year_window.min` unless the user asks for a classic.
- **selection_priority**:
  - `reference_labs_first` (default): among recent on-topic hits, a paper by a
    listed reference lab/author beats a newer non-reference-lab one.
  - `recency_first`: newest on-topic wins regardless of lab.
  - `mixed`: score by lab-match + recency + core fit together.
- **Core fit**: matches `research.interests`.
- **Venue weight**: a journal generally beats a short conference paper when both fit.
- **Downloadable**: must be on IEEE Xplore. **Not a dup** (exclude `index.md`).
- Tie-break toward what advances the reading queue or a 🟡/🔴 concept in `mastery.md`.

## Step 4 — Return the pick
```
PICK: <arnumber>
Title / Authors / Venue / Year / DOI
Why this one: <2–4 lines>
Runner-up (optional): <arnumber + one line>
```
The orchestrator then calls `ieee-pdf-fetch <arnumber>`.

## Boundaries
Selection only — no downloading, summarizing, or profile editing. If access can't
be established, say so rather than guessing a paper you can't verify is
downloadable. Honor `selection_priority` — don't silently optimize for "newest".
