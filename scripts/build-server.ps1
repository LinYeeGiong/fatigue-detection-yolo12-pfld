$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'

if (-not (Test-Path -LiteralPath $Python)) {
    throw 'Python 3.11 virtual environment not found. Create .venv and install server/requirements-dev.txt.'
}

& $Python -m pip install pyinstaller==6.16.0 waitress==3.0.2 backports.tarfile==1.2.0
& $Python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --name fatigue-server `
    --hidden-import server.services.onnx_detector `
    --distpath (Join-Path $ProjectRoot 'dist') `
    --workpath (Join-Path $ProjectRoot 'build\pyinstaller') `
    --specpath (Join-Path $ProjectRoot 'build') `
    --add-data "$(Join-Path $ProjectRoot 'server\templates');server\templates" `
    --add-data "$(Join-Path $ProjectRoot 'server\static');server\static" `
    --paths $ProjectRoot `
    (Join-Path $ProjectRoot 'server\entrypoint.py')
