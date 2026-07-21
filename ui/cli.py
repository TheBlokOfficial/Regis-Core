import os
import questionary
from questionary import Style
from rich.console import Console
from rich.rule import Rule

import datetime
from integrations.ha_client import HomeAssistantClient
from core.llm_engine import LLMEngine
from core.gemini_engine import GeminiEngine
from core.exceptions import HomeAssistantConnectionError, LLMConnectionError
from core import config
from core.tools_registry import ToolsRegistry

console = Console()

custom_style = Style([
    ('qmark', 'fg:ansigray bold'),
    ('question', 'bold'),
    ('answer', 'fg:white bold'),
    ('pointer', 'fg:white bold'),
    ('highlighted', 'fg:white bold'),
    ('selected', 'fg:white bold'),
    ('separator', 'fg:ansigray'),
    ('instruction', 'fg:ansigray'),
    ('text', ''),
])

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    clear_screen()
    console.print(f"[bold white]{title}[/bold white]")
    console.print(Rule(style="dim"))
    console.print("")




def print_production_header(model_name: str, tier: str, display_name: str, temperature: float = 0.5):
    console.print(f"[bold white]REGIS CORE[/bold white] [dim]| Warstwa: {display_name} | Model: {model_name} | Temp: {temperature}[/dim]\n[dim]Komendy: '/exit' / '/clear' / '/tier' / '/models'[/dim]")
    console.print(Rule(style="dim"))
    console.print("")

