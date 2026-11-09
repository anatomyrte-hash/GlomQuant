@echo off
chcp 65001 >nul
setlocal
"%~dp0runtime\python.exe" -I "%~dp0tools\bootstrap.py" check
if errorlevel 1 (
  echo.
  echo Islem tamamlanamadi. Yukaridaki mesaji ve kurulum kaydini saklayin.
)
pause
