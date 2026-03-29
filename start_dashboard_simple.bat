@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

set "REPO_RAW=https://raw.githubusercontent.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo/main"
set "DB_USER=root"
set "DB_PASSWORD=Password1!"
set "DB_NAME=mes4"

if not exist "eval_3" mkdir "eval_3"
if not exist "TELEFAN" mkdir "TELEFAN"

echo [1/5] Verification de Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo ERROR: Python introuvable. Installe Python 3.10+ puis relance.
  pause
  exit /b 1
)

echo [2/5] Preparation de l'environnement Python...
if not exist ".venv" (
  echo Creation d'un environnement virtuel...
  python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip >nul 2>&1
python -m pip install streamlit pandas plotly mysql-connector-python >nul 2>&1
echo Python packages installes avec succes

echo [3/5] Telechargement des fichiers depuis GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/eval_3/maquette_simple.py' -OutFile 'eval_3/maquette_simple.py' -ErrorAction SilentlyContinue" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/eval_3/README_SIMPLE.md' -OutFile 'eval_3/README_SIMPLE.md' -ErrorAction SilentlyContinue" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/TELEFAN/docker-compose.yml' -OutFile 'TELEFAN/docker-compose.yml' -ErrorAction SilentlyContinue" >nul 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/TELEFAN/FestoMES-2025-03-27.sql' -OutFile 'TELEFAN/FestoMES-2025-03-27.sql' -ErrorAction SilentlyContinue" >nul 2>&1
echo Fichiers telecharges ou deja presents

echo [4/5] Verification de Docker et de la base de donnees...
where docker >nul 2>&1
if %ERRORLEVEL% equ 0 (
  echo Docker trouve. Tentative de lancement...
  docker ps >nul 2>&1
  if %ERRORLEVEL% neq 0 (
    echo Docker n'est pas actif. Lancement...
    start "" "C:\Program Files\Docker\Docker\Docker.exe"
    timeout /t 30 /nobreak
  )
  docker ps >nul 2>&1
  if %ERRORLEVEL% equ 0 (
    echo Docker est pret. Lancement conteneurs...
    docker compose -f "TELEFAN\docker-compose.yml" up -d >nul 2>&1
    timeout /t 15 /nobreak
  ) else (
    echo Docker n'a pas pu demarrer.
  )
) else (
  echo Docker n'est pas installe.
)

echo [5/5] Lancement du tableau de bord Streamlit...
echo.
echo =========================================================
echo Dashboard demarrage sur http://localhost:8501
echo =========================================================
echo.

call ".venv\Scripts\activate.bat"
streamlit run "eval_3\maquette_simple.py"

endlocal
