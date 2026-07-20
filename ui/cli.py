import os
import questionary
from questionary import Style
from rich.console import Console
from rich.rule import Rule

import datetime
from integrations.ha_client import HomeAssistantClient
from core.llm_engine import LLMEngine
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
    console.print(f"[bold white]REGIS CORE[/bold white] [dim]| Warstwa: {display_name} | Model: {model_name} | Temp: {temperature}[/dim]\n[dim]Komendy: '/exit' / '/clear' / '/tier'[/dim]")
    console.print(Rule(style="dim"))
    console.print("")

def run_production_loop(llm_engine: LLMEngine, ha_client: HomeAssistantClient, display_name: str = "Brak profilu"):
    clear_screen()
    print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
    tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
    
    while True:
        try:
            user_input = console.input("\n[bold white]Ty:[/bold white] ")
            if user_input.lower() == "/exit":
                break
                
            if user_input.lower() == "/help":
                console.print("\n[bold white]Dostępne komendy:[/bold white]")
                console.print("[dim]/help[/dim] - [dim]Wyświetla tę listę komend[/dim]")
                console.print("[dim]/exit[/dim] - [dim]Kończy działanie programu[/dim]")
                console.print("[dim]/clear[/dim] - [dim]Czyści historię bieżącej konwersacji[/dim]")
                console.print("[dim]/tier[/dim] - [dim]Przełącza pomiędzy warstwą lokalną a Szefem na obecną sesję[/dim]\n")
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
                if llm_engine.tier == "local":
                    llm_engine.tier = "boss"
                    llm_engine.model_name = "qwen2.5:14b"
                    llm_engine.temperature = 0.7
                    display_name = "Szef (Główny Gospodarz)"
                else:
                    llm_engine.tier = "local"
                    llm_engine.model_name = "qwen2.5:7b"
                    llm_engine.temperature = 0.5
                    display_name = "Recepcjonista (Lokalny)"
                    
                tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
                settings = config.load_settings()
                settings["active_tier"] = llm_engine.tier
                config.save_settings(settings)
                
                clear_screen()
                print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
                console.print(f"\n[green]Pomyślnie przełączono na warstwę: {display_name}[/green]")
                continue
                
            if not user_input.strip():
                continue
                
            clear_screen()
            print_production_header(llm_engine.model_name, llm_engine.tier, display_name, getattr(llm_engine, 'temperature', 0.5))
            
            for msg in llm_engine.history:
                if msg.get("is_internal"):
                    continue
                
                ts = msg.get("timestamp", "")
                ts_str = f"[dim green][{ts}][/dim green] " if ts else ""
                
                if msg["role"] == "user":
                    console.print(f"\n{ts_str}[bold white]Ty:[/bold white] {msg['content']}\n", highlight=False)
                elif msg["role"] == "assistant":
                    console.print(f"{ts_str}[bold white]Regis:[/bold white] {msg['content']}", highlight=False)
                elif msg["role"] == "tool_log":
                    console.print(f"{ts_str}[dim]{msg['content']}[/dim]", highlight=False)
                        
            now = datetime.datetime.now().strftime("%H:%M:%S")
            console.print(f"\n[dim green][{now}][/dim green] [bold white]Ty:[/bold white] {user_input}\n", highlight=False)
                
            status = console.status("[dim]Regis analizuje żądanie...[/dim]", spinner="dots")
            status.start()
            
            first_token_received = False
            
            def status_update(msg_text):
                nonlocal first_token_received
                if first_token_received:
                    print() # Zamknięcie poprzedniej linii z tekstem
                    first_token_received = False
                status.stop()
                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                console.print(f"[dim green][{ts_now}][/dim green] [dim]{msg_text}[/dim]", highlight=False)
                status.start()
                
            def stream_update(token: str):
                nonlocal first_token_received
                if not first_token_received:
                    if not token.strip():
                        return
                    status.stop()
                    now_regis = datetime.datetime.now().strftime("%H:%M:%S")
                    console.print(f"[dim green][{now_regis}][/dim green] [bold white]Regis:[/bold white] ", end="", highlight=False)
                    first_token_received = True
                print(token, end="", flush=True)

            try:
                response_text = llm_engine.generate_response(user_input, tools_registry, status_update, stream_update)
            except (HomeAssistantConnectionError, LLMConnectionError) as e:
                status.stop()
                console.print(f"\n[red]Błąd systemu (Połączenie): {e}[/red]", highlight=False)
                import logging
                logging.exception("Błąd w trakcie analizy otoczenia/LLM.")
                continue
            finally:
                status.stop()
            
            if first_token_received:
                print()
                
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
