\
@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo DATAFORGE - VERIFICATION
echo ============================================================

if not exist ".\venv312\Scripts\python.exe" (
    echo [ERREUR] venv312 introuvable.
    pause
    exit /b 1
)

".\venv312\Scripts\python.exe" --version

echo.
echo [1] Compilation...
".\venv312\Scripts\python.exe" -m py_compile ".\app\streamlit_app.py"
if errorlevel 1 goto :error

".\venv312\Scripts\python.exe" -m py_compile ".\scraper_runner.py"
if errorlevel 1 goto :error

".\venv312\Scripts\python.exe" -m py_compile ".\scraping\books_scraper.py"
if errorlevel 1 goto :error

".\venv312\Scripts\python.exe" -m py_compile ".\scraping\gaaraas_full_scraper.py"
if errorlevel 1 goto :error

echo OK - compilation

echo.
echo [2] Verification SQLite...
".\venv312\Scripts\python.exe" ".\check_sqlite.py"
if errorlevel 1 goto :error

echo.
echo VERIFICATION TERMINEE AVEC SUCCES.
pause
exit /b 0

:error
echo.
echo [ERREUR] Une verification a echoue.
pause
exit /b 1
