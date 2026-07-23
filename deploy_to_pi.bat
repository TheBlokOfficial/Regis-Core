@echo off
echo ========================================================
echo       Wdrazanie kodu Regis-Core na Raspberry Pi (Wheel)
echo ========================================================
echo.

echo [1/3] Budowanie paczki .whl...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
)
python -m build --wheel
if %ERRORLEVEL% NEQ 0 (
    echo [BŁĄD] Budowanie paczki .whl nie powiodło się! Zainstaluj braki: pip install -r requirements.txt
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Kopiowanie paczki .whl na Malinke (192.168.0.119)...
for /f "delims=" %%i in ('dir /b /o-d dist\regis_core-*.whl 2^>nul') do (
    set WHEEL_FILE=%%i
    goto :found_wheel
)
echo [BŁĄD] Nie znaleziono paczki .whl w folderze dist\
pause
exit /b 1
:found_wheel
echo Znaleziono paczke: %WHEEL_FILE%
scp dist\%WHEEL_FILE% theblok@192.168.0.119:~

echo.
echo [3/3] Instalacja paczki na Malince i restartowanie uslug...
ssh theblok@192.168.0.119 "cd ~/regis-core ; source .venv/bin/activate ; pip install --force-reinstall ~/%WHEEL_FILE% ; rm ~/%WHEEL_FILE% ; sudo systemctl daemon-reload ; sudo systemctl restart regis.service regis-worker.service"

echo.
echo ========================================================
echo SUKCES! Malinka zainstalowala najnowsza paczke i zrestartowala API.
echo ========================================================
pause
