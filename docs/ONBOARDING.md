# Regis-Core: Mapa Kodu (Onboarding)

Ten dokument to przewodnik po strukturze repozytorium. Wyjaśnia, co robi każdy katalog i każdy plik — prostym językiem, bez nadmiernego zagłębiania się w szczegóły implementacji. Jest przeznaczony zarówno dla człowieka wracającego do projektu po przerwie, jak i dla agenta AI rozpoczynającego pracę w projekcie.

Zanim zaczniesz czytać ten dokument, upewnij się, że zapoznałeś się z `docs/MANIFEST.md` — to on definiuje *dlaczego* kod jest zbudowany w taki, a nie inny sposób.

---

## Struktura Katalogów — Obraz Ogólny

```
regis-core/
│
├── apps/           ← Punkty wejścia — uruchamialne aplikacje
│   ├── controller/ ← Kontroler: lekki router API + integracja HA (daemon RPi5)
│   ├── worker/     ← Węzeł Roboczy: LLMEngine + STTEngine, bez logiki HTTP
│   ├── satellite/  ← Satelita audio (VAD + I/O)
│   └── terminal/   ← Terminal CLI (satelita tekstowa, deweloperska)
├── core/           ← Serce systemu — współdzielona logika
├── integrations/   ← Klienci zewnętrznych API (świat zewnętrzny)
├── data/           ← Konfiguracja, logi, prompty (wykluczone z Git)
├── docs/           ← Dokumentacja projektu
├── scripts/        ← Pliki pomocnicze do deploymentu
└── tests/          ← Testy jednostkowe pytest
```

**Prosta zasada podziału:**
- `core/` = **mózg** — nie uruchamia się sam, ale wszystko go używa.
- `apps/` = **kończyny** — uruchamiane bezpośrednio, używają `core/`.
- `integrations/` = **zmysły** — mówią systemowi co dzieje się w świecie (HA, Gemini).
- `data/` = **pamięć** — konfiguracja i stan, który przeżywa restarty.

---

## `apps/` — Aplikacje (Punkty Wejścia)

Każdy podkatalog to osobna, niezależna aplikacja. Uruchamiane przez `python -m apps.<nazwa>`.

### `apps/controller/` — Kontroler (FastAPI)
**Rola:** Lekki daemon uruchamiany na Raspberry Pi 5. Mózg systemu: wystawia REST API dla Satelit, zarządza integracją z Home Assistant i deleguje inferencję do Węzła Roboczego.

**Plik:** `main.py`
- Przy starcie ładuje konfigurację (`config.py`), inicjalizuje `HomeAssistantClient`, `ToolsRegistry` i `WorkerNode`.
- Wystawia trzy endpointy:
  - `POST /v1/chat/stream` — przyjmuje wiadomość tekstową, zwraca odpowiedź modelu jako **Server-Sent Events (SSE)**. Każdy token/myśl/wywołanie narzędzia to osobne zdarzenie strumieniowe.
  - `POST /v1/chat/audio_stream` — przyjmuje plik `.wav`, przekazuje do Węzła Roboczego (STT → LLM). Reszta jak wyżej.
  - `POST /v1/clear_history` — resetuje historię konwersacji węzła roboczego.

> **Uwaga architektoniczna:** Kontroler na tym etapie importuje `WorkerNode` bezpośrednio. Po wdrożeniu Rejestru Encji (`[ARCH]` w TASKS.md) WorkerNode stanie się osobnym procesem HTTP, a Kontroler będzie go tylko wykrywać i routować do niego żądania.

---

### `apps/worker/` — Węzeł Roboczy
**Rola:** Hostuje model LLM i silnik STT. Odpowiada wyłącznie za inferencję. Nie zawiera żadnej logiki HTTP ani integracji z Home Assistant.

**Plik:** `node.py`
- Klasa `WorkerNode` — inicjalizuje `LLMEngine` i `STTEngine`.
- Interfejs publiczny: `handle_chat()`, `handle_audio()`, `clear_history()`.
- `handle_audio()` wewnętrznie: STT (Whisper) → `handle_chat()` → LLM.

---

### `apps/terminal/` — Terminal CLI (Satelita tekstowa)
**Rola:** Interfejs deweloperski. Działa jako "Satelita tekstowa" — można go podłączyć lokalnie do `LLMEngine` (tryb `prod`) lub zdalnie do Kontrolera przez SSE (tryb `remote`).

**Plik:** `main.py`
- Wyświetla główne menu (tryb `prod` lub `remote`).
- W trybie `prod`: inicjalizuje własną instancję `LLMEngine` i uruchamia pętlę CLI lokalnie.
- W trybie `remote`: tworzy `RemoteClient` i łączy się z `apps/controller/` przez HTTP/SSE.

