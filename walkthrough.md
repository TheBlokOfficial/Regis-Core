# Dokumentacja techniczna dla agentów LLM (Regis-Core)

## Cel projektu
Regis to lokalny, prywatny system AI, pełniący rolę administratora domu. Nasłuchuje komend tekstowych (docelowo głosowych) i w oparciu o stan urządzeń domowych decyduje, jakie API zawołać w systemie Home Assistant. Projekt nie używa usług chmurowych, działa w pełni lokalnie w ramach sieci domowej.

## Struktura katalogów
- `core/`: 
  - `llm_engine.py`: Moduł odpowiedzialny za komunikację z API Ollamy (pobieranie tagów, generowanie odpowiedzi), zarządzanie promptem systemowym. 
  - `config.py`: Centralne zarządzanie konfiguracją i plikami JSON (settings, aliases, active_models).
  - `exceptions.py`: Definicje niestandardowych wyjątków (np. `HomeAssistantConnectionError`, `LLMConnectionError`).
  - `action_parser.py`: Bezstanowa logika parsowania JSON od LLM na obiekt `ActionResult`.
- `integrations/`:
  - `ha_client.py`: Klient HTTP komunikujący się z zewnętrznym REST API Home Assistanta (oparty na bibliotece `requests`).
  - `ha_mock.py`: Moduł mockujący zachowanie serwera HA.
- `ui/`:
  - `cli.py`: Warstwa prezentacji, odpowiedzialna za terminalowe menu graficzne w oparciu o biblioteki `rich` i `questionary`.
- `tools/`:
  - `symulator_llm.py`: Skrypt developerski umożliwiający ręczne wysyłanie JSON-ów do parsera aplikacji celem debugowania (tzw. Wizard of Oz).
- `tests/`:
  - Katalog zawierający testy jednostkowe w oparciu o środowisko `pytest` (np. `test_config.py`, `test_ha_mock.py`).
- `data/`: Katalog przeznaczony na logi (`regis.log`) oraz pliki konfiguracyjne (`settings.json`, `aliases.json`, `active_models.json`, `ha_state.json`). Wyłączony z repozytorium.
- `main.py`: Punkt wejściowy (Orchestrator). Inicjalizuje system, ładuje konfigurację i deleguje sterowanie główną pętlą do modułu `ui.cli`.

## Stos technologiczny
- **Kod**: Python 3.10+
- **Model / Silnik**: Ollama (endpointy: `http://localhost:11434/api/generate` oraz `/api/tags`).
- **Konsola**: Biblioteka `rich` dla struktur układu oraz `questionary` do interaktywnego wyboru zmiennych. Interfejs jest stonowany i ascetyczny (bez zbędnych jaskrawych kolorów).
- **Komunikacja**: Pakiet `requests` do bezpiecznych i stabilnych połączeń REST API.
- **Testowanie**: Narzędzie `pytest` do testów jednostkowych środowiska DX.

## Planowane kierunki rozwoju (Kolejka)
1. System Pamięci Kontekstowej: Dodanie bufora i logiki do zachowywania historii konwersacji między cyklami (włączenie pamięci dla LLM, by rozumiał zapytania oparte o poprzednie interakcje).
2. Agentic Tools: Ekstrakcja operacji na Home Assistant do zunifikowanego systemu narzędzi (Tool Calling), aby model mógł w przyszłości wzywać inne funkcje (np. sprawdzanie pogody z osobnego API).
3. Integracja WakeWord: Moduł serwerowy do obróbki bezpośredniego strumienia audio wpadającego od satelitów (ESP32).
