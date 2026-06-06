# AGENTS.md — research-daily-digest (Codex / generic-agent playbook)

You are running the user's **daily research-paper routine**. Goal: pick the most
important recent paper in *their* field, download it, write a deep learning-oriented
review **that withholds answers and hands the reader challenges**, fetch its key
references, log to a spreadsheet, and quiz the user the next day on what they
understood — adapting over time. This trains the user's thinking; it must **not
spoon-feed**.

Codex has no "skill tool"; *you* run the steps below over `scripts/`. The detailed
spec for each step is in `skills/<name>/SKILL.md` — read the relevant one when you
need depth. (The same files double as Claude Code skills.)

## Config (read first)
Load `config.yaml` at the repo/project root. Everything personal is there:
`research.{field,interests,reference_labs,search_keywords}`,
`report.{summary_languages,dialogue_language,refs_per_paper,selection_priority,year_window,pedagogy}`,
`sources`, `excel.{enabled,path,sheet}`, `paths.project_root`, `browser.*`. Use these
values wherever a step says "the user's field / labs / language".

## One-time setup
```
pip install -r requirements.txt
cp config.example.yaml config.yaml      # user edits this for their field
python scripts/seed_profile.py          # creates research_profile/, report/, index.md, the xlsx
```

## Conventions
- Work under `paths.project_root`. Daily outputs: `report/<YYMMDD>/{main,refs}/`
  (`<YYMMDD>` = today's date).
- **PDF filename = the paper's sanitized title** (strip `\ / : * ? " < > |`, ≤100
  chars). Ref summaries: `<title>_summary_<LANG>.md`. Main review: `review_<LANG>.md`.
- In any markdown link to a file whose name has spaces, wrap the path in angle
  brackets: `[PDF](<main/My Title.pdf>)`.
- **Math in Unicode, never LaTeX or `<sub>`** (the user's viewer renders neither).
  Remap subscript letters with no Unicode form and gloss once: `Lₗ = N²/(Rₗ + M·Rₘ)`.
- IEEE access is **institution-IP based** — run on the institution network; no login.

## Daily routine (run in order)

### 1. Authenticated browser
```
python scripts/launch_browser.py        # reuses :port if already up; dedicated profile
python scripts/cdp_check_access.py       # expect ACCESS_OK: True + your institution
```
If access is False, stop and tell the user to get on the institution network.

### 2. Understanding check + profile  (spec: skills/learner-profile/SKILL.md)
Read `research_profile/open-questions.md` section A. If non-empty, run a short
interactive Q&A (2–4 questions, in `dialogue_language`) on yesterday's challenges;
grade for understanding; update `research_profile/mastery.md` and `open-questions.md`.
If `excel.enabled`, write the confirmed gaps to the prior paper's "My lack":
```
python scripts/xlsx_log.py set_mylack --xlsx <excel.path> --sheet <excel.sheet> \
  --match "<yesterday's title>" --text "<gaps found>"
```
First run (no profile / empty section A): skip the quiz.

### 3. Select today's paper  (spec: skills/paper-select/SKILL.md)
Build queries from `reference_labs` + `search_keywords` (+ reading queue in
`open-questions.md` B). For each: `python scripts/cdp_ieee_search.py "QUERY" 30`
(set `PYTHONIOENCODING=utf-8`; query is plain text). Filter by `year_window`,
`selection_priority`, core fit, **not in `index.md`**, IEEE-downloadable. Pick one
arnumber; show the user the pick + rationale before downloading.

### 4. Download  (spec: skills/ieee-pdf-fetch/AGENTS.md)
```
python scripts/ieee_download.py <arnumber> --cdp http://localhost:<port> \
  -o "report/<YYMMDD>/main/<title>.pdf"
```
Validate it's a real article (page count, first line), not a bot-wall page.

### 5. Deep review  (spec: skills/paper-deep-review/SKILL.md)
`python scripts/pdf_to_text.py "report/<YYMMDD>/main/<title>.pdf"`, read it, then
write `review_<LANG>.md` for each `summary_languages` using the 11-section structure
(detailed in 1–6; **withhold answers** in the §8 challenges and §10 self-check;
transfer prompts use `research.interests`). Tie difficulty to `mastery.md`.

### 6. Mine references  (spec: skills/paper-ref-miner/SKILL.md)
Pick `refs_per_paper` load-bearing refs, download to `report/<YYMMDD>/refs/` as
`<title>.pdf`, write `<title>_summary_<LANG>.md` (core + withheld questions, with the
main↔ref connection). Update `index.md`.

### 7. Assemble `report/<YYMMDD>/README.md`
A hub that **leads with thinking**: yesterday's check result; today's main paper
(links wrapped in `<>`); **challenges + self-check up top** (answers withheld);
reference table; reading queue; meta line.

### 8. Log to the spreadsheet  (if `excel.enabled`)
Build a JSON list (main + each ref) and:
```
python scripts/xlsx_log.py append --xlsx <excel.path> --sheet <excel.sheet> --json today_rows.json
```
Each row: `title`, `author` (first author full name), `journal` (short venue),
`year`, `summary` (numbered short summary in the primary language), `cons`,
`abstract_pdf` (the PDF path → auto-extracts the abstract), `insights`, `is_main`
(true shades the row). Never set `#` (a formula) or `My lack` (filled next day).

### 9. Update profile + hand off
Append today's paper + concepts to `read-log.md`; add new concepts to `mastery.md`
(⚪); push today's challenges/self-check into `open-questions.md` A; add suggestions
to B. Then present the pick, links, and nudge the user to attempt the challenges —
**do not answer them**.

## Scheduling (unattended)
Run this routine daily (cron / Task Scheduler invoking your Codex agent). The
dedicated-profile browser must be reachable (launch_browser.py reuses it). The only
step needing a human is the step-2 live Q&A — unattended, read written answers from
`research_profile/answers.md` if present, else skip grading and leave "My lack" blank.
