$ErrorActionPreference = 'Stop'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'yt-librarian\.venv'
$env:UV_LINK_MODE = 'copy'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try { uv run streamlit run src/youtube_knowledge_manager/ui/app.py @args }
finally { Pop-Location }
