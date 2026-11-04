param(
    [string]$BindAddress = "127.0.0.1",
    [int]$Port = 8000,
    [switch]$CheckOnly
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $projectPython)) {
    throw "Missing project .venv. Run: python -m venv .venv; .venv\Scripts\python.exe -m pip install -r backend/requirements-windows.txt"
}

$env:RAG_ENABLE_VECTOR = "true"
$env:CHROMA_API_IMPL = "chromadb.api.segment.SegmentAPI"
$env:CHROMA_PERSIST_DIRECTORY = "chroma_db_segment"
$env:ANONYMIZED_TELEMETRY = "false"
Push-Location $PSScriptRoot
try {
    & $projectPython scripts/check_runtime.py --probe
    if ($LASTEXITCODE -ne 0) {
        throw "Real model/vector checks failed. Backend was not started."
    }
    if (-not $CheckOnly) {
        & $projectPython -m uvicorn main:app --host $BindAddress --port $Port
        if ($LASTEXITCODE -ne 0) {
            throw "Backend exited with code $LASTEXITCODE"
        }
    }
} finally {
    Pop-Location
}
