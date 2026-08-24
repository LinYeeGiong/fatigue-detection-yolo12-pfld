$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot

& (Join-Path $PSScriptRoot 'build-server.ps1')
Push-Location (Join-Path $ProjectRoot 'desktop')
try {
    npm ci
    npm test
    npm run dist
} finally {
    Pop-Location
}
