# Lista Zadań (Task List)

Plik służy do śledzenia postępów w zaplanowanych zadaniach programistycznych i konfiguracyjnych.
Używaj konwencji: `[ ]` do zrobienia, `[/]` w trakcie, `[x]` ukończone.

## Aktywne Zadania
- [x] Opracowanie i wdrożenie zautomatyzowanej architektury komunikacji agentowej (Handoffs & State Protocols w `AGENTS.md`).
- [x] Rozwój CLI: Usunięcie błędów renderowania, wprowadzenie pętli REPL (Infinite Scrolling) bez utraty danych.
- [x] Kuloodporność modelu (Solid-State AI): Dedukcja narzędzi The Warden i ekstrakcja promptów psychologicznych.
- [x] Wdrożenie funkcji narzędziowych dla Regis: Odczytywanie Czasu (`get_current_time`) oraz Pogody z sieci (`get_weather`).
- [x] Uproszczenie architektury i wdrożenie Zasady Apple: rezygnacja z profili na rzecz sztywnych warstw (Recepcjonista i Szef).
- [x] Stabilizacja Tool Callingu: Wdrożenie Chain of Thought w Fazi Myśli i adaptacja architektoniczna pod modele 7B i 14B (afirmatywny prompt, array support).
- [x] Zaprojektowanie i wdrożenie Pamięci Długoterminowej (Notatnika) dla agenta LLM.
- [x] Wdrożenie testowej integracji Gemini API (silnik `GeminiEngine`) obsługującej pobieranie modeli z publicznego API i obsługę restrykcyjnego formatu function-callingu Google.
- [x] Przejście na modele `qwen2.5:7b-instruct` i `qwen2.5:14b-instruct` (warianty Instruct lepsze do tool callingu i instruction following).
- [x] Usunięcie Two-Pass Generation — uproszczenie do single-pass ReAct z jedną stałą temperaturą.
- [x] Przebudowa promptów systemowych na format wypunktowanych list (lepsze instruction following dla Instruct).
- [x] Wdrożenie wewnętrznego monologu `<thought>...</thought>` z real-time streamingiem w CLI.
- [x] Refaktoryzacja pętli konwersacyjnej ReAct na architekturę Event-Driven ze StreamingTokenParserem.
- [ ] Stworzenie usługi telemetrycznej "Handoff" do przerzucania zadań z Maliny na PC (Boss Mode).
- [ ] Integracja systemu WakeWord (oczekiwanie na dyskusję nt. wyboru narzędzia).
- [ ] Integracja systemu Speech-To-Text.
