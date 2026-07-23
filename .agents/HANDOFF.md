# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Deployment, Konfiguracja i Wdrożenie Fallbacku)

### Co zostało zrobione

W ramach tej sesji zrealizowano ostateczne wdrożenie nowej architektury systemu (Kontroler + Worker) na sprzęcie docelowym (RPi5 + Desktop PC). Przeprowadzono testy end-to-end, debugowanie sieciowe i rozwiązano problemy komunikacyjne. Zwieńczeniem prac było pełne skonfigurowanie mechanizmu "graceful degradation" (fallback).

**Główne zadania i poprawki:**
- **Wdrożenie na RPi5**: Zaktualizowano kod na Malince przez SSH (`pip install -e .`), utworzono usługę systemd `regis.service` dla Kontrolera.
- **Konfiguracja adresacji**: W `settings.json` na obu urządzeniach zaktualizowano poprawne IP dla `controller_url` oraz `worker_host`.
- **Naprawa komunikacji (Zapora)**: Rozwiązano problem braku połączenia na linii RPi -> PC, dodając regułę Inbound w Windows Firewall dla portu `8001`.
- **Wdrożenie mechanizmu Fallback (RPi jako Worker)**: Stworzono i zainstalowano nową usługę systemową na RPi: `regis-worker.service`. RPi uruchamia na sobie w tle lekki węzeł (model 1.5B, tier `butler`). Gdy desktop PC zostanie odłączony lub zamknie aplikację Workera, Kontroler automatycznie i błyskawicznie przerzuca ruch z niedostępnego `regis` na obecnego zawsze w tle `butler`.
- **Testowanie End-to-End**: Przetestowano strumieniowanie czatu (SSE), rejestrację narzędzi (Tool Calling) po obu stronach sieci i potwierdzono poprawną propagację logów i zapytań. System w całości działa.

**Nowe/Zmodyfikowane pliki:**
- `data/settings.json` na obu maszynach (prawidłowe URL i Hosty).
- `scripts/regis.service` na RPi5 (uruchamia Kontroler: `apps.controller.main:app` na 0.0.0.0:8000).
- `scripts/regis-worker.service` na RPi5 (uruchamia Fallback Worker: `apps.worker.server:app` na 127.0.0.1:8001).

### Stan testów

Kod źródłowy nie został zmieniony, testy logiczne pozostają w stanie PASSED. Testy na produkcji (end-to-end flow sieciowy i LLM z Ollamą) zakończyły się pełnym sukcesem.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Daemon RPi5 (FastAPI router) + Rejestr Węzłów + Rejestr Satelit + Tool Proxy + SCF
├── worker/
│   ├── node.py          ← WorkerNode (klasa) + start() → uruchamia server.py
│   └── server.py        ← FastAPI app Węzła Roboczego
├── satellite/           ← w budowie
└── terminal/            ← działa; rejestruje się jako Satelita w trybie remote
core/
├── remote_tools_registry.py
├── remote_client.py
├── tools_registry.py
├── config.py
└── schemas.py
```

---

## Jak uruchomić

### 1. Na Raspberry Pi 5 (Ciągła praca w tle)
Obie usługi startują automatycznie wraz ze sprzętem:
- `regis.service` (Kontroler - port 8000)
- `regis-worker.service` (Węzeł Awaryjny "Butler" - port 8001)

### 2. Na Desktop PC (Inteligentny Węzeł Roboczy i Terminal)
W pierwszej kolejności musi zostać uruchomiona **Ollama** w tle. Następnie w folderze projektu:
```bash
# Główny węzeł dla modelu 14B
.venv\Scripts\regis-worker

# Komunikacja z systemem
.venv\Scripts\regis-terminal
```

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Cała restrukturyzacja architektoniczna jest już skończona. System jest w pełni rozproszony, działający i stabilny na środowisku docelowym użytkownika.
3. Kontynuuj w oparciu o aktualne priorytety użytkownika z `TASKS.md`:
   - Integracja WakeWord i mikrofonów
   - Finalizacja STT / TTS w Satelicie
   - Projekt Nowej Pamięci Długoterminowej
