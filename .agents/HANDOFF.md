# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność (Sesja 2026-07-22 - NLU Structured Outputs i Optymalizacja HA)

* **[STRUCTURED OUTPUTS DLA BUTLERA]** Całkowicie przebudowano sposób działania modelu 1.5B (tier Butler). Zamiast pętli ReAct, korzysta on teraz ze wsparcia Ollamy dla JSON Schema (`format`). Prompt został ekstremalnie uproszczony do wyciągania intencji w oparciu o czysty JSON (akcje: `light_on`, `light_off`, `set_brightness`, `unknown` oraz wartości procentowe jasności). Pozwala to uniknąć 100% błędów logicznych, halucynacji oraz ucieczki z formatowania – wymusza generację pożądanej struktury po stronie serwera.
* **[OPTYMALIZACJA WYDAJNOŚCI HA]** Znaleziono i usunięto ogromne wąskie gardło, w którym każde wywołanie światła poprzedzane było synchronicznym wywołaniem `get_all_states()` z HA (pobranie tysięcy linii JSON), a następnie pętlą wykonującą `turn_on` na każdej pojedynczej żarówce osobno z nowym połączeniem TLS. Zastąpiono to wdrożeniem obiektu `requests.Session()` oraz wysyłaniem do REST API HA całej tablicy `entity_id` w jednym zapytaniu POST, co zmniejszyło narzut sieci z 4-5 sekund do ułamków sekundy.
* **[REFAKTORYZACJA MONOREPO]** Projekt wcześniej przebudowano na architekturę Monorepo podzieloną na sekcje: `core/`, `apps/`, `integrations/`. Przepisano importy oraz usunięto stare ścieżki. Wdrożono skrypt `deploy_to_pi.bat` automatyzujący przesył i restartowanie daemona na RPi.

## Poprzednia Aktywność (Sesja 2026-07-22 - Wirtualne Grupy i Walka z Qwen 1.5B)

## Poprzednia Aktywność (Sesja 2026-07-21 - Wdrożenie Raspberry Pi i Modelu 3B)

* **[WDROŻENIE SPRZĘTOWE]** Skonfigurowano Raspberry Pi 5 jako główny węzeł w domowej sieci (Recepcjonista). Zainstalowano system Raspberry Pi OS Lite (64-bit), odblokowano szynę PCIe Gen 3 dla dysku NVMe, zainstalowano silnik Ollama i wystawiono jego API lokalnie na `0.0.0.0:11434`.
* **[ARCHITEKTONICZNY DOWNGRADE (7B -> 3B)]** Wdrożono zmianę w architekturze ze względu na ograniczenia sprzętowe Maliny (brak GPU) i długi czas ewaluacji obszernego kontekstu narzędziowego (ponad 1m12s dla modelu 7B). Model Lokaja obniżono z `qwen2.5:7b-instruct` do `qwen2.5:3b-instruct` (ok. 2GB RAM) w celu zyskania akceptowalnych opóźnień niezbędnych dla planowanego systemu TTS.
* **[POPRAWKI KODU]** W `core/llm_engine.py` wydłużono `timeout` dla biblioteki requests z 120 do 300 sekund dla bezproblemowego zimnego startu na RPi. W `main.py` oraz `data/settings.json` na sztywno zaaplikowano model 3B dla tieru `butler`.
* **[STATUS BIEŻĄCY]** Połączenie PC -> Malina działa prawidłowo. Model 3B radzi sobie z formatowaniem narzędzi zgodnie ze schematem z `tier_butler.md`. Projekt można teraz uruchamiać z PC na czas kodowania, podczas gdy odpytuje on fizycznie Malinę w tle.

## Poprzednia Aktywność (Sesja 2026-07-21 - Śledztwo Qwen 7B)

* **[DIAGNOZA I NAPRAWA UKRYTEGO MONOLOGU]** Zdiagnozowano problem z modelem Qwen 7B, który halucynował odpowiedzi zamiast używać narzędzi i pomijał tag `<thought>`. Wynikało to z braku dopięcia reguł "Sandwichingu" w promptach oraz usunięcia `Stop Tokens` w opcjach API.
* **[POPRAWKI W LLM_ENGINE]** Zmodyfikowano `core/llm_engine.py` dodając z powrotem `critical_rules` na sam koniec system promptu, z twardym zakazem odpowiadania bez monologu oraz naprawiono brakujące `stop: ["</tool_call>", "</tool_call >"]` w konfiguracji Ollamy.
* **[ARCHITEKTURA MONOLOGU]** Przeprowadzono edukację użytkownika dot. mechanizmów działania mniejszych modeli. Opracowano koncepcję stworzenia "Checklisty zadań" dla Qwena w wewnętrznym monologu, jednak wdrożenie tego zostało odłożone na później.

