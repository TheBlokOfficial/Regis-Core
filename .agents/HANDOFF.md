# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Przeniesienie hardcode'owanych IP do konfiguracji)

### Co zostało zrobione

Zrealizowano drugi punkt z długu architektonicznego: **Przeniesienie hardcode'owanych adresów IP do `data/settings.json`**. Zmiana eliminuje na stałe wpisane w kodzie adresy serwera API oraz Ollamy, co pozwala na łatwiejszą zmianę topologii sieci bez modyfikacji kodu.

**Zaktualizowane pliki:**
- `data/settings.json` — dodano pole `"ollama_url": "http://192.168.0.119:11434"`.
- `core/config.py` — uwzględniono `ollama_url` w `default_settings` (jako lokalny fallback `127.0.0.1`).
- `core/llm_engine.py` — dynamiczne pobieranie adresu Ollamy z ustawień w każdej niezbędnej metodzie, usunięto statyczne zmienne globalne.
- `core/remote_client.py` — zmiana domyślnego IP w sygnaturze konstruktora na adres lokalny `127.0.0.1`.
- `apps/terminal/main.py` — aplikacja konsolowa zaczytuje `server_url` z `settings.json` przy inicjalizacji `RemoteClient`.

### Stan testów
`pytest tests/ -v` — 5/5 PASSED.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Aktywny daemon RPi5 (FastAPI router)
├── worker/              ← Węzeł Roboczy (LLM + STT, bez HTTP)
├── satellite/           ← w budowie
└── terminal/            ← działa, bez zmian
core/                    ← Logika (bez hardcode'ów IP RPi5)
data/                    ← Pliki konfiguracyjne (z adresami IP w settings.json)
```

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[DONE]** Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy
2. **[DONE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json`
3. **[KOLEJNE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[ARCH]** Implementacja Rejestru Encji (Satelity i Węzły rejestrują się w Kontrolerze z metadanymi) — tu WorkerNode staje się osobnym procesem HTTP
5. **[ARCH]** Implementacja Spatial Context Filtering

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Kod po tej sesji jest czystszy o konfigurację IP — adresy usług znajdują się w `data/settings.json`.
3. Następne zadanie z backlogu to: **Dodanie `pyproject.toml` z grupami opcjonalnych zależności (extras)**. Trzeba przejść z obecnego modelu wywoływania skryptów Pythonem na model pakietów (np. `pip install .[controller]`). Opis docelowego modelu dystrybucji znajduje się w sekcji "Model Dystrybucji" w `docs/ONBOARDING.md`.
4. Przed przejściem do tworzenia `pyproject.toml` koniecznie zaplanuj zmiany i uzgodnij je z użytkownikiem, gdyż wpływają na sposób instalacji i deploymentu (np. na RPi5).
