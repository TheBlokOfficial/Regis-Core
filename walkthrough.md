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
- **Model Tiering i System Profili**: Całkowicie porzucono globalne zmienne (np. temperaturę) na rzecz hermetycznych *Profili Modelu* (konfiguracja `profiles.json`). Każdy profil posiada powiązany model, temperaturę, nazwę i uprawnienia (`tier` – basic/advanced). Wdrożono komendy w locie zmieniające wybrane opcje bez resetowania całej sesji (`temp <wartość>`, `tier <poziom>`, `profile`). 
- **Ascetyczny UX**: Ekran zarządzania i panel czatu dopracowano zgodnie z purystycznymi wytycznymi designu (`AGENTS.md`). Całość opiera się na inteligentnych pustych przestrzeniach (negative space) i spłaszczonych procesach.

## Planowane kierunki rozwoju (Kolejka)
1. Integracja WakeWord: Moduł serwerowy do obróbki bezpośredniego strumienia audio wpadającego od satelitów (ESP32).
2. Obsługa Błędów Narzędzi: Bardziej zaawansowana logika podpowiadania modelowi rozwiązań, gdy wywoła funkcję ze złymi argumentami.
