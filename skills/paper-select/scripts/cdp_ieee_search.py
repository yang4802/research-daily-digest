"""Query IEEE Xplore from inside the CDP-attached, authenticated browser and print
structured results (articleNumber, year, title, authors, venue), newest first.

Uses the same /rest/search endpoint the Xplore frontend calls (in-page fetch so it
inherits cookies + origin and passes the bot wall).

Usage: python cdp_ieee_search.py "QUERY TEXT" [rows]
Set PYTHONIOENCODING=utf-8 to avoid console encoding errors on non-ASCII names.
"""
import sys
from playwright.sync_api import sync_playwright

query = sys.argv[1] if len(sys.argv) > 1 else "coupled inductor"
rows = int(sys.argv[2]) if len(sys.argv) > 2 else 25
cdp = "http://localhost:9222"

JS = """
async ([q, rows]) => {
  try {
    const body = {
      queryText: q, highlight: true, returnFacets: ["ALL"], returnType: "SEARCH",
      matchPubs: true, rowsPerPage: rows, pageNumber: 1, sortType: "newest"
    };
    const res = await fetch("/rest/search", {
      method: "POST", credentials: "include",
      headers: {"Content-Type": "application/json", "Accept": "application/json"},
      body: JSON.stringify(body)
    });
    if (!res.ok) return {error: "http " + res.status};
    const j = await res.json();
    const recs = (j.records || []).map(r => ({
      ar: r.articleNumber, year: r.publicationYear,
      title: (r.articleTitle || "").replace(/<[^>]+>/g, ""),
      authors: (r.authors || []).map(a => a.preferredName || a.normalizedName).join(", "),
      venue: r.publicationTitle, type: r.contentType
    }));
    return {total: j.totalRecords, records: recs};
  } catch (e) { return {error: String(e)}; }
}
"""

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp)
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    if "ieeexplore.ieee.org" not in page.url:
        page.goto("https://ieeexplore.ieee.org/Xplore/home.jsp", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(1200)
    out = page.evaluate(JS, [query, rows])
    if out.get("error"):
        print("REST_ERROR:", out["error"])
    else:
        print("TOTAL:", out.get("total"))
        for r in out.get("records", []):
            print(f"{r['year']}\t{r['ar']}\t{r['type']}\t{r['title']}  | {r['authors']}  | {r['venue']}")
