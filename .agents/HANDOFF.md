# Agent Handoff & State Journal

Ten plik służy do przekazywania kontekstu między agentami. Zawsze czytaj go na starcie sesji i zawsze zastępuj jego zawartość nową wersją przed zakończeniem (zgodnie z protokołem w AGENTS.md). Nie dopisuj — zastępuj.

---

## Ostatnia Aktywność (Sesja 2026-07-23 — Failover & Continuous Registration)

### Co zostało zrobione

W drugiej turze tej sesji uodporniono środowisko węzłów i rozwiązano poważne błędy wyścigowe oraz problemy braku odporności sieciowej. 
- **Zwalnianie pamięci VRAM**: Skonfigurowano rutynę Węzła Roboczego, by podczas uśmiercania wysyłał polecenie do LLM engine nakazujące wyczyszczenie 14B/3B z VRAM przy użyciu parametru `keep_alive: 0`.
- **Failover timeout i Heartbeat**: Kontroler został wyposażony w 30-sekundowego loopa odpytującego porty, by automatycznie ubijać martwe węzły. Podczas proxy-owania czatu dodano elastyczne timeouty (`timeout=(1.0, 300.0)`), natychmiast wrzucające fallback-węzeł (Butlera) na pierwszą linię frontu w przypadku padu Desktopu PC.
- **Continuous Registration**: Odkryto lukę – po resecie Kontrolera, rejestr czyścił RAM i odcinał wciąż żyjące węzły. Węzły otrzymały loopa asynchronicznego w tle, który co 15 sekund melduje Kontrolerowi swoją obecność (nawet jeśli odpowiedź zwrotna się załamie, ukrywa to i ponawia do skutku).
- **Zdefiniowanie Długu Architektonicznego**: Odkryto krytyczny błąd w dystrybucji na skutek monolitycznego pliku konfiguracyjnego `data/settings.json`, który podczas wysyłania (Deploy'a) psuje tożsamość Węzła docelowego (Raspberry Pi zaczęło udawać PC, ponieważ nadpisało sobie pliki po reboocie). Powstał w dokumencie dedykowany raport usterki – `docs/architectural_debt_report.md`. Skrypt powłoki na doraźne zniwelowanie usterki dostał tymczasową flagę omijania przesyłu pliku (`--exclude=data/settings.json`).

### Stan testów

Kod źródłowy pomyślnie zwalidowano kompilatorem Pythona. Działanie procedur pomyślnie zweryfikowano testami operacyjnymi na docelowych maszynach przez terminal oraz system logowania `journalctl`.

---

## Aktualny Stan Kodu

```
apps/
├── controller/          ← Posiada Heartbeat Węzłów
├── worker/
│   ├── node.py          
│   └── server.py        ← Posiada Continuous Registration i odłącza VRAM
├── satellite/           
└── terminal/            
core/
├── llm_engine.py        ← Zaktualizowany pod czyszczenie VRAM (unload_model)
└── ...
docs/
├── architectural_debt_report.md  ← Raport usterki dla agentów
└── ...
```

---

## Kroki Startowe dla Następnego Agenta

1. Przeczytaj `docs/MANIFEST.md` i `docs/AGENT_GUIDE.md` (obowiązkowe).
2. Koniecznie przeczytaj raport `docs/architectural_debt_report.md`. Twoim priorytetem jest w tej chwili pozbycie się długu konfiguracyjnego opisanego w tym dokumencie (Profile, Pliki `.env`). Bez tego każda aktualizacja na RPi5 może stwarzać luki bezpieczeństwa lub nadpisywać tożsamość maszyn.
3. Gdy problem konfiguracji i Długu Architektonicznego zostanie rozstrzygnięty i wyczyszczony, możesz w miarę możliwości przejść do kontynuacji bazowych założeń `TASKS.md` (np. WakeWord/STT).
