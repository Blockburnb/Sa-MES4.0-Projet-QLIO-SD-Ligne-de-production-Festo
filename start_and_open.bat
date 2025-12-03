@echo off
rem Script pour lancer docker compose puis ouvrir http://localhost:8080 une fois le service disponible

rem Se placer dans le dossier du script (racine du projet)
cd /d "%~dp0"

rem --- Vérification et installation/démarrage de Docker si nécessaire ---
echo Vérification de la présence de Docker...
where docker >nul 2>&1
if ERRORLEVEL 1 (
  echo Docker non trouvé sur le système.
  rem Vérifier si winget est disponible pour tenter une installation automatique
  where winget >nul 2>&1
  if ERRORLEVEL 1 (
    echo winget non disponible. J'ouvre la page d'installation de Docker Desktop dans le navigateur.
    start https://www.docker.com/get-started
    echo Après installation, relancez ce script.
    pause
    exit /b 1
  ) else (
    echo Tentative d'installation de Docker Desktop via winget (une élévation peut être demandée)...
    powershell -NoProfile -Command "Start-Process -FilePath 'winget' -ArgumentList 'install --id Docker.DockerDesktop -e -h' -Verb runAs -Wait"

    echo Lancement de Docker Desktop...
    if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" (
      start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
    ) else (
      rem Si le binaire n'existe pas, ouvrir la page web pour terminer l'installation manuellement
      start https://www.docker.com/get-started
    )

    echo Attente que le moteur Docker soit disponible (maximum ~120s)...
    powershell -NoProfile -Command "for ($i=0;$i -lt 60;$i++) { try { docker version | Out-Null; exit 0 } catch { Start-Sleep -Seconds 2 } }; exit 1"
    if ERRORLEVEL 1 (
      echo Docker reste indisponible après installation. Vérifiez Docker Desktop et relancez le script.
      pause
      exit /b 1
    )
  )
)

echo Docker est présent.

echo Lancement de Docker Compose...
docker compose up
if ERRORLEVEL 1 (
  echo Erreur lors de l'execution de 'docker compose'. Verifiez Docker et le fichier docker-compose.yml.
  pause
  exit /b 1
)

echo Attente du service sur http://localhost:8080 ...
rem On utilise PowerShell pour poller le port et attendre qu'il réponde (timeout ~120s)
powershell -NoProfile -Command "$url='http://localhost:8080/'; for ($i=0;$i -lt 60;$i++) { try { $r=Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 5; if ($r.StatusCode -eq 200) { exit 0 } } catch {} Start-Sleep -Seconds 2 }; exit 1"
if ERRORLEVEL 1 (
  echo Délai d'attente écoulé ou service indisponible. J'ouvre quand même le navigateur.
  start http://localhost:8080
  exit /b 1
)

echo Service disponible — ouverture du navigateur...
start http://localhost:8080
exit /b 0
