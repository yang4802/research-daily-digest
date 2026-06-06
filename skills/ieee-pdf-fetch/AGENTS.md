# IEEE Xplore PDF fetcher — Codex / generic-agent instructions

This folder is a portable skill. Claude Code reads `SKILL.md`; OpenAI **Codex**
(and any agent that reads `AGENTS.md`) should use the instructions here. The
underlying logic is identical — a standalone Python script does the work.

## When to use

Use this whenever the task involves getting the full-text PDF of an **IEEE
Xplore** paper (`ieeexplore.ieee.org/document/<number>`), for open-access *or*
institution-licensed/paywalled articles — e.g. "download this IEEE paper",
"save the PDF and summarize it", or a link/DOI that resolves to IEEE Xplore.

Do **not** use it for arXiv, eScholarship, Springer, author sites, etc. — those
download directly with `curl`/`requests`. And do not try `curl`/`requests` on
IEEE itself: it returns an Akamai bot-challenge page, not a PDF (see
`references/method.md`).

## One-time setup

```bash
pip install playwright pypdf
playwright install chromium
# Sign in to IEEE via your institution once; the login persists in a profile dir:
python scripts/ieee_download.py 10329461 --login
```

## Usage

```bash
# Article number, /document/<n> path, or full URL all work:
python scripts/ieee_download.py 10329461 -o ./mini-lego.pdf
python scripts/ieee_download.py https://ieeexplore.ieee.org/document/10909706

# Alternative: attach to a browser you already run logged-in
#   (start it once:  msedge --remote-debugging-port=9222  — or use chrome)
python scripts/ieee_download.py 10909706 --cdp http://localhost:9222
```

Exit/printout tells you the saved path, page count, and the first line of the
PDF. A real article begins with `IEEE TRANSACTIONS ON ... VOL. xx`. If you see a
tiny file or HTML, the browser session wasn't authenticated — re-run with
`--login` (or re-attach a logged-in browser via `--cdp`).

## Notes for the agent

- The script is **headful** (a visible browser) on purpose: it needs a real
  session for the login and to pass bot detection. In a headless CI box, use
  `--cdp` to attach to a separately-managed logged-in browser.
- Only download what the user is entitled to; respect IEEE Terms of Use; don't
  loop it to bulk-download.
- After downloading, read/summarize the PDF with `pypdf` (already a dependency):
  ```bash
  python -c "from pypdf import PdfReader; r=PdfReader('FILE.pdf'); print(len(r.pages),'pages'); print((r.pages[0].extract_text() or '')[:300])"
  ```
- Full rationale and troubleshooting: `references/method.md`.
