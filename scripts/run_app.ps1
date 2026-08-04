$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try { uv run streamlit run src/youtube_knowledge_manager/ui/app.py @args }
finally { Pop-Location }