**Plik:** `cli.py`
- Cały wizualny interfejs użytkownika w terminalu (biblioteki `rich`, `questionary`).
- Zawiera pętlę REPL (Read-Eval-Print-Loop) — nieskończona pętla wczytywania inputu i wyświetlania odpowiedzi strumieniowo (token po tokenie).
- Obsługuje komendy specjalne: `/clear`, `/provider`, `/model` itp.

---

### `apps/satellite/` — Satelita Audio *(w budowie)*
**Rola:** Moduł przechwytywania i odtwarzania dźwięku. Nagrywa audio z mikrofonu i wysyła je do Kontrolera (`/v1/chat/audio_stream`).

---

## `core/` — Serce Systemu

Pliki w tym katalogu **nigdy nie są uruchamiane bezpośrednio**. Są importowane przez `apps/` i przez siebie nawzajem.

### `llm_engine.py` — Silnik LLM
**Co robi:** Zarządza całą komunikacją z Ollamą. To najbardziej centralny plik w projekcie.

Kluczowe odpowiedzialności:
- Buduje kompletny system prompt (tożsamość modelu z `data/prompts/` + opis narzędzi).
- Implementuje **pętlę ReAct** — wysyła zapytanie do modelu, parsuje odpowiedź, jeśli model wywołał narzędzie — wykonuje je przez `ToolsRegistry` i wraca do modelu z wynikiem. Powtarza dopóki model nie skończy.
- Dla tieru `butler` (1.5B): używa **Structured Outputs** (JSON Schema wymuszany przez Ollamę) zamiast pętli ReAct — szybszy parser NLU.
- Zarządza historią konwersacji (lista tur `user` + `assistant`, z limitem).
- Używa wzorca **Droga A**: opisy narzędzi są renderowane jako tekst XML-like (`<tools>`) do promptu — nie jako pole `tools` w API. Eliminuje to kolizję z natywnym angielskim blokiem instrukcji Ollamy.

### `stream_parser.py` — Parser Strumieniowy
**Co robi:** Przetwarza surowy strumień tokenów z Ollamy i segreguje go na trzy kanały zdarzeń.

- Rozpoznaje tagi `<thought>...</thought>` → token leci do callbacka `on_thought_token`.
- Rozpoznaje tagi `<tool_call>...</tool_call>` → przechwytuje JSON i przekazuje go silnikowi jako gotowe wywołanie narzędzia.
- Reszta → callback `on_content_token` (to co widzi użytkownik).
- Posiada bufor Lookahead — zabezpiecza przed sytuacją, gdy tag zostaje podzielony na dwa osobne chunki TCP.

### `tools_registry.py` — Rejestr Narzędzi
**Co robi:** Wie jakie narzędzia istnieją i co robią. Weryfikuje uprawnienia i wykonuje wywołania.

- Przy wywołaniu narzędzia przez LLM sprawdza, czy tier aktualnego modelu ma do niego dostęp (system uprawnień `butler < regis < prime`).
- Kieruje wywołania do odpowiednich klientów (np. `ha_client.turn_on()` dla narzędzia `turn_on`).
- Zwraca wynik narzędzia jako string JSON z powrotem do `llm_engine.py`.

### `schemas.py` — Definicje Narzędzi
**Co robi:** Przechowuje `BASE_TOOLS_SCHEMA` — listę wszystkich dostępnych narzędzi z ich opisami, parametrami i wymaganym tierem.

To jest "menu narzędzi" systemu. `llm_engine.py` używa go do renderowania opisu narzędzi do promptu, a `tools_registry.py` do weryfikacji czy narzędzie istnieje.

### `config.py` — Konfiguracja
**Co robi:** Centralny punkt ładowania plików konfiguracyjnych z katalogu `data/`.

- `load_settings()` → `data/settings.json` (aktywny tier, URL HA, token HA)
- `load_aliases()` → `data/aliases.json` (ludzkie nazwy urządzeń)
- `load_virtual_groups()` → `data/virtual_groups.json` (logiczne grupy urządzeń)

### `remote_client.py` — Klient Zdalny
**Co robi:** Implementuje ten sam interfejs co `LLMEngine`, ale zamiast lokalnie odpytywać Ollamę — wysyła żądania do `apps/server/` przez HTTP/SSE.

Terminal CLI nie wie, czy rozmawia z lokalnym silnikiem czy z serwerem — oba obiekty wyglądają tak samo z zewnątrz (ten sam interfejs `generate_response()`).

### `stt_engine.py` — Silnik STT
**Co robi:** Cienka warstwa opakowująca model `faster-whisper`. Przyjmuje plik `.wav` w pamięci (jako `BytesIO`) i zwraca transkrypcję jako string.

