@echo off
echo ========================================================
echo       Wdrazanie kodu Regis-Core na Raspberry Pi
echo ========================================================
echo.

echo [1/3] Pakowanie projektu (ignorowanie .venv i plikow cache)...
tar.exe -czf regis-core.tar.gz --exclude=.venv --exclude=.git --exclude=__pycache__ --exclude=.pytest_cache --exclude=.idea .

echo.
echo [2/3] Kopiowanie plikow na Malinke (192.168.0.119)...
scp regis-core.tar.gz theblok@192.168.0.119:~

echo.
echo [3/3] Rozpakowywanie kodu i restartowanie uslugi systemd...
ssh theblok@192.168.0.119 "tar -xzf ~/regis-core.tar.gz -C ~/regis-core ; rm ~/regis-core.tar.gz ; sudo systemctl daemon-reload ; sudo systemctl restart regis.service"

echo.
echo Sprzatanie lokalnych plikow tymczasowych...
del regis-core.tar.gz

echo.
echo ========================================================
echo SUKCES! Malinka ma teraz najnowszy kod i zrestartowala API.
echo ========================================================
pause
