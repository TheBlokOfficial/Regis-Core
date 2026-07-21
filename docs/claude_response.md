# Ocena Architektoniczna — Regis-Core

**Wersja:** 1.0 | **Zakres:** ReAct loop, system biurka, zarządzanie historią, prompty, diagnoza bugów, rekomendacja przebudowy

---

## TL;DR — trzy rzeczy, które naprawiłbym najpierw

1. **Kolizja natywnego tool-callingu Ollamy z customowymi tagami.** Wysyłacie `tools: tools_registry.tools_schema` do Ollamy, a Ollama dla modeli Qwen 2.5 *automatycznie* dokleja do system message własny, **angielski** blok instrukcji o wywoływaniu funkcji (sekcję `# Tools`, ze zdaniem *"You may call one or more functions to assist with the user query..."*), definiujący **te same tagi `<tool_call>`**, których wy również używacie w swoim promptcie. Macie więc dwa niezależne, nie do końca spójne zestawy instrukcji o tym samym mechanizmie, z których jeden jest po angielsku i wstrzykiwany bliżej końca system message (czyli z wyższą wagą recency). To najbardziej prawdopodobne wyjaśnienie Testu 2.
2. **`num_ctx: 4096` to bomba zegarowa, a Ollama ucina kontekst OD PRZODU.** Gdy prompt przekroczy `num_ctx`, Ollama nie zwraca błędu — po cichu obcina najstarsze tokeny. "Najstarsze" w Waszym payloadzie to **system message** (3 warstwy promptu + schematy narzędzi + few-shoty). Przy 4096 tokenach i tylu narzędziach + przykładach, jesteście bardzo blisko sytuacji, w której model dostaje ucięty początek instrukcji — co idealnie tłumaczyłoby "nieprzewidywalność między turami".
3. **Wzorzec "biurka" myli dwa różne stany: "nic nie otworzyłem" z "nie ma danych".** Placeholder `"Biurko jest puste"` jest semantycznie przeciążony i to on jest odpowiedzialny za Test 1.

Poniżej szczegółowa odpowiedź na każde z 6 pytań.

---

## Pytanie 1 — Architektura scaffoldu (custom tagi vs natywny tool calling)

Krótka odpowiedź: **obecne rozwiązanie miesza dwa mechanizmy, które powinny być rozłączne, i to jest błąd projektowy, nie szczegół.**

Ollama dla rodziny Qwen 2.5 ma natywny szablon czatu, który — gdy w payloadzie API pojawia się niepuste pole `tools` — wstrzykuje do system message dodatkową sekcję (po angielsku), instruującą model, by zwracał wywołania funkcji jako JSON w tagach `<tool_call></tool_call>`. To dokładnie te same tagi, które definiujecie ręcznie w `sandwich` i `tier_prime.md`. Efekt: model dostaje **dwie kopie** instrukcji o tym samym formacie, z drobnymi rozbieżnościami we frazowaniu, jedna po polsku (wasza), jedna po angielsku (natywna, doklejona przez Ollamę na podstawie `.Tools`).

Dla modelu 7B/14B/32B trenowanego mocno na formacie Hermes-style function-calling (a Qwen 2.5 tak właśnie był trenowany), obecność natywnego, angielskiego bloku "# Tools" jest silnym sygnałem aktywującym wyuczone zachowanie z fine-tuningu: *najpierw krótkie zdanie po angielsku wyjaśniające co model zamierza zrobić, potem wywołanie*. To jest dokładnie to, co widzicie w Teście 2.

Macie więc dwie sensowne drogi, ale **nie wolno ich mieszać**:

