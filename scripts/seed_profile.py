"""Initialize a user's workspace from config.yaml:
  research_profile/{profile.md, mastery.md, read-log.md, open-questions.md}
  report/  inbox/  index.md   and (if excel.enabled) the Papers spreadsheet.
Idempotent: never overwrites an existing file unless --force is passed.

Usage: python seed_profile.py [--config config.yaml] [--force]
"""
import os, argparse, datetime
try:
    import yaml
except ImportError:
    raise SystemExit("Please `pip install pyyaml` (see requirements.txt).")

def w(path, text, force):
    if os.path.exists(path) and not force:
        print("  skip (exists):", path); return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("  wrote:", path)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    cfg = yaml.safe_load(open(a.config, encoding="utf-8"))
    root = os.path.expanduser(cfg.get("paths", {}).get("project_root", "."))
    today = datetime.date.today().isoformat()
    R = lambda *p: os.path.join(root, *p)

    research = cfg.get("research", {})
    interests = research.get("interests", [])
    labs = research.get("reference_labs", [])
    user = cfg.get("user", {})

    for d in ("research_profile", "report", "inbox"):
        os.makedirs(R(d), exist_ok=True)

    # profile.md
    profile = f"""# Research Profile
_Last updated: {today}_

## Who
{user.get('name','')} — {user.get('role','')} @ {user.get('institution','')}

## Field
{research.get('field','')}

## Interests & subfields (priority order)
""" + "".join(f"{i+1}. {t}\n" for i, t in enumerate(interests)) + """
## Reference labs / authors to prioritize
""" + "".join(f"- {l}\n" for l in labs) + f"""
## Notes (how to pitch reports)
{cfg.get('report',{}).get('pedagogy','')}
- Summary languages: {cfg.get('report',{}).get('summary_languages')}; dialogue: {cfg.get('report',{}).get('dialogue_language')}.
"""
    w(R("research_profile", "profile.md"), profile, a.force)

    w(R("research_profile", "mastery.md"),
      "# Concept Mastery\n_Legend: 🟢 solid · 🟡 shaky · 🔴 not yet · ⚪ just introduced (untested)_\n\n"
      "| Concept | Level | Last touched | Evidence / note |\n|---|---|---|---|\n", a.force)

    w(R("research_profile", "read-log.md"),
      "# Reading Log (learning record)\n\n| Date | Paper (title · arnumber · role) | Key concepts introduced |\n|---|---|---|\n", a.force)

    w(R("research_profile", "open-questions.md"),
      "# Open Questions & Reading Queue\n\n## A. Pending questions / challenges (to check next time)\n\n## B. Reading queue (next papers / topics)\n", a.force)

    w(R("index.md"),
      "# Download ledger (dedup)\n\n> Each day's paper selection must NOT repeat anything listed here.\n\n"
      "| arnumber | year | title | venue | location |\n|---|---|---|---|---|\n", a.force)

    # Excel
    exc = cfg.get("excel", {})
    if exc.get("enabled"):
        xlsx = R(exc.get("path", "Papers_Summary.xlsx"))
        if os.path.exists(xlsx) and not a.force:
            print("  skip (exists):", xlsx)
        else:
            import openpyxl
            wb = openpyxl.Workbook(); ws = wb.active; ws.title = exc.get("sheet", "Papers")
            headers = ["#", "Title", "Author", "Journal Name", "Year", "Short Summary",
                       "Cons of the paper", "My lack", "ABSTRACT", "Insights"]
            for c, h in enumerate(headers, start=1):
                ws.cell(1, c, h)
            wb.save(xlsx); print("  wrote:", xlsx)

    print("Seed complete. Workspace root:", os.path.abspath(root))

if __name__ == "__main__":
    main()
