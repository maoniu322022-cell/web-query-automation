@echo off
chcp 65001 >nul
cls
echo.
echo ======================================
echo   People Search Now ????
echo ======================================
echo.

cd /d "%~dp0"

echo [*] ?? Python ??...
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Python ???????? PATH
    pause
    exit /b 1
)

echo [*] ????...
pip show playwright >nul 2>&1
if errorlevel 1 (
    echo [*] ?? Playwright...
    pip install playwright -q
    python -m playwright install chromium -q
)

pip show openpyxl >nul 2>&1
if errorlevel 1 (
    echo [*] ?? openpyxl...
    pip install openpyxl -q
)

pip show beautifulsoup4 >nul 2>&1
if errorlevel 1 (
    echo [*] ?? BeautifulSoup4...
    pip install beautifulsoup4 -q
)

echo [?] ??????
echo.
echo [*] ????...
echo.

python main.py

echo.
echo ======================================
echo   ??????????? search_results.xlsx
echo ======================================
echo.
pause
