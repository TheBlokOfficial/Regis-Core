# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Przejście na Architekturę 'src' layout)

### Co zostało zrobione

Podczas tej sesji sfinalizowano wdrożenie "src layout", co stanowiło absolutny priorytet:
1. **Wdrożenie src layout:** Utworzono katalog `src/` w głównym katalogu projektu i przeniesiono do niego wszystkie pakiety źródłowe (`core/`, `integrations/`, `regis_cli/`, `regis_controller/`, `regis_satellite/`, `regis_terminal/`, `regis_worker/`).
2. **Czyszczenie atrybutów:** Zgodnie z nową architekturą, pliki konfiguracyjne w katalogu głównym projektu przestały być ukrywane (zdjęto atrybut Hidden).
3. **Aktualizacja Konfiguracji:** Dostosowano pliki konfiguracyjne do nowej ścieżki pakietów: `pyproject.toml` (wskazuje teraz na `where = ["src"]`), `pytest.ini` (`pythonpath = src`), oraz startowy skrypt `regis.bat` (aktualizacja `PYTHONPATH`).
4. **Aktualizacja PyInstallera:** W module `regis_cli/builders.py` podmieniono parametry kompilacji (`--paths src` oraz ścieżki do plików `main.py` czy `node.py`).

### Stan testów

Paczki `.whl` budują się prawidłowo z nową strukturą. Testy `pytest` wykonują się bez problemów z odnalezieniem ścieżek importu (26 testów przeszło z sukcesem, wystąpił 1 błąd w `test_pi_discovery.py` ze względu na błędnie zadeklarowaną przestarzałą metodę testu, który jest niezwiązany ze zmianą struktury i nie był dotykany).

---

## Aktualny Stan Kodu

```text
(Główny folder projektu — w pełni widoczny, zachowujący czysty podział na kod i konfigurację)
├── src/                   ← [NOWY] Cały kod źródłowy projektu
│   ├── core/
│   ├── integrations/
│   ├── regis_cli/
│   ├── regis_controller/
│   ├── regis_satellite/
│   ├── regis_terminal/
│   └── regis_worker/
├── tests/
├── pyproject.toml         ← Zaktualizowany
├── pytest.ini             ← Zaktualizowany
├── regis.bat              ← Zaktualizowany
└── ...
```

---

## Kroki Startowe dla Następnego Agenta

1. **Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).**
2. Architektura "src layout" została pomyślnie zaimplementowana i działa. Przejdź do głównego zadania.
3. Sprawdź `TASKS.md` — najważniejszym niezrealizowanym jeszcze zadaniem jest **zaprojektowanie i wdrożenie nowej Pamięci Długoterminowej (Long-Term Memory)** (np. wektorowej) dla systemu Regis. Przed rozpoczęciem, zapoznaj się z problematyką.
