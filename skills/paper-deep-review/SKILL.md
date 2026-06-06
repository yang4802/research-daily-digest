---
name: paper-deep-review
description: >-
  Produce a deep, learning-oriented review of ONE research paper (PDF) for a
  master's/PhD student, written to build the reader's ability to ASK GOOD
  QUESTIONS and reason about mechanisms — not to spoon-feed answers. Use whenever
  the user wants to deeply read, review, analyze, study, or "really understand" a
  specific paper, asks for a detailed write-up, or when a daily-research-report
  workflow needs the main paper analyzed. Writes a detailed review per configured
  language, ending with challenges and a next-to-read list whose answers are
  withheld. This is the heavy reviewer; for a paper's references use paper-ref-miner.
---

# paper-deep-review

## Why this exists (it changes how you write)
The user is **deliberately resisting AI over-reliance**. They don't want a tidy
summary that does their thinking for them — they want a review that keeps them
asking *"why? what's the mechanism? what insight generalizes?"* and that **trains
the habit of asking good questions**.

So the review holds two layers in tension: (1) a genuinely **detailed, correct
technical analysis** (this is a *deep* review), and (2) a **thinking-promotion
layer** that models expert questions, withholds some answers on purpose, and hands
the reader challenges. Explain mechanisms and the *why* thoroughly, but do **not**
pre-chew the judgment calls, the "so what", or the transfer to the reader's own
work — turn those into questions/challenges. **Never answer the challenges or
self-check** — those are the user's, and the next-day quiz material.

## Config & I/O
Read `config.yaml`: `report.summary_languages` (write one review file per language,
e.g. `review_KR.md`, `review_EN.md`), `report.dialogue_language` (the language for
the interactive layer, sections 7–10), and `research.interests` (the user's
domains — use these for the "transfer" prompts instead of any hardcoded field).
If `research_profile/mastery.md` exists, read it: re-explain 🔴/🟡 concepts, go
faster on 🟢, pitch questions just above the user's level.

Input PDF lives at `report/<YYMMDD>/main/<title>.pdf` in the daily workflow. When
you link a local file whose name has spaces, wrap the path in angle brackets —
`[PDF](<…/My Title.pdf>)` — or it won't be clickable.

## Read before writing
1. `python scripts/pdf_to_text.py "<paper>.pdf"` → `<paper>_fulltext.txt`. Confirm
   the first line is a real article, not a challenge page.
2. Read at least: abstract, intro + stated contributions, method/modeling,
   results/experiments (key tables/figures), conclusion; skim references.
3. Find the **one core idea** and the **mechanism** that makes it work. If you
   can't state the mechanism in your own words, read more.

## Review structure (write per language; be detailed in 1–6, withhold 7–10)
```
0. Bibliography   — title / authors(+affil) / venue / year / arnumber·DOI / length / lineage
1. At a glance    — 2–4 sentences: what it solved, why it matters now
2. Problem & why hard  — + a ⟨your turn⟩: "before seeing the solution, what would you try?" (no answer)
3. Key insight    — the one core idea + the intuition for why it works
4. How it works (detailed)  — circuit/structure/math with the *meaning* of each key term;
                    end each subsection with a one-line "🔎 why?" margin question
5. Key results / numbers   — the numbers + what they mean; "🔎 convinced? what would falsify this?"
6. Limits / assumptions / trade-offs   — stated & hidden assumptions, when they break, the cost
7. Question ladder ⟨model⟩  — definitional→mechanism→assumption→limit→generalization, 2–3 sharp
                    questions about THIS paper; for each, one line on why it's sharp (no answers)
8. Your turn + challenges ⟨withheld⟩  — ask the reader to write 2 of their own questions; then
                    1–2 challenges (derive / predict / critique / apply-to-your-interests). No answers.
9. Connections & insight   — where it sits in the field / the user's interests; a "🔎 insight" prompt
10. Self-check (active recall) ⟨withheld⟩  — 3–5 questions the reader should be able to answer next time
11. Next to read  — 3–5 papers/topics with one-line reasons (arnumber/author if known)
```
The interactive layer (7–10) lives in the `dialogue_language` file; the analytical
sections (0–6, 9) are mirrored into every `summary_languages` file in clean prose
the user could lift into their own writing.

## Style (this makes or breaks it)
- Explain the *why*, not just the *what*; for each key equation/structure say what
  each important term does physically.
- Be honest about difficulty and limitations — don't sell the paper.
- **Withhold deliberately**: the ⟨withheld⟩ sections stay open. If you find yourself
  answering a challenge, stop.
- Model great questions: the ladder is the core teaching device — specific to this
  paper, graded from concrete to transferable, tied to the user's interests.
- **No LaTeX, no `<sub>`/`<sup>`** — the viewer renders none. Use Unicode
  subscripts/superscripts (`₀₁₂ ₐ ₑ ₕ ᵢ ₖ ₗ ₘ ₙ ₒ ₚ ᵣ ₛ ₜ`, `² ³`, Greek `β γ Γ Δ μ`).
  Where a subscript letter has no Unicode form (C, uppercase, …), remap to a nearby
  one and gloss once (e.g. `Lₗ = N²/(Rₗ + M·Rₘ)`).

## Boundaries
Reviews ONE paper. Reference handling/downloading/selection belong to
`paper-ref-miner`, `ieee-pdf-fetch`, `paper-select`. Don't fabricate numbers. When
done, report the file paths; the caller folds them into the report and passes the
§8 challenges + §10 self-check to `learner-profile`.
