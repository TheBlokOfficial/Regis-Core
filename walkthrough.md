# Projekt Regis - Inteligentny Lokaj Domowy

## Wizja Projektu
Regis to system zarządzania inteligentnym domem oparty na zaawansowanym modelu językowym (LLM). Projekt ma na celu stworzenie lokalnego, w pełni prywatnego asystenta pełniącego rolę domowego administratora ("lokaja"). Regis nie jest zwykłym chatbotem – posiada dostęp do dynamicznej listy narzędzi. Z ich pomocą potrafi analizować stan otoczenia, podejmować decyzje i fizycznie sterować inteligentnym domem.

## Architektura Systemu
System działa jako rozproszona sieć lokalna i składa się z trzech głównych filarów:

1. **Centrala Obliczeniowa (Regis-Core + Regis-Wakeword)**
   - **Obecnie (Dev):** Komputer stacjonarny (PC) wyposażony w kartę graficzną NVIDIA RTX 5070, która uciąga ciężar wnioskowania modeli językowych.
   - **Docelowo (Prod):** Raspberry Pi 5 (8 GB RAM) z dyskiem 1 TB NVMe (970 EVO) działające jako serwer 24/7.
   - **Zadanie:** Działanie jako główny mózg – uruchamianie modelu LLM, odbieranie i analizowanie sygnału z satelit (Wakeword) oraz zarządzanie narzędziami.

2. **Warstwa Wykonawcza (Home Assistant)**
   - **Infrastruktura:** Uruchomiony w kontenerze Docker na osobnym Raspberry Pi (4 GB).
   - **Zadanie:** Pośredniczenie między inteligentnym domem (żarówki, sensory, termostaty) a Regisem. Główny Mózg łączy się z API Home Assistanta jako zwykły klient o uprawnieniach administratora.

3. **Infrastruktura Satelitarna (Nasłuch i Komunikacja)**
   - **Sprzęt:** Płytki deweloperskie ESP32 wyposażone w mikrofony i głośniki rozmieszczone we wszystkich pomieszczeniach w domu.
   - **Zadanie:** Czuwanie i strumieniowanie dźwięku do głównej centrali. To one są "uszami i ustami" systemu w całym domu.

## Moduły w repozytorium Regis-Core
W projekcie zastosowano architekturę modułową:
- `core/` (Silnik) - Zawiera m.in. `llm_engine.py` wstrzykujący konteksty dla LLMa i odbierający komendy w formacie JSON. Pobiera też dynamicznie listę modeli z API Ollamy (`api/tags`).
- `integrations/` (Zewnętrzne systemy) - Posiada `ha_client.py` (komunikacja API z fizycznym HA) oraz `ha_mock.py` (środowisko testowe na sucho).
- `data/` (Pamięć) - Katalog z ignorowanymi w repozytorium plikami lokalnymi (np. stan mockowanego domu, lista aktywnych modeli).
- `tools/` (Narzędzia Dev) - Skrypty pomocnicze jak `symulator_llm.py` oraz `test_context.py` ułatwiające debugowanie (z ładnym kolorowaniem składni dzięki bibliotece `rich`).
- `main.py` - Główny punkt wejściowy programu. Renderuje w pełni responsywny i czysty interfejs za pomocą `rich` oraz `questionary`.

## 🎨 Interfejs i UX
Aby pozbyć się "terminalowego bałaganu" i ściany tekstu, projekt używa zaawansowanego formatowania:
- **Konfigurator startowy**: Użytkownik wybiera model ze wstrzykiwanej na żywo listy z Ollamy. Modele mogą być oznaczane jako "Aktywne", co filtruje ekran startowy.
- **Single-Turn Render**: Główna pętla czatu czyści ekran przy każdej wiadomości, zapewniając zawsze jeden czysty, zorganizowany widok (Wiadomość użytkownika -> Systemowa detekcja -> Odpowiedź Regisa).

## Najbliższe Kroki i Rozwój
- **Wielozadaniowość i Narzędzia:** Aktualnie głównym i jedynym narzędziem Regisa jest Home Assistant. W planach jest stworzenie systemu wtyczek (Agentic Tools), którymi LLM będzie mógł operować.
- **Audio i Komunikacja:** Integracja serwera odbierającego dźwięk z urządzeń ESP32 oraz połączenie z `Regis-Wakeword`.
- **System Pamięci:** Dopisanie zarządzania historią konwersacji, aby Regis pamiętał kontekst wypowiedzi sprzed kilku minut.
- **Optymalizacja i Migracja:** Przeniesienie całości na RPi5 i testy płynności oraz responsywności lokalnego modelu AI.
