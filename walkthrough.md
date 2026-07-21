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
- **System Pamięci Kontekstowej**: LLM zachowuje historię konwersacji (domyślnie do 10 ostatnich wiadomości) w obrębie sesji RAM. Możliwość wyczyszczenia bufora komendą `reset`. Zaimplementowano z wykorzystaniem endpointu Ollama `/api/chat`.
- **Narzędzia Agenta (Agentic Tools / Function Calling)**: Zrezygnowano z wstrzykiwania pełnego stanu systemu i wymuszania formatu JSON na rzecz natywnego wywoływania funkcji. LLM działa w wieloetapowej *pętli agentowej* (Agent Loop), sam odpytuje o dostępne urządzenia i ich stany, a na koniec swobodnym tekstem odpisuje użytkownikowi. Interfejs zyskał "tok myśleniowy", który na żywo wyświetla kroki pośrednie wywoływane przez model.
  - *Fallback Parser*: Zaimplementowano solidny algorytm Bracket Matching na wypadek problemów z szablonami (Chat Templates) małych modeli w Ollama (np. Qwen2.5 7B). Jeśli model zamiast wywołać natywne API "wycieknie" surowym JSON-em do tekstu konwersacji, parser wycina go, uruchamia narzędzie i oczyszcza tekst, chroniąc UI oraz docelowy syntezator mowy (TTS) przed śmieciowymi stringami (jak np. "lashes" czy markdown).
  - *Grounding & Future-Proofing*: Wdrożono elegancki prompt uziemiający ("Zanim wykonasz akcję, musisz fizycznie wywołać narzędzie"). Zwiększono też szczegółowość logowania błędów i rygorystyczne zwracanie błędnych ID prosto do kontekstu modelu, wymuszając poprawę.
- **Optymalizacja VRAM i Wydajności (Ollama)**: Wprowadzono sztywny limit wielkości kontekstu (`num_ctx: 4096`) w połączeniach z API Ollamy. Zapobiega to przepełnianiu VRAMu przez KV Cache (dla kart 12GB i modeli rzędu 12-14B), eliminując spadki wydajności wynikające z tzw. offloadingu do systemowego RAMu. Zrezygnowano z rozbudowanych promptów wymuszających tryb kompatybilności po przejściu na modele w pełni wspierające natywne API narzędzi (Gemma 2, Qwen 2.5).
- **Odświeżony UI (Live Streaming & Timestamps)**:
  - Wdrożono *Live Streaming* odpowiedzi od modelu (token po tokenie), z jednoczesnym ukrywaniem spinnera ("Regis analizuje..."), co dało niesamowicie płynne wrażenia UX.
  - Zaimplementowano znaczniki czasowe `[HH:MM:SS]` zarówno dla wiadomości, jak i dla logów użycia narzędzi.
  - Logi narzędzi ("Regis używa narzędzia...") są teraz trwałe – zapisują się w pamięci lokalnej (jako rola `tool_log`) i przetrwają odświeżanie interfejsu (czyszczenie ekranu). Silnik dba o to, by przycinając własne znaczniki czasu i sztuczne role przed wysłaniem requestu, nie popsuć restrykcyjnego API Ollamy.
