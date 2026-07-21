# Dokumentacja techniczna dla agentów LLM (Regis-Core)

## Cel projektu
Regis to lokalny, prywatny system AI, pełniący rolę administratora domu. Nasłuchuje komend tekstowych (docelowo głosowych) i w oparciu o stan urządzeń domowych decyduje, jakie API zawołać w systemie Home Assistant. Projekt nie używa usług chmurowych, działa w pełni lokalnie w ramach sieci domowej.

## Struktura katalogów
- `core/`: 
  - `llm_engine.py`: Moduł odpowiedzialny za komunikację z API Ollamy (pobieranie tagów, generowanie odpowiedzi), zarządzanie promptem systemowym. 
  - `config.py`: Centralne zarządzanie konfiguracją i plikami JSON (settings, aliases, active_models).
  - `exceptions.py`: Definicje niestandardowych wyjątków (np. `HomeAssistantConnectionError`, `LLMConnectionError`).
  - `tools_registry.py`: Rejestr narzędzi (Function Calling) dostarczanych dla modelu LLM, integrujący je z wywołaniami HA.
- `integrations/`:
  - `ha_client.py`: Klient HTTP komunikujący się z zewnętrznym REST API Home Assistanta (oparty na bibliotece `requests`).
  - `ha_mock.py`: Moduł mockujący zachowanie serwera HA.
- `ui/`:
  - `cli.py`: Warstwa prezentacji, odpowiedzialna za terminalowe menu graficzne w oparciu o biblioteki `rich` i `questionary` (odświeżony, minimalistyczny UX bez jaskrawych paneli i kolorów).
- `tools/`:
  - Katalog narzędzi pomocniczych (obecnie pusty po usunięciu starego symulatora).
- `tests/`:
  - Katalog zawierający testy jednostkowe w oparciu o środowisko `pytest` (np. `test_config.py`, `test_ha_mock.py`).
- `data/`: Katalog przeznaczony na logi (`regis.log`) oraz pliki konfiguracyjne (`settings.json`, `aliases.json`, `active_models.json`, `ha_state.json`). Wyłączony z repozytorium.
- `main.py`: Punkt wejściowy (Orchestrator). Inicjalizuje system, ładuje konfigurację i deleguje sterowanie główną pętlą do modułu `ui.cli`.

## Stos technologiczny
- **Kod**: Python 3.10+
- **Model / Silnik**: Ollama (endpointy: `http://localhost:11434/api/chat` oraz `/api/tags`).
- **Konsola**: Biblioteka `rich` dla struktur układu oraz `questionary` do interaktywnego wyboru zmiennych. Interfejs jest stonowany i ascetyczny (bez zbędnych jaskrawych kolorów).
- **Komunikacja**: Pakiet `requests` do bezpiecznych i stabilnych połączeń REST API.
- **Testowanie**: Narzędzie `pytest` do testów jednostkowych środowiska DX.

## Zrealizowane funkcje
- **System Pamięci Kontekstowej**: LLM zachowuje historię konwersacji (domyślnie do 10 ostatnich wiadomości) w obrębie sesji RAM. Możliwość wyczyszczenia bufora komendą `/clear`. Zaimplementowano z wykorzystaniem endpointu Ollama `/api/chat`.
- **Narzędzia Agenta (Agentic Tools / Function Calling)**: LLM działa w wieloetapowej *pętli agentowej ReAct* (Reasoning and Acting), sam odpytuje o dostępne urządzenia i ich stany. Interfejs wyświetla kroki pośrednie wywoływane przez model w czasie rzeczywistym.
  - *Fallback Parser*: Solid-State algorytm oparty o skanowanie klamer (Bracket Matching). Jeśli model "wycieknie" surowym JSON-em do tekstu, parser wycina go w całości, uruchamia narzędzie i oczyszcza tekst dla UI i warstwy TTS. Parser obsługuje wiele wywołań narzędzi naraz.
  - *Grounding & Future-Proofing*: Elegancki prompt uziemiający. Szczegółowe logowanie błędów i rygorystyczne zwracanie komunikatów błędów do kontekstu modelu, wymuszając auto-korekcję.
