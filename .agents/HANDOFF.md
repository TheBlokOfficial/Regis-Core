# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność
* Naprawiono bugi CLI związane z formatowaniem i odstępami (ujednolicenie renderowania wiadomości w czasie rzeczywistym i po odświeżeniu, dezaktywacja auto-highlightera biblioteki `rich`).
* Zmieniono architekturę zapamiętywania `tool_calls`. Teraz historia przetrzymuje "ukryte wewnętrzne przemyślenia" ze znacznikiem `is_internal: True`, zignorowane przez UI, co zapobiega awariom API.
* Dodano i wdrożono narzędzia dla asystenta: `get_current_time` oraz `get_weather` (korzystające z darmowego publicznego API wttr.in).

## Obecny Stan Projektu
* Interfejs graficzny działa bez zarzutów, wszystkie wiadomości i timestampy renderują się spójnie (kolor dim green).
* Czas, pogoda i podstawowe narzędzia HA działają w integracji z modelem LLM.

## Następne Kroki (Next Steps)
1. **Długoterminowa Pamięć (Notatnik):** Zaimplementowanie notatnika, o którym rozmawiano z użytkownikiem, by bot zapamiętywał miasto dla pogody.
2. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper), jak zaplanowano.

## Wiedza i Przemyślenia (Gotchas)
* Pamiętaj o zachowaniu ascetycznego UX (zgodnie z `AGENTS.md`).
* Nie zmieniaj kodu źródłowego bez wyraźnego polecenia użytkownika.
* Pamiętaj o uruchomieniu procedury zamykającej, gdy użytkownik powie "kończymy" lub podobnie.