- **Droga A (pełna kontrola, rekomendowana dla produkcji):** nie wysyłajcie w ogóle pola `tools` w payloadzie do Ollamy. Opiszcie narzędzia ręcznie w swoim promptcie (macie to już częściowo zrobione w `schemas.py` — po prostu renderujcie ten opis do tekstu promptu zamiast do pola API). Wtedy Ollama nie dokleja niczego automatycznie, a Wy macie 100% kontroli nad formatem, językiem i tonem instrukcji.
- **Droga B (natywna):** zrezygnujcie z customowego parsera i budujcie na natywnym mechanizmie Ollamy — czytacie strukturalne pole `message.tool_calls` z odpowiedzi zamiast parsować tekst. Ale uwaga: w praktyce zgłaszano niestabilności natywnego tool-callingu Ollamy z Qwen 2.5 (np. zwracanie wywołania jako zwykły tekst w `content` zamiast w `tool_calls`, albo halucynowanie argumentów niezgodnych ze schematem) — to nie jest w 100% niezawodny mechanizm i wymaga fallbacku parsującego też `content`.

Biorąc pod uwagę, że projekt ma być produkcyjny i celowo rezygnujecie z "fallbacków dla słabych modeli" — **Droga A jest spójniejsza z waszą filozofią**: dajecie sobie pełną, deterministyczną kontrolę nad promptem i nie polegacie na niezweryfikowanym, zmieniającym się między wersjami Ollamy zachowaniu natywnego parsera.

Co do samego `<thought>` — to nie koliduje z niczym natywnym (Qwen 2.5 Instruct, w odróżnieniu od QwQ czy Qwen3-thinking, nie ma wbudowanego trybu rozumowania), więc customowy tag scratchpada jest tu uzasadnionym i potrzebnym wyborem projektowym, a nie czymś do wyrzucenia. Problem nie leży w `<thought>` — leży w tym, że współistnieje z konfliktującym, natywnym blokiem o `<tool_call>`.

---

## Pytanie 2 — System biurka (desk_state)

Pomysł "otwierania aplikacji" jako sposobu na trzymanie dużych, rzadko potrzebnych danych poza stałym kontekstem jest sam w sobie rozsądny — to w gruncie rzeczy lazy-loading kontekstu. Ale w obecnej implementacji ma dwie realne wady.

**Wada 1 — dokładnie ten paradoks, o którym piszecie.** Model *musi* wywołać narzędzie, żeby zobaczyć treść, ale w iteracji, w której je wywołuje, `desk_state` jest jeszcze puste (albo ze starej sesji). To nie jest fatalne samo w sobie — typowy wzorzec "wywołaj, potem przeczytaj w następnej iteracji" — ale wymaga od modelu utrzymania intencji przez granicę iteracji ("otworzyłem, teraz muszę spojrzeć na desk_state"), co jest dokładnie tym typem stanu, który mniejsze/średnie modele gubią pod obciążeniem (a jeśli do tego dochodzi ucinanie kontekstu z Pytania 4 — gubią to jeszcze łatwiej).

**Wada 2 — i to jest prawdziwe źródło Testu 1.** Placeholder `"Biurko jest puste."` dla stanu "nic nie otworzyłem" jest semantycznie mylący. Model czyta "biurko jest puste" i completion najbliższy tej frazie to "nie ma nic do zrobienia" — a nie "system jeszcze nie sprawdził danych". To nie jest kwestia inteligencji modelu, to kwestia tego, że dajecie mu dwuznaczny sygnał i on wybiera bardziej prawdopodobną (dla LLM) interpretację tej frazy.

**Rekomendacja:** rozdzielcie te dwa stany eksplicytnie i instruktażowo, np.:

```
<desk_state>
STATUS: brak otwartych aplikacji.
Jeśli pytanie użytkownika dotyczy sprawdzenia jakichkolwiek danych 
(notatek, zaległości, pamięci) — MUSISZ najpierw użyć odpowiedniego 
narzędzia open_*. Nigdy nie zakładaj braku danych na podstawie samego 
faktu, że biurko jest puste.
</desk_state>
```

To zamienia pasywny placeholder w aktywną instrukcję następnego kroku, co jest dużo trudniejsze do błędnej interpretacji.