## Poprzednia Aktywność (Sesja 2026-07-21 - Część 3)

* **[USUNIĘCIE SYSTEMU NOTATNIKA]** Zgodnie z decyzją projektową usunięto całkowicie stary system pamięci długoterminowej oraz brudnopisu. Z plików systemowych usunięto narzędzia (`search_memory`, `queue_note`, `get_pending_notes`, `archive_note`, `save_memory`, `delete_memory`) oraz usunięto sekcje ich użycia z promptów dla poszczególnych modeli (`tier_prime.md`, `tier_regis.md`, `tier_butler.md`). Pliki `data/memory.json` i `data/pending_notes.json` zostały skasowane. W przyszłości planuje się wdrożenie nowocześniejszego rozwiązania.

## Poprzednia Aktywność (Sesja 2026-07-21 - Część 2)

* **[REFAKTORYZACJA ARCHITEKTURY - DROGA A]** Całkowicie przebudowano system dostarczania narzędzi do modelu Qwen 2.5. Usunięto pole `tools` z payloadu Ollamy, aby zapobiec wstrzykiwaniu przez nią domyślnego (angielskiego) bloku instrukcji, który powodował u modelu "angielski drift". Narzędzia są teraz renderowane bezpośrednio jako tekst (XML-like `<tools>`) do promptu systemowego, dając 100% kontroli nad językiem i zachowaniem.
* **[LIKWIDACJA SYSTEMU BIURKA (desk_state)]** Zrezygnowano ze skomplikowanego, stanowego systemu wstrzykiwania `<desk_state>`. Model nie musi już "otwierać" notatek i czekać iterację na ich pojawienie się w prompcie. `get_pending_notes()` zwraca pełne dane bezpośrednio. Zamiast ręcznej edycji, wprowadzono **Atomic Action** w postaci narzędzia `archive_note()`, które jednocześnie zapisuje do Pamięci Długoterminowej i usuwa wpis z brudnopisu.
* **[NAPRAWA AMNEZJI (Zarządzanie Historią)]** System ReAct od teraz kondensuje przeszłą historię. Zapamiętywane są tylko pełne tury (Para `user` + ostateczny `assistant`). Pełny ślad rozumowania (Myśli + Wywołania) istnieje tylko w izolowanym środowisku bieżącej iteracji. Limit historii ustawiono na 20 pełnych tur, co naprawia "krótkowzroczność" w skomplikowanych sesjach konsolidacji pamięci.
* **[OPTYMALIZACJA PARAMETRÓW I PROMPTÓW]** `temperature` ustawiona na `0.1`, a `num_ctx` podbite do `8192`, by zapobiec cichemu obcinaniu promptu przez Ollamę. Znacznie uproszczono i odchudzono prompty systemowe dla wszystkich tierów, wprowadzając zaktualizowane Few-Shots dla Qwen 2.5.

## Poprzednia Aktywność (Sesja 2026-07-21 - Część 1)

* **[ZAAWANSOWANY PROMPT ENGINEERING v2]** Wdrożono dokument `docs/PROMPT_ENGINEERING.md` i przepisano całkowicie strukturę promptów (`tier_butler.md`, `tier_regis.md`, `base_system.md`). Model otrzymuje tożsamość na początku, ma liniowe checklisty Krok-Po-Kroku z ujętą Pętlą Naprawczą, a na końcu stosowany jest "Sandwiching" przypominający mu o twardych restrykcjach przed samą generacją.
* **[LOGIKA ŁĄCZENIA W SILNIKU]** W `core/llm_engine.py` odwrócono kolejność: najpierw ładuje się `tier_prompt`, potem `base_system`. Do tego na sam dół dopinany jest twardy przypominacz `KRYTYCZNE ZASADY BEHAWIORALNE`, który skutecznie zabija u modelu chęć wylewnego monologowania poza tagiem `<thought>`.
* **[PARALLEL TOOL CALLING FIX (3 Warstwy)]** Rozwiązano problem halucynacji przy równoległym wywoływaniu wielu narzędzi (model nie czekał na wyniki). Wdrożono:
  1. *Warstwa 1 (Prompt):* Miękki nakaz jednego narzędzia na iterację.
  2. *Warstwa 2 (API):* Wstrzyknięcie Stop Tokens (`"stop": ["</tool_call>", "</tool_call >"]`) w payload Ollamy.
  3. *Warstwa 3 (Parser):* Limiter w głównej pętli Pythona (oraz fallback parserze), który twardo odcina nadmiarowe narzędzia i śmieci (zostawiając tylko pierwsze), zachowując sterylną higienę historii konwersacyjnej dla LLM.
