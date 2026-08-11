$ErrorActionPreference = 'Stop'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $env:LOCALAPPDATA 'yt-librarian\.venv'
$env:UV_LINK_MODE = 'copy'

$RepoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $RepoRoot
try {
    uv sync --all-extras
    uv run playwright install chromium
    if (-not (Test-Path .env)) { Copy-Item .env.example .env }
    if (-not (Test-Path config/categories.yaml)) {
        Copy-Item config/categories.example.yaml config/categories.yaml
    }
    if (-not (Test-Path config/rules.yaml)) {
        Copy-Item config/rules.example.yaml config/rules.yaml
    }
    uv run ykm init-db
    Write-Host 'Setup complete. Run: uv run ykm browser-login'
}
finally {
    Pop-Location
}
