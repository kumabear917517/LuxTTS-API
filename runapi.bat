@echo off
chcp 65001
cd /d "%~dp0"
set PYTHONUSERBASE=.\python\Lib\site-packages
set PYTHONPATH=.\python\Lib\site-packages
set PATH=%PATH%;.\python\Scripts
echo ========================================
echo   LuxTTS API Server
echo   http://127.0.0.1:7860
echo ========================================
echo.
echo   API:  POST /api/tts
echo   Docs: http://127.0.0.1:7860/docs
echo   UI:   http://127.0.0.1:7860/ui/
echo.
.\python\python.exe app.py
pause