### `exceptions.py` — Wyjątki
**Co robi:** Definicje niestandardowych wyjątków projektu (np. `LLMConnectionError`).

### `gemini_engine.py` — Silnik Gemini *(eksperymentalny)*
**Co robi:** Alternatywny silnik LLM używający chmurowego API Google Gemini zamiast lokalnej Ollamy. Implementuje ten sam interfejs co `LLMEngine`. Aktywowany przez komendę `/provider gemini` w terminalu.

---

## `integrations/` — Klienci Zewnętrznych API

### `ha_client.py` — Klient Home Assistant
**Co robi:** Zarządza całą komunikacją z Home Assistant REST API.

Kluczowe cechy:
- Używa `requests.Session()` — jedno długotrwałe połączenie zamiast nowego połączenia TLS przy każdym wywołaniu. Dramatycznie redukuje latencję.
- Obsługuje **Wirtualne Grupy** (`virtual_groups.json`) — pozwala sterować 7 żarówkami jednym wywołaniem API zamiast 7 osobnymi.
- Obsługuje aliasy — mapuje ludzkie nazwy ("lampa w salonie") na `entity_id` HA.
- Wysyła komendy do HA jako pojedyncze żądania POST z tablicą `entity_id` — zamiast pętli po urządzeniach.

### `ha_mock.py` — Mock Home Assistant
**Co robi:** Atrapa klienta HA do testowania i developmentu bez fizycznego Home Assistanta. Zwraca statyczne dane.

---

## `data/` — Konfiguracja i Stan *(wykluczony z Git)*

### `settings.json`
Główna konfiguracja aplikacji: aktywny tier, URL i token HA, URL serwera, historia.

### `prompts/`
Pliki Markdown definiujące osobowość i instrukcje dla każdego tieru modelu:
- `tier_butler.md` — instrukcje dla modelu 1.5B (NLU, minimalistyczny prompt Few-Shot JSON)
- `tier_regis.md` — instrukcje dla modelu 14B (pełny agent ReAct z Chain of Thought)
- `tier_prime.md` — instrukcje dla modelu 32B (rozszerzone możliwości)

Te pliki są ładowane dynamicznie przez `llm_engine.py` przy każdym starcie silnika.

### `virtual_groups.json`
Definicja logicznych grup urządzeń. Pozwala modelowi sterować wieloma urządzeniami jedną komendą bez potrzeby znajomości ich indywidualnych `entity_id`.

### `aliases.json`
Mapowanie przyjaznych nazw urządzeń na ich `entity_id` w Home Assistant.

### `regis.log`
Plik logów aplikacji — zapisywany przy każdym uruchomieniu.

---

## `docs/` — Dokumentacja Projektu

- `MANIFEST.md` — **Czytaj jako pierwszy.** Wizja, filozofia i cele projektu.
- `ARCHITECTURE.md` — Nadrzędne zasady projektowe i specyfikacja sprzętowa (starszy dokument).
- `ONBOARDING.md` — Ten plik. Mapa kodu.

---

## `scripts/`

### `regis.service`
Plik konfiguracyjny `systemd` do uruchamiania `apps/server/` jako daemona systemowego na Raspberry Pi (autostart przy starcie systemu).

---

## Skrypty w Katalogu Głównym

| Plik | Co robi |
|---|---|
| `run_server.bat` | Uruchamia `apps/controller/` na Windowsie (dev) |
| `run_terminal.bat` | Uruchamia `apps/terminal/` na Windowsie |
| `deploy_to_pi.bat` | Wysyła aktualne pliki na Raspberry Pi przez SSH i restartuje daemona |
| `cleanup.sh` | Usuwa pliki `__pycache__` i `.pyc` |

---

## Jak Przepływa Jedno Polecenie (od A do Z)

```
Użytkownik wpisuje "włącz lampę"
        ↓
[apps/terminal/cli.py]
Odczytuje input, wywołuje engine.generate_response("włącz lampę", ...)
        ↓
[core/llm_engine.py] — pętla ReAct, iteracja 1
Buduje system prompt (tier_regis.md + opisy narzędzi z schemas.py)
Wysyła do Ollamy → Ollama zaczyna streamować tokeny
        ↓
[core/stream_parser.py]
Token po tokenie parsuje strumień:
  - <thought>Muszę sprawdzić urządzenia...</thought>  → callback: on_thought_token
  - <tool_call>{"name": "get_devices"}</tool_call>    → przechwycone jako wywołanie
        ↓
[core/tools_registry.py]
Weryfikuje uprawnienia tieru → wywołuje ha_client.get_devices()
        ↓
[integrations/ha_client.py]
Pyta Home Assistant REST API o listę urządzeń → zwraca JSON
        ↓
[core/llm_engine.py] — pętla ReAct, iteracja 2
Wynik narzędzia dodany do historii jako wiadomość "tool"
Ponownie odpytuje Ollamę z pełnym kontekstem (łącznie z wynikiem)
        ↓
Ollama generuje: "Rozumiem. Włączam light.salon."
  - <tool_call>{"name": "turn_on", "entity_id": "light.salon"}</tool_call>
        ↓
[integrations/ha_client.py]
Wysyła POST do HA → lampa się zapala
        ↓
[core/llm_engine.py] — pętla ReAct, iteracja 3
Model generuje finalną odpowiedź bez tool_call → koniec pętli
        ↓
[apps/terminal/cli.py]
Wyświetla odpowiedź użytkownikowi token po tokenie
```

