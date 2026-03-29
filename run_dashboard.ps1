# Script PowerShell pour lancer le dashboard Streamlit
# Plus simple et plus robuste

Write-Host "[1/5] Verification de Python..."
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python introuvable"
    exit 1
}

Write-Host "[2/5] Preparation de l'environnement Python..."
$venvPath = ".\.venv"

if (-not (Test-Path $venvPath)) {
    Write-Host "Creation du venv..."
    python -m venv .venv
}

# Activate venv
& ".\.venv\Scripts\Activate.ps1"

# Install packages silently
Write-Host "Installation des packages..."
python -m pip install --upgrade pip -q 2>$null
python -m pip install streamlit pandas plotly mysql-connector-python -q 2>$null

Write-Host "[3/5] Telechargement des fichiers..."
$repoRaw = "https://raw.githubusercontent.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo/main"

@(
    ("$repoRaw/eval_3/maquette_simple.py", "eval_3/maquette_simple.py"),
    ("$repoRaw/eval_3/README_SIMPLE.md", "eval_3/README_SIMPLE.md"),
    ("$repoRaw/TELEFAN/docker-compose.yml", "TELEFAN/docker-compose.yml"),
    ("$repoRaw/TELEFAN/FestoMES-2025-03-27.sql", "TELEFAN/FestoMES-2025-03-27.sql")
) | ForEach-Object {
    $url, $file = $_
    if (-not (Test-Path $file)) {
        try {
            Invoke-WebRequest -Uri $url -OutFile $file -ErrorAction SilentlyContinue
        } catch {}
    }
}

Write-Host "[4/5] Verification de Docker..."
$dockerAvailable = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)

if ($dockerAvailable) {
    Write-Host "Docker found. Attempting to start database..."
    try {
        $null = docker ps 2>$null
        Write-Host "Docker is running. Starting containers..."
        $null = docker compose -f "TELEFAN\docker-compose.yml" up -d 2>$null
        Start-Sleep -Seconds 15
    } catch {
        Write-Host "Note: Docker is available but database startup had issues. Continuing..."
    }
} else {
    Write-Host "Docker not installed. Continuing without database..."
}

Write-Host "[5/5] Lancement du dashboard..."
Write-Host ""
Write-Host "========================================================="
Write-Host "Dashboard available at: http://localhost:8501"
Write-Host "Press CTRL+C to stop"
Write-Host "========================================================="
Write-Host ""

streamlit run "eval_3\maquette_simple.py"
