@echo off
chcp 65001 >nul
setlocal

echo ============================================================
echo  Création de l'exécutable MES 4.0 - T'EleFan
echo ============================================================
echo.

:: --- Vérification de Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python n'est pas trouvé dans le PATH.
    echo          Installez Python 3.10+ depuis https://www.python.org/downloads/
    echo          puis cochez "Add Python to PATH" lors de l'installation.
    pause
    exit /b 1
)
echo [OK] Python détecté.

:: --- Mise à jour de pip ---
echo.
echo [INFO] Mise à jour de pip...
python -m pip install --upgrade pip

:: --- Installation des dépendances Python ---
echo.
echo [INFO] Installation des dépendances...
python -m pip install --upgrade ^
    streamlit ^
    plotly ^
    mysql-connector-python ^
    pandas ^
    pyinstaller

if errorlevel 1 (
    echo.
    echo [ERREUR] L'installation des dépendances a échoué.
    pause
    exit /b 1
)
echo [OK] Dépendances installées.

:: --- Création de l'exécutable avec PyInstaller ---
echo.
echo [INFO] Génération de l'exécutable (cela peut prendre plusieurs minutes)...
pyinstaller --noconfirm --onefile --windowed --icon=icone.ico --collect-all streamlit --collect-all plotly --collect-all mysql.connector --add-data "app.py;." --add-data "icone.png;." launcher.py

if errorlevel 1 (
    echo.
    echo [ERREUR] PyInstaller a rencontré une erreur.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  [OK] Exécutable créé avec succès dans le dossier dist\
echo ============================================================
pause
