# Method, rationale, and troubleshooting

This file explains *why* the skill works the way it does, so the approach can be
adapted when IEEE changes details. Read it if a download returns the wrong
content or you need to port the logic.

## What does NOT work (and why)

| Approach | Result | Reason |
|---|---|---|
| `curl` / `requests` / `Invoke-WebRequest` / `WebFetch` on the document or stamp URL | A ~6 KB HTML page starting `<APM_DO_NOT_TOUCH>` with obfuscated JS | **Akamai Bot Manager**. Non-browser clients get a JS challenge instead of the PDF. You cannot solve it server-side, and you shouldn't try to evade it. |
| Clicking the IEEE **"PDF"** button or the PDF viewer's **download icon** | A native Windows/macOS **"Save As" dialog** | The dialog is an OS-level window. Browser-automation tools (Claude-in-Chrome, Playwright `click`) drive *web page* content, not OS chrome. An agent can't press "Save". |
| `fetch()` of `metadata.pdfPath` and treating it as the PDF | `text/html`, ~6 KB | `pdfPath` is the **viewer** page, not the PDF. The real PDF is the viewer's `<iframe src>`. |
| Matching the iframe src with `/\.pdf/` | `no-iframe-src` for paywalled papers | Open-access PDFs live at a `…/iel*/…/<id>.pdf` URL, but **paywalled** PDFs are streamed by a **`getPDF.jsp`** endpoint with **no `.pdf` extension**. Match *any* iframe `src`. |

## What works

An **authenticated, real browser** session:

- passes the Akamai challenge (real TLS/headers/JS execution), and
- carries the institutional entitlement cookie (e.g. KAIST/university SSO or
  IP-based access), which unlocks paywalled articles.

Running `fetch(..., {credentials:'include'})` **inside that page** therefore
returns the actual PDF bytes. We turn the bytes into a Blob and click a hidden
`<a download>`; the browser writes the file to its download folder. Playwright's
`expect_download` (path B) intercepts that download object, so it lands wherever
you tell it regardless of the "ask where to save" setting that would otherwise
pop the native dialog.

## The flow (both paths use the same idea)

```
authenticated browser tab
  → goto ieeexplore.ieee.org/document/<arnumber>
  → wait for window.xplGlobal.document.metadata           (article metadata loaded)
  → pdfPath = metadata.pdfPath                             (the VIEWER url)
  → html   = fetch(pdfPath, credentials:'include')         (viewer HTML, ~6KB)
  → pdfUrl = first <iframe|frame src> in html              (.pdf OR getPDF.jsp)
  → blob   = fetch(pdfUrl, credentials:'include')          (the real PDF bytes)
  → <a href=blobURL download> .click()                     (saved, no dialog)
  → validate with pypdf
```

## Why "fire-and-forget" in the MCP path

A 10–15 MB blob fetch can exceed the MCP's JS-eval timeout (~45 s) even though
the download itself completes fine. So the MCP snippet kicks off the async work,
returns immediately, and stashes the outcome on `window.__dlDone` / `__dlErr`.
Poll those instead of awaiting the evaluate. (The Playwright path doesn't need
this — `expect_download` waits on the download event, not the eval.)

## MCP content-filter caveat (Claude-in-Chrome)

The Claude-in-Chrome tool blocks results that look like cookies/query strings, so
returning the PDF URL (it has `?tp=&arnumber=…`) yields `[BLOCKED: Cookie/query
string data]`. Keep every URL **inside** the page and return only booleans/sizes.
The same tool truncates big text payloads (~1 KB visible per result) and blocks
chunks of article text containing query-like tokens — which is exactly why you
should download the PDF and read it with `pypdf` locally rather than scraping the
DOM text.

## Troubleshooting

- **`no-metadata`**: the page isn't an article page, or hadn't finished loading.
  Confirm the URL is `…/document/<digits>` and wait for `window.xplGlobal`.
- **`no-iframe-src`** or a tiny `text/html` blob: the session isn't
  authenticated (login expired, or off the institution network/VPN), so IEEE
  served a login/challenge page. Re-run with `--login` (path B) or re-auth the
  browser, then retry.
- **`not-a-pdf`**: same cause as above, or the article genuinely has no full text
  (rare). Open the document page in the browser and check you can read it.
- **Native save dialog still appears (path A only)**: you used the viewer's
  download button instead of the in-page `fetch`+`<a download>` snippet. Use the
  snippet. (Path B sidesteps this entirely via `expect_download`.)
- **Playwright can't find your login (path B)**: persistent `--profile` is a
  *separate* profile from your everyday browser — sign in once with `--login`, or
  use `--cdp` to attach to your already-running, already-logged-in browser
  (start it with `--remote-debugging-port=9222`).
- **`channel msedge` not found**: omit `--channel` to use Playwright's bundled
  Chromium, or pass `--channel chrome`.

## If IEEE changes their markup

The brittle parts are `metadata.pdfPath` and the viewer `<iframe src>`. If they
move, open one article's PDF manually with DevTools Network open, find the request
that returns `application/pdf`, and update the selector. The Akamai/auth principle
(fetch from inside a logged-in browser) stays the same.
