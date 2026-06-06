"""Extract text from a PDF to a sibling _fulltext.txt (one PAGE marker per page).
Usage: python pdf_to_text.py <paper.pdf> [out.txt]
Prints page count and the first non-empty line so you can confirm it's a real
article (not an Akamai/bot-wall challenge page).
"""
import sys, os
from pypdf import PdfReader

pdf = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(pdf)[0] + "_fulltext.txt"
r = PdfReader(pdf)
chunks = []
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    chunks.append(f"===== PAGE {i+1} =====\n{t}")
full = "\n".join(chunks)
with open(out, "w", encoding="utf-8") as f:
    f.write(full)
first = next((ln for ln in full.splitlines() if ln.strip() and not ln.startswith("=====")), "")
print(f"PAGES: {len(r.pages)}")
print(f"OUT: {out}")
print(f"FIRST: {first[:90]}")
