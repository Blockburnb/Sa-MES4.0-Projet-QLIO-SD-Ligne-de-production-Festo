# Simple dashboard launcher
# Skip Docker checks and just launch Streamlit

Write-Host "[1/3] Preparing Python environment..."

# Ensure venv exists
if (-not (Test-Path ".\.venv")) {
    python -m venv .venv
}

# Activate venv
& ".\.venv\Scripts\Activate.ps1"

# Install dependencies silently
python -m pip install --upgrade pip -q 2>$null
python -m pip install streamlit pandas plotly mysql-connector-python -q 2>$null

Write-Host "[2/3] Files ready"

Write-Host "[3/3] Starting dashboard..."
Write-Host ""
Write-Host "========================================================="
Write-Host "Dashboard available at: http://localhost:8501"
Write-Host "Press CTRL+C to stop"
Write-Host "========================================================="
Write-Host ""

# Launch Streamlit - this will run in foreground
streamlit run "eval_3\maquette_simple.py"