- **Optymalizacja VRAM i Wydajności (Ollama)**: Sztywny limit kontekstu (`num_ctx: 4096`). Zapobiega przepełnianiu VRAMu przez KV Cache, eliminując offloading do systemowego RAM.
- **Modele Instruct (qwen2.5-instruct)**: Projekt używa wariantów `-instruct` modeli Qwen 2.5 (`qwen2.5:7b-instruct` dla Lokaja, `qwen2.5:14b-instruct` dla Regisa). Modele Instruct oferują znacznie lepsze instruction following, tool calling i reasoning niż warianty bazowe. Temperatura: Lokaj=0.1, Regis=0.4.
- **Single-Pass ReAct (zastąpiło Two-Pass Generation)**: Architektura zredukowana do jednego przebiegu generowania. Narzędzia są zawsze dostępne w payloadzie. Pętla ReAct kontynuuje dopóki model wywołuje narzędzia; gdy ich nie wywoła — to jest finalna odpowiedź. Eliminuje podwójny czas oczekiwania i podwójne "Myśli agenta".
- **Wewnętrzny Monolog `<thought>` (Event-Driven Real-Time Streaming)**: Model ma obowiązek pisać tok rozumowania w tagach `<thought>...</thought>`. W najnowszej wersji architektury zrezygnowano ze skomplikowanego buforowania w warstwie prezentacji. Zamiast tego zaimplementowano scentralizowany `StreamingTokenParser` z buforem Lookahead w rdzeniu, działający w architekturze *Event-Driven* (callbacki: `on_thought_token`, `on_content_token`, `on_tool_call`). Interfejs w terminalu jest teraz głupi i lekki, reagując tylko na odfiltrowane tagi w czasie rzeczywistym. Wdrożono rygorystyczne zabezpieczenia chroniące przez pętlami nieskończonymi oraz awariami rich Markup (`markup=False`). JSON-y tool-callów, a także śmieciowe znaczniki nowej linii po tagach, są bezbłędnie filtrowane i nie wysadzają UI.
- **Odświeżony UI (Live Streaming & Timestamps)**: Live Streaming odpowiedzi (token po tokenie) z precyzyjnymi znacznikami `[HH:MM:SS]`. Logi narzędzi są trwałe w historii sesji. Interfejs jest stonowany i ascetyczny (bez jaskrawych paneli i kolorów).
- **Tool Memory Persistence**: Wyeliminowano defekt halucynacyjny, przez który agent zapominał co zrobił. `self.history` używa natywnego standardu ról `assistant` (z `tool_calls`) oraz `tool` (ze zwrotką JSON), uodparniając agenta na długie sesje.
- **Solid-State AI (The Warden & Dynamic Deduction)**: Agent zaczyna z pustym "biurkiem" i nakazem używania narzędzi badawczych (`get_devices`). Błędne akcje są odcinane z instrukcją naprawczą kierowaną do modelu, zmuszając do weryfikacji przed wykonaniem fizycznej akcji.
- **Pamięć Długoterminowa (Notatnik)**: Narzędzia `read_notes`, `save_note`, `delete_note` umożliwiają trwałe zapamiętywanie preferencji użytkownika między sesjami (JSON na dysku). Model jest proaktywny — sam zapisuje fakty o użytkowniku i czyta notatki przed zadawaniem pytań.
  - *Tier Permissions & Staging*: Wdrożono architekturę uprawnień. Model 14B (Regis) ma pełen dostęp do `save_note` i `delete_note`. Model 7B (Lokaj) posiada własne narzędzie `queue_note` służące jako bezpieczny bufor (Staging), by bez ryzyka notować fakty wyłapane w codziennym small-talku do późniejszej weryfikacji, bez wybudzania ciężkiego modelu.
  - *Harness Error Interception*: Nieuprawnione wywołania narzędzi lub narzędzia spoza tieru są przechwytywane przez parser, który zamiast je ignorować i wylewać do UI, zwraca do modelu twardy błąd `Odmowa dostępu w obecnym trybie`, wymuszając samo-naprawę.
