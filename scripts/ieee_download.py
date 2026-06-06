#!/usr/bin/env python3
"""
ieee_download.py — Download an IEEE Xplore full-text PDF via an *authenticated* browser.

Why a browser (and not requests/curl)?
  IEEE Xplore sits behind Akamai bot management. A plain HTTP client gets a
  JavaScript challenge page (`<APM_DO_NOT_TOUCH> ...`), not a PDF. A real,
  logged-in browser session passes the challenge and carries your institutional
  entitlement, so the in-page `fetch()` below succeeds for both open-access and
  paywalled (institution-licensed) articles.

How it works:
  1. Navigate the authenticated browser to the article page.
  2. Read `window.xplGlobal.document.metadata.pdfPath` (the PDF "viewer" URL).
  3. fetch() that viewer HTML and pull the first <iframe src> — for paywalled
     papers the PDF is served by a `getPDF.jsp` endpoint with NO `.pdf` suffix,
     so we match any iframe src, not just `*.pdf`.
  4. fetch() that URL (credentials included) as a Blob and click a hidden
     <a download> — Playwright's expect_download captures the file regardless of
     the browser's "ask where to save" setting (which otherwise pops a native
     OS dialog an agent cannot click).
  5. Optionally validate with pypdf.

Browser session (pick one):
  --cdp http://localhost:9222   Reuse a browser you already started with
                                `--remote-debugging-port=9222` (your exact login).
  --profile <dir>               Use a persistent profile dir (login persists across
                                runs). First time, add --login to sign in once.

Legal/ethical: only download what you're entitled to (open access, or content your
institution licenses). Respect IEEE's Terms of Use. This is a single-article helper,
not a bulk scraper — don't loop it over many IDs.
"""
import argparse
import re
import sys
from pathlib import Path

IN_PAGE_JS = r"""
async () => {
  const meta = window.xplGlobal && window.xplGlobal.document && window.xplGlobal.document.metadata;
  if (!meta || !meta.pdfPath) throw new Error('no-metadata (not an article page, or not loaded yet)');
  let p = meta.pdfPath;
  let viewer = p.startsWith('http') ? p : location.origin + (p[0] === '/' ? '' : '/') + p;
  const html = await fetch(viewer, {credentials: 'include'}).then(r => r.text());
  let m = html.match(/<iframe[^>]+src="([^"]+)"/i) || html.match(/<frame[^>]+src="([^"]+)"/i);
  if (!m) throw new Error('no-iframe-src in viewer (login expired? Akamai challenge?)');
  let pdfUrl = m[1].replace(/&amp;/g, '&');
  if (!pdfUrl.startsWith('http')) pdfUrl = location.origin + (pdfUrl[0] === '/' ? '' : '/') + pdfUrl;
  const b = await fetch(pdfUrl, {credentials: 'include'}).then(r => r.blob());
  if (b.type.indexOf('pdf') === -1 && b.size < 100000) throw new Error('not-a-pdf (' + b.type + ', ' + b.size + ' bytes) — likely a login/challenge page');
  const o = URL.createObjectURL(b);
  const a = document.createElement('a');
  a.href = o; a.download = 'ieee.pdf';
  document.body.appendChild(a); a.click(); a.remove();
  return {kb: Math.round(b.size / 1024)};
}
"""


def arnumber_to_url(s: str) -> str:
    """Accept a raw article number, a /document/<n> path, or a full URL."""
    s = s.strip()
    if s.isdigit():
        return f"https://ieeexplore.ieee.org/document/{s}"
    m = re.search(r"document/(\d+)", s)
    if m:
        return f"https://ieeexplore.ieee.org/document/{m.group(1)}"
    if s.startswith("http"):
        return s
    raise SystemExit(f"Could not parse an IEEE article number from: {s!r}")


def get_context(p, args):
    """Return a Playwright browser context that is logged in to IEEE."""
    if args.cdp:
        browser = p.chromium.connect_over_cdp(args.cdp)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context(accept_downloads=True)
        return ctx, browser
    profile = Path(args.profile).expanduser()
    profile.mkdir(parents=True, exist_ok=True)
    launch_kwargs = dict(user_data_dir=str(profile), headless=False, accept_downloads=True)
    if args.channel:
        launch_kwargs["channel"] = args.channel  # 'msedge' or 'chrome'
    try:
        ctx = p.chromium.launch_persistent_context(**launch_kwargs)
    except Exception:
        launch_kwargs.pop("channel", None)  # fall back to bundled Chromium
        ctx = p.chromium.launch_persistent_context(**launch_kwargs)
    return ctx, None


def main():
    ap = argparse.ArgumentParser(description="Download an IEEE Xplore PDF via an authenticated browser.")
    ap.add_argument("article", help="IEEE article number, /document/<n> path, or full URL")
    ap.add_argument("-o", "--output", help="Output PDF path (default: ./<arnumber>.pdf)")
    ap.add_argument("--cdp", help="Connect to a running browser's CDP endpoint, e.g. http://localhost:9222")
    ap.add_argument("--profile", default="~/.ieee-pdf-fetch-profile",
                    help="Persistent browser profile dir (login persists). Default: ~/.ieee-pdf-fetch-profile")
    ap.add_argument("--channel", default="msedge",
                    help="Browser channel for --profile mode: msedge | chrome (default msedge; falls back to Chromium)")
    ap.add_argument("--login", action="store_true",
                    help="Open IEEE and pause so you can sign in via your institution (persists in --profile)")
    ap.add_argument("--timeout", type=int, default=180, help="Download timeout in seconds (default 180)")
    args = ap.parse_args()

    url = arnumber_to_url(args.article)
    arnum = re.search(r"document/(\d+)", url)
    out = Path(args.output) if args.output else Path(f"{arnum.group(1) if arnum else 'ieee'}.pdf")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise SystemExit("Playwright not installed. Run:  pip install playwright  &&  playwright install chromium")

    with sync_playwright() as p:
        ctx, browser = get_context(p, args)
        ctx.set_default_timeout(args.timeout * 1000)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        if args.login:
            page.goto("https://ieeexplore.ieee.org", wait_until="domcontentloaded")
            input("\n>> Sign in via your institution in the browser window, then press Enter here...\n")

        print(f"[*] Opening {url}")
        page.goto(url, wait_until="domcontentloaded")
        page.wait_for_function("() => window.xplGlobal && window.xplGlobal.document && window.xplGlobal.document.metadata",
                               timeout=args.timeout * 1000)

        print("[*] Fetching PDF inside the authenticated page...")
        with page.expect_download(timeout=args.timeout * 1000) as dl_info:
            info = page.evaluate(IN_PAGE_JS)
        download = dl_info.value
        download.save_as(str(out))
        print(f"[+] Saved {out}  (~{info.get('kb', '?')} KB reported by browser)")

        if browser is None:
            ctx.close()
        else:
            browser.close()

    # Optional validation
    try:
        from pypdf import PdfReader
        r = PdfReader(str(out))
        first = (r.pages[0].extract_text() or "").strip().splitlines()
        title = next((ln for ln in first if ln.strip()), "")
        print(f"[+] Valid PDF: {len(r.pages)} pages | first line: {title[:90]}")
    except ImportError:
        print("[i] Install pypdf to auto-validate:  pip install pypdf")
    except Exception as e:
        print(f"[!] Could not validate PDF ({e}). Open it manually to check.")


if __name__ == "__main__":
    main()
