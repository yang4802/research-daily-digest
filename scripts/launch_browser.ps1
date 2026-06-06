# Launch (or reuse) a dedicated-profile Chrome with remote debugging for IEEE access.
# A separate --user-data-dir runs as its OWN Chrome instance, so this does NOT
# disturb the user's normal browser and does NOT need to kill anything.
# Chrome 136+ blocks remote-debugging on the *default* profile, hence a dedicated dir.
param(
  [int]$Port = 9222,
  [string]$ProfileDir = "$env:USERPROFILE\cdp-profile"
)

# Reuse if already up.
try {
  $r = Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$Port/json/version" -TimeoutSec 3
  "ALREADY_UP: " + $r.Content
  return
} catch {}

$chrome = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path $chrome)) { $chrome = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" }
if (-not (Test-Path $chrome)) { $chrome = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" }

Start-Process $chrome -ArgumentList `
  "--remote-debugging-port=$Port", `
  "--user-data-dir=$ProfileDir", `
  "--no-first-run", `
  "--no-default-browser-check"

Start-Sleep -Seconds 4
try {
  (Invoke-WebRequest -UseBasicParsing -Uri "http://localhost:$Port/json/version" -TimeoutSec 5).Content
} catch {
  "PORT_FAILED: $($_.Exception.Message)"
}