- **Two-Pass Generation (Dynamiczna Temperatura)**: Wdrożono mechanizm podwójnego generowania zapobiegający "głupieniu" modelu w narzędziach. Pętla wykonująca wywołania funkcji (Function Calling) do Home Assistanta pracuje ze sztywną temperaturą `0.1` (tryb matematyczny/analityczny). Dopiero po powrocie wszystkich wymaganych danych z HA następuje drugi "pass", w którym model wykorzystuje naturalną temperaturę konwersacji (`0.7`), generując z pełnym kontekstem błyskotliwą, charyzmatyczną odpowiedź dla użytkownika. Narzędzia pozostają wpięte do pamięci na obu etapach, pozwalając na swobodne uaktywnianie Chain of Thought.
- **Tool Memory Persistence**: Wyeleminowano krytyczny defekt halucynacyjny, przez który agent z małym modelem, zapominając co zrobił kilka sekund wcześniej, uciekał się do kłamstw ("Zrobiłem to", nie wykonując akcji). `self.history` używa teraz natywnego standardu przetrzymywania wywołań w oryginalnych rolach `assistant` (wraz ze sztywnym atrybutem `tool_calls`) oraz `tool` (ze zwrotką JSON). Uodporniło to agenta na długie sesje konwersacyjne i pozwoliło na nieograniczone budowanie wątków wokół skomplikowanych kaskad funkcji.
- **Solid-State AI (The Warden & Dynamic Deduction)**: Wdrożono mechanikę "Pancernej Architektury" po stronie Pythona. Agent rozpoczyna pracę z pustym "biurkiem" i rygorystycznym nakazem używania narzędzi badawczych (`get_devices`), dzięki czemu nie zatyka się zbędnymi danymi o tysiącach urządzeń (Dynamic Deduction). Wszystkie niewłaściwe akcje lub próby odgadywania identyfikatorów 'entity_id' są brutalnie odcinane w warstwie Pythona z jednoczesnym dostarczeniem instrukcji naprawczej do nowo sformułowanego zapytania JSON (The Warden). To zmusza sztuczną inteligencję do proaktywnego sprawdzania i weryfikacji sprzętu przed wykonaniem akcji fizycznej.
- **Wewnętrzny Monolog (Visible Scratchpad)**: Odblokowano dla modelu (Lokaja 7B) możliwość wygłaszania przemyśleń i autokorekt w pierwszej fazie (z temperaturą 0.1) w reakcji na błędnie ułożony JSON (Tzw. "Głośne Myślenie" naprawiające u LLM zjawisko lenistwa halucynacyjnego). W konsoli CLI monolog ten strumieniowany jest dyskretną, przygaszoną na szaro czcionką (`[dim] 🧠 Myśli Agenta:`), tworząc niesamowity pogląd na żywo w trzewia maszyny naprawiającej własne wywołania, oddzielając to od potężnych, czystych wypowiedzi w Fali Drugiej.
- **Model Tiering i System Profili**: Całkowicie porzucono globalne zmienne (np. temperaturę) na rzecz hermetycznych *Profili Modelu* (konfiguracja `profiles.json`). Każdy profil posiada powiązany model, temperaturę, nazwę i uprawnienia (`tier` – butler/regis). Wdrożono komendy w locie zmieniające wybrane opcje bez resetowania całej sesji (`temp <wartość>`, `tier <poziom>`, `profile`). 
- **Infinite Scrolling UX**: Ekran zarządzania (CLI) przeprojektowano w natywny REPL. Pozbyto się wymuszonego czyszczenia ekranu oraz konfliktujących animacji (spinnerów). Użytkownik ma pełne, natywne przewijanie terminala, podczas gdy szare logi 🧠 Myśli Agenta, strumienie narzędzi i odpowiedzi tekstowe pojawiają się w precyzyjnie podzielonych, pojedynczych wierszach, dając poczucie pancernej stabilności.
- **Separation of Concerns (Dynamic Prompts)**: Oczyszczono pliki binarne kodu z hardcodowanych instrukcji psychologicznych agentów. `BASE_SYSTEM_PROMPT` oraz wytyczne dla poszczególnych warstw są dynamicznie doczytywane w locie (Lazy Loading) przez główny silnik prosto z czystych plików tekstowych zlokalizowanych w katalogu `data/prompts/`. Umożliwia to zjawiskowo łatwą edycję osobowości czy dodawanie nowych agentów bez naruszania struktury kodu.
- **Chain of Thought (Kaskada Dedukcji)**: Wymuszono na wszystkich modelach głośną analizę historii przed dotknięciem mechaniki JSON. Prowadzi to do całkowitego zniwelowania zjawiska halucynowania zmyślonych narzędzi w pierwszej rundzie, a the Warden na bieżąco koryguje zapytania, prowadząc je na właściwe tory (zapobiega to tzw. The Echoing Hallucinations).
- **Optymalizacja "Lokaja" i Wsparcie Masowych Tablic (List Support)**: Przebudowano warstwę sprzętową by ratować zacinające się modele 7B. Zezwolono The Wardenowi przyjmować listy identyfikatorów (`array`) dla narzędzi takich jak `get_device_state`, zmniejszając narzut wywołań w pętlach i unikając przepalania małych okien kontekstowych. W locie ustalono ścisłą maszynową temperaturę `0.1` w konfiguracji (`main.py` oraz `cli.py`), ostatecznie zamykając sprawę halucynacji w tanich środowiskach 24/7.

## Planowane kierunki rozwoju (Kolejka)
1. Integracja WakeWord: Moduł serwerowy do obróbki bezpośredniego strumienia audio wpadającego od satelitów (ESP32).
2. Obsługa Błędów Narzędzi: Bardziej zaawansowana logika podpowiadania modelowi rozwiązań, gdy wywoła funkcję ze złymi argumentami.
4. **Docelowa Architektura Agentowa (Tiered System / Handoff)**: 
   - Przebudowa Regis-Core w kierunku architektury dwuwarstwowej, sprofilowanej pod konkretne modele (np. Qwen).
   - **"Recepcjonista" (Raspberry Pi 5)**: Mniejszy model działający 24/7 jako podproces, odpowiedzialny za codzienną, lekką interakcję i proste narzędzia.
   - **"Szef" (Desktop PC z GPU)**: Wielki model wyposażony w pulę zaawansowanych narzędzi, uruchamiany wyłącznie na żądanie (np. przez narzędzie `call_boss()`).
   - System na żądanie sprawdzi dostępność stacji roboczych PC (działająca w tle usługa monitorująca VRAM), załaduje Szefa z pełnym przekazaniem kontekstu rozmowy (wysyłając prośbę do Ollamy po lokalnym IP), a po rozwiązaniu skomplikowanego zadania zwolni kartę graficzną. Pozwoli to na łączenie potężnej dedukcji z zerowym marnotrawieniem energii.
