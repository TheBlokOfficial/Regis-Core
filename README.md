# 🎩 Regis Core - Twój Lokalny Lokaj

**Regis** to w 100% prywatny, działający całkowicie lokalnie (Offline-First) administrator inteligentnego domu. Silnik jest napędzany przez potężne Modele Językowe (LLM), które z niesamowitą precyzją zamieniają język naturalny na konkretne komendy sterujące inteligentnym sprzętem.

Wizją projektu jest stworzenie bezbłędnego, prywatnego "Kamerdynera", który dba o dom, sterując nim poprzez ekosystem [Home Assistant](https://www.home-assistant.io/), bez wysyłania jakichkolwiek danych głosowych czy tekstowych do zewnętrznych chmur.

---

## ✨ Główne Funkcje

* **Całkowita Prywatność**: Regis działa i interpretuje Twoje polecenia całkowicie lokalnie przy pomocy serwera [Ollama](https://ollama.com/). Żadne dane nie opuszczają Twojej sieci LAN.
* **Integracja z Home Assistant**: Projekt wykorzystuje REST API systemu HA, automatycznie wstrzykując obecny stan urządzeń do kontekstu modelu.
* **Dynamiczne Zarządzanie Modelami**: Regis łączy się z Twoją instancją Ollamy, pobiera dostępne modele i pozwala zapisać ulubione, które będą zawsze gotowe do akcji w eleganckim menu startowym.
* **Single-Turn Render UI**: Główne narzędzie uruchomieniowe oferuje niesamowicie czysty, nieprzewijający się interfejs konsolowy (stworzony przy pomocy bibliotek `rich` oraz `questionary`), który pozwala na płynną, natychmiastową komunikację.

## 🛠️ Modułowa Architektura

* **`core/`** - Silnik rozumowania. Tutaj znajdują się prompty systemowe oraz logika wysyłająca zapytania i żądająca surowego zwrotu struktury `JSON` od modeli AI.
* **`integrations/`** - Moduły komunikacji ze światem zewnętrznym (np. klient Home Assistant wykonujący akcje na prawdziwym sprzęcie).
* **`tools/`** - Zbiór przydatnych skryptów (w tym genialny `symulator_llm.py`, dzięki któremu w fazie developmentu możesz wcielić się w LLMa i odsyłać payloady "z palca", by testować poprawność sprzętu).

## 🚀 Jak uruchomić?

### Wymagania
* Zainstalowana lokalnie [Ollama](https://ollama.com/).
* Zainstalowany Python 3.10+
* (Opcjonalnie) Skonfigurowana instancja Home Assistant.

### Instalacja
1. Sklonuj to repozytorium:
   ```bash
   git clone https://github.com/TheBlokOfficial/Regis-Core.git
   cd Regis-Core
   ```
2. Zainstaluj wymagane biblioteki interfejsu wizualnego:
   ```bash
   pip install -r requirements.txt
   ```
3. Uruchom Regisa:
   ```bash
   python main.py
   ```

## 🖥️ Środowiska Uruchomieniowe
Aplikacja została zaprojektowana z myślą o:
* **DEV**: Desktop Windows / Linux (Testowano na RTX 5070).
* **PROD**: Raspberry Pi 5 (8GB RAM, Dysk 1TB NVMe 970 EVO) działający 24/7.
* **SATELITY (Planowane)**: Mikrokontrolery ESP32 rozstawione po domu, wykorzystujące framework WakeWord do budzenia głównej jednostki Regisa.
