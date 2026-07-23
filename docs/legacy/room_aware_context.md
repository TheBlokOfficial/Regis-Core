# Koncepcja: Świadomość Przestrzenna (Room-Aware Context)

## Problem z małymi modelami LLM (1.5B/3B)
Małe modele mają skłonność do "lenistwa" lub gubienia się podczas korzystania z narzędzi analitycznych (np. `get_devices`), co wydłuża czas reakcji lub prowadzi do błędów (halucynowania ID).

## Propozycja rozwiązania
Zamykanie dostępnych urządzeń Home Assistant tylko do tych, które fizycznie znajdują się w pokoju, w którym operuje dana Satelita nasłuchująca (np. w Salonie).

Gdy użytkownik wyda polecenie w rodzaju "zapal światło", model otrzyma z góry zdefiniowany, bardzo wąski kontekst z listą dostępnych w tym pokoju urządzeń. Zamiast odpytywać API o ID, model odruchowo wywoła `execute_ha_action(turn_on, ID_LOKALNEJ_LAMPY)`. Powoduje to, że proste komendy stają się jednoznaczne i są realizowane ułamkach sekund bez dodatkowych poszukiwań.

## Projekt Architektury (Stateless Server)
Zamiast trzymać mapowanie pokojów na serwerze API na Malince, to **Satelita (klient)** będzie wysyłał serwerowi gotową listę swoich urządzeń w paczce żądania. Każda satelita będzie posiadać swój lokalny plik konfiguracyjny (np. `.env` lub `config.json`) z listą powiązanych ID.

### Planowane Zmiany w Kodzie

**1. apps/server/main.py**
Rozszerzenie modelu wejściowego `ChatRequest` o nowe, opcjonalne pole `context_devices`:
```python
class ChatRequest(BaseModel):
    message: str
    context_devices: list[dict[str, str]] | None = None
```

**2. core/llm_engine.py**
Odbiór `context_devices` z żądania HTTP i przekazanie ich aż do metody budowania promptu. Jeśli lista istnieje, zostanie dynamicznie doklejona na sam koniec system_promptu, tworząc tzw. "Kontekst Lokalny" (np. "Jesteś fizycznie w Kuchni. Urządzenia: ...").

**3. apps/terminal/cli.py oraz apps/satellite/main.py**
Dodanie do klientów możliwości doczepiania swojej predefiniowanej listy urządzeń (symulującej fizyczne umiejscowienie w przestrzeni domu) i doklejania ich do payloadu HTTP `POST /v1/chat/stream`.

## Pytania otwarte na przyszłość
* Czy w przypadku poleceń w rodzaju "Zgaś wszystkie światła w domu", Satelita powinien tracić tę hermetyczność i wysyłać zapytanie o całą bazę HA? A może Satelita powinien z założenia sterować TYLKO swoim pokojem?
