# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność
* Wydzielono założenia projektowe z `AGENTS.md` do dedykowanego pliku `docs/ARCHITECTURE.md` (Zasada Apple, RPi5 dla `qwen2.5:7b` oraz PC dla `qwen2.5:14b`).
* Usunięto cały stary system profili (`profiles.json`) oraz zrefaktoryzowano architekturę tak, aby działała w oparciu o sztywno zdefiniowane warstwy (tier): `local` (Recepcjonista) i `boss` (Główny Gospodarz).
* Wyczyszczono `ui/cli.py` z nadmiarowych opcji, trybu debugowania oraz komend czatu dla profili i temperatur. Menu to teraz tylko "Uruchom" i "Wyjście", a w czacie jedyną komendą konfiguracyjną jest `/tier`.
* Naprawiono bug wyciekającego kodu JSON z Qwen2.5 poprzez dopisanie restrykcyjnej zasady (brak tekstu przed uruchomieniem narzędzia) w `BASE_SYSTEM_PROMPT`.

## Obecny Stan Projektu
* Interfejs graficzny działa bez zarzutów i ładuje się natychmiastowo. Pętla uruchomieniowa opiera się na konfiguracji `settings.json` (klucz `active_tier`).
* Funkcje narzędziowe działają, model nie powinien już wypisywać surowego kodu JSON na ekran (dzięki sztywnej dyrektywie promptu).

## Następne Kroki (Next Steps)
1. **Długoterminowa Pamięć (Notatnik):** Zaimplementowanie notatnika, o którym rozmawiano z użytkownikiem, by bot zapamiętywał miasto dla pogody. To jest NAJWYŻSZY priorytet na początek następnej sesji.
2. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do modelu 14b, jeśli dostępne są zasoby VRAM.
3. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).

## Wiedza i Przemyślenia (Gotchas)
* Pamiętaj o zachowaniu ascetycznego UX (zgodnie z `AGENTS.md`).
* Nie zmieniaj kodu źródłowego bez wyraźnego polecenia użytkownika.
* Nie dodawaj nowych komend konfiguracyjnych; system ma być bezobsługowy dla użytkownika (zasada Apple).
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
