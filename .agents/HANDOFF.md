# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Implementacja Spatial Context Filtering)

### Co zostało zrobione

Zrealizowano piąty (ostatni) punkt z długu architektonicznego: **Spatial Context Filtering (SCF)**.

Gdy Satelita z konkretnego pokoju wysyła żądanie, Kontroler przekazuje kontekst pokoju przez cały stos aż do `ToolsRegistry`. Model widzi tylko urządzenia z pokoju Satelity zamiast pełnej listy HA. Filtrowanie jest transparentne dla modelu — nie wymaga zmian w `LLMEngine` ani promptach.

**Kluczowe decyzje architektoniczne (zrealizowane):**
- Mapowanie pokojów (`data/rooms.json`) wewnątrz Regis, niezależne od HA i od konkretnej integracji (MANIFEST.md §3.5)
- Cross-room: model może wywołać `get_devices(room="inny_pokoj")` — jawny parametr w schemacie narzędzia
- Fallback: brak `room` lub nieznany pokój → wszystkie urządzenia (model nie traci kontekstu)
- Terminal CLI rejestruje się jako Satelita przy starcie trybu `remote`; pokój konfigurowalny przez `terminal_room` w `settings.json` (domyślnie `null`)
- Tier `butler` i `regis` dostają filtrowany kontekst identycznie — filtrowanie na poziomie Kontrolera

**Nowe pliki:**
- `data/rooms.json` — mapowanie pokoju `moj_pokoj` → 7 lampek Yeelight Colorc
- `tests/test_spatial_context.py` — 12 testów (26/26 PASSED)

**Zaktualizowane pliki:**
- `core/config.py` — `load_rooms()`
- `core/schemas.py` — `SatelliteRegistrationRequest`, `room` w `ToolExecutionRequest`, `room` w schemacie narzędzia `get_devices`
- `core/tools_registry.py` — `rooms` w `__init__`, filtrowanie w `_get_devices(room=...)`
- `core/remote_tools_registry.py` — `room` w `__init__` i payloadzie `execute_tool`
- `core/remote_client.py` — `satellite_id` w `__init__` i payloadzie `generate_response`
- `apps/controller/main.py` — `satellite_registry` (in-memory dict), endpointy `/v1/satellites/register` i `/v1/satellites/{id}` DELETE, `rooms` w lifespan, propagacja `room` w proxy czatu
- `apps/worker/server.py` — `room` w `ChatRequest`, przekazanie do `RemoteToolsRegistry`
- `apps/terminal/main.py` — rejestracja Satelity przy starcie trybu `remote`, wyrejestrowanie przez `atexit`
- `data/settings.json` — pole `terminal_room: null`
- `docs/ONBOARDING.md` — sekcja `rooms.json`
- `docs/MANIFEST.md` — §3.5 (integracje jako pluggable layer, HA jako jedna z wielu)

### Stan testów

`pytest tests/ -v` — **26/26 PASSED** (14 starych + 12 nowych SCF).

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Daemon RPi5 (FastAPI router) + Rejestr Węzłów + Rejestr Satelit + Tool Proxy + SCF
├── worker/
│   ├── node.py          ← WorkerNode (klasa) + start() → uruchamia server.py
│   └── server.py        ← FastAPI app Węzła Roboczego (room w ChatRequest)
├── satellite/           ← w budowie
└── terminal/            ← działa; rejestruje się jako Satelita w trybie remote
core/
├── remote_tools_registry.py  ← proxy narzędzi → Kontroler (room w payloadzie)
├── remote_client.py          ← klient HTTP terminala (satellite_id w payloadzie)
├── tools_registry.py         ← filtrowanie per pokój z rooms.json
├── config.py                 ← load_rooms()
└── schemas.py                ← SatelliteRegistrationRequest, room w ToolExecutionRequest
data/
├── rooms.json           ← NOWY: moj_pokoj → 7 Yeelight Colorc
├── settings.json        ← terminal_room: null (zmień na nazwę pokoju by aktywować SCF)
└── ...
```

---

## Jak uruchomić

System wymaga dwóch osobnych procesów:
```bash
# Terminal 1 — Kontroler (RPi5, port 8000)
regis-controller

# Terminal 2 — Węzeł Roboczy (port 8001)
regis-worker
```

Terminal CLI (`regis` lub `python -m apps.terminal.main`) → tryb `remote` → rejestruje się automatycznie jako Satelita z `terminal_room` z settings.

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[DONE]** Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy
2. **[DONE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json`
3. **[DONE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[DONE]** Implementacja Rejestru Encji — WorkerNode jako osobny proces HTTP
5. **[DONE]** Implementacja Spatial Context Filtering

**Cały dług architektoniczny z listy HANDOFF jest spłacony.**

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. System wymaga dwóch procesów: `regis-controller` (port 8000) i `regis-worker` (port 8001). Worker rejestruje się automatycznie.
3. Uzupełnij `data/rooms.json` — dodaj pozostałe pokoje i ich urządzenia (aktualnie tylko `moj_pokoj` z 7 Yeelight Colorc).
4. Aby aktywować SCF dla terminala: ustaw `"terminal_room": "moj_pokoj"` w `data/settings.json`.
5. Kolejne priorytety (brak aktywnego zadania — do ustalenia z użytkownikiem):
   - Nowa Pamięć Długoterminowa (wektorowa)
   - Integracja WakeWord
   - Finalizacja STT/TTS
