"""Mirror daily research-digest outputs to a Google Drive desktop sync folder.

This script intentionally uses only local filesystem operations. The Codex Google
Drive connector can inspect the target folder, but in this environment it does
not expose raw PDF/Markdown upload or folder-create operations. When a local
Google Drive for desktop folder is configured, this script keeps the Drive copy
updated by writing into that synced folder.

Usage:
  python scripts/drive_sync.py --date 260606

Config:
  google_drive.enabled: true
  google_drive.folder_url: "https://drive.google.com/drive/folders/..."
  google_drive.local_sync_root: "G:/My Drive/research-daily-digest"

Alternatively set:
  GOOGLE_DRIVE_DAILY_DIGEST_ROOT=G:/My Drive/research-daily-digest
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path


def load_config(project_root: Path) -> dict:
    try:
        import yaml
    except ImportError:
        return {}
    cfg_path = project_root / "config.yaml"
    if not cfg_path.exists():
        return {}
    with cfg_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def today_yymmdd() -> str:
    return datetime.now().strftime("%y%m%d")


def clean_path(value: str | None) -> str:
    return os.path.expandvars(os.path.expanduser(value or "")).strip()


def common_drive_roots() -> list[Path]:
    home = Path.home()
    candidates = [
        Path("G:/My Drive/research-daily-digest"),
        Path("G:/내 드라이브/research-daily-digest"),
        home / "Google Drive" / "research-daily-digest",
        home / "My Drive" / "research-daily-digest",
        home / "Google 드라이브" / "research-daily-digest",
    ]
    return [p for p in candidates if p.exists()]


def resolve_sync_root(cfg: dict, cli_root: str | None) -> Path | None:
    gd = cfg.get("google_drive") or {}
    raw = (
        clean_path(cli_root)
        or clean_path(os.environ.get("GOOGLE_DRIVE_DAILY_DIGEST_ROOT"))
        or clean_path(os.environ.get("GOOGLE_DRIVE_SYNC_ROOT"))
        or clean_path(gd.get("local_sync_root"))
    )
    if raw:
        return Path(raw)
    found = common_drive_roots()
    return found[0] if found else None


def copy_tree(src: Path, dst: Path) -> int:
    copied = 0
    for path in src.rglob("*"):
        if path.is_dir():
            continue
        rel = path.relative_to(src)
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        copied += 1
    return copied


def make_bundle(project_root: Path, date: str) -> Path:
    day_dir = project_root / "report" / date
    bundle = day_dir / f"research-daily-digest-{date}.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in day_dir.rglob("*"):
            if path.is_dir() or path.suffix.lower() == ".zip":
                continue
            zf.write(path, path.relative_to(project_root))
        for rel in ["Papers_Summary.xlsx", "index.md"]:
            path = project_root / rel
            if path.exists():
                zf.write(path, path.relative_to(project_root))
        profile = project_root / "research_profile"
        if profile.exists():
            for path in profile.glob("*.md"):
                zf.write(path, path.relative_to(project_root))
    return bundle


def write_manifest(project_root: Path, date: str, cfg: dict, bundle: Path) -> Path:
    gd = cfg.get("google_drive") or {}
    day_dir = project_root / "report" / date
    files = []
    for path in day_dir.rglob("*"):
        if path.is_file():
            files.append(str(path.relative_to(project_root)).replace("\\", "/"))
    for rel in ["Papers_Summary.xlsx", "index.md"]:
        if (project_root / rel).exists():
            files.append(rel)
    profile = project_root / "research_profile"
    if profile.exists():
        files.extend(str(p.relative_to(project_root)).replace("\\", "/") for p in profile.glob("*.md"))

    manifest = {
        "date": date,
        "drive_folder_url": gd.get("folder_url", ""),
        "drive_folder_id": gd.get("folder_id", ""),
        "bundle": str(bundle.relative_to(project_root)).replace("\\", "/"),
        "files": sorted(set(files)),
    }
    out = day_dir / "drive_upload_manifest.json"
    out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def parse_folder_id(url: str) -> str:
    match = re.search(r"/folders/([^/?#]+)", url or "")
    return match.group(1) if match else ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirror daily digest outputs to a Google Drive desktop sync folder.")
    parser.add_argument("--date", default=today_yymmdd(), help="Daily report date folder, e.g. 260606.")
    parser.add_argument("--project-root", default=".", help="Project root. Defaults to current directory.")
    parser.add_argument("--sync-root", default=None, help="Override local Google Drive sync root.")
    parser.add_argument("--require-sync", action="store_true", help="Fail if no local sync root is configured.")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    cfg = load_config(project_root)
    gd = cfg.get("google_drive") or {}
    if not gd.get("enabled", False):
        print("DRIVE_SYNC_DISABLED")
        return 0

    folder_url = gd.get("folder_url", "")
    folder_id = gd.get("folder_id") or parse_folder_id(folder_url)
    day_dir = project_root / "report" / args.date
    if not day_dir.exists():
        print(f"ERROR: missing daily folder: {day_dir}", file=sys.stderr)
        return 2

    bundle = make_bundle(project_root, args.date)
    manifest = write_manifest(project_root, args.date, cfg, bundle)
    sync_root = resolve_sync_root(cfg, args.sync_root)

    print(f"DRIVE_FOLDER_URL: {folder_url}")
    print(f"DRIVE_FOLDER_ID: {folder_id}")
    print(f"BUNDLE: {bundle}")
    print(f"MANIFEST: {manifest}")

    if not sync_root:
        print("SYNC_STATUS: bundle_created_no_local_drive_sync_path")
        if args.require_sync:
            return 3
        return 0

    sync_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    copied += copy_tree(day_dir, sync_root / "report" / args.date)
    for rel in ["Papers_Summary.xlsx", "index.md"]:
        src = project_root / rel
        if src.exists():
            dst = sync_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    profile = project_root / "research_profile"
    if profile.exists():
        copied += copy_tree(profile, sync_root / "research_profile")

    print(f"SYNC_ROOT: {sync_root}")
    print(f"SYNC_STATUS: copied {copied} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
