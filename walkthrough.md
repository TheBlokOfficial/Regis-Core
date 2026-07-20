# Dokumentacja techniczna dla agentów LLM (Regis-Core)

## Cel projektu
Regis to lokalny, prywatny system AI, pełniący rolę administratora domu. Nasłuchuje komend tekstowych (docelowo głosowych) i w oparciu o stan urządzeń domowych decyduje, jakie API zawołać w systemie Home Assistant. Projekt nie używa usług chmurowych, działa w pełni lokalnie w ramach sieci domowej.

## Struktura katalogów
- `core/`: 
  - `llm_engine.py`: Moduł odpowiedzialny za komunikację z API Ollamy (pobieranie tagów, generowanie odpowiedzi), zarządzanie promptem systemowym i wymuszanie zwrotu w formacie JSON. 
- `integrations/`:
  - `ha_client.py`: Klient HTTP komunikujący się z zewnętrznym REST API Home Assistanta w celu fizycznego egzekwowania komend sprzętowych.
  - `ha_mock.py`: Moduł mockujący zachowanie serwera HA, używany do testowania bez połączenia z właściwym fizycznym serwerem.
- `tools/`:
  - `symulator_llm.py`: Skrypt developerski umożliwiający ręczne wysyłanie JSON-ów do parsera aplikacji celem debugowania, bez angażowania i czekania na odpowiedź modelu LLM.
- `data/`: Katalog przeznaczony na pliki konfiguracyjne i stany (.json) generowane podczas działania programu (wyłączony z repozytorium gita).
  - `active_models.json`: Przechowuje listę stringów modeli, które użytkownik zdecydował się uczynić widocznymi w głównym konfiguratorze.
  - `ha_state.json`: Przechowuje stan sztucznego/mockowanego domu.
- `main.py`: Główny plik startowy. Inicjalizuje system, pozwala zarządzać modelami poprzez bibliotekę `questionary`, a następnie odpala główną pętlę interakcji w oparciu o wyciszony `rich` z architekturą Single-Turn Render (ekran jest czyszczony wywołaniem `os.system('cls')` na każdym cyklu w celu czytelności).

## Stos technologiczny
- **Kod**: Python 3.10+
- **Model / Silnik**: Ollama (endpointy: `http://localhost:11434/api/generate` oraz `/api/tags`).
- **Konsola**: Biblioteka `rich` dla struktur układu oraz `questionary` do interaktywnego wyboru zmiennych. Interfejs jest stonowany i ascetyczny (bez zbędnych jaskrawych kolorów).

## Planowane kierunki rozwoju (Kolejka)
1. System Pamięci Kontekstowej: Dodanie bufora i logiki do zachowywania historii konwersacji między cyklami (włączenie pamięci dla LLM, by rozumiał zapytania oparte o poprzednie interakcje).
2. Agentic Tools: Ekstrakcja operacji na Home Assistant do zunifikowanego systemu narzędzi (Tool Calling), aby model mógł w przyszłości wzywać inne funkcje (np. sprawdzanie pogody z osobnego API).
3. Integracja WakeWord: Moduł serwerowy do obróbki bezpośredniego strumienia audio wpadającego od satelitów (ESP32).
