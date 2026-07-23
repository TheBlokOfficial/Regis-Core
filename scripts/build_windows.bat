@echo off
echo ========================================================
echo       Kompilacja aplikacji brzegowych (Windows)
echo ========================================================
echo.

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo [1/3] Budowanie regis-satellite...
pyinstaller --name regis-satellite --onefile --clean apps\satellite\main.py
mkdir dist\Regis-Satellite\data 2>nul
move /Y dist\regis-satellite.exe dist\Regis-Satellite\ >nul
copy /Y .env.example dist\Regis-Satellite\.env >nul

echo.
echo [2/3] Budowanie regis-worker...
pyinstaller --name regis-worker --onefile --clean apps\worker\node.py
mkdir dist\Regis-Worker\data 2>nul
move /Y dist\regis-worker.exe dist\Regis-Worker\ >nul
copy /Y .env.example dist\Regis-Worker\.env >nul

echo.
echo [3/3] Budowanie regis-terminal...
pyinstaller --name regis-terminal --onefile --clean apps\terminal\main.py
mkdir dist\Regis-Terminal\data 2>nul
move /Y dist\regis-terminal.exe dist\Regis-Terminal\ >nul
copy /Y .env.example dist\Regis-Terminal\.env >nul

echo.
echo ========================================================
echo SUKCES! Gotowe paczki (foldery) znajduja sie w 'dist\'.
echo Kazda z nich posiada juz swoj katalog 'data/' oraz 
echo wzorcowy plik .env gotowy do edycji. 
echo ========================================================
pause
