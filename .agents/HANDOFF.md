# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność
* Wydzielono założenia projektowe z `AGENTS.md` do dedykowanego pliku `docs/ARCHITECTURE.md` (Zasada Apple, RPi5 dla `qwen2.5:7b` oraz PC dla `qwen2.5:14b`).
* Usunięto cały stary system profili (`profiles.json`) oraz zrefaktoryzowano architekturę tak, aby działała w oparciu o sztywno zdefiniowane warstwy (tier): `local` (Recepcjonista) i `boss` (Główny Gospodarz).
* Wyekstraktowano wszystkie prompty psychologiczne z kodu Pythonowego do plików Markdown (`data/prompts/`). Baza jest oddzielona od charyzmatycznego Regisa i surowego Lokaja. Silnik ładuje je używając Lazy Loadingu.
* Poprawiono nomenklaturę systemu: warstwy zostały przemianowane w kodzie i plikach z `local`/`boss` na `butler`/`regis`. Zablokowano w profilu `tier_regis.md` możliwość uciążliwego "chwalenia się" swoimi narzędziami.
* Wdrożono "Solid-State AI" (Dynamic Deduction). Agent nie otrzymuje już listy urządzeń w system promptcie (puste biurko). Jeśli zmyśli encję, The Warden odbija akcję żądając od niego zbadania środowiska przez narzędzie `get_devices`.
* Usunięto błędy terminalowe, naprawiając znikające myśli i podwójne entery. Wprowadzono architekturę "Infinite Scrolling REPL" w miejsce wymazywanego ekranu.
* Zmierzono się z ograniczeniami mniejszych modeli LLM. Opracowano rozwiązanie dla "Kaskady Halucynacji" dodając rygorystyczny mechanizm **Chain of Thought** (Głośnej Analizy przed wywołaniem API) w pliku `base_system.md`. Przetestowano `qwen2.5:32b`, ostatecznie wspierając lekkiego Lokaja (`qwen2.5:7b`) i Regisa (`qwen2.5:14b`) rygorystycznymi, zimnymi temperaturami (0.1 / 0.4) w `ui/cli.py` i `main.py`.
* Zoptymalizowano system the Wardena w `core/schemas.py` i `tools_registry.py` (`get_device_state`) o zdolność przetwarzania masowych tablic urządzeń na raz, rozwiązując problem gubienia kontekstu i pętli przez 7B. Zmieniono prompt `tier_regis.md` z zakazowego na w pełni afirmatywny, odcinając ucieczki modelu w obce języki.

## Obecny Stan Projektu
* Interfejs graficzny działa bez zarzutów. Konsola działa płynnie jako REPL, pozwalając na scrollowanie tysięcy linii w górę, zachowując zgrabne rozdzielenia wizualne pomiędzy narzędziami a promptami.
* Model posiada genialny wewnętrzny monolog strumieniowany w locie kolorem szarym (`🧠 Myśli agenta:`).
* Funkcje narzędziowe (Tool Calling) zostały zrefaktoryzowane pod kątem "kuloodporności". Wdrożono "The Warden" w `core/tools_registry.py`, który odrzuca halucynacje z twardym błędem informacyjnym.
* Wdrożono rozwiązanie **Two-Pass Generation**. W pierwszej pętli agent głośno myśli z temp 0.1, po odnalezieniu wyników z narzędzi generuje końcową, charyzmatyczną odpowiedź dla użytkownika.

## Następne Kroki (Next Steps)
1. **Długoterminowa Pamięć (Notatnik):** Zaimplementowanie notatnika, o którym rozmawiano z użytkownikiem, by bot zapamiętywał miasto dla pogody. To jest NAJWYŻSZY priorytet na początek następnej sesji.
2. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do modelu 14b, jeśli dostępne są zasoby VRAM.
3. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).

## Wiedza i Przemyślenia (Gotchas)
* Pamiętaj o zachowaniu ascetycznego UX. Unikaj bogatych, krzykliwych kolorów (tylko zgaszona zieleń lub szarość). W konsoli odstawiliśmy skomplikowane grafiki by uzyskać potężny terminal REPL.
* Małe modele 7B są potężnie leniwe bez myślenia na głos. Muszą prowadzić monolog. Jeśli wdrożysz nową mechanikę i zniknie strumień myśli z terminala - przerwij i to napraw, bo jakość spadnie drastycznie!
* Nie dodawaj agentom instrukcji jak do głupków ("Zasada Krytyczna: zrób to czy tamto"). Daj im same narzędzia i pozwól działać. To prawdziwe Agenty!
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
