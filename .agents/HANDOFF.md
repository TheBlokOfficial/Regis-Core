# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze aktualizuj przed jej zakończeniem (zgodnie z protokołem w AGENTS.md).

## Ostatnia Aktywność (Sesja 2026-07-22 — Restrukturyzacja Dokumentacji i Filozofia Projektu)

### Co zostało zrobione
Sesja była w 100% dokumentacyjna — żaden kod nie został zmieniony.

* **[NOWY PLIK] `docs/MANIFEST.md`** — Stworzono od zera podczas dyskusji z użytkownikiem. Definiuje filozofię projektu, Złotą Zasadę ("Nie Przeszkadzaj"), nową architekturę dynamicznego dispatchera (Kontroler + Węzły Robocze + Satelity), Rejestr Encji z metadanymi przestrzennymi, decyzję o dwóch trybach pracy modelu (Baseline NLU vs Agent ReAct), Persona Contract oraz dług architektoniczny. To jest NAJWAŻNIEJSZY PLIK w projekcie.

* **[NOWY PLIK] `docs/ONBOARDING.md`** — Pełna mapa kodu: opis każdego katalogu, pliku i ich roli, przepływ jednego polecenia przez wszystkie warstwy systemu (od CLI do Home Assistanta), docelowy model dystrybucji (pip extras), workflow deweloperski i lista miejsc z hardcode'owanymi adresami IP.

* **[NOWY PLIK] `docs/AGENT_GUIDE.md`** — Przewodnik dla agentów AI pracujących nad projektem. Zawiera: hierarchię lektury, tabelę podjętych decyzji których nie należy ruszać, ostrzeżenie przed skażeniem kontekstu (context contamination), mechanizm Czystego Architectural Handoff (format wpisu DECYZJA_ARCHITEKTONICZNA w HANDOFF.md), prawa zapisu do dokumentów.

* **[ZAKTUALIZOWANY] `.agents/AGENTS.md`** — Protokół startowy rozszerzony: agent musi teraz czytać `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` jako pierwsze (przed HANDOFF.md i TASKS.md). Sekcja filozofii zaktualizowana — MANIFEST.md jest najwyższym autorytetem, ARCHITECTURE.md jest starszym dokumentem.

### Stan projektu
* Wszystkie nowe pliki działają — są to dokumenty Markdown, nie wymagają uruchamiania.
* Kod jest niezmieniony. Wszystkie poprzednie funkcje działają tak samo jak przed tą sesją.
* Plik `walkthrough.md` NIE został zaktualizowany — zmiany tej sesji były czysto dokumentacyjne, nie architektoniczne w sensie kodu.

### Kluczowe ustalenia z tej sesji (dla kolejnego agenta)
1. **Nowa architektura (docelowa, niezaimplementowana):** Dynamiczny Dispatcher — Kontroler (singleton na RPi5) + Węzły Robocze (desktop, laptop) + Satelity (ESP32, desktop, terminal). Szczegóły w `docs/MANIFEST.md`.
2. **Dwa tryby pracy modelu (rozstrzygnięte):** 1.5B = NLU parser (Structured Outputs), 14B = ReAct Agent. Przepaść jest świadomą decyzją — nie walczyć z nią.
3. **Największy dług techniczny:** `apps/server/main.py` pełni rolę i Kontrolera i Węzła Roboczego. Musi być rozdzielone przed jakąkolwiek refaktoryzacją dystrybucji.
4. **Hardcode'owane adresy IP:** Są w `core/llm_engine.py`, `core/remote_client.py`, `apps/terminal/main.py` i `data/settings.json`. Powinny być scentralizowane.
5. **Protokół eskalacji:** Gdy agent roboczy natrafi na decyzję architektoniczną w zaśmieconym kontekście — zapisuje wpis `DECYZJA_ARCHITEKTONICZNA` w HANDOFF.md i kończy sesję. Nie decyduje sam.

### Następne kroki (dla kolejnego agenta)
Priorytety kodowe z TASKS.md:
* TTS (Text-To-Speech) — następna warstwa po STT
* WakeWord — czekamy na próbki audio użytkownika
* Handoff/routing między węzłami — wymaga rozdzielenia Kontrolera od Węzła Roboczego

---

## Poprzednia Aktywność (Sesja 2026-07-22 — Wdrożenie Scentralizowanego STT Whisper)

* **[PROTOTYP STT]** Skonstruowano aplikację "Satelity", która służy do przechwytywania dźwięku (`sounddevice`) po stronie klienta PC (symulując fizyczny mikrofon).
* **[ZCENTRALIZOWANY STT NA SERWERZE]** Satelita wysyła zarejestrowany plik `.wav` przez sieć, a cały ciężar przetwarzania dźwięku za pomocą modelu `faster-whisper` (rozmiar `small`) przejął główny serwer API. Model STT utrzymywany jest 24/7 w pamięci RAM.
* **[WYDAJNOŚĆ]** Model `small` skutkuje opóźnieniem ~9 sekund na Malince. Docelowo rozważyć zejście na model `tiny` dla 1-2 sekund latencji.

## Poprzednia Aktywność (Sesja 2026-07-22 — Konfiguracja NAS na RPi 5)

* Skonfigurowano RPi 5 jako dysk sieciowy (NAS/Samba) z dyskiem NVMe. Zmapowano dyski sieciowe na Windowsie.

## Poprzednia Aktywność (Sesja 2026-07-22 — NLU Structured Outputs i Optymalizacja HA)

* Przebudowano tier Butler na Structured Outputs (JSON Schema). Usunięto wąskie gardło GET all_states i pętli TCP. Wdrożono `requests.Session()`.

## Wiedza i Przemyślenia (Gotchas)

* Małe modele (7B) nie znoszą zakazów w próżni — użyj kontrastujących Few-Shot.
* Qwen 2.5 natywnie wymusza parallel tool calling — Stop Tokens to absolutna konieczność.
* Pamiętaj o ascetycznym UX. Unikaj jaskrawych kolorów.
* Zawsze używaj `;` zamiast `&&` w PowerShell.
