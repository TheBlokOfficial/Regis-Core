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
                
            _first_thought = True
            _first_content = True
            
            def on_thought_token(chunk):
                nonlocal _first_thought, _first_content
                if _first_thought:
                    if not _first_content:
                        print()
                        print()
                        _first_content = True
                    ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                    console.print(f"[{ts_now}] ", style="dim green", end="", highlight=False)
                    console.print("Myśli agenta: ", style="dim", end="", highlight=False)
                    _first_thought = False
                console.print(chunk, style="dim", end="", highlight=False, markup=False)

            def on_content_token(chunk):
                nonlocal _first_content, _first_thought
                if _first_content:
                    if not chunk.strip():
                        return
                    if not _first_thought:
                        print()
                        print()
                        _first_thought = True 
                    ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                    console.print(f"[{ts_now}] ", style="dim green", end="", highlight=False)
                    console.print("Regis: ", style="bold white", end="", highlight=False)
                    _first_content = False
                print(chunk, end="", flush=True)

            def on_tool_call(msg_text):
                nonlocal _first_thought, _first_content
                if not _first_thought or not _first_content:
                    print()
                    if not _first_thought:
                        print()
                    _first_thought = True
                    _first_content = True
                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                console.print(f"[{ts_now}] ", style="dim green", end="", highlight=False)
                console.print(msg_text, style="dim", highlight=False, markup=False)

            try:
                response_text = llm_engine.generate_response(
                    user_input, 
                    tools_registry, 
                    on_tool_call=on_tool_call, 
                    on_thought_token=on_thought_token, 
                    on_content_token=on_content_token
                )
            except (HomeAssistantConnectionError, LLMConnectionError) as e:
                console.print(f"\n[red]Błąd systemu (Połączenie): {e}[/red]", highlight=False)
                import logging
                logging.exception("Błąd w trakcie analizy otoczenia/LLM.")
                continue
            
            if not _first_content or not _first_thought:
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
