---
name: paper-ref-miner
description: >-
  Given ONE paper (a PDF path, a PDF dropped into the inbox folder, or an IEEE
  Xplore link / DOI), pick the few references that matter most for understanding
  it, download and save them alongside, and write a concise "core + questions"
  summary of each (in the configured languages) that always explains HOW the
  reference connects back to the main paper — leaving thinking questions
  unanswered. Use whenever the user uploads/gives a paper and wants its key
  references found, fetched, and summarized, asks "what should I read to understand
  this paper", or when a daily-research-report workflow needs the references mined.
---

# paper-ref-miner

A paper stands on a few load-bearing references; you can't really understand it
without them. This skill finds those, brings them local, and explains *why each
matters to the main paper* — concise, ending in **open questions** (withheld) so
the user keeps thinking.

## Config
Read `config.yaml`: `report.refs_per_paper` (how many to fetch), `summary_languages`
(a summary file per language), `dialogue_language` (the questions' language),
`research.reference_labs` + `research.interests` (for ranking), `sources`,
`paths.project_root`.

## Step 1 — Resolve input to a local main PDF
Accept: a **file path**; a PDF in the **inbox** folder (use the most recent); or an
**IEEE link/DOI** (no local PDF yet → invoke **ieee-pdf-fetch** to download first).
A non-IEEE title/DOI → try a direct download (arXiv/author site); if paywalled and
not IEEE, note it and ask how to proceed.

## Step 2 — Extract the reference list
`python scripts/pdf_to_text.py "<main>.pdf"`; find the `REFERENCES` section, parse
numbered entries (authors/title/venue/year). Also scan the body for which
references are cited at the **load-bearing moments** (where the paper states its
core model/structure/method — often the contributions paragraph and methods).

## Step 3 — Rank & pick `refs_per_paper`
Score by: (a) load-bearing (the core idea/derivation depends on it), (b)
foundational (origin of a method/structure family it extends), (c) authored by a
listed `reference_labs` group, (d) tied to `research.interests`. **Dedup**: skip
references already in `index.md` (note them as "already have"). Pick the ones that
best help *understand the main paper*, and say why each was chosen.

## Step 4 — Fetch
- **IEEE**: find the arnumber (search the exact title via paper-select's
  `cdp_ieee_search.py`, or web search), then download with **ieee-pdf-fetch** into
  `report/<YYMMDD>/refs/` as `<sanitized title>.pdf` (strip `\ / : * ? " < > |`,
  ≤100 chars).
- **Non-IEEE (arXiv/open)**: download directly, same title-based filename.
- **Paywalled non-IEEE**: don't force it — record title + venue + why it matters.
- Validate each: `python scripts/pdf_to_text.py "<title>.pdf"`, page count > 1, sane
  first line (no `APM_DO_NOT_TOUCH`/HTML).

## Step 5 — Summarize each (core + questions)
For each fetched ref write `<title>_summary_<LANG>.md` per `summary_languages`,
next to its PDF. Concise (not a deep review):
```
Bibliography (authors+affil / venue / year / arnumber·DOI)
Core (3–5 bullets): the problem in one line; 2–3 key contributions (a word on why each works)
Connection to the main paper  ← most important: in what context the main paper cites it;
                                 which equation/structure/lineage it underpins. Be specific.
Relevance to my research (1–2 lines, tied to research.interests)
🔎 Questions to ponder (withheld): 2–3, focused on the main↔ref relationship
```
Math in Unicode (no LaTeX/`<sub>`). The questions live in the `dialogue_language`
file.

## Step 6 — Update the ledger
Append each newly downloaded reference to `index.md` (arnumber · year · title ·
venue · location) so future runs don't re-download it.

## Boundaries
Mines references for ONE main paper. It does not write the main paper's deep review
(`paper-deep-review`) or select the day's paper (`paper-select`). Don't answer the
🔎 questions. Report the fetched refs (and any skipped/paywalled) to the caller.
