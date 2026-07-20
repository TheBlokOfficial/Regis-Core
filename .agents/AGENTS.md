# Regis-Core Workspace Rules

- **KRYTYCZNE:** Model pracujący w tym projekcie nie może wprowadzać ŻADNYCH zmian w kodzie, chyba że użytkownik wyraźnie i jednoznacznie mu to nakaże.
- **Unikaj nadmiernego używania emotikon (ikonek) w interfejsie CLI i logach.**
- Używaj ich tylko tam, gdzie są niezbędne do kierowania wzrokiem lub faktycznie poprawiają czytelność (np. krzyżyk oznaczający wyjście/błąd, ptaszek oznaczający sukces). Dodawanie ikon do absolutnie każdej opcji menu wygląda nieprofesjonalnie. Interfejs Regis-Core ma docelowo pozostać stonowany i ascetyczny.

## Zalecenia dotyczące UX (CLI)
Poniższe wytyczne stanowią zbiór dobrych praktyk wypracowanych podczas refaktoryzacji interfejsu (są to luźne propozycje na przyszłość pomagające utrzymać spójność, a nie sztywne reguły):
- **Minimalizm barwny**: Preferuj użycie czystej bieli (`[bold white]`) dla nagłówków czy ważnych tekstów i szarości (`[dim]`) dla elementów "tła" (logi, instrukcje pomocnicze, długie dumpy JSON).
- **Kolory celowe**: Staraj się unikać jaskrawych barw (np. `cyan`, `yellow`), jeśli pełnią funkcje wyłącznie estetyczne. Rezerwuj wyraziste kolory (np. `[red]`, `[green]`) do informowania o istotnych zdarzeniach (błędy, sukcesy).
- **Lżejsza struktura**: Zamiast otaczać bloki tekstu masywnymi panelami z obramowaniami (`Panel`), używaj pogrubionych tytułów oddzielonych delikatnymi liniami poziomymi (`Rule(style="dim")`).
- **Niestandardowe motywy w promptach**: Przy korzystaniu z bibliotek wyboru (np. `questionary`) warto aplikować własny, wyciszony motyw stylów (np. stosując `fg:ansigray`), aby pozbyć się "krzykliwych", domyślnych niebieskich lub żółtych highlightów.
