# Regis-Core: Manifest Projektu

Ten dokument definiuje duszę projektu Regis-Core. Służy jako najwyższy kompas dla programistów oraz agentów AI pracujących przy kodzie. Jeśli jakakolwiek nowa funkcja, narzędzie lub decyzja architektoniczna jest sprzeczna z tym dokumentem — należy ją odrzucić.

---

## 1. Czym jest Regis-Core?

Projekt to **lekka i błyskawiczna warstwa abstrakcji** pomiędzy domownikami a urządzeniami Smart Home.
Jego siłą napędową nie jest paląca potrzeba, lecz czysta, technologiczna pasja (hobby). Celem samym w sobie jest zbudowanie **autonomicznej, modularnej i perfekcyjnie zorganizowanej architektury** zarządzania domem. Z tego powodu jakość, spójność i czystość kodu są tu ważniejsze niż szybkie dostarczanie funkcji (tzw. "dowożenie").

---

## 2. Złota Zasada: Przezroczystość (Zasada "Nie Przeszkadzaj")

**System musi być organiczny i nigdy nie może wchodzić użytkownikowi w drogę.**

Największym grzechem w tym projekcie jest implementacja funkcji "na siłę", tylko dlatego, że technologia na to pozwala. Jeśli nowa funkcjonalność (nawet najbardziej zaawansowana technologicznie) sprawia, że system staje się uciążliwy, wolny lub irytujący — należy ją usunąć lub całkowicie przeprojektować. W najgorszym scenariuszu Regis ma być po prostu **niewidzialny i bezkolizyjny** dla domowników.

---

## 3. Architektura: Dwie Usługi Produkcyjne

System składa się z dwóch oddzielnych, luźno powiązanych usług produkcyjnych. Każda jest niezależnie instalowana na dedykowanym urządzeniu.

### 3.1 Kontroler (`regis_controller`)
- **Rola:** Mózg systemu i jedyne źródło prawdy. Zarządza rejestrem aktywnych węzłów roboczych, routingiem sesji oraz wykonywaniem narzędzi Home Assistant.
- **Deployment:** Zawsze i tylko Raspberry Pi 5 (Linux). Singleton — może istnieć dokładnie jedna instancja. Dystrybuowany jako pakiet `.whl`.
- **Kluczowa zasada:** Kontroler to lekki daemon — nigdy nie hostuje modelu LLM. Jest jedynym punktem komunikacji z Home Assistant; węzły robocze nigdy nie mają dostępu do HA bezpośrednio.
- **Migracja kontekstu:** Przy pojawieniu się mocniejszego węzła, Kontroler czeka na zakończenie aktywnych konwersacji na słabszym węźle, a nowe sesje od razu kieruje do mocniejszego. Downgrade uznawany jest za edge case pomijalny.

### 3.2 Węzeł (`regis_node`)
- **Rola:** Zunifikowana usługa Windows łącząca rolę Węzła Roboczego i Satelity w jednej aplikacji.
- **Deployment:** Instalowany na dowolnym Windows PC zdolnym do uruchomienia modelu (desktop, laptop). Dystrybuowany jako **Portable App** (folder z binarką PyInstaller + `Uruchom.bat`).
- **Forma:** Aplikacja **System Tray** — działa jako ikona w pasku zadań. Worker LLM i Satellite audio to ukryte procesy w tle zarządzane przez panel tray.
- **Koegzystencja:** Worker (inferencja LLM) i Satellite (przechwytywanie audio) mogą działać jednocześnie na tym samym PC — nie wykluczają się.
- **Uwaga:** Sam RPi 5 jest jednocześnie Kontrolerem i węzłem roboczym (fallback z najmniejszym modelem). Jeśli nie ma innych węzłów — RPi 5 przejmuje całość.

### 3.3 Satelita — typy interfejsów
Każdy interfejs użytkownika jest architektonicznie Satelitą — różnią się medium:
  - **ESP32** — miniaturowy, dedykowany sprzęt w domu; robi tylko VAD i strumieniowanie.
  - **Windows PC** (`regis_node`) — aplikacja tray; robi VAD + WakeWord lokalnie, resztę deleguje.
  - **Android** *(niepewna, odległa przyszłość)* — aplikacja mobilna.

### 3.4 Pipeline Przetwarzania Audio (Rozstrzygnięte)

Każde żądanie głosowe przechodzi przez następujące etapy — podział pracy między Satelitą a Węzłem Roboczym zależy od możliwości sprzętu:

**Dla ESP32 (ograniczony sprzęt):**
```
[ESP32]                              [Worker Node]
Cisza
 → VAD wykrywa mowę ludką
 → strumieniuje audio ──────────────→ WakeWord detection
                                          → brak WakeWord → odrzuć
                                          → WakeWord! → STT (Whisper)
                                          → LLM (pętla ReAct + narzędzia)
                                          → TTS
                       ←────────────── odpowiedź audio
 → odgrywa odpowiedź
```