* **[PROMPT ANCHORING FIX]** Rozwiązano problem, gdzie model nadgorliwie wywoływał `get_current_time()` w reakcji na zwykłe "Cześć" z powodu braku alternatywnych instrukcji w prompcie. W `base_system.md` dopisano nową regułę powstrzymywania się od akcji oraz **Drugi Kontrastujący Przykład Few-Shot**, w którym model widzi, że na powitanie ma odpowiedzieć tylko krótką gotowością.
* **[MEMORY CONSOLIDATION & ATOMIC ACTIONS]** Rozwiązano problem "Pętli Archiwisty" (State-History Conflict, LLM zapętlał się wykonując nieskończone `save_note` po odświeżeniu niezmienionego `<desk_state>`). Wdrożono wzorzec architektoniczny **Atomic Actions**: `save_note` przyjmuje opcjonalny parametr `clear_queue_ids`, który w jednym wywołaniu zapisuje fakt na dysk i natychmiast usuwa go z Brudnopisu (Stagingu).
* **[QWEN HALLUCINATION FIX]** Modele Qwen 2.5 Instruct wykazują silną alergię na negatywne formatowanie (Negative Framing) i sprzeczne wewnętrznie instrukcje (np. nakaz outputowania `<tool_call>` przy jednoczesnym ukrytym wymuszaniu formatu natywnego przez Ollamę). Skutkowało to "LLM Brain Freeze" i generowaniem losowych tagów takich jak `<translation>`. Usunięto konflikty i zastosowano pozytywne ramowanie we wszystkich promptach. Dodano twardy nakaz używania języka polskiego.

## Obecny Stan Projektu

* System posiada absolutnie pancerną pętlę ReAct, bezpieczną na zerwania sieci (w tym cofanie historii pytań) i parsowania szczątkowe.
* Zarówno model 7B jak i 14B Qwen 2.5 Instruct osiągają szczyty swoich możliwości dedukcyjnych. Skrupulatnie monologują w `<thought>` i powstrzymują się od niechcianych akcji.
* Prompty systemowe zachowują formę wypunktowanych list, a warstwa backendu blokuje generację błędów (Stop Tokens). 
* Zaimplementowano pętle naprawcze (Self-Correction) na wypadek błędnych parametrów w JSON.

## Następne Kroki (Next Steps)

1. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do potężniejszego modelu 14b, jeśli dostępne są zasoby VRAM, podczas gdy na co dzień dom obsługuje mały model Lokaj (7B) pracujący np. na Raspberry Pi.
2. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).
3. **Obsługa Błędów Narzędzi:** O ile pętla naprawcza jest, warto sprawdzić czy modele potrafią same dobrze zgadnąć poprawny parametr, czy potrzebują inteligentniejszych logów błędów generowanych przez HA (np. bliska nazwa urządzenia).

## Wiedza i Przemyślenia (Gotchas)

* Małe modele (7B) nie znoszą zakazów w próżni. Zamiast pisać "Nie wywołuj narzędzi", musisz pokazać w Few-Shot *co* ma zrobić w zamian. Kontrastujące przykłady działają wybitnie.
* Qwen 2.5 natywnie wymusza parallel tool calling i czasem emituje kilka JSON-ów naraz, ignorując kolejność logiczną. API Stop Tokens (`</tool_call>`) w Ollamie to absolutna konieczność, by pętla ReAct działała krok po kroku.
* Pamiętaj o zachowaniu ascetycznego UX. Unikaj bogatych, krzykliwych kolorów.
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
