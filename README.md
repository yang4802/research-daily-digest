# research-daily-digest

A daily research-paper routine that **trains your thinking instead of replacing it.**
Each day it picks the most important recent paper in *your* field from IEEE Xplore,
downloads it, writes a deep learning-oriented review (that withholds answers and
hands you challenges), fetches its key references, logs everything to a
spreadsheet, and quizzes you the next day on what you said you understood —
adapting to your gaps over time.

Works in **Claude Code** (skills) and **OpenAI Codex** (AGENTS.md playbook). You
configure it once by editing **one YAML file** describing your research field.

> Built for users on an **institution network** (e.g. KAIST) where IEEE Xplore
> access is **IP-based** — no personal login needed; just run on the campus/lab
> network.

---

## What you get each day
- `report/<YYMMDD>/main/` — the paper (PDF named by title) + a deep review
  (`review_KR.md` / `review_EN.md`) ending with **challenges** and **self-checks**
  whose answers are deliberately *not* given.
- `report/<YYMMDD>/refs/` — 3–4 key references, each with a concise "core + questions"
  summary explaining how it connects to the main paper.
- `research_profile/` — your living learner model (interests, per-concept mastery,
  reading log, open questions). This is the cross-day memory.
- `Papers_Summary.xlsx` (optional) — one row per paper; main rows shaded; the
  "My lack" column is filled the *next* day from your understanding check.
- `index.md` — a dedup ledger so you never get the same paper twice.

## The daily loop
```
Day N:  quiz yesterday's challenges → update mastery + Excel "My lack"
        → pick today's paper → download → deep-review → mine references
        → assemble report → log to Excel → update profile
Day N+1: repeat   (first day skips the quiz)
```

---

## Prerequisites
- **Python 3.9+**, and **Google Chrome or Microsoft Edge** installed.
- Run on your **institution's network** (IP-based IEEE access). No IEEE login step.
- `pip install -r requirements.txt`

## Setup (once)
```bash
pip install -r requirements.txt
cp config.example.yaml config.yaml      # then EDIT config.yaml for your field
python scripts/seed_profile.py          # creates research_profile/, report/, index.md, the xlsx
```
`config.yaml` is the only thing you personalize — see `config.example.yaml` for a
fully-commented example (filled with a high-frequency-magnetics profile you can
replace).

## Run it — Claude Code
1. Install the skills (copy or symlink) so Claude Code can see them:
   - Windows: copy `skills\*` into `%USERPROFILE%\.claude\skills\`
   - macOS/Linux: copy `skills/*` into `~/.claude/skills/`
   (Also copy `skills/ieee-pdf-fetch` — the downloader.)
2. In your project folder (where `config.yaml` lives), say **`/daily-research-report`**
   (or "do my daily paper routine"). The agent runs the whole loop and pauses for
   the understanding-check Q&A.
3. To automate: use Claude Code's scheduling (the `schedule` skill) to run
   `/daily-research-report --auto` each morning. `--auto` reads written answers
   instead of a live quiz.

## Run it — OpenAI Codex
1. Open this repo as your Codex workspace. Codex reads **`AGENTS.md`**, which is the
   same pipeline written as a step-by-step playbook over `scripts/`.
2. Tell Codex: **"run the daily research digest"** (or schedule it). It will launch
   the browser, select, download, review, mine references, log, and update the
   profile by following `AGENTS.md`.

## How IEEE access works (no login)
`scripts/launch_browser.py` starts a **dedicated-profile** Chrome/Edge with remote
debugging (Chrome 136+ blocks debugging on the default profile, so a separate
profile is used; it does **not** disturb your normal browser). On an institution
network the entitlement is granted by IP, so downloads work without signing in.
`scripts/cdp_check_access.py` confirms access before downloading.

## Layout produced in your project
```
<project_root>/
├─ config.yaml
├─ index.md
├─ Papers_Summary.xlsx
├─ research_profile/  (profile.md · mastery.md · read-log.md · open-questions.md)
├─ inbox/             (drop a PDF here to mine just its references)
└─ report/<YYMMDD>/{main,refs}/
```

## Customize
Everything personal lives in `config.yaml`: field, interests, reference labs,
search keywords, summary languages, refs-per-paper, selection priority, year
window, sources, Excel sheet name, browser port/profile. The skills and AGENTS.md
read these — you should not need to edit them.
