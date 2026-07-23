# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Dług Architektoniczny Konfiguracji)

### Co zostało zrobione

W tej sesji rozwiązaliśmy poważny problem z długiem dystrybucyjnym (monolityczną dystrybucją plików konfiguracyjnych po urządzeniach brzegowych):
- **Profile konfiguracyjne:** Wprowadzono wsparcie dla pakietu `python-dotenv`. Od teraz architektura pozwala na stworzenie pliku `.env` na maszynie (zmienna `ACTIVE_PROFILE`), co steruje z którego pliku JSON docelowo ładuje się konfiguracja (np. `data/settings.rpi5-controller.json`). Eliminuje to problem przypadkowego nadpisywania ról między maszynami. Zmieniono stary `settings.json` na `settings.default.json`.
- **Dystrybucja "na czysto" na Raspberry:** Skrypt `deploy_to_pi.bat` korzysta od teraz z paczek dystrybucyjnych `.whl` budowanych za pomocą pypa buildera. Instalacja odbywa się przez `pip install` na Malince, co kompletnie ucina problem transferowania "śmieciowych" folderów z logami, konfiguracjami i środowiskiem wirtualnym na urządzenie docelowe. Działa z uprawnieniami systemd.
- **Kompilacja aplikacji pod Windows:** Powstał nowy skrypt `scripts/build_windows.bat` bazujący na PyInstaller. Generuje on niezależne paczki dla aplikacji (Worker, Satellite, Terminal), automatycznie przygotowując im foldery docelowe w `dist/` wraz ze wzorcowymi plikami środowiskowymi.
- **Zdefiniowanie długu Auto-Discovery:** Zaakceptowano uciążliwość związaną z ciągłym hardkodowaniem adresu IP Malinki. Został przygotowany obszerny dokument `docs/auto_discovery_rfc.md` z propozycją wykonania protokołu Zero-Conf (UDP Broadcast) i dołączeniem mechanizmu auto-generowania gotowych profili do skryptu `.bat`. Zadanie to jest gotowe do implementacji.

### Stan testów

Suita testowa `pytest` pomyślnie zwalidowała działanie modułu konfiguracji w obliczu zmienionych bibliotek (26 testów passed). Działanie instalatora na RPi (PIP) potwierdzono poprawką.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          
├── worker/              
├── satellite/           
└── terminal/            
core/
├── config.py            ← Zaktualizowany do pracy z os.getcwd() (wspiera PyInstaller i .whl)
└── ...
docs/
├── architectural_debt_report.md  
├── auto_discovery_rfc.md         ← Zarys protokołu UDP (Zero-Conf) do zrobienia w następnej kolejności
└── MANIFEST.md                   ← Uzupełniony o notatkę Zero-Conf
scripts/
└── build_windows.bat             ← Nowy skrypt budujący aplikacje brzegowe wraz z otoczką plików
```

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Wyśledź notatki w dokumencie `docs/auto_discovery_rfc.md`. 
3. Twoim zadaniem będzie wdrożenie własnego, natywnego protokołu UDP ucinającego potrzebę wpisywania adresów IP (Zero-Conf) i zaktualizowanie skryptu kompilującego tak, aby sam wklepywał JSON z gotowym wygenerowanym profilem zamiast `.env.example`. Masz już gotowy plan i zgodę użytkownika na działanie.
