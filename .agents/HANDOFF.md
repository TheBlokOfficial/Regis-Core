# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Porządki Architektoniczne, Portable App & CLI)

### Co zostało zrobione

Podczas tej sesji skupiliśmy się na potężnym sprzątaniu długu architektonicznego wynikającego z nadmiaru folderów i nieustrukturyzowanych plików w głównym katalogu projektu:
1. **Wypłaszczenie Monorepo (No-Apps):** Całkowicie zlikwidowano sztuczny katalog zbiorczy `apps/`. Wszystkie aplikacje lądują teraz w katalogu głównym.
2. **Standaryzacja Nazewnictwa (regis_):** Foldery aplikacyjne otrzymały ujednolicone przedrostki (np. `regis_controller`, `regis_satellite`), co z automatu ładnie grupuje je alfabetycznie i oddziela wizualnie od rdzenia (`core/`). Zaktualizowano wszystkie importy w kodzie na nowy standard.
3. **Architektura Windows Portable App:** PyInstaller ładuje teraz paczki używając trybu folderowego (`--onedir`). Kompilator sam wypluwa gotowe struktury `Regis-Satellite\system\` (gdzie chowane są pliki .exe) oraz `Regis-Satellite\data\` dla plików `.json`. Użytkownik widzi tylko pojedynczy, estetyczny plik `Uruchom.bat` (wyposażony w mechanizm zapobiegający od razu zamykaniu okna w razie błędu - `Smart Pause`).
4. **Stworzenie dedykowanego menedżera `regis_cli`:** Pozbyliśmy się brzydkich, potężnych skryptów `make-windows.bat` i `make-raspberry.bat`. Powstał 5. moduł o nazwie `regis_cli` (z wykorzystaniem bibliotek `rich` i `questionary`). Działa on jako potężny, pythonowy silnik dla interaktywnego CLI w Terminalu. W głównym folderze znajduje się tylko minimalny aktywator `regis.bat`.
5. **Krytyczny fix UDP:** Serwer automatycznego wykrywania (Auto-Discovery) nie rzuca już logów do na sztywno wpisanych linuksowych ścieżek `/home/theblok/`, ale korzysta z biblioteki `logging`. Usunięto błędy dla środowiska Windows oraz objęto serwer pętlą samo-reanimującą na wypadek błędu bindowania gniazda.
6. **"Ukrywanie" w Windows:** Ponieważ docelowe przeniesienie kodu do struktury `src/` zostało przesunięte na kolejną sesję, doraźnie nadano atrybuty Windows Hidden (`attrib +h`) zbędnym folderom konfiguracyjnym w głównym widoku, co zapewniło użytkownikowi natychmiastowy "Zen Mode".

### Stan testów

Kompilator przeszedł testy składni gładko. Struktura wygenerowanych projektów CLI i dystrybucji Windowsowej jest poprawna. Oczekuje się jedynie przetestowania `regis.bat` ze względu na to, że moduł zbudowano pod koniec sesji.

---

## Aktualny Stan Kodu

```text
(Główny folder projektu — w dużej części sztucznie ukryty przed widokiem z zewnątrz)
├── core/
├── integrations/
├── regis_cli/             ← [NOWY] Piąty moduł zarządzający projektem
├── regis_controller/
├── regis_satellite/
├── regis_terminal/
├── regis_worker/
├── tests/
├── deploy_to_pi.bat       ← Obsolete? Przejęty przez regis_cli. Do usunięcia w next patch.
├── regis.bat              ← [NOWY] Jedyny plik wejściowy dla CLI zarządzającego
├── pyproject.toml         ← Wskazuje zaktualizowane importy `regis_`
└── ... 
```

---

## Kroki Startowe dla Następnego Agenta

1. **Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).**
2. **UWAGA - PRIORYTET NR 1:** Użytkownik zatwierdził przeniesienie struktury Monorepo na profesjonalny, pythonowy **"src layout"** (katalog `src/` wchłaniający `core/` oraz `regis_...`). Jest to absolutnie pierwsze zadanie, którym musisz się zająć. Pamiętaj, aby "odkryć" ukryte wcześniej pliki w root (usunięcie atrybutu Hidden), zmienić ścieżki w `pyproject.toml`, zaktualizować flagi PyInstallera w `regis_cli/builders.py` oraz testy w `pytest.ini`. Twój poprzednik przygotował gotowy `implementation_plan.md` pod to wdrożenie w plikach systemowych (.gemini), ale użytkownik nakazał realizację dopiero Tobie. Przeczytaj `implementation_plan.md` i przystąp do działania.
3. Potem możesz zająć się faktycznym rozwojem możliwości AI systemu Regis (Long-Term Memory).
