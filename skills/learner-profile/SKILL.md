---
name: learner-profile
description: >-
  Maintain a living "learner profile" of the user — research interests, per-concept
  mastery, what they've read, and open questions / reading queue — as markdown
  under research_profile/ in the project. Use at the START of a daily run to quiz
  the user (interactive Q&A) on yesterday's open questions/challenges and update
  mastery, and at the END to record new concepts and open questions. Also trigger
  when the user asks to "check my understanding", "update my profile", "what should
  I study next", or review learning progress. The profile is the cross-day memory
  that lets reports push the user's thinking instead of spoon-feeding.
---

# learner-profile

## Why this exists
The user is fighting **AI over-reliance** — they want to keep the ability to ask
questions, reason about mechanisms, and extract insight. This skill keeps a living
model of the learner so daily reports adapt to their actual understanding: revisit
what's shaky, stop re-explaining what's solid, and honestly record which questions
they've truly answered vs. dodged. Be a demanding-but-fair tutor; probe for the
*why*, and be honest in the profile (marking something "solid" that was half-grasped
makes future reports worse).

## Config & location
Read `config.yaml`: `report.dialogue_language` (the Q&A language), `excel.*`
(for the "My lack" update), `paths.project_root`. The profile lives in
`research_profile/` (under the project root): `profile.md`, `mastery.md`,
`read-log.md`, `open-questions.md`. Create any that are missing. If the folder
doesn't exist, this is the **first run**: seed `profile.md` from config (and any
saved memory), then skip the quiz and tell the user the profile was initialized.

## Mode A — Understanding check (start of a daily run / "check my understanding")
1. Read `open-questions.md` section A and the latest `read-log.md` entries
   (yesterday's challenges / unresolved questions).
2. If section A is empty, say so and skip — don't invent a quiz.
3. Run a short interactive Q&A (2–4 questions, not an exam) in `dialogue_language`.
   Ask one or two at a time, wait, then follow up. Grade for *understanding*, not
   wording; if vague, ask a gentle follow-up ("why does that hold?", "one level
   deeper?") before judging. "I don't know" is valuable signal — capture it as a gap.
4. Update: `mastery.md` (🟢 demonstrated, 🟡 half, 🔴 unanswered; date + one-line
   evidence); `open-questions.md` (resolve answered items, sharpen the rest).
5. Give a brief, honest read-back ("solid: … / needs work: …") — the report uses it
   to tune difficulty.
6. If Excel is enabled, the daily workflow writes these confirmed gaps into the
   matching paper's **"My lack"** column (the "next-day update"):
   `python <daily-research-report>/scripts/xlsx_log.py set_mylack --xlsx <excel.path>
   --sheet <excel.sheet> --match "<paper title>" --text "<gaps>"`. The `#` column
   there is a formula — never write it.

## Mode B — Profile update (end of a daily run / "log this")
1. Append to `read-log.md`: date, paper (title + arnumber + role), key concepts.
2. Update `mastery.md`: add newly-introduced concepts at ⚪ (untested) — don't
   inflate to 🟢.
3. Append to `open-questions.md`: section A ← the challenges/self-check the report
   posed today (tomorrow's quiz); section B ← "next to read" suggestions (deduped).
4. Confirm what was logged in a line or two.

## The questions you ask (model the habit)
Favor a ladder over trivia: **definitional** (what exactly does this mean?) →
**mechanism** (why does it work — physical/circuit cause?) → **assumption** (what
must hold; when does it break?) → **limit/trade-off** (what's the cost?) →
**generalization** (how does this transfer to the user's `research.interests`?).
Prefer questions whose answers reveal understanding, not recall of a number.
Math in Unicode (no LaTeX/`<sub>`); remap subscript letters with no Unicode form
and gloss once (`Lₗ = N²/(Rₗ + M·Rₘ)`).

## File templates (use when creating missing files)
- `profile.md`: Who / Field / Interests (priority) / Reference labs / Notes.
- `mastery.md`: `| Concept | Level (🟢🟡🔴⚪) | Last touched | Evidence |`.
- `read-log.md`: `| Date | Paper (title · arnumber · role) | Key concepts |`.
- `open-questions.md`: `## A. Pending (to check)` and `## B. Reading queue`.

## Boundaries
Reads/writes the profile and runs the Q&A. It does not select, download, or
summarize papers — hand back to the caller when done. Never fabricate that the user
answered something; an empty/"don't know" answer is recorded as a gap.
