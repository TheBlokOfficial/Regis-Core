# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Wdrożenie pyproject.toml i paczek extras)

### Co zostało zrobione

Zrealizowano trzeci punkt z długu architektonicznego: **Dodanie `pyproject.toml` z extras**. System został przełączony z tradycyjnego wywoływania skryptów Pythonem na instalowalny pakiet środowiska wirtualnego, z opcjonalnymi zależnościami dla poszczególnych komponentów.

**Zaktualizowane pliki:**
- `pyproject.toml` — stworzono plik z pięcioma grupami: `[controller]`, `[worker]`, `[satellite]`, `[dev]`, `[all]`. Skonfigurowano w nim punkty wejścia CLI.
- `requirements.txt` — przebudowano tak, by delegował zadanie do setuptools przez: `-e .[all]`, zachowując kompatybilność z `deploy_to_pi.bat`.
- `apps/controller/main.py` — dodano funkcję `start()` dla polecenia `regis-controller`.
- `apps/worker/node.py` — dodano podstawową obsługę funkcji `start()` dla polecenia `regis-worker`.
- `apps/terminal/main.py` — używany poprzez punkt wejścia `regis-terminal`.

### Stan testów
`pytest tests/ -v` — 5/5 PASSED.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Aktywny daemon RPi5 (FastAPI router, dostępny również z polecenia regis-controller)
├── worker/              ← Węzeł Roboczy (LLM + STT, bez HTTP)
├── satellite/           ← w budowie
└── terminal/            ← działa, dostępny również z polecenia regis-terminal
core/                    ← Logika (bez hardcode'ów IP RPi5)
data/                    ← Pliki konfiguracyjne (z adresami IP w settings.json)
```

---

## Dług Architektoniczny (kolejność ma znaczenie)

1. **[DONE]** Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy
2. **[DONE]** Przeniesienie hardcode'owanych adresów IP do `data/settings.json`
3. **[DONE]** Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`)
4. **[ARCH]** Implementacja Rejestru Encji (Satelity i Węzły rejestrują się w Kontrolerze z metadanymi) — tu WorkerNode staje się osobnym procesem HTTP
5. **[ARCH]** Implementacja Spatial Context Filtering

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Pamiętaj, że projekt jest teraz instalowalnym pakietem opartym o `pyproject.toml`.
3. Następne zadanie z backlogu to: **Implementacja Rejestru Encji**. Węzeł roboczy ma stać się zintegrowanym systemem z API, a Kontroler nie będzie go już importować lokalnie, a zarządzać nim i odpytywać.
4. Zmiana wymaga dokładnego planowania i konsultacji z użytkownikiem, zgodnie z procedurą w MANIFEST.md.