**Głębsza rekomendacja architektoniczna:** dla operacji typu "sprawdź co jest w brudnopisie" rozważcie w ogóle rezygnację z pośredniego kroku "otwórz, potem przeczytaj w desk_state" i zwracajcie treść **bezpośrednio jako wynik wywołania narzędzia** (`open_notes()` zwraca od razu pełną zawartość w tool result, a nie tylko podgląd + wskazówkę "patrz niżej"). To eliminuje całą warstwę pośrednią i jest zgodne z naturalnym wzorcem function-calling, na którym model był trenowany: wywołujesz funkcję → dostajesz wynik natychmiast. Mechanizm "biurka" z TTL i pamięcią między turami możecie zostawić jako wewnętrzną optymalizację cache'u (żeby nie odpytywać źródła danych ponownie przy każdej iteracji), ale nie jako coś, co model musi rozumieć koncepcyjnie, żeby dostać dane, o które prosi.

---

## Pytanie 3 — Zarządzanie historią

`history_limit=10` liczony w **surowych krokach ReAct**, a nie w **turach konwersacji**, to realny błąd projektowy, nie tylko nieoptymalna wartość.

Konsekwencje:
- Jedna tura użytkownika z 3 wywołaniami narzędzi generuje łatwo 5-8 wpisów w `self.history` (thought+call modelu, kilka tool results, finalna odpowiedź). Przy limicie 10 zostaje wam pamięć **1-2 pełnych tur konwersacji** — dla asystenta domowego, który ma "pamiętać" kontekst rozmowy, to bardzo mało.
- Poważniejszy problem: przycinanie do ostatnich N *wpisów* (a nie *tur*) może uciąć historię w środku sekwencji ReAct, zostawiając wiadomość `tool` bez poprzedzającej ją wiadomości `assistant` z odpowiadającym `tool_call`. To potencjalnie niepoprawna struktura konwersacji z punktu widzenia szablonu czatu — może prowadzić do błędów renderowania albo do sytuacji, w której model dostaje "wynik narzędzia" bez wiedzy, jakie pytanie/wywołanie ten wynik odpowiada.

**Jak to powinno wyglądać:** przycinajcie na poziomie **kompletnych tur**, nigdy nie zostawiając osieroconego `tool` bez jego `assistant`/`tool_call`. Praktyczny wzorzec, który sprawdza się w agentowych pętlach wieloturowych:

1. Trzymajcie osobno: (a) surowy ReAct trace bieżącej/ostatniej tury (pełny, do debugowania i kontynuacji wątku), (b) skondensowaną historię starszych tur — jedna zwięzła linia na turę: "użytkownik zapytał X → asystent zrobił Y i odpowiedział Z", bez surowych `<thought>` i wywołań narzędzi.
2. Limit stosujcie do liczby **tur**, nie wpisów — np. "pełny ReAct trace tylko dla ostatniej tury, skondensowane podsumowania dla poprzednich 5-8 tur".
3. Nigdy nie przycinajcie w połowie tury — jeśli limit wypada w środku sekwencji tool-call, przesuńcie granicę do najbliższej kompletnej tury.

To rozwiązuje jednocześnie problem budżetu kontekstu (mniej surowego szumu ReAct z przeszłości) i problem ciągłości (asystent faktycznie "pamięta" więcej realnych wymian, tylko w skondensowanej formie).

---

## Pytanie 4 — Prompty (tier_prime + base_system + sandwich)

**Największa słabość: budżet kontekstu, nie styl.** Macie `num_ctx: 4096` przy trzywarstwowym promptcie (tier_prime + base_system + sandwich), pełnych schematach narzędzi (Home Assistant + pamięć + brudnopis — realistycznie kilkanaście narzędzi z opisami to łatwo 500-1500 tokenów), few-shotach w `base_system.md` i do tego wstrzykiwanym `desk_state`. To wszystko zanim policzycie choć jedną wiadomość użytkownika czy historię.

To jest istotne, bo **Ollama przy przekroczeniu `num_ctx` nie zgłasza błędu — po cichu obcina najstarsze tokeny**, a najstarsze tokeny w Waszym payloadzie to właśnie system message, czyli wszystkie krytyczne zasady behawioralne. Jeśli kiedykolwiek zbliżacie się do limitu (a przy 4096 i takim stackowaniu promptów jest to bardzo prawdopodobne, zwłaszcza gdy `desk_state` zawiera dłuższą zawartość brudnopisu), to dokładnie tłumaczy "nieprzewidywalność między turami" — model raz dostaje pełne instrukcje, raz ich część, w zależności od tego, ile miejsca zajęła aktualna tura.

