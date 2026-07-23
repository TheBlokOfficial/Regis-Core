# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Sesja Architektoniczna: Plan Restrukturyzacji)

### Co zostało zrobione

Przeprowadzono sesję architektoniczną z użytkownikiem (bez pisania kodu). Wynikiem jest kompletny plan restrukturyzacji projektu do dwóch usług produkcyjnych.

1. **Stworzono dokument `docs/arch_restrukturyzacja_2025.md`** — szczegółowy plan implementacji dla następnych agentów. Zawiera wizję docelową, flow użytkownika, strukturę nowych pakietów i plan 4 sesji.
2. **Przepisano `docs/ONBOARDING.md`** — stary dokument opisywał strukturę `apps/` (nieistniejącą). Nowy opisuje aktualną strukturę `src/` i nową architekturę dwóch usług.
3. **Zaktualizowano `docs/MANIFEST.md §3`** — zmieniono "Trzy Niezależne Procesy" na "Dwie Usługi Produkcyjne" zgodnie z decyzją podjętą w tej sesji.

### Kluczowe Decyzje Architektoniczne Podjęte w Tej Sesji

| Decyzja | Szczegół |
|---|---|
| Windows = tray app | `regis_node` to ikona System Tray (pystray), nie CLI |
| Worker + Satellite jednocześnie | Nie wykluczają się — oba mogą działać na tym samym PC |
| Ukryte procesy | Worker i Satellite jako `subprocess.Popen` z `CREATE_NO_WINDOW` |
| Autostart przez Registry | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` |
| Konfiguracja: wizard + edycja z tray | Questionary przy pierwszym uruchomieniu, opcja edycji z menu tray |
| Kontroler tylko Linux | `.whl`, bez wersji Windows — bez zmian |
| Terminal: niski priorytet | Stara wersja przestarzała. Nowa (monitor systemu) — osobna sesja w przyszłości |
| Pystray jako biblioteka tray | Nowa zależność w extras `[node]` |

---

## Aktualny Stan Kodu

Kod **nie był modyfikowany** w tej sesji. Zmiany dotyczyły wyłącznie dokumentacji.

```text
src/
├── core/                   ← biblioteka wspólna [BEZ ZMIAN]
├── integrations/           ← klient HA          [BEZ ZMIAN]
├── regis_controller/       ← 1 plik main.py (361 linii) — do refaktoryzacji
│   └── main.py
├── regis_worker/           ← do usunięcia po migracji do regis_node
├── regis_satellite/        ← do usunięcia po migracji do regis_node
├── regis_terminal/         ← do usunięcia (koncepcja wycofana)
├── regis_cli/              ← builders.py wymaga aktualizacji (1 paczka zamiast 3)
└── [regis_node/]           ← JESZCZE NIE ISTNIEJE — do stworzenia
```

Testy: 26/27 przechodzi (1 niezwiązany błąd w `test_pi_discovery.py`).

---

## Kroki Startowe dla Następnego Agenta

1. **Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).**
2. **Przeczytaj `docs/arch_restrukturyzacja_2025.md`** — to jest Twoja główna instrukcja. Zawiera plan 4 sesji implementacyjnych.
3. Zacznij od **Sesji A** (sprzątanie i weryfikacja bazy) — jest to warunek wstępny przed jakimkolwiek kodem.
4. Sesja A → B → C → D — nie pomijaj kolejności, każda sesja ma zdefiniowany warunek weryfikacji.

### Ważne: co sprawdzić na początku Sesji A
- Czy `regis_satellite/` ma `__init__.py` (podejrzenie że go brakuje)
- Czy `regis_terminal/` istnieje w `src/` (nie był widoczny na liście pakietów)
- Uruchom `pytest` i zapisz wynik bazowy