def run_production_loop(llm_engine: LLMEngine, ha_client: HomeAssistantClient, display_name: str = "Brak profilu"):
    clear_screen()
    print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
    tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
    
    while True:
        try:
            now_input = datetime.datetime.now().strftime("%H:%M:%S")
            user_input = console.input(f"[dim green][{now_input}][/dim green] [bold white]Ty:[/bold white] ")
            if user_input.lower() == "/exit":
                break
                
            if user_input.lower() == "/help":
                console.print("\n[bold white]Dostępne komendy:[/bold white]")
                console.print("[dim]/help[/dim] - [dim]Wyświetla tę listę komend[/dim]")
                console.print("[dim]/exit[/dim] - [dim]Kończy działanie programu[/dim]")
                console.print("[dim]/clear[/dim] - [dim]Czyści historię bieżącej konwersacji[/dim]")
                console.print("[dim]/tier[/dim] - [dim]Przełącza pomiędzy Lokajem a Regisem na obecną sesję[/dim]")
                console.print("[dim]/models[/dim] - [dim]Pozwala zmienić aktywny model LLM z listy dostępnych na Ollamie[/dim]")
                console.print("[dim]/provider[/dim] - [dim]Przełącza między lokalnym Ollama a chmurowym Gemini API[/dim]\n")
                console.input("[dim]Naciśnij Enter, aby kontynuować...[/dim]")
                clear_screen()
                print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                continue
                
            if user_input.lower() == "/clear":
                llm_engine.clear_history()
                clear_screen()
                print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                console.print("\n[dim]Pamięć podręczna modelu została wyczyszczona.[/dim]")
                continue
                
            if user_input.lower() == "/tier":
                if llm_engine.tier == "butler":
                    llm_engine.tier = "regis"
                    llm_engine.model_name = "qwen2.5:14b-instruct"
                    llm_engine.temperature = 0.4
                    display_name = "Regis"
                else:
                    llm_engine.tier = "butler"
                    llm_engine.model_name = "qwen2.5:7b-instruct"
                    llm_engine.temperature = 0.1
                    display_name = "Lokaj"
                    
                tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
                settings = config.load_settings()
                settings["active_tier"] = llm_engine.tier
                config.save_settings(settings)
                
                clear_screen()
                print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                console.print(f"\n[green]Pomyślnie przełączono na warstwę: {display_name}[/green]")
                continue
                
            if user_input.lower() == "/models":
                available_models = LLMEngine.get_available_models()
                if not available_models:
                    console.print("[red]Nie udało się pobrać listy modeli z Ollamy (czy serwer działa?).[/red]")
                    continue
                
                selected_model = questionary.select(
                    "Wybierz model na tę sesję:",
                    choices=available_models,
                    style=custom_style
                ).ask()
                
                if selected_model:
                    llm_engine.model_name = selected_model
                    clear_screen()
                    print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                    console.print(f"\n[green]Zmieniono model na: {selected_model}[/green]")
                continue
                
            if user_input.lower() == "/provider":
                provider_choice = questionary.select(
                    "Wybierz dostawcę LLM na tę sesję:",
                    choices=["Ollama (Lokalnie)", "Gemini API (Chmura)"],
                    style=custom_style
                ).ask()
                
                if provider_choice == "Gemini API (Chmura)":
                    api_key = console.input("[dim]Wprowadź klucz Gemini API (zostanie zapisany tylko w RAM na czas sesji): [/dim]")
                    if api_key.strip():
                        import os
                        os.environ["GEMINI_API_KEY"] = api_key.strip()
                        
                        gemini_models = GeminiEngine.get_available_models()
                        selected_model = questionary.select(
                            "Wybierz model Gemini:",
                            choices=gemini_models,
                            style=custom_style
                        ).ask()
                        
                        if selected_model:
                            llm_engine = GeminiEngine(model_name=selected_model, tier=llm_engine.tier, temperature=getattr(llm_engine, 'temperature', 0.5))
                            display_name = f"Regis ({provider_choice})"
                            clear_screen()
                            print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                            console.print(f"\n[green]Pomyślnie przełączono na Gemini API ({selected_model})[/green]")
                
                elif provider_choice == "Ollama (Lokalnie)":
                    llm_engine = LLMEngine(model_name="qwen2.5:7b-instruct" if llm_engine.tier == "butler" else "qwen2.5:14b-instruct", tier=llm_engine.tier)
                    display_name = "Lokaj" if llm_engine.tier == "butler" else "Regis"
                    clear_screen()
                    print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                    console.print("\n[green]Pomyślnie powrócono do lokalnej Ollamy.[/green]")
                    
                continue
                
            if not user_input.strip():
                continue
                
            console.print("")
                
            first_regis_token = False
            _thought_header_shown = False
            _thought_mode = False
            _thought_stream_buf = ""   # rolling buffer do detekcji tagów w locie
            _scratchpad_buf = ""       # reszta (jsony, śmieci) — do cichego porzucenia
            tools_called_in_this_pass = False

            _OPEN_TAG = "<thought>"
            _CLOSE_TAG = "</thought>"
            _JUNK_TAGS = ("<tool_call>", "</tool_call>")

            def flush_scratchpad():
                """Myśli zostały już wyświetlone w real-time przez stream_update.
                Ta funkcja tylko czyści bufory przed wyświetleniem statusu narzędzia."""
                nonlocal _scratchpad_buf, _thought_stream_buf, _thought_mode
                if _thought_mode and _thought_stream_buf.strip():
                    # Jeśli model urwał myśl w połowie przed wywołaniem narzędzia — doflushuj
                    console.print(f"[dim]{_thought_stream_buf.strip()}[/dim]", highlight=False)
                    console.print("")
                _scratchpad_buf = ""
                _thought_stream_buf = ""
                _thought_mode = False

            def status_update(msg_text):
                nonlocal tools_called_in_this_pass, first_regis_token
                if first_regis_token:
                    print()
                    first_regis_token = False
                if not tools_called_in_this_pass:
                    tools_called_in_this_pass = True
                    flush_scratchpad()
                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                console.print(f"[dim green][{ts_now}][/dim green] [dim]{msg_text}[/dim]", highlight=False)

            def stream_update(token: str, is_scratchpad: bool = False):
                """Maszyna stanów do real-time wykrywania i wyświetlania tagów <thought>.
                
                Stany:
                  _thought_mode=False: czekamy na <thought> lub przepuszczamy do bufora śmieci
                  _thought_mode=True:  jesteśmy wewnątrz <thought>...</thought>, 
                                       streamujemy na bieżąco jako 'Myśli agenta'
                """
                nonlocal first_regis_token, _thought_header_shown, _thought_mode
                nonlocal _thought_stream_buf, _scratchpad_buf

                if not token:
                    return

                if not is_scratchpad:
                    # Drugi przebieg (po narzędziach) — finalna odpowiedź. Streamuj jako Regis:.
                    if not first_regis_token:
                        ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                        console.print(f"[dim green][{ts_now}][/dim green] [bold white]Regis:[/bold white] ", end="", highlight=False)
                        first_regis_token = True
                    print(token, end="", flush=True)
                    return

                # Tryb scratchpad — przetwarzaj token przez maszynę stanów z rolling buforem
                _thought_stream_buf += token

                # Filtruj śmieciowe tagi Qwen Instruct na bieżąco
                for junk in _JUNK_TAGS:
                    _thought_stream_buf = _thought_stream_buf.replace(junk, "")

                while True:
                    if not _thought_mode:
                        # Szukamy otwierającego tagu <thought>
                        if _OPEN_TAG in _thought_stream_buf:
                            idx = _thought_stream_buf.index(_OPEN_TAG)
                            _scratchpad_buf += _thought_stream_buf[:idx]  # śmieci przed tagiem
                            _thought_stream_buf = _thought_stream_buf[idx + len(_OPEN_TAG):]
                            _thought_mode = True
                            if not _thought_header_shown:
                                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                                console.print(f"[dim green][{ts_now}][/dim green] [dim]Myśli agenta:[/dim] ", end="", highlight=False)
                                _thought_header_shown = True
                            # Kontynuuj pętlę — być może jest też treść myśli w buforze
                        else:
                            # Tag może być podzielony między tokeny — trzymaj koniec bufora
                            safe_len = max(0, len(_thought_stream_buf) - len(_OPEN_TAG) + 1)
                            _scratchpad_buf += _thought_stream_buf[:safe_len]
                            _thought_stream_buf = _thought_stream_buf[safe_len:]
                            break
                    else:
                        # Jesteśmy w środku <thought> — szukamy zamykającego tagu
                        if _CLOSE_TAG in _thought_stream_buf:
                            idx = _thought_stream_buf.index(_CLOSE_TAG)
                            thought_content = _thought_stream_buf[:idx]
                            if thought_content:
                                console.print(f"[dim]{thought_content}[/dim]", end="", highlight=False)
                            _thought_stream_buf = _thought_stream_buf[idx + len(_CLOSE_TAG):]
                            _thought_mode = False
                            console.print("")   # nowa linia po myśli
                            console.print("")
                            # Kontynuuj pętlę — mogą być kolejne tagi w tym samym tokenie
                        else:
                            # Tag zamykający może być podzielony — trzymaj koniec bufora w rezerwie
                            safe_len = max(0, len(_thought_stream_buf) - len(_CLOSE_TAG) + 1)
                            thought_content = _thought_stream_buf[:safe_len]
                            if thought_content:
                                console.print(f"[dim]{thought_content}[/dim]", end="", highlight=False)
                            _thought_stream_buf = _thought_stream_buf[safe_len:]
                            break

            def final_response_callback(final_text):
                """Wywoływana przez silnik po zakończeniu pętli ReAct z finalną odpowiedzią.
                
                Jeśli narzędzia nie były użyte: wyświetla odpowiedź jako 'Regis:' 
                (usuwając wcześniej wyświetlone tagi thought ze strumienia).
                """
                import re
                nonlocal tools_called_in_this_pass, _scratchpad_buf, first_regis_token, _thought_header_shown
                if not tools_called_in_this_pass:
                    # Tagi <thought> zostały już wyświetlone przez stream_update w real-time.
                    # Usuwamy je z finalnego tekstu, by nie dublować i nie wyświetlać śmieciowych JSON-ów.
                    clean_text = re.sub(r'<thought>.*?</thought>', '', final_text, flags=re.DOTALL)
                    for junk in _JUNK_TAGS:
                        clean_text = clean_text.replace(junk, "")
                    clean_text = clean_text.strip()
                    if clean_text:
                        if _thought_header_shown:
                            console.print("")
                        ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                        console.print(f"[dim green][{ts_now}][/dim green] [bold white]Regis:[/bold white] ", end="", highlight=False)
                        console.print(f"{clean_text}", highlight=False)
                        print()
                else:
                    if first_regis_token:
                        print()
                        first_regis_token = False
                _scratchpad_buf = ""

            try:
                response_text = llm_engine.generate_response(
                    user_input, 
                    tools_registry, 
                    status_update, 
                    stream_update, 
                    final_response_callback
                )
            except (HomeAssistantConnectionError, LLMConnectionError) as e:
                console.print(f"\n[red]Błąd systemu (Połączenie): {e}[/red]", highlight=False)
                import logging
                logging.exception("Błąd w trakcie analizy otoczenia/LLM.")
                continue
            
            if first_regis_token:
                print()
                console.print("")
                
        except KeyboardInterrupt:
            console.print("\n[dim]Zamykam system Regis.[/dim]")
            break

def run_main_menu():
    """Główne menu zwracające wybór użytkownika, by plik główny mógł podjąć decyzję."""
    print_header("REGIS CORE - MENU GŁÓWNE")
    
    mode_choice = questionary.select(
        "Wybierz akcję:",
        choices=[
            questionary.Separator(" "),
            questionary.Choice(title="Uruchom system Regis", value="prod"),
            questionary.Separator(" "),
            questionary.Choice(title="Wyjście", value="exit")
        ],
        style=custom_style
    ).ask()
    
    return mode_choice
