# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność (Sesja 2026-07-21)

* **[ZMIANA MODELI]** Przełączono wszystkie referencje modeli z `qwen2.5:7b` i `qwen2.5:14b` na warianty **Instruct**: `qwen2.5:7b-instruct` i `qwen2.5:14b-instruct`. Zmiana dotyczy: `main.py`, `ui/cli.py`, `test_stream.py`, `docs/ARCHITECTURE.md`. Modele zostały pobrane przez `ollama pull`.
* **[USUNIĘCIE TWO-PASS]** Całkowicie usunięto mechanizm "Two-Pass Generation" z `core/llm_engine.py`. Zamiast dwóch osobnych przebiegów (faza narzędziowa z temp=0.1 + faza odpowiedzi z temp=0.7), system ma teraz **jeden przebieg** z narzędziami zawsze dostępnymi i stałą temperaturą. Temperatura Regisa obniżona do **0.4** (z 0.7), Lokaja pozostała **0.1**. Usunięto parametr `tool_temperature` z konstruktora `LLMEngine`. Pętla ReAct działa nadal poprawnie.
* **[PROMPTY W WYPUNKTOWANEJ LIŚCIE]** Przepisano wszystkie 3 pliki promptów (`base_system.md`, `tier_butler.md`, `tier_regis.md`) z formy akapitów prozatorskich na wypunktowane listy, co znacznie poprawia instruction following w modelach Instruct.
* **[NAPRAWA PARSERA FALLBACK]** Naprawiono błąd w `_parse_fallback_tool_calls` w `llm_engine.py` - stary kod przerywał pętlę po znalezieniu pierwszego tool calla (`break`), ignorując kolejne. Teraz zbiera wszystkie tool calle i czyści z tekstu pełne JSON-y. Dodano czyszczenie znaczników `<tool_call>`, `</tool_call>` i artefaktu `icz`.
* **[REFAKTORYZACJA PĘTLI STREAMINGOWEJ (Event-Driven)]** Wyrzucono logikę parsowania tagów myśli z CLI i przeniesiono ją do modułu rdzenia `core/stream_parser.py` (StreamingTokenParser). System jest teraz w pełni event-driven:
  - Silnik używa prostych callbacks: `on_thought_token`, `on_content_token`, `on_tool_call`.
  - Parser w locie ucina potencjalne błędy Ollamy przy użyciu Stateful Buffer i Lookaheadu. Posiada zabezpieczenia wycinające ucięte śmieci po tagach. Na początku każdej iteracji ReAct robiony jest twardy reset parsera `reset_state()`.
  - Pętla ReAct posiada teraz twardy bezpiecznik `max_iterations = 15`, chroniący przed uwięzieniem systemu w halucynacji LLM-a.
* **[ZABEZPIECZENIA W UI (Rich)]** W `ui/cli.py` użyto twardego flagowania `markup=False`, by model nie rzucał błędu MarkupError podczas emitowania myśli bogatych w nawiasy kwadratowe. Interfejs inteligentnie wstrzymuje druk linii `Regis: `, dopóki z parsera nie wpadnie pierwszy prawdziwie "nie-biały" znak preambuły (likwidacja "pustych" sierocych logów).
* **[ULEPSZONY FALLBACK PARSER]** Fallback parser uodporniono na "brudne" wstrzykiwanie cudzysłowów podczas tekstu - wykorzystano fuzzy repair na bazie maszyny stosowej wyłapującej stringi i klamry.

## Obecny Stan Projektu

* System posiada absolutnie pancerną pętlę ReAct, bezpieczną na zerwania sieci (w tym cofanie historii pytań) i parsowania szczątkowe.
* Fallback parser łata wadliwe outputy Qwena bez zawieszania pętli.
* Terminal został zoptymalizowany.
* Prompty systemowe zachowują formę wypunktowaną, ale aktualny model jest nadmiernie wylewny pomiędzy jednym a drugim użyciem narzędzia w pętli. 

## Następne Kroki (Next Steps)

1. **Prompt Engineering:** Niezbędne jest drastyczne dostrojenie promptów. Aktualnie model ma tendencję do "gadania" między fazami poszukiwania informacji (np. "Sprawdzę co u ciebie"). Należy w instrukcjach systemowych `tier_regis.md` / `base_system.md` wymusić całkowity, żelazny zakaz zwracania tekstu podczas iteracji, ograniczając monolog WYŁĄCZNIE do wnętrza tagów `<thought>`.
2. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do modelu 14b, jeśli dostępne są zasoby VRAM.
2. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).
3. **Przetestowanie monologu `<thought>` live** — warto obserwować czy model 7B (Lokaj) też solidnie używa tagów, czy trzeba mu mocniej to wymusić w `tier_butler.md`.

## Wiedza i Przemyślenia (Gotchas)

* Pamiętaj o zachowaniu ascetycznego UX. Unikaj bogatych, krzykliwych kolorów.
* Modele Instruct używają natywnych znaczników `<tool_call>` / `</tool_call>` podczas generowania. Parser CLI i fallback parser w silniku muszą je filtrować — jest to już wdrożone.
* Artefakt `icz` pojawia się jako resztka po Qwen Instruct podczas streamowania tool-callów. Jest filtrowany w `stream_update`.
* Temperatura 0.4 dla Regisa (14B Instruct) daje dobre wyniki — modele Instruct nie potrzebują 0.7 do naturalnych odpowiedzi.
* Małe modele 7B mogą nie pisać monologu `<thought>` tak chętnie jak 14B — jeśli nie, wzmocnij instrukcję w `tier_butler.md`.
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
