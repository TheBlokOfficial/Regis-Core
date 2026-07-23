# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Implementacja Rejestru Encji)

### Co zostało zrobione

Zrealizowano czwarty punkt z długu architektonicznego: **Implementacja Rejestru Encji (Etap 3a)**.

WorkerNode przestał być importowany bezpośrednio przez Kontroler. Jest teraz **osobnym procesem HTTP** (FastAPI na porcie 8001), który rejestruje się w Kontrolerze przy starcie i wyrejestrowuje przy zamknięciu.

**Kluczowa decyzja architektoniczna (zrealizowana):**
- Rejestr węzłów: **in-memory dict** (poprawna semantyka — każdy węzeł rejestruje się przy starcie)
- Tool calling: **ReAct loop pozostaje w Worker** (bez refaktoryzacji LLMEngine)
- Worker nie ma bezpośredniego dostępu do HA — używa `RemoteToolsRegistry`, który proxy-uje wywołania do Kontrolera (`POST /v1/tools/execute`)
- Kontroler jest jedynym źródłem prawdy dla HA (zgodnie z MANIFEST.md §3.1)

**Nowe pliki:**
- `core/remote_tools_registry.py` — `RemoteToolsRegistry`: proxy narzędzi przez HTTP do Kontrolera. Implementuje ten sam interfejs co `ToolsRegistry` — podmiana jest transparentna dla `LLMEngine`.
- `apps/worker/server.py` — FastAPI app Węzła Roboczego. Lifespan: rejestracja/wyrejestrowanie. Endpointy: `/v1/health`, `/v1/chat/stream`, `/v1/chat/audio_stream`, `/v1/clear_history`.
- `tests/test_entity_registry.py` — 9 nowych testów (14/14 PASSED).

**Zaktualizowane pliki:**
- `core/schemas.py` — dodano `WorkerRegistrationRequest` i `ToolExecutionRequest` (modele Pydantic)
- `apps/worker/node.py` — `start()` teraz naprawdę uruchamia serwer HTTP przez uvicorn (port z settings)
- `apps/controller/main.py` — **duży refaktor**: usunięto import WorkerNode; dodano `worker_registry` (dict), `_pick_worker()` (wybór po tierze: prime > regis > butler); nowe endpointy: `/v1/workers/register`, `/v1/workers/{id}` DELETE, `/v1/workers` GET, `/v1/tools/execute`; endpointy czatu teraz proxy-ują SSE do Worker przez HTTP
- `data/settings.json` — dodano: `controller_url`, `worker_port` (8001), `worker_host`, `worker_id`

### Jak uruchomić (nowy model)

System wymaga teraz **dwóch osobnych procesów**:
```bash
# Terminal 1 — Kontroler (RPi5, port 8000)
regis-controller

# Terminal 2 — Węzeł Roboczy (RPi5 lub desktop, port 8001)
regis-worker
```

Worker rejestruje się w Kontrolerze automatycznie. Żadne inne zmiany nie są potrzebne — Terminal CLI i inne Satelity komunikują się nadal z Kontrolerem na porcie 8000.

### Stan testów

`pytest tests/ -v` — **14/14 PASSED** (5 starych + 9 nowych).

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Daemon RPi5 (FastAPI router) + Rejestr Węzłów + Tool Proxy
├── worker/
│   ├── node.py          ← WorkerNode (klasa) + start() → uruchamia server.py
│   └── server.py        ← NOWY: FastAPI app Węzła Roboczego
├── satellite/           ← w budowie
└── terminal/            ← działa, bez zmian
core/
├── remote_tools_registry.py  ← NOWY: proxy narzędzi → Kontroler
├── schemas.py           ← Zaktualizowany: dodane modele Pydantic rejestracji
└── ...
data/settings.json       ← Zaktualizowany: controller_url, worker_port, worker_host, worker_id
```

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[DONE]** Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy
2. **[DONE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json`
3. **[DONE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[DONE]** Implementacja Rejestru Encji — WorkerNode jako osobny proces HTTP, rejestracja w Kontrolerze
5. **[KOLEJNE]** Implementacja Spatial Context Filtering (filtrowanie urządzeń HA per pokój na podstawie metadanych Satelity)

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. System wymaga dwóch procesów: `regis-controller` (port 8000) i `regis-worker` (port 8001). Worker rejestruje się automatycznie.
3. Następne zadanie: **Implementacja Spatial Context Filtering** (punkt 5 długu). Wymaga:
   - Rozszerzenia modelu rejestracji Satelit (pole `room`)
   - Rozszerzenia endpointu `/v1/workers/register` lub nowego `/v1/satellites/register`
   - Modyfikacji logiki w Kontrolerze: gdy Satelita wysyła żądanie, Kontroler filtruje urządzenia HA do pokoju Satelity i buduje wąski kontekst dla modelu
   - Patrz MANIFEST.md §4 (Rejestr Encji / Metadane Satelity + Kontekst Przestrzenny)
4. Otwarta kwestia cross-room commands (nierozstrzygnięta — patrz MANIFEST.md §4): omówić z użytkownikiem przed implementacją.
