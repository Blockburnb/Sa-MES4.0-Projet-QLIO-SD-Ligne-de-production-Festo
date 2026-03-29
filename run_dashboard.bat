@echo off
REM Simple launcher for the Streamlit dashboard
REM This just calls the PowerShell script which is more robust

cd /d "%~dp0"

powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\run_dashboard.ps1'"

pause
