# Lista Zadań (Task List)

Plik służy do śledzenia postępów w zaplanowanych zadaniach programistycznych i konfiguracyjnych.
Używaj konwencji: `[ ]` do zrobienia, `[/]` w trakcie, `[x]` ukończone.

## Aktywne Zadania
- [x] Naprawa regresji Tool Callingu: Przywrócenie Sandwichingu i Stop Tokens w `core/llm_engine.py` dla modeli Qwen 7B.
- [ ] (Wstrzymane) Wdrożenie "Checklisty Zadań" w monologach modeli, by poprawić zdolności analityczne na wzór Scratchpadu.
- [x] Opracowanie i wdrożenie zautomatyzowanej architektury komunikacji agentowej (Handoffs & State Protocols w `AGENTS.md`).
- [x] Rozwój CLI: Usunięcie błędów renderowania, wprowadzenie pętli REPL (Infinite Scrolling) bez utraty danych.
- [x] Kuloodporność modelu (Solid-State AI): Dedukcja narzędzi The Warden i ekstrakcja promptów psychologicznych.
- [x] Wdrożenie funkcji narzędziowych dla Regis: Odczytywanie Czasu (`get_current_time`) oraz Pogody z sieci (`get_weather`).
- [x] Uproszczenie architektury i wdrożenie Zasady Apple: rezygnacja z profili na rzecz sztywnych warstw (Recepcjonista i Szef).
- [x] Stabilizacja Tool Callingu: Wdrożenie Chain of Thought w Fazi Myśli i adaptacja architektoniczna pod modele 7B i 14B (afirmatywny prompt, array support).
- [x] Całkowite wycięcie starego systemu Notatnika (Pamięć Długoterminowa / Brudnopis) w celu zastąpienia go nowym rozwiązaniem.
- [ ] Zaprojektowanie i wdrożenie nowej Pamięci Długoterminowej (np. wektorowej).
- [x] Wdrożenie testowej integracji Gemini API (silnik `GeminiEngine`) obsługującej pobieranie modeli z publicznego API i obsługę restrykcyjnego formatu function-callingu Google.
- [x] Przejście na modele `qwen2.5:7b-instruct` i `qwen2.5:14b-instruct` (warianty Instruct lepsze do tool callingu i instruction following).
- [x] Usunięcie Two-Pass Generation — uproszczenie do single-pass ReAct z jedną stałą temperaturą.
- [x] Przebudowa promptów systemowych na format wypunktowanych list (lepsze instruction following dla Instruct).
- [x] Wdrożenie wewnętrznego monologu `<thought>...</thought>` z real-time streamingiem w CLI.
- [x] Refaktoryzacja pętli konwersacyjnej ReAct na architekturę Event-Driven ze StreamingTokenParserem.
- [x] Zaawansowany Prompt Engineering: Wdrożenie checklist, pętli self-correction i 3-warstwowej ochrony przed halucynacjami Parallel Tool Calling (w tym Prompt Anchoring) dla Qwen 2.5.
- [x] Stabilizacja logiki konsolidacji pamięci: Rozwiązanie State-History Conflict poprzez wzorzec Atomic Actions oraz całkowite zlikwidowanie halucynacji Qwen 2.5 poprzez Positive Framing.
- [x] Refaktoryzacja architektury (Droga A): Usunięcie natywnego function-callingu Ollamy, usunięcie systemu biurka, kondensacja historii do pełnych tur.
- [x] Konfiguracja środowiska sprzętowego na Raspberry Pi 5 (OS, PCIe Gen 3, Ollama).
- [x] Zmiana architektury Lokaja ze ślamazarnego modelu 7B na błyskawiczny 3B.
- [x] Przeniesienie skryptów Pythona (Regis-Core) fizycznie na Raspberry Pi 5 jako natywna usługa systemowa.
- [x] Szlifowanie promptów dla modelu 3B (ewaluacja zejścia do modelu 1.5B).
- [x] Implementacja Wirtualnych Grup (virtual_groups.json).
- [x] Przebudowa kodu na architekturę Monorepo (`core/`, `apps/`, `integrations/`).
- [x] Wdrożenie mechanizmu "Structured Outputs" (JSON Schema) dla modelu 1.5B (Butler).
- [x] Konfiguracja Raspberry Pi 5 jako dysku sieciowego NAS (Samba) wykorzystującego dysk NVMe.
- [ ] Integracja systemu WakeWord (oczekiwanie na paczki próbek użytkownika do modelu).
- [/] Integracja systemu Speech-To-Text i Text-To-Speech (Zrealizowano scentralizowane STT na serwerze API).
- [x] Restrukturyzacja dokumentacji projektu: stworzenie MANIFEST.md, ONBOARDING.md, AGENT_GUIDE.md i aktualizacja protokołów w AGENTS.md.
- [ ] [ARCH] Rozdzielenie `apps/server/main.py` na Kontroler i Węzeł Roboczy (krytyczny dług architektoniczny).
- [ ] [ARCH] Przeniesienie hardcode'owanych adresów IP do `data/settings.json`.
- [ ] [ARCH] Dodanie `pyproject.toml` z extras (`[controller]`, `[worker]`, `[satellite]`).
- [ ] [ARCH] Implementacja Rejestru Encji (Satelity i Węzły rejestrują się w Kontrolerze z metadanymi).
- [ ] [ARCH] Implementacja Spatial Context Filtering (filtrowanie urządzeń HA per pokój na podstawie metadanych Satelity).
