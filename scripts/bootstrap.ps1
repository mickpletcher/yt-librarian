$ErrorActionPreference = 'Stop'

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
    uv run alembic upgrade head
    Write-Host 'Setup complete. Run: uv run ykm browser-login'
}
finally {
    Pop-Location
}
