$ErrorActionPreference = 'Stop'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'yt-librarian\.venv'
$env:UV_LINK_MODE = 'copy'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try { uv run ykm sync @args }
finally { Pop-Location }
