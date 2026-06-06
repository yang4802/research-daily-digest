"""Check IEEE Xplore institutional access on the CDP-attached browser (port 9222).
Loads a sample document and reports whether a PDF path / entitlement is present.
Usage: python cdp_check_access.py [arnumber]
"""
import sys
from playwright.sync_api import sync_playwright

ar = sys.argv[1] if len(sys.argv) > 1 else "9650554"  # paywalled sample
cdp = "http://localhost:9222"

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(cdp)
    ctx = browser.contexts[0]
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(f"https://ieeexplore.ieee.org/document/{ar}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(2500)
    info = page.evaluate(
        """() => {
            let r = {pdfPath: null, instName: null};
            try { r.pdfPath = window.xplGlobal.document.metadata.pdfPath; } catch(e) {}
            try { r.instName = (document.querySelector('.institutional-access, .inst-name, [class*=institution]') || {}).innerText || null; } catch(e) {}
            return r;
        }"""
    )
    print("URL:", page.url)
    print("pdfPath:", info.get("pdfPath"))
    print("instName:", info.get("instName"))
    print("ACCESS_OK:", bool(info.get("pdfPath")))