**Dla Desktop PC (pełny sprzęt):**
```
[Desktop Satelita]                   [Worker Node]
Cisza
 → VAD wykrywa mowę
 → WakeWord detection (lokalnie)
 → przesyła audio ──────────────────→ STT (Whisper) — standaryzacja jakości
                                       → LLM (pętla ReAct + narzędzia)
                                       → TTS
                   ←───────────────── odpowiedź audio
 → odgrywa odpowiedź
```

**Kluczowe decyzje projektowe:**
- **VAD (Voice Activity Detection)** siedzi zawsze na Satelicie — jest to lekki algorytm energetyczny (kilka KB), radykalnie redukuje niepotrzebne strumieniowanie.
- **WakeWord** na ESP32 jest zbyt kosztowny — siedzi na Węźle Roboczym. Na desktopie może siedzieć lokalnie.
- **STT zawsze na Węźle Roboczym** — standaryzuje jakość transkrypcji niezależnie od Satelity. Jeden model Whisper = jedna jakość dla wszystkich urządzeń.

---

## 3.5 Warstwa Integracji (Rozstrzygnięta Zasada Architektoniczna)

**Home Assistant jest jedną z możliwych integracji — nie jedyną.**

Katalog `integrations/` to granica między logiką systemu a światem zewnętrznym. HA jest pierwszą i prawdopodobnie największą integracją (żarówki, przełączniki, klimatyzacja, odtwarzacze — wszystko co najłatwiej podłączyć przez HA), ale architektura nie zakłada jego wyłączności.

Przyszłe integracje mogą obejmować m.in.:
- Bezpośrednia komunikacja MQTT
- Inne platformy Smart Home (np. Zigbee2MQTT)
- Własne skrypty i usługi sieciowe
- Dowolny inny endpoint, który ma sens w kontekście sterowania domem

**Konsekwencja dla kodu:** `ToolsRegistry` i `RemoteToolsRegistry` są agnostyczne wobec źródła narzędzi — rozmawiają z `integrations/` przez abstrakcyjny interfejs, nie bezpośrednio z HA. Dodanie nowej integracji oznacza: nowy plik w `integrations/`, nowe narzędzie w `core/schemas.py` i nowy handler w `core/tools_registry.py`. Żadne inne warstwy nie wymagają zmian.

---

## 4. Rejestr Encji (Entity Registry)

Kontroler jest jedynym źródłem prawdy. Wszystkie procesy w systemie — Satelity i Węzły Robocze — **rejestrują się** w Kontrolerze przy starcie oraz cyklicznie odnawiają swą rejestrację w tle (Continuous Registration). Dostarczają mu w ten sposób metadanych o sobie, a dzięki pętli ponawiania uodpornione są na restarty Kontrolera. Kontroler używa tych metadanych do podejmowania decyzji routingowych i budowania kontekstu dla modelu.

### Metadane Satelity
Każda Satelita przy rejestracji podaje:
- `id` — unikalny identyfikator urządzenia
- `room` — pomieszczenie, w którym fizycznie się znajduje (np. `"salon"`, `"sypialnia"`)
- `type` — typ Satelity (`esp32`, `desktop`, `terminal`)
- `capabilities` — co potrafi robić (`audio_in`, `audio_out`, `text`)
- `wakeword_local` — czy obsługuje WakeWord lokalnie (prawda dla desktopów, fałsz dla ESP32)

### Metadane Węzła Roboczego
Każdy Węzeł Roboczy przy rejestracji podaje:
- `id` — unikalny identyfikator
- `model_tier` — poziom możliwości (`low` / `medium` / `high`)
- `model_name` — konkretny model Ollamy (np. `qwen2.5:14b-instruct`)
- `vram_available` — dostępna moc obliczeniowa (VRAM lub RAM)

### Kontekst Przestrzenny (Spatial Context Filtering)

To jest kluczowy mechanizm umożliwiający efektywną pracę małych modeli.

Gdy Satelita z pomieszczenia `salon` wysyła żądanie, Kontroler **nie podaje modelowi pełnej listy urządzeń domowych**. Zamiast tego filtruje ją do urządzeń przypisanych do pokoju `salon` i buduje dla modelu wąski, precyzyjny kontekst. Model 1.5B operuje wtedy na liście 5 urządzeń zamiast 50 — to nie jest ograniczenie, to jest precyzja.

**Otwarta kwestia — cross-room commands:** Co gdy użytkownik w salonie mówi "wyłącz światło w sypialni"? Propozycja: model dostaje domyślnie swój pokój, ale posiada narzędzie `get_devices(room=...)` pozwalające mu sięgnąć po inne pomieszczenie gdy wyraźnie o to prosi. Większy model na desktopie może od razu otrzymywać pełną listę urządzeń. **Nierozstrzygnięte — wymaga dalszej dyskusji.**

### Co Kontroler synchronizuje do Węzłów
Kontroler przechowuje i dystrybuuje:
- **Prompty systemowe** — tożsamość Regisa, instrukcje behawioralne (rdzeń persony)
- **Historia konwersacji** — aktywne sesje, umożliwia migrację kontekstu między węzłami
- **Rejestr wszystkich encji** — lista aktywnych Satelit i Węzłów z metadanymi

