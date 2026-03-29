@echo off
REM Minimal launcher for dashboard
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "& '.\launch.ps1'"