---

## Model Dystrybucji (Docelowy — Jeszcze Niezaimplementowany)

> [!IMPORTANT]
> Sekcja ta opisuje docelową architekturę dystrybucji, która NIE jest jeszcze zaimplementowana. Aktualnie projekt to zbiór skryptów uruchamianych przez `python -m`. Poniższy model należy wdrożyć DOPIERO po ustabilizowaniu architektury (rozdzieleniu Kontrolera od Węzła Roboczego).

### Problem z aktualnym stanem
Urządzenie, które chce być tylko Satelitą, musi dziś sklonować cały monorepo — łącznie z kodem `llm_engine.py`, `ha_client.py` i wszystkimi zależnościami Kontrolera i Węzła. To jest nieakceptowalne w finalnej wersji.

### Docelowy Model: Jeden Repo, Osobne Pakiety

Projekt powinien używać jednego `pyproject.toml` z **grupami opcjonalnych zależności (extras)**. Każde urządzenie instaluje tylko to, czego potrzebuje:

```bash
# Raspberry Pi 5 (Kontroler):
pip install "regis-core[controller]"

# Desktop PC (Węzeł Roboczy):
pip install "regis-core[worker]"

# Laptop / dowolne urządzenie (Satelita):
pip install "regis-core[satellite]"

# Wszystko naraz (deweloper):
pip install "regis-core[all]"
```

Mechanizm extras w `pyproject.toml` sprawia, że każda instalacja pobiera tylko odpowiedni podzbiór zależności. Wspólna biblioteka (`core/`) jest zawsze pobierana jako zależność bazowa.

### Docelowy Model: Usługi, nie Konsola

Satelita i Węzeł Roboczy nie powinny być aplikacjami konsolowymi dla końcowego użytkownika. Powinny obsługiwać dwa tryby uruchomienia:

```bash
# Tryb deweloperski (pierwszoplanowy, z logami w terminalu):
regis-satellite run

# Instalacja jako usługa systemowa (autostart, tło):
regis-satellite install-service
regis-worker install-service
```

| System | Mechanizm usługi |
|---|---|
| Linux / Raspberry Pi | `systemd` — plik `.service` (już istnieje w `scripts/`) |
| Windows | `pywin32` (WinService) lub zewnętrzne narzędzie NSSM |

Po zainstalowaniu jako usługa — urządzenie startuje i Satelita/Węzeł automatycznie zgłasza się do Kontrolera bez żadnej interakcji użytkownika.

---

## Workflow Deweloperski (Stan Aktualny)

Projekt jest rozwijany na komputerze deweloperskim (Windows PC) i deployowany na Raspberry Pi 5.

### Środowisko lokalne
1. Sklonuj repozytorium.
2. Utwórz wirtualne środowisko: `python -m venv .venv ; .venv\Scripts\Activate.ps1`
3. Zainstaluj zależności: `pip install -r requirements.txt`
4. Uruchom terminal: `python -m apps.terminal.main`

### Deployment na Raspberry Pi
Skrypt `deploy_to_pi.bat` automatyzuje cały proces:
1. Kopiuje pliki projektu na RPi przez SSH/SCP (z pominięciem `.venv`, `data/`, `__pycache__`).
2. Restartuje daemona `systemd` (`systemctl restart regis`), który uruchamia `apps/server/main.py`.

Adres IP Raspberry Pi jest na stałe wpisany w kilku miejscach w kodzie (dług techniczny). Docelowo powinien być konfigurowalny przez `data/settings.json`.

### Gdzie są na stałe wpisane adresy IP (hardcode)
Przy zmianie topologii sieci należy zaktualizować ręcznie:
- `core/llm_engine.py` — adres Ollamy na RPi (`OLLAMA_BASE_URL`)
- `core/remote_client.py` — adres serwera API RPi
- `apps/terminal/main.py` — adres serwera przy trybie `remote`
- `data/settings.json` — adres HA i URL serwera
