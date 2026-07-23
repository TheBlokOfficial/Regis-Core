# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Rozdzielenie Controller / Worker)

### Co zostało zrobione

Zrealizowano krytyczny dług architektoniczny: **rozdzielenie `apps/server/main.py`** na Kontroler i Węzeł Roboczy. Żadna logika biznesowa nie została zmieniona — to było czyste, strukturalne cięcie kodu.

**Nowe pliki:**
- `apps/controller/__init__.py` — pusty init pakietu
- `apps/controller/main.py` — FastAPI daemon (dawne `apps/server/main.py`). Inicjalizuje `HomeAssistantClient`, `ToolsRegistry` i `WorkerNode`. Deleguje inferencję do WorkerNode. Nie importuje już LLMEngine ani STTEngine bezpośrednio.
- `apps/worker/__init__.py` — pusty init pakietu
- `apps/worker/node.py` — klasa `WorkerNode`. Enkapsuluje `LLMEngine` + `STTEngine`. Interfejs: `handle_chat()`, `handle_audio()`, `clear_history()`. Nie zawiera żadnej logiki HTTP.

**Usunięte katalogi:**
- `apps/server/` — zastąpiony przez `apps/controller/`
- `apps/boss_node/` — zastąpiony przez `apps/worker/`

**Zaktualizowane pliki:**
- `run_server.bat` — zmiana modułu z `apps.server.main` na `apps.controller.main`
- `scripts/regis.service` — zmiana `ExecStart` na `apps.controller.main:app`
- `docs/ONBOARDING.md` — opisy katalogów zsynchronizowane z nową strukturą

### Stan testów
`pytest tests/ -v` — 5/5 PASSED (bez zmian w logice `core/`)

### Kluczowe decyzje podjęte w tej sesji

1. **WorkerNode importowany bezpośrednio przez Kontroler** — separacja procesów przez API HTTP to następny krok (Rejestr Encji). W docstringu `WorkerNode` i `controller/main.py` są komentarze architektoniczne wskazujące ten kierunek.
2. **Nazwy semantycznie poprawne**: `controller` (nie `server`), `worker` (nie `boss_node`).
3. **Błąd STT obsługiwany inaczej:** w starym kodzie serwer wysyłał `{"type": "error"}` bezpośrednio w wątku. W nowym `WorkerNode.handle_audio()` zwraca string z komunikatem błędu, a kontroler sprawdza go i emituje odpowiednie zdarzenie SSE — zachowanie zewnętrzne identyczne.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Aktywny daemon RPi5 (FastAPI router)
│   ├── __init__.py
│   └── main.py
├── worker/              ← Węzeł Roboczy (LLM + STT, bez HTTP)
│   ├── __init__.py
│   └── node.py
├── satellite/           ← w budowie
└── terminal/            ← działa, bez zmian
```

Deployment: `deploy_to_pi.bat` → SSH → `systemctl restart regis.service` → uruchamia `apps/controller/main.py`.

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[KRYTYCZNE → DONE]** ~~Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy~~
2. **[KOLEJNE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json` (lista w `docs/ONBOARDING.md`)
3. **[KOLEJNE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[ARCH]** Implementacja Rejestru Encji (Satelity i Węzły rejestrują się w Kontrolerze z metadanymi) — tu WorkerNode staje się osobnym procesem HTTP
5. **[ARCH]** Implementacja Spatial Context Filtering

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Kod po tej sesji jest podzielony — Kontroler (`apps/controller/`) i Węzeł Roboczy (`apps/worker/`) istnieją jako osobne pakiety ale jeszcze komunikują się przez import.
3. Następne zadanie z backlogu: przeniesienie hardcode'owanych adresów IP do `data/settings.json`. Lista miejsc do zmiany w `docs/ONBOARDING.md § Gdzie są na stałe wpisane adresy IP`.
4. NIE zaczynaj od Rejestru Encji bez dyskusji z użytkownikiem — to duże zadanie wymagające decyzji o protokole komunikacji HTTP między Controller a Worker.
