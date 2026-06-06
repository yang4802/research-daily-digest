"""Launch (or reuse) a dedicated-profile Chrome/Edge with remote debugging, on
any OS. A separate --user-data-dir runs as its OWN browser instance, so this does
NOT disturb the user's normal browser and needs to kill nothing. Chrome 136+
blocks remote-debugging on the *default* profile, hence the dedicated dir.

Reads browser.port / browser.profile_dir / browser.executable from ./config.yaml
if present; CLI flags override. Reuses the browser if the port already answers.

Usage:
  python launch_browser.py
  python launch_browser.py --port 9222 --profile ~/cdp-profile
"""
import os, sys, time, json, argparse, platform, subprocess, urllib.request

def load_cfg():
    try:
        import yaml
        with open("config.yaml", encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get("browser", {}) or {}
    except Exception:
        return {}

def port_up(port):
    try:
        with urllib.request.urlopen(f"http://localhost:{port}/json/version", timeout=3) as r:
            return r.read().decode("utf-8", "replace")
    except Exception:
        return None

def find_browser():
    sysname = platform.system()
    cands = []
    if sysname == "Windows":
        pf = os.environ.get("ProgramFiles", r"C:\Program Files")
        pfx = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        la = os.environ.get("LOCALAPPDATA", "")
        cands = [
            os.path.join(pf, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(pfx, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(la, r"Google\Chrome\Application\chrome.exe"),
            os.path.join(pfx, r"Microsoft\Edge\Application\msedge.exe"),
            os.path.join(pf, r"Microsoft\Edge\Application\msedge.exe"),
        ]
    elif sysname == "Darwin":
        cands = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
            "/Applications/Chromium.app/Contents/MacOS/Chromium",
        ]
    else:  # Linux
        cands = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge"]
    for c in cands:
        if os.path.sep in c:
            if os.path.exists(c):
                return c
        else:
            from shutil import which
            p = which(c)
            if p:
                return p
    return None

def main():
    cfg = load_cfg()
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=cfg.get("remote_debugging_port", 9222))
    ap.add_argument("--profile", default=os.path.expanduser(str(cfg.get("profile_dir", "~/cdp-profile"))))
    ap.add_argument("--exe", default=cfg.get("executable"))
    args = ap.parse_args()

    up = port_up(args.port)
    if up:
        print("ALREADY_UP:", up)
        return

    exe = args.exe or find_browser()
    if not exe:
        sys.exit("No Chrome/Edge found. Set browser.executable in config.yaml.")
    profile = os.path.expanduser(args.profile)
    os.makedirs(profile, exist_ok=True)
    cmd = [exe, f"--remote-debugging-port={args.port}", f"--user-data-dir={profile}",
           "--no-first-run", "--no-default-browser-check"]
    kwargs = {}
    if platform.system() == "Windows":
        kwargs["creationflags"] = 0x00000008  # DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)

    for _ in range(15):
        time.sleep(1)
        up = port_up(args.port)
        if up:
            print("LAUNCHED:", up)
            return
    sys.exit(f"PORT_FAILED: browser did not open CDP on :{args.port}")

if __name__ == "__main__":
    main()