To jest fix praktycznie darmowy na warstwie Desktop/GPU: **podnieście `num_ctx` do co najmniej 8192-16384** i zmierzcie realny koszt tokenowy system promptu + schematów narzędzi + few-shotów, żeby wiedzieć, ile realnie zostaje na historię i desk_state. Na warstwie Raspberry Pi 5 (7B) może to wymagać kompromisu z pamięcią RAM, ale to osobna decyzja inżynierska — warto ją podjąć świadomie, a nie zostawiać domyślną wartość.

**Druga słabość: trzykrotna redundancja tej samej zasady.** "Zamknij `<thought>`, potem absolutna cisza, potem tool_call" pojawia się niemal identycznie w `tier_prime.md`, `base_system.md` i `sandwich`. Intencja jest zrozumiała (wzmocnić przez powtórzenie), ale dla modelu instruction-tuned trzy nieco różne sformułowania tej samej reguły to nie jest "wzmocnienie" — to trzy osobne, drobno rozjeżdżające się instrukcje konkurujące o uwagę, plus czysty koszt tokenowy bez dodatkowej wartości. Skonsolidujcie to do **jednego, kanonicznego sformułowania**, umieszczonego raz, najbliżej końca system message (najwyższa waga recency).

**Trzecia słabość, mniej krytyczna: ton `tier_prime.md`.** Sformułowania typu "uwolniona z kagańca warstwa analityczna", "nie jesteś uwięziony w skryptach, samodzielnie decydujesz" to kolorystyka person, która dla modeli 32B-instruct tej klasy nie szkodzi bezpieczeństwu, ale **rozprasza uwagę modelu kosztem sztywnych wymogów formatu**. Przy zadaniu wymagającym bardzo ścisłego przestrzegania struktury (tagi, cisza między myślą a wywołaniem, dokładne parametry), im mniej "barwnej" narracji person konkuruje o tokeny uwagi z twardymi regułami formatu, tym lepiej. To nie jest zarzut etyczny, czysto pragmatyczny: leaner prompt = bardziej przewidywalne przestrzeganie formatu.

**Co jest dobre i warto zostawić:** struktura "checklisty" w `tier_prime.md` (analiza → narzędzia → self-correction → agregacja) jest solidnym szkieletem ReAct. Few-shoty w `base_system.md` (przykład z narzędziem i bez) też są dobrą praktyką — tylko upewnijcie się, że są blisko końca kontekstu, a nie zagrzebane w środku trzywarstwowego stosu.

---

## Pytanie 5 — Diagnoza konkretnych bugów

**a) "Biurko jest puste" → brak wywołania `open_notes`, mimo pytania o zaległości.**

To bezpośredni skutek Wady 2 z Pytania 2: placeholder `desk_state` dla stanu "nic nie otworzyłem" brzmi identycznie jak stwierdzenie "nie ma danych". Dodatkowo w promptach nie ma jawnej reguły łączącej *konkretne intencje użytkownika* ("czy mamy zaległości") z *obowiązkowym* wywołaniem `open_notes` niezależnie od aktualnego stanu biurka. Few-shot w `base_system.md` uczy modelu dwóch skrajności — "jest polecenie → użyj narzędzia" i "samo powitanie → nie używaj" — ale nie ma przykładu na sytuację pośrednią: "pytanie sugerujące sprawdzenie danych + biurko puste → to properties biurka pustego nie znaczy braku danych, tylko brak sprawdzenia". Model wypełnia tę lukę najbardziej prawdopodobnym (dla LLM) skojarzeniem: "puste" = "nic".

**b) Przejście na angielski + deklaracja działania zamiast wykonania, po `open_notes`.**

