# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność
* **[NOWE]** Wdrożono eksperymentalną, testową integrację z modelami chmurowymi z rodziny **Gemini API** firmy Google. Dodano klasę `GeminiEngine` zdolną do parsowania formatu OpenAI, omijając hacki wymagane dla lokalnej Ollamy.
* Rozbudowano CLI o komendę `/provider`, dzięki czemu użytkownik może w każdej chwili "w locie" przełączyć się pomiędzy bezpiecznym lokalnym modelem (Qwen z Ollamy) a potężnym chmurowym bytem (np. `gemini-1.5-pro` lub najnowszymi modelami z rodziny 3.0/3.1 pobieranymi dynamicznie z API za pomocą klucza). Odpowiedzi na narzędzia zostały specjalnie "utwardzone" pod kątem restrykcyjnego parsera Google (dodanie `name` oraz `thought_signature`).
* Zaimplementowano Pamięć Długoterminową (Notatnik). Zrefaktoryzowano prompt systemowy w `base_system.md`, eliminując sztywne zakazy nakładające "paranoję" na model. Przełączono model na podejście proaktywne: ma swobodę rozmawiania, dopytywania o kontekst i ZAWSZE sprawdza `read_notes` przed zadawaniem pytań w ciemno.
* Dostosowano parametry LLM w `core/llm_engine.py`: Zwiększono karę za powtórzenia na ostrożne 1.05. Zastosowano dynamiczny `num_predict`.
* Dodano komendę `/models` w `ui/cli.py` umożliwiającą szybkie testowanie (hot-swap) różnych modeli z Ollamy za pomocą interfejsu questionary podczas jednej sesji.

## Obecny Stan Projektu
* Interfejs graficzny działa bez zarzutów. Konsola działa płynnie jako REPL, pozwalając na scrollowanie tysięcy linii w górę, zachowując zgrabne rozdzielenia wizualne pomiędzy narzędziami a promptami.
* Model posiada genialny wewnętrzny monolog strumieniowany w locie kolorem szarym (`🧠 Myśli agenta:`).
* Wdrożono rozwiązanie **Two-Pass Generation**.
* Pamięć długoterminowa jest w 100% stabilna (dynamiczne czytanie z/do dysku przez JSON). Model 14b/32b skutecznie posługuje się nią by omijać halucynacje.

## Następne Kroki (Next Steps)
1. **Handoff (Boss Mode):** System w tle na PC nasłuchujący żądań i delegowanie do modelu 14b, jeśli dostępne są zasoby VRAM.
2. **System Audio:** Badania i integracja WakeWord (Porcupine / OpenWakeWord) oraz silnika STT (Whisper).
3. **Optymalizacja Modelu 32b:** Model jest doskonały pod kątem logiki, ale wysyca VRAM na RTX 5070 i powoduje dramatyczne "zwisy" (aż 15 sekund na odzew) z uwagi na RAM offloading. Znaleźć złoty środek między inteligencją 14b a możliwościami dedykowanymi pod STT.

## Wiedza i Przemyślenia (Gotchas)
* Pamiętaj o zachowaniu ascetycznego UX. Unikaj bogatych, krzykliwych kolorów (tylko zgaszona zieleń lub szarość). W konsoli odstawiliśmy skomplikowane grafiki by uzyskać potężny terminal REPL.
* Małe modele 7B/14B są potężnie leniwe bez myślenia na głos. Muszą prowadzić monolog. Jeśli wdrożysz nową mechanikę i zniknie strumień myśli z terminala - przerwij i to napraw, bo jakość spadnie drastycznie!
* Modele z rodziny Qwen mają gigantyczną bazę danych w wielu językach (np. rosyjski, chiński). Zbyt wysokie `repeat_penalty` (np. 1.15) zmusza je do ratowania się przed powtórzeniami ucieczką w inny język! Pilnuj tego parametru.
* Nie dodawaj agentom instrukcji jak do głupków ("Zasada Krytyczna: zrób to czy tamto"). Daj im same narzędzia, stwórz przykład few-shot lub jasno napisz kontekst, a poradzą sobie genialnie.
* Zawsze używaj operatora średnika `;` zamiast `&&` w terminalu podczas pracy, ponieważ OS to Windows/PowerShell.