- **Separation of Concerns (Dynamic Prompts)**: Instrukcje psychologiczne agentów są doczytywane dynamicznie z plików `data/prompts/` (`base_system.md`, `tier_butler.md`, `tier_regis.md`). Pliki są w formacie wypunktowanych list, co optymalnie współpracuje z modelami Instruct. Prompt systemowy jest ściśle dopasowany ("tier-aware") do posiadanych przez dany profil narzędzi.
- **Zaawansowany Prompt Engineering (Qwen 2.5)**: System promptów został całkowicie przebudowany zgodnie z inżynieryjnymi standardami dla modeli 7B-14B (dokument `PROMPT_ENGINEERING.md`). Wdrożono:
  - Odwrócenie logiki łączenia promptów w silniku (tożsamość ładuje się jako pierwsza).
  - Pętlę naprawczą (Self-Correction) wymuszającą analizę błędów narzędzi w obrębie `<thought>`.
  - Strukturę Checklist (Task Decomposition) ułatwiającą modelom liniowe rozwiązywanie problemów.
  - "Sandwiching" kluczowych reguł (wymuszenie formatu JSON i monologu jest dołączane jako twardy przypominacz na samym końcu wynikowego prompta).
  - Techniki pozytywnego ramowania oraz One-Shot Prompting (przykład idealnej iteracji wywołania).
- **Zabezpieczenie przed Halucynacjami Narzędzi Równoległych (Parallel Tool Calling Fix)**: Wdrożono 3-warstwową barierę, wymuszającą ściśle liniową pętlę ReAct (Jedna Myśl -> Jedno Narzędzie -> Zasilenie wynikiem):
  - *Prompt*: miękki nakaz z góry określający limit jednego narzędzia.
  - *Stop Tokens*: twarde ucinanie samplowania API Ollamy po napotkaniu `</tool_call>`.
  - *Parser Limiter*: odcinanie nadmiarowych (zhalucynowanych) wywołań w pętli (ograniczenie tablicy do `[0]`) dla pełnej higieny historii modelu.
- **Integracja Gemini API**: Eksperymentalny silnik `GeminiEngine` pozwala przełączyć się na chmurowe modele Google przez komendę `/provider`. Obsługuje restrykcyjny format function-callingu Google i dynamiczne pobieranie listy modeli z API.

## Planowane kierunki rozwoju (Kolejka)
1. Integracja WakeWord: Moduł serwerowy do obróbki bezpośredniego strumienia audio wpadającego od satelitów (ESP32).
2. Obsługa Błędów Narzędzi: Bardziej zaawansowana logika podpowiadania modelowi rozwiązań, gdy wywoła funkcję ze złymi argumentami.
4. **Docelowa Architektura Agentowa (Tiered System / Handoff)**: 
   - Przebudowa Regis-Core w kierunku architektury dwuwarstwowej, sprofilowanej pod konkretne modele (np. Qwen).
   - **"Recepcjonista" (Raspberry Pi 5)**: Mniejszy model działający 24/7 jako podproces, odpowiedzialny za codzienną, lekką interakcję i proste narzędzia.
   - **"Szef" (Desktop PC z GPU)**: Wielki model wyposażony w pulę zaawansowanych narzędzi, uruchamiany wyłącznie na żądanie (np. przez narzędzie `call_boss()`).
   - System na żądanie sprawdzi dostępność stacji roboczych PC (działająca w tle usługa monitorująca VRAM), załaduje Szefa z pełnym przekazaniem kontekstu rozmowy (wysyłając prośbę do Ollamy po lokalnym IP), a po rozwiązaniu skomplikowanego zadania zwolni kartę graficzną. Pozwoli to na łączenie potężnej dedukcji z zerowym marnotrawieniem energii.
