@echo off
rem Przejdź do głównego katalogu projektu (katalog nadrzędny wobec 'scripts')
cd /d "%~dp0.."

echo ========================================================
echo       Kompilacja aplikacji brzegowych (Windows)
echo ========================================================
echo.

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)

echo [1/3] Budowanie regis-satellite...
pyinstaller --paths . --name regis-satellite --onefile --clean apps\satellite\main.py
mkdir dist\Regis-Satellite\data 2>nul
move /Y dist\regis-satellite.exe dist\Regis-Satellite\ >nul
echo ACTIVE_PROFILE=satellite> dist\Regis-Satellite\.env
echo {> dist\Regis-Satellite\data\settings.satellite.json
echo     "controller_url": "auto",>> dist\Regis-Satellite\data\settings.satellite.json
echo     "server_url": "auto">> dist\Regis-Satellite\data\settings.satellite.json
echo }>> dist\Regis-Satellite\data\settings.satellite.json

echo.
echo [2/3] Budowanie regis-worker...
pyinstaller --paths . --name regis-worker --onefile --clean apps\worker\node.py
mkdir dist\Regis-Worker\data 2>nul
move /Y dist\regis-worker.exe dist\Regis-Worker\ >nul
echo ACTIVE_PROFILE=worker> dist\Regis-Worker\.env
echo {> dist\Regis-Worker\data\settings.worker.json
echo     "controller_url": "auto",>> dist\Regis-Worker\data\settings.worker.json
echo     "worker_port": 8001,>> dist\Regis-Worker\data\settings.worker.json
echo     "worker_host": "0.0.0.0",>> dist\Regis-Worker\data\settings.worker.json
echo     "active_tier": "regis">> dist\Regis-Worker\data\settings.worker.json
echo }>> dist\Regis-Worker\data\settings.worker.json

echo.
echo [3/3] Budowanie regis-terminal...
pyinstaller --paths . --name regis-terminal --onefile --clean apps\terminal\main.py
mkdir dist\Regis-Terminal\data 2>nul
move /Y dist\regis-terminal.exe dist\Regis-Terminal\ >nul
echo ACTIVE_PROFILE=terminal> dist\Regis-Terminal\.env
echo {> dist\Regis-Terminal\data\settings.terminal.json
echo     "controller_url": "auto",>> dist\Regis-Terminal\data\settings.terminal.json
echo     "server_url": "auto">> dist\Regis-Terminal\data\settings.terminal.json
echo }>> dist\Regis-Terminal\data\settings.terminal.json

echo.
echo ========================================================
echo SUKCES! Gotowe paczki (foldery) znajduja sie w 'dist\'.
echo Kazda z nich posiada juz swoj katalog 'data/' oraz 
echo wygenerowany profil .json i zmienna .env gotowe do pracy (Plug-and-Play).
echo ========================================================
pause
