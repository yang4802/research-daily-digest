# ieee-pdf-fetch

A small, portable **skill** that downloads the full-text PDF of an IEEE Xplore
paper — open-access *or* institution-paywalled — by driving an **authenticated
browser**. Plain `curl`/`requests` can't do this (IEEE's Akamai bot wall returns
a challenge page, not a PDF); a logged-in browser session can.

Works from **Claude Code** (`SKILL.md`) and **OpenAI Codex** / any agent
(`AGENTS.md`), backed by one standalone Python script.

```
ieee-pdf-fetch/
├── SKILL.md                 # Claude Code skill (auto-discovered)
├── AGENTS.md                # Codex / generic-agent instructions
├── README.md                # this file (humans)
├── scripts/
│   └── ieee_download.py     # portable Playwright downloader
└── references/
    └── method.md            # why it works, what fails, troubleshooting
```

## Quick start

```bash
pip install playwright pypdf
playwright install chromium

# First time: sign in to IEEE via your institution (login persists in a profile)
python scripts/ieee_download.py 10329461 --login

# Then download by article number, /document/<n>, or full URL
python scripts/ieee_download.py 10329461 -o mini-lego.pdf
python scripts/ieee_download.py https://ieeexplore.ieee.org/document/10909706
```

Prefer to reuse the browser you already have logged in? Start it once with a
debug port and attach to it (uses your exact session):

```bash
# Windows (Edge):
#   & "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222
python scripts/ieee_download.py 10909706 --cdp http://localhost:9222
```

## Install as a Claude Code skill

Copy the folder into your skills directory; Claude Code discovers it
automatically:

```bash
# personal (all projects):
cp -r ieee-pdf-fetch ~/.claude/skills/
# or project-local (shareable via the repo):
cp -r ieee-pdf-fetch <your-project>/.claude/skills/
```

Then just ask, e.g. *"download IEEE paper 10329461 and summarize it"* — the
skill triggers on IEEE Xplore download/fetch/summarize requests.

## Use with OpenAI Codex

Drop the folder into the repo (or `~/.codex/`), and Codex will read `AGENTS.md`.
Or point Codex at it explicitly: *"follow ieee-pdf-fetch/AGENTS.md to download
this IEEE paper."* The script is plain Python + Playwright — no Claude-specific
APIs — so it runs anywhere.

## Requirements

- Python 3.8+
- `playwright` (+ `playwright install chromium`, or use `--channel msedge|chrome`
  to drive an installed browser)
- `pypdf` (optional, for auto-validation and text extraction)
- A real IEEE login: institutional SSO or on-network/VPN IP access.

## Scope & ethics

Download only what you're entitled to (open access, or content your institution
licenses). Respect IEEE's Terms of Use. This is a **single-article** helper — not
a bulk harvester. For arXiv/eScholarship/author copies, just download directly;
you don't need this.

See `references/method.md` for the full how/why and troubleshooting.
