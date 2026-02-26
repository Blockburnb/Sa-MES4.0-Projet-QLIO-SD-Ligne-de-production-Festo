@echo off
setlocal

cd /d "%~dp0"

set "REPO_RAW=https://raw.githubusercontent.com/Blockburnb/Sa-MES4.0-Projet-QLIO-SD-Ligne-de-production-Festo/main"

if "%DB_USER%"=="" set "DB_USER=example_user"
if "%DB_PASSWORD%"=="" set "DB_PASSWORD=example_password"
if "%DB_NAME%"=="" set "DB_NAME=MES4"

if not exist "eval_3" mkdir "eval_3"
if not exist "TELEFAN" mkdir "TELEFAN"

echo [1/4] Verification de Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo Python introuvable. Installe Python 3.10+ puis relance.
  exit /b 1
)

echo [2/5] Preparation de l'environnement...
if not exist ".venv" (
  python -m venv .venv
)
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install streamlit pandas plotly mysql-connector-python

echo [3/5] Telechargement des fichiers depuis GitHub...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/eval_3/maquette_simple.py' -OutFile 'eval_3/maquette_simple.py'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/eval_3/README_SIMPLE.md' -OutFile 'eval_3/README_SIMPLE.md'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/TELEFAN/docker-compose.yml' -OutFile 'TELEFAN/docker-compose.yml'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Invoke-WebRequest -Uri '%REPO_RAW%/TELEFAN/FestoMES-2025-03-27.sql' -OutFile 'TELEFAN/FestoMES-2025-03-27.sql'"

echo [4/5] Demarrage de la base MariaDB (Docker)...
echo Docker n'est pas demarre automatiquement par ce script.
echo Lance Docker Desktop (ou le daemon Docker) maintenant, puis appuie sur une touche pour continuer.
pause >nul

where docker >nul 2>&1
if %ERRORLEVEL% neq 0 (
  echo docker non detecte. lancer docker manuellement puis relance le .bat
  exit /b 1
)

docker compose version >nul 2>&1
if %ERRORLEVEL% equ 0 (
  docker compose -f "TELEFAN\docker-compose.yml" up -d
  for /f %%i in ('docker compose -f "TELEFAN\docker-compose.yml" ps -q mariadb') do set "DB_CID=%%i"
) else (
  docker-compose -f "TELEFAN\docker-compose.yml" up -d
  for /f %%i in ('docker-compose -f "TELEFAN\docker-compose.yml" ps -q mariadb') do set "DB_CID=%%i"
)
if not "%DB_CID%"=="" (
  echo Import de la base SQL...
  docker exec -i %DB_CID% mariadb --force -u%DB_USER% -p%DB_PASSWORD% %DB_NAME% < "TELEFAN\FestoMES-2025-03-27.sql"
)

echo [5/5] Lancement du tableau de bord...
streamlit run "eval_3\maquette_simple.py"

endlocal
