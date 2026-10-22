# Install responsive-audit as a skill on Windows.
param([string]$Target = "$env:USERPROFILE\.hermes\skills\design\responsive-audit")
$ErrorActionPreference = "Stop"
$parent = Split-Path $Target -Parent
New-Item -ItemType Directory -Force -Path $parent | Out-Null
if (Test-Path "$Target\.git") { git -C $Target pull --ff-only }
else { git clone https://github.com/lareesahu/responsive-audit.git $Target }
python -m pip install --quiet playwright
python -m playwright install chromium
Write-Host "Installed to $Target"
Write-Host "Audit something: python `"$Target\scripts\responsive_audit.py`" --url https://example.com --devices iphone"
