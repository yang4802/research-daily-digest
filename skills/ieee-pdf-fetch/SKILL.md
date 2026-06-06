---
name: ieee-pdf-fetch
description: >-
  Download the full-text PDF of an IEEE Xplore paper (ieeexplore.ieee.org), for
  both open-access and institution-licensed/paywalled articles, by driving an
  authenticated browser. Use this whenever the user asks to download, fetch,
  save, open, read, or summarize an IEEE / IEEE Xplore paper, gives an
  ieeexplore.ieee.org/document/<number> link or an IEEE article/DOI, or wants a
  local copy of an IEEE PDF to extract or summarize — even if they don't say the
  word "skill". Plain curl/requests downloads of IEEE DO NOT work (Akamai bot
  wall); this skill is the reliable path. Not for arXiv, eScholarship, Springer,
  or other publishers — those download directly without a browser.
---

# IEEE Xplore PDF fetcher

## What this solves

IEEE Xplore is behind Akamai bot management, so a scripted HTTP download
(`curl`, `requests`, `Invoke-WebRequest`, `WebFetch`) returns a JavaScript
challenge page (`<APM_DO_NOT_TOUCH>...`), **not a PDF**. The only reliable route
is an **authenticated, real browser session**: it passes the bot check and
carries the institutional entitlement that unlocks paywalled papers. Open-access
papers work the same way. See `references/method.md` for the full diagnosis.

## Two ways to run it — pick based on what you have

### A) You control an authenticated browser via an MCP (e.g. Claude-in-Chrome)

Best when the user already has IEEE/their institution logged into a connected
browser. Run the fetch **inside the page** so it inherits cookies and passes the
bot wall. Do NOT click the IEEE "PDF" button or the PDF-viewer download icon —
that opens a native OS "Save As" dialog you cannot operate.

Steps:
1. Connect to / select the browser, open a tab, navigate to
   `https://ieeexplore.ieee.org/document/<arnumber>`.
2. Run this in the page (via the MCP's JS/eval tool). It saves to the browser's
   download folder with no dialog:

```js
(() => {
  let p = null;
  try { p = window.xplGlobal.document.metadata.pdfPath; } catch (e) {}
  if (!p) { window.__dlErr = 'no-metadata'; return { ok: false }; }
  window.__dlDone = null; window.__dlErr = null;
  (async () => {
    try {
      let viewer = p.startsWith('http') ? p : location.origin + (p[0]==='/'?'':'/') + p;
      const html = await fetch(viewer, { credentials: 'include' }).then(r => r.text());
      // Paywalled PDFs come from a getPDF.jsp endpoint (no .pdf extension) — match ANY iframe src.
      let m = html.match(/<iframe[^>]+src="([^"]+)"/i) || html.match(/<frame[^>]+src="([^"]+)"/i);
      if (!m) { window.__dlErr = 'no-iframe-src'; return; }
      let pdfUrl = m[1].replace(/&amp;/g, '&');
      if (!pdfUrl.startsWith('http')) pdfUrl = location.origin + (pdfUrl[0]==='/'?'':'/') + pdfUrl;
      const b = await fetch(pdfUrl, { credentials: 'include' }).then(r => r.blob());
      if (b.type.indexOf('pdf') === -1 && b.size < 100000) { window.__dlErr = 'not-a-pdf'; return; }
      const o = URL.createObjectURL(b);
      const a = document.createElement('a');
      a.href = o; a.download = '<arnumber>.pdf';
      document.body.appendChild(a); a.click(); a.remove();
      window.__dlDone = { kb: Math.round(b.size / 1024) };
    } catch (e) { window.__dlErr = String(e); }
  })();
  return { ok: true };  // fire-and-forget: a big (10MB+) blob exceeds the eval timeout but still completes
})()
```

3. The eval returns immediately. Poll `({done: window.__dlDone, err: window.__dlErr})`
   until `done` is set, then confirm the file in the download folder.
4. Validate/extract with `pypdf` (see below).

Gotchas specific to the Claude-in-Chrome MCP: its result filter blocks strings
that look like query strings/cookies, so **never return the PDF URL** from
`evaluate` — keep URLs inside the page and return only sizes/status. The MCP also
truncates large text results, so don't try to scrape the whole article via
`get_page_text`; download the PDF and read it locally instead.

### B) No interactive browser MCP (Codex, plain Claude Code, CI) — use the bundled script

`scripts/ieee_download.py` is a standalone Playwright reproduction that works for
any agent. It reuses the user's login and uses `expect_download` to capture the
file even when the browser would otherwise show a save dialog.

```bash
pip install playwright pypdf && playwright install chromium

# First time only: sign in once; the login persists in a profile dir
python scripts/ieee_download.py 10329461 --login

# After that, just pass the article number / URL / DOI-resolved link
python scripts/ieee_download.py 10329461 -o ./mini-lego.pdf
python scripts/ieee_download.py https://ieeexplore.ieee.org/document/10909706

# Or reuse a browser you already run logged-in (your exact session):
#   start it once with:  msedge --remote-debugging-port=9222
python scripts/ieee_download.py 10909706 --cdp http://localhost:9222
```

The script prints the saved path and, if `pypdf` is installed, the page count and
first line so you can confirm it's the real article (not a challenge page).

## Validate / extract after download

```bash
python -c "from pypdf import PdfReader; r=PdfReader('FILE.pdf'); print(len(r.pages),'pages'); print((r.pages[0].extract_text() or '')[:300])"
```
A genuine article starts with `IEEE TRANSACTIONS ON ... VOL. xx`. If you instead
see HTML/`APM_DO_NOT_TOUCH`/a tiny file, the session wasn't authenticated — see
troubleshooting in `references/method.md`.

## Scope and ethics

Download only what you're entitled to — open access, or content your institution
licenses. Respect IEEE's Terms of Use. This is a single-article helper; do not
loop it to bulk-harvest. For non-IEEE sources (arXiv, eScholarship, author sites)
just download directly — they don't need this.

## Files

- `scripts/ieee_download.py` — portable Playwright downloader (path B).
- `references/method.md` — why curl/the PDF-button fail, the getPDF.jsp detail,
  and troubleshooting. Read it when a download returns the wrong content.
- `AGENTS.md` — how to invoke this from OpenAI Codex.
