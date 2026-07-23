# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Wdrożenie Auto-Discovery Zero-Conf)

### Co zostało zrobione

W tej sesji całkowicie usunęliśmy potrzebę wpisywania adresów IP oraz ręcznej konfiguracji połączeń pomiędzy aplikacjami brzegowymi a Kontrolerem:
- **Serwer Discovery (Kontroler):** Kontroler uruchamia w tle asynchroniczny serwer UDP na porcie 8002, który stale nasłuchuje komunikatów `DISCOVER_REGIS_CONTROLLER`. Gdy tylko usłyszy taki komunikat, odsyła odpowiedź zawierającą swój prawdziwy (wyliczony) adres HTTP oraz port.
- **Klient Auto-Discovery:** Terminal, Worker oraz Satelita mają zintegrowaną funkcję, która w przypadku ustawienia `server_url` (lub `controller_url`) na wartość `"auto"`, wykonuje broadcsat UDP (`<broadcast>`) na interfejsach sieciowych, czekając 3 sekundy na odpowiedź od Kontrolera. Po jej uzyskaniu system dynamicznie przypisuje prawidłowy IP do połączenia (np. `http://192.168.0.119:8000`).
- **Aktualizacja skryptów i prekonfiguracja:** Zaktualizowano `core/config.py`, by domyślnie wymuszać `"auto"` w kluczowych polach adresowych (dla bezobsługowego plug-and-play). Konfiguracja ta jest natywnie budowana w aplikacje `.exe` Windowsa za pomocą skryptu `scripts/build_windows.bat`. Dodatkowo, Kontroler potrafi dynamicznie wstrzykiwać swoje lokalne IP podczas odbierania żądań, aby uniknąć przekazywania stringu `"auto"` pomiędzy logiką wewnętrzną backendu.
- **Fix "Shadowingu":** Zdiagnozowano i usunięto problem podczas instalacji nowej wersji `.whl` na Raspberry Pi. Stare (nieskompilowane) foldery `apps` i `core` rezydujące w głównym katalogu przysłaniały zainstalowany pakiet z `.venv`. Skrypt wdrażający `deploy_to_pi.bat` automatycznie usuwa teraz te foldery przy updacie.

### Stan testów

Pomyślnie zwalidowano przesył UDP, usunięto błędy shadowingowe i z powodzeniem uruchomiono skompilowane wersje `regis-worker.exe` oraz `regis-satellite.exe`. Obie aplikacje wygenerowały domyślną konfigurację z flagą `"auto"`, wysłały pakiety po całej domowej sieci i niemalże natychmiast znalazły serwer Kontrolera na RPi, logując sukces i parując się z API.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Działa nasłuch UDP w tle. API obsługuje dynamiczne generowanie IP dla "auto"
├── worker/              
├── satellite/           
└── terminal/            
core/
├── config.py            ← controller_url i server_url są ustawione domyślnie na "auto"
└── discovery.py         ← [NOWY] Rozbudowany mechanizm serwera UDP i Klienta Zero-Conf
docs/
├── architectural_debt_report.md  
├── auto_discovery_rfc.md         
└── MANIFEST.md                   
scripts/
└── build_windows.bat             
deploy_to_pi.bat         ← Czyści stare pliki by zapobiec shadowingowi przed instalacją koła
```

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Spójrz do pliku `.agents/TASKS.md`, by zobaczyć aktualnie niezrealizowane zadania. Ostatnia wielka paczka strukturalno-konfiguracyjna ("Dług Architektoniczny") została właśnie w pełni zamknięta z rąk do rąk (zwieńczona systemem UDP Zero-Conf).
3. Możesz powrócić do rozwoju inteligentnego mózgu systemu lub rozpocząć wdrażanie integracji audio/wakeword (jeśli sprzęt jest gotowy). Zapytaj użytkownika co chciałby zrobić w pierwszej kolejności.