To jest dokładnie mechanizm z Pytania 1: Ollama, widząc niepuste pole `tools` w payloadzie, dokleiła do system message natywny, angielski blok instrukcji o function-callingu, zdefiniowany w szablonie czatu Qwen 2.5. Ten blok — bliżej końca system message niż wasze polskie instrukcje z `tier_prime.md` — aktywuje wyuczone w fine-tuningu zachowanie: krótkie zdanie po angielsku wyjaśniające plan, zanim (albo zamiast) faktycznego wywołania. Odpowiedź modelu ("Based on the information provided... I will proceed to save each fact...") to podręcznikowy przykład tego wzorca z function-callingu Qwen, nie przypadkowa "halucynacja" czy zignorowanie polecenia — model robi dokładnie to, na co jest naturalnie skłonny przez konkurujący, natywny system prompt, którego sami nie widzicie w swoim kodzie (bo dokleja go Ollama, nie wy).

Fix z Pytania 1 (nie wysyłać `tools` w payload, opisać narzędzia wyłącznie w waszym własnym promptcie) powinien usunąć ten konkretny bug niemal całkowicie, bo eliminuje źródło konkurencyjnych, angielskich instrukcji.

---

## Pytanie 6 — Rekomendacja: co bym zmienił, projektując od nowa

**Zostawiłbym:**
- Dwuwarstwową architekturę Lokaj/Prime dopasowaną do sprzętu — to sensowny podział pod kątem kosztu/lokalności.
- Ideę pamięci długoterminowej jako klucz-JSON, z osobną kolejką "brudnopisu" do konsolidacji — model mentalny jest w porządku, problem leży w wykonaniu (patrz Pytanie 2), nie w koncepcji.
- Customowy tag `<thought>` jako scratchpad — Qwen 2.5 Instruct nie ma natywnego trybu rozumowania, więc to uzasadniony wybór, nie coś do zastąpienia natywnym CoT (bo go tu po prostu nie ma; to inna rodzina modeli niż np. QwQ czy Qwen3-thinking).
- Filozofię "szczupły kod pod konkretny model" — to rozsądne dla lokalnego, produkcyjnego wdrożenia, o ile "szczupły" nie oznacza "niesprawdzony pod kątem realnego budżetu tokenów".

**Zmieniłbym fundamentalnie:**
1. **Nie wysyłałbym pola `tools` do Ollamy.** Pełny, ręczny opis narzędzi w promptcie, bez natywnego mechanizmu function-callingu Ollamy. Jeden format, jedno źródło prawdy, żadnej konkurencji językowej.
2. **Spłaszczyłbym "biurko"** dla operacji odczytu — wynik narzędzia wraca bezpośrednio w tool result, a nie przez wstrzykiwany, opóźniony o iterację `desk_state`. Sam mechanizm cache'u/TTL zostawiłbym jako wewnętrzną optymalizację silnika, niewidoczną koncepcyjnie dla modelu.
3. **Historię przycinałbym po turach, nie po krokach ReAct**, z kondensacją starszych tur do jednej linii podsumowania, nigdy nie zostawiając osieroconej wiadomości `tool`.
4. **Zmierzyłbym i podniósł budżet kontekstu.** Policzyłbym realny koszt tokenowy system promptu + schematów + few-shotów, podniósł `num_ctx` odpowiednio wyżej (przynajmniej 2-4x na warstwie Desktop/GPU) i pilnował marginesu, zamiast polegać na cichym, front-truncating zachowaniu Ollamy.
5. **Skonsolidowałbym trzywarstwowy prompt do jednej, spójnej wersji** bez potrójnego powtarzania tej samej reguły o ciszy między `<thought>` a `<tool_call>`, z lżejszą, mniej "barwną" personą tam, gdzie konkuruje ona o uwagę z twardymi wymogami formatu.

To nie jest przebudowa filozofii projektu — to usunięcie kilku konkretnych, dobrze zidentyfikowanych źródeł konfliktu i marnotrawstwa kontekstu, które w połączeniu prawdopodobnie tłumaczą większość zaobserwowanych objawów.
