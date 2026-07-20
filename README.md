# Regis-Core

Projekt Regis-Core to centralny serwer prywatnego asystenta głosowego (LLM-based) służący do sterowania infrastrukturą Home Assistant. Projekt jest zamknięty, przeznaczony na użytek prywatny i zaprojektowany pod kątem działania w odizolowanym środowisku LAN. Nie jest to oprogramowanie typu Open Source.

## Topologia sprzętowa

1. Środowisko deweloperskie (Dev): Windows / Linux (Testowano na RTX 5070).
2. Środowisko produkcyjne (Prod): Raspberry Pi 5 (8GB RAM, Dysk 1TB NVMe 970 EVO).
3. Urządzenia peryferyjne (Satelity): Moduły ESP32 z oprogramowaniem WakeWord.
4. Serwer Home Assistant: Zewnętrzne Raspberry Pi (4GB RAM) z zainstalowanym Dockerem.

## Architektura i działanie

System korzysta z założeń Czystej Architektury (Clean Architecture). Posiada centralny moduł Orchestratora (`main.py`), odseparowaną warstwę UI w terminalu (`ui/cli.py`) oraz hermetyczną logikę wnioskowania LLM i parsowania akcji (`core/`). Komunikacja odbywa się przez stabilne połączenia (`requests`), a błędy środowiskowe obsługiwane są za pomocą niestandardowych wyjątków.  
Zwrócony przez model ciąg znaków jest walidowany, a następnie w strukturze `ActionResult` wysyłany jako fizyczna akcja do serwera HA.

## Wymagania systemowe

- Python 3.10+
- Skonfigurowany i działający serwer Ollama.
- Zależności projektowe:
  ```bash
  pip install -r requirements.txt
  ```

## Uruchamianie

Głównym punktem wejściowym całego systemu jest plik:
```bash
python main.py
```

## Testowanie (Środowisko Deweloperskie)

Aby zweryfikować poprawność kodu po wprowadzonych zmianach, uruchom:
```bash
pytest
```
