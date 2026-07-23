# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Dodanie `pyproject.toml` z extras)

### Co zostało zrobione

Zrealizowano trzeci punkt z długu architektonicznego: **Dodanie `pyproject.toml` z grupami opcjonalnych zależności (extras)**. Projekt przeszedł z modelu pojedynczego `requirements.txt` na model instalowalnego pakietu `regis-core`.

**Nowe i zaktualizowane pliki:**
- `pyproject.toml` — nowy plik; definiuje pakiet `regis-core`, `requires-python = ">=3.11"`, 5 grup extras: `[controller]`, `[worker]`, `[satellite]`, `[dev]`, `[all]` oraz CLI entry pointy.
- `requirements.txt` — zastąpiony jedną linią `-e .[all]`; zachowuje pełną kompatybilność wsteczną.
- `apps/controller/main.py` — dodano funkcję `start()` jako CLI entry point dla `regis-controller`.
- `apps/worker/node.py` — dodano funkcję `start()` jako CLI entry point dla `regis-worker` (placeholder do czasu Rejestru Encji).
- `apps/terminal/main.py` — funkcja `main()` już istniała; bez zmian.

**Podział zależności (finalna decyzja):**
- `[dev]` zawiera: `rich`, `questionary`, `pytest` — terminal CLI jest narzędziem deweloperskim, nie osobną warstwą.
- `deploy_to_pi.bat` — bez zmian, odkładany do etapu Rejestru Encji.

### Stan testów
`pytest tests/ -v` — 5/5 PASSED.
`pip install -e .[all]` — instalacja przebiegła pomyślnie.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Aktywny daemon RPi5 (FastAPI router) + entry point start()
├── worker/              ← Węzeł Roboczy (LLM + STT, bez HTTP) + entry point start()
├── satellite/           ← w budowie
└── terminal/            ← działa, bez zmian
core/                    ← Logika (bez hardcode'ów IP)
data/                    ← Pliki konfiguracyjne (adresy IP w settings.json)
pyproject.toml           ← NOWY: definicja pakietu + extras + CLI entry pointy
requirements.txt         ← Zaktualizowany: deleguje do pyproject.toml (-e .[all])
```

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[DONE]** Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy
2. **[DONE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json`
3. **[DONE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[KOLEJNE]** Implementacja Rejestru Encji (Satelity i Węzły rejestrują się w Kontrolerze z metadanymi) — tu WorkerNode staje się osobnym procesem HTTP
5. **[ARCH]** Implementacja Spatial Context Filtering

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Projekt ma teraz `pyproject.toml`. Instalacja środowiska: `pip install -e ".[all]"` lub `pip install -r requirements.txt` (oba działają).
3. Następne zadanie z backlogu to: **Implementacja Rejestru Encji**. Jest to duża zmiana architektoniczna — WorkerNode musi stać się osobnym procesem HTTP, który rejestruje się w Kontrolerze. Opis w `docs/MANIFEST.md` (sekcja 4) i `docs/ONBOARDING.md` (uwaga architektoniczna w sekcji `apps/controller/`).
4. Przed przejściem do implementacji Rejestru Encji **koniecznie zaplanuj zmiany i uzgodnij z użytkownikiem** — to fundamentalna zmiana modelu komunikacji między komponentami.
