---
name: daily-research-report
description: >-
  Run the user's full daily paper-study routine end to end and produce a daily
  research report built to grow the user's ability to ask questions rather than
  spoon-feed them. Reads the user's field from config.yaml, then orchestrates:
  check yesterday's understanding + update the learner profile (learner-profile),
  pick today's most important recent paper (paper-select), download it
  (ieee-pdf-fetch), deep-review it (paper-deep-review), mine 3–4 key references
  (paper-ref-miner), assemble a dated report, log to the spreadsheet, update the
  profile. Use when the user says "daily report", "do my paper routine", runs a
  scheduled daily task, or wants the whole select→download→review→reference→report
  pipeline. Optional arg overrides the config field for the day.
---

# daily-research-report (master orchestrator)

This is a **playbook you (the agent) execute**, invoking the other skills in order
with the Skill tool and passing results forward. The goal is the user's **learning
loop** and their fight against AI over-reliance: (1) the report keeps the user
thinking (build questioning ability + challenges, **answers withheld**), and
(2) `research_profile/` is the cross-day memory that adapts each day to what the
user understood the day before.

## Config (read first)
Load `config.yaml` from the project root (`paths.project_root`, default `.`). Use:
`research.interests` / `reference_labs` / `search_keywords`, `report.summary_languages`
(produce a summary file per language), `report.dialogue_language` (the Q&A /
challenge language), `report.refs_per_paper`, `report.selection_priority`,
`report.year_window`, `excel.*`, `browser.*`. Wherever this doc says "the user's
field / labs / language", substitute config values. An optional skill argument
overrides `research` focus for today only.

## Conventions
- **Folders**: `report/<YYMMDD>/{main,refs}/` (date via system date). **PDF filename
  = the paper's sanitized title** (strip `\ / : * ? " < > |`, ≤100 chars).
- **Markdown links to spaced filenames must be wrapped in angle brackets**:
  `[PDF](<main/My Title.pdf>)`. Math in Unicode, never LaTeX/`<sub>`.
- **Excel**: if `excel.enabled`, the log lives at `excel.path`, sheet `excel.sheet`.
  Its `#` column may be a formula — never write `#` yourself; `scripts/xlsx_log.py`
  handles placement, numbering, and main-row shading.

## Pipeline
1. **Understanding check → `learner-profile` (Mode A).** Quiz yesterday's pending
   questions/challenges in `dialogue_language`, grade for understanding, update
   `mastery.md` / `open-questions.md`, and capture a read-back to tune today. Then,
   if Excel is enabled, write yesterday's gaps to the "My lack" column:
   `python scripts/xlsx_log.py set_mylack --xlsx <excel.path> --sheet <excel.sheet>
   --match "<yesterday's title>" --text "<gaps>"`. First run: skip the quiz;
   learner-profile initializes the profile from config.
2. **Select → `paper-select`** (pass today's focus if given). Returns one
   `PICK: <arnumber>` + rationale (honors reference_labs, year_window, reading
   queue, dedup vs `index.md`). Show the pick + runner-up before downloading.
3. **Download → `ieee-pdf-fetch`** to `report/<YYMMDD>/main/<title>.pdf`; validate
   it's a real article (page count, first line), not a bot-wall page.
4. **Deep review → `paper-deep-review`** on the PDF, handing it the Step 1
   read-back. Writes `review_<LANG>.md` for each `summary_languages`, with §8
   challenges, §10 self-check, §11 next-to-read.
5. **References → `paper-ref-miner`** on the same PDF: `refs_per_paper` key refs to
   `report/<YYMMDD>/refs/`, concise "core + questions" summaries, updates `index.md`.
6. **Assemble `report/<YYMMDD>/README.md`** — a hub that **leads with thinking**:
   yesterday's check result; today's main paper (links wrapped in `<>`); **the
   challenges + self-check up top** (answers withheld); the reference table; the
   reading queue; a meta line.
7. **Log to Excel → `scripts/xlsx_log.py append`** (if enabled): one row per paper
   (main + each ref). Per row: `title`, `author` (first author, full name),
   `journal` (short venue e.g. TPEL/APEC), `year`, `summary` (numbered short
   summary in the primary language — the script puts each point on its own line),
   `cons`, `abstract_pdf` (the PDF path → auto-extracts the real abstract) or
   `abstract`, `insights`, `is_main` (true shades the row). Never set `#` or
   `My lack`.
8. **Update profile → `learner-profile` (Mode B).** Log today's paper + concepts to
   `read-log.md`; add new concepts to `mastery.md` (⚪); push today's challenges +
   self-check into `open-questions.md` A (tomorrow's quiz); add §11/ref suggestions
   to B; confirm `index.md`.
9. **Hand off**: present the pick + why, links, and nudge the user to attempt the
   challenges (checked tomorrow). Do **not** answer them.

## Failure handling
- Browser/IEEE access down → stop at Step 2/3, tell the user to run
  `paper-select`'s `scripts/launch_browser.py` and be on the institution network.
  Don't fabricate a paper or review.
- No suitable new paper (all dups / nothing recent) → report and offer to widen
  the year/topic or pull from the reading queue.
- Paywalled non-IEEE reference → ref-miner logs it; note in README, skip its Excel row.

## Automation (`--auto`)
A scheduled run still needs an agent and the dedicated-profile browser reachable
(launch_browser.py reuses it if up). The only step needing a human is the Step 1
live Q&A — under `--auto`, read written answers if present (e.g.
`research_profile/answers.md`), grade those, else skip grading and leave "My lack"
blank. Everything else runs unchanged.

## Boundaries
Orchestrate only; the real work lives in the sub-skills — invoke them so
improvements stay in one place.
