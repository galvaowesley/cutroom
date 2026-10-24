# Windows wrapper for install.py (the cross-platform installer). Same options:
#   .\install.ps1 [--agent claude,codex] [--home "$HOME\Documents\cutroom"] [--output DIR] [--language pt-BR] [--uninstall]
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (Get-Command py -ErrorAction SilentlyContinue) { py -3 install.py @args }
elseif (Get-Command python -ErrorAction SilentlyContinue) { python install.py @args }
else { Write-Error "Python 3 is required: winget install Python.Python.3.13"; exit 2 }
exit $LASTEXITCODE
