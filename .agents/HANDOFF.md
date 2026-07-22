# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-22 — Restrukturyzacja Dokumentacji i Architektury)

Ta sesja była w 100% dokumentacyjna. Żaden plik kodu nie został zmieniony.

### Co zostało zrobione

**Nowe pliki dokumentacji:**
- `docs/MANIFEST.md` — Manifest projektu. Definiuje filozofię, cele, architekturę (Dynamiczny Dispatcher, Persona Contract, Dwa Tryby Pracy) i rozstrzygnięte decyzje projektowe. **Najważniejszy plik w projekcie — czytaj jako pierwszy.**
- `docs/ONBOARDING.md` — Mapa kodu. Opis każdego katalogu i pliku, przepływ danych od komendy użytkownika do zapalenia lampy, docelowy model dystrybucji (pyproject.toml + extras), aktualny workflow deweloperski.
- `docs/AGENT_GUIDE.md` — Przewodnik dla agentów AI. Hierarchia lektury, protokół eskalacji decyzji architektonicznych, ostrzeżenie o skażeniu kontekstu (context contamination), mechanizm Architectural Decision Handoff, prawa zapisu do dokumentów, lista decyzji już podjętych.

**Zaktualizowane pliki:**
- `.agents/AGENTS.md` — Procedura startowa teraz wymaga czytania MANIFEST.md i AGENT_GUIDE.md jako pierwszych plików (przed HANDOFF.md). Procedura zamykania sesji teraz nakazuje zastępowanie (nie dopisywanie) HANDOFF.md. Usunięto obowiązek aktualizacji walkthrough.md.

### Kluczowe decyzje architektoniczne podjęte w tej sesji

1. **Dynamiczny Dispatcher zamiast statycznego Lokaj/Szef** — RPi5 jest Kontrolerem i węzłem fallback. Desktopy rejestrują się jako węzły robocze. Najlepszy dostępny węzeł dostaje ruch. Bezszwowa migracja kontekstu przy zmianie węzła.

2. **Trzy niezależne procesy:** `regis-controller` (singleton na RPi5), `regis-worker` (instalowany na dowolnym urządzeniu), `regis-satellite` (VAD + I/O, możliwie głupi klient).

3. **Pipeline audio (rozstrzygnięte):** VAD na Satelicie → WakeWord na Węźle Roboczym (ESP32) lub lokalnie (desktop) → STT zawsze na Węźle Roboczym (standaryzacja jakości).

4. **Dwa tryby Regisa (rozstrzygnięta decyzja produktowa):** Model 1.5B = deterministyczny parser NLU (Baseline). Model 14B = pełny agent ReAct (Agent). Przepaść między nimi jest akceptowalna i wynika z naturalnej korelacji użycia.

5. **Rejestr Encji z metadanymi:** Satelity i Węzły rejestrują się w Kontrolerze z metadanymi (m.in. `room`). Kontroler używa `room` do Spatial Context Filtering — model dostaje tylko urządzenia z danego pokoju.

6. **Protokół eskalacji decyzji architektonicznych:** Gdy agent roboczy natrafi na decyzję architektoniczną po długiej sesji kodowania (skażony kontekst), wyekstrahowuje problem do HANDOFF.md w formacie `DECYZJA_ARCHITEKTONICZNA` i kończy sesję. Użytkownik otwiera świeżą rozmowę do dyskusji.

7. **Cykl życia dokumentów:** HANDOFF.md zastępowany co sesję (git przechowuje historię). TASKS.md rośnie, archiwizowany tylko na polecenie użytkownika.

### Dług Architektoniczny (do implementacji w przyszłości — kolejność ma znaczenie)

1. **[KRYTYCZNE] Rozdzielenie `apps/server/main.py`** na Kontroler i Węzeł Roboczy — to odblokuje wszystkie kolejne kroki.
2. **Przeniesienie hardcode'owanych adresów IP** do `data/settings.json` (lista w `docs/ONBOARDING.md`).
3. **Dodanie `pyproject.toml` z extras** (`[controller]`, `[worker]`, `[satellite]`).
4. **Komendy `install-service`** dla Satelity i Węzła Roboczego.

---

## Aktualny Stan Kodu

Kod jest niezmieniony względem poprzedniej sesji. Działa według opisów w HANDOFF.md z poprzedniej sesji (scentralizowane STT, pętla ReAct, Structured Outputs dla 1.5B). Dokumentacja jest teraz kompletna i aktualna.

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` — to nowy najważniejszy plik, zastępuje stary ARCHITECTURE.md jako główny autorytet.
2. Sprawdź czy zadanie dotyczy kodu czy architektury. Jeśli kodu — przeczytaj `docs/ONBOARDING.md` i działaj. Jeśli architektury — wróć do rozmowy z użytkownikiem.
3. Dług architektoniczny jest jasno opisany powyżej — nie zaczynaj od niego bez wyraźnego polecenia.