---

## 5. Dwa Tryby Pracy (Rozstrzygnięta Decyzja Produktowa)

Na Raspberry Pi 5 model 3B generuje tokeny zbyt wolno przy braku GPU — wzrost inteligencji nie jest proporcjonalny do kosztów. Model 1.5B nadaje się tylko do parsera NLU. Tworzy to przepaść, nie płynną skalę.

**Decyzja: Zaakceptować przepaść, nie walczyć z nią.** Regis ma dwa tryby pracy i jest to świadomy wybór projektowy, nie defekt.

| | Regis-Baseline (1.5B, RPi5) | Regis-Agent (14B, Desktop) |
|---|---|---|
| **Rola** | Deterministyczny parser komend | Myślący agent z pętlą ReAct |
| **Dostępność** | 24/7, zawsze | Tylko gdy desktop jest włączony |
| **Zakres** | Komendy urządzeń z danego pokoju | Pełny zakres narzędzi i rozmowa |
| **Odpowiedź na pytania poza zasięgiem** | *"To przekracza moje obecne możliwości."* — zwięźle, bez tłumaczeń | Obsługuje |  

**Dlaczego przepaść jest akceptowalna:**
Użycie głosowe i użycie konwersacyjne są naturalnie rozdzielone w czasie. Gdy użytkownik chce sterować domem głosem, siedzi na kanapie — komputer jest wyłączony. Gdy chce rozmawiać z agentem, siedzi przy komputerze — który jest włączony. Korelacja jest naturalna. Użytkownik przez doświadczenie uczy się oczekiwań bez żadnych komunikatów technicznych.

---

## 6. Persona Regisa

**Zasada: Dla użytkownika zawsze istnieje jeden Regis.** Niezależnie od tego, który model pracuje pod spodem, persona i zachowanie muszą być spójne.

### Charakter
Regis jest **charakterny, rzeczowy i bezpośredni.** Nie owija w bawełnę. Priorytetem jest szybkość, niezawodność i precyzja. Nie jest chatbotem — jest narzędziem z osobowością. Mówi do rzeczy, nie dopełnia odpowiedzi niepotrzebnymi wstępami ani podziękowaniami.

### Implementacja spójności między trybami
- **Wspólny rdzeń persony:** W każdym prompcie, niezależnie od trybu i tieru, osadzony jest nienaruszalny opis tożsamości Regisa. Jego ton i styl nie zmieniają się — Baseline brzmi tak samo jak Agent.
- **Graceful Degradation (Elegancki Upadek):** Baseline nigdy nie udaje, że potrafi coś, czego nie potrafi. Odpowiada zwięźle i bez przepraszania. Brak tłumaczeń technicznych.
- **Capability Layer (Warstwa Możliwości):** Prompty pisane są warstwowo. Rdzeń persony jest stały. Zestaw narzędzi i tryb pracy (NLU vs ReAct) zmienia się w zależności od tieru aktywnego węzła.

---

## 7. Dług Architektoniczny (Stan Obecny vs. Wizja)

Mimo że `apps/controller/` i `apps/worker/` są dziś rozdzielnymi procesami API połączonymi przez Rejestr Encji, cały projekt zderzył się ze ścianą monolitycznej dystrybucji kodu i plików konfiguracyjnych.

**Problem Monolitu i Konfiguracji (Priorytet Architektoniczny)**
**Rozwiązany Dług Dystrybucyjny i Konfiguracyjny (Zrealizowano)**
W początkowej fazie projektu wszystkie procesy dzieliły zcentralizowane pliki konfiguracyjne, a transfer kodu źródłowego na węzły brzegowe prowadził do nadpisywania ich tożsamości. Problem ten, opisany w raporcie `docs/architectural_debt_report.md`, został już pomyślnie i permanentnie rozwiązany. 
System został rozbity na w pełni wyizolowane instancje — konfiguracja opiera się teraz na profilach ładowanych z plików `.env` (np. `settings.rpi5-worker.json`), a przestarzałą dystrybucję kodu zastąpiono hermetycznymi paczkami instalacyjnymi (`.whl` dla Linuksa oraz `.exe` przez PyInstaller dla Windows). To ostatecznie uczyniło architekturę modularną.
**Problem Hardkodowania IP i Auto-Konfiguracji (Oczekujące na realizację)**
Obecnie rozwiązano problem nadpisywania tożsamości urządzeń, ale proces wciąż posiada defekt "hardkodowanych IP". Wymusza to ręczne ustawianie adresu IP Malinki na każdym urządzeniu satelitarnym. Został przygotowany dokument `docs/auto_discovery_rfc.md` szczegółowo opisujący plan wdrożenia protokołu **Zero-Conf (UDP Broadcast)** oraz zautomatyzowanego generowania plików po kompilacji. Będzie to kolejny kluczowy krok w ewolucji systemu.
