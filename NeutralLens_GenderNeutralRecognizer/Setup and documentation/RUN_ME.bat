@echo off
setlocal
cd /d "%~dp0"
title NeutralLens - Gender-Neutral Language Recognizer

echo ================================================
echo      NEUTRALLENS - DOCUMENT RECOGNIZER
echo ================================================
echo.

python --version
if errorlevel 1 (
    echo Python was not found. Install Python and add it to PATH.
    pause
    exit /b 1
)

python -c "import docx, pypdf" >nul 2>&1
if errorlevel 1 (
    echo Installing document-reading libraries...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependencies could not be installed.
        pause
        exit /b 1
    )
)

echo Starting NeutralLens...
python main.py
if errorlevel 1 (
    echo The application closed with an error.
    pause
)
endlocal
