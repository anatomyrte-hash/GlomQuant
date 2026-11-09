@echo off
chcp 65001 >nul
"%~dp0runtime\python.exe" -I "%~dp0tools\compare_full_slide.py"
pause
