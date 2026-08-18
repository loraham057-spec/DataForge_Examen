@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo DATAFORGE - DEMARRAGE GOOGLE CHROME
echo ==========================================

if not exist ".\venv\Scripts\python.exe" (
    echo [ERREUR] venv introuvable.
    pause
    exit /b 1
)

echo Demarrage de Streamlit...
start "DATAFORGE STREAMLIT" /min cmd /c "".\venv\Scripts\python.exe" -m streamlit run ".\app\streamlit_app.py" --server.headless true --browser.gatherUsageStats false"

timeout /t 3 /nobreak >nul

echo Ouverture de Google Chrome...
set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"

if exist "%CHROME%" (
    start "" "%CHROME%" "http://localhost:8501"
) else (
    echo [AVERTISSEMENT] Google Chrome introuvable.
    echo Ouvrez manuellement : http://localhost:8501
)

echo.
echo DATAFORGE est lance.
echo Laissez la fenetre Streamlit ouverte.
echo.
endlocal
