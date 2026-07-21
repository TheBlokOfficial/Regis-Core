# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność (Sesja 2026-07-21)

* **[ZMIANA MODELI]** Przełączono wszystkie referencje modeli z `qwen2.5:7b` i `qwen2.5:14b` na warianty **Instruct**: `qwen2.5:7b-instruct` i `qwen2.5:14b-instruct`. Zmiana dotyczy: `main.py`, `ui/cli.py`, `test_stream.py`, `docs/ARCHITECTURE.md`. Modele zostały pobrane przez `ollama pull`.
* **[USUNIĘCIE TWO-PASS]** Całkowicie usunięto mechanizm "Two-Pass Generation" z `core/llm_engine.py`. Zamiast dwóch osobnych przebiegów (faza narzędziowa z temp=0.1 + faza odpowiedzi z temp=0.7), system ma teraz **jeden przebieg** z narzędziami zawsze dostępnymi i stałą temperaturą. Temperatura Regisa obniżona do **0.4** (z 0.7), Lokaja pozostała **0.1**. Usunięto parametr `tool_temperature` z konstruktora `LLMEngine`. Pętla ReAct działa nadal poprawnie.
* **[PROMPTY W WYPUNKTOWANEJ LIŚCIE]** Przepisano wszystkie 3 pliki promptów (`base_system.md`, `tier_butler.md`, `tier_regis.md`) z formy akapitów prozatorskich na wypunktowane listy, co znacznie poprawia instruction following w modelach Instruct.
* **[NAPRAWA PARSERA FALLBACK]** Naprawiono błąd w `_parse_fallback_tool_calls` w `llm_engine.py` - stary kod przerywał pętlę po znalezieniu pierwszego tool calla (`break`), ignorując kolejne. Teraz zbiera wszystkie tool calle i czyści z tekstu pełne JSON-y. Dodano czyszczenie znaczników `<tool_call>`, `</tool_call>` i artefaktu `icz`.
* **[PRZEPROJEKTOWANIE CLI - STREAMING]** Całkowicie przepisano logikę streamowania w `ui/cli.py`. System ma teraz:
  - Maszynę stanów do real-time parsowania tagów `<thought>...</thought>` token po tokenie (sliding window buffer)
  - "Myśli agenta" wyświetlają się na bieżąco gdy model pisze wewnątrz `<thought>` 
  - Gdy model nie używa narzędzi: brak sekcji "Myśli agenta", odpowiedź bezpośrednio jako "Regis:"
  - Gdy model używa narzędzi: "Myśli agenta" → status narzędzia → "Regis:" w real-time (is_scratchpad=False)
  - `final_response_callback` stripuje tagi `<thought>` z finalnego tekstu
  - Bezpieczny parser klamer (zamiast regex) do czyszczenia JSON-ów ze scratchpada
* **[MONOLOG <thought>]** Dodano do `base_system.md` instrukcję nakazującą modelowi pisać wewnętrzny monolog w tagach `<thought>...</thought>` przed każdą akcją lub odpowiedzią.

## Obecny Stan Projektu

* System działa w architekturze **single-pass ReAct** bez Two-Pass Generation.
* Modele Instruct są pobrane i skonfigurowane.
* CLI poprawnie parsuje `<thought>` tagi w locie i wyświetla monolog w szarym kolorze.
* Fallback parser tool-callów jest naprawiony i obsługuje wiele narzędzi naraz.
* Prompty są w formacie wypunktowanej listy (lepsze instruction following dla Instruct).

## Następne Kroki (Next Steps)

1. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do modelu 14b, jeśli dostępne są zasoby VRAM.
2. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).
3. **Przetestowanie monologu `<thought>` live** — warto obserwować czy model 7B (Lokaj) też solidnie używa tagów, czy trzeba mu mocniej to wymusić w `tier_butler.md`.

## Wiedza i Przemyślenia (Gotchas)

* Pamiętaj o zachowaniu ascetycznego UX. Unikaj bogatych, krzykliwych kolorów.
* Modele Instruct używają natywnych znaczników `<tool_call>` / `</tool_call>` podczas generowania. Parser CLI i fallback parser w silniku muszą je filtrować — jest to już wdrożone.
* Artefakt `icz` pojawia się jako resztka po Qwen Instruct podczas streamowania tool-callów. Jest filtrowany w `stream_update`.
* Temperatura 0.4 dla Regisa (14B Instruct) daje dobre wyniki — modele Instruct nie potrzebują 0.7 do naturalnych odpowiedzi.
* Małe modele 7B mogą nie pisać monologu `<thought>` tak chętnie jak 14B — jeśli nie, wzmocnij instrukcję w `tier_butler.md`.
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
