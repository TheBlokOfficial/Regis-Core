import os
import questionary
from questionary import Style
from rich.console import Console
from rich.rule import Rule

from integrations.ha_client import HomeAssistantClient
from core.llm_engine import LLMEngine
from core.exceptions import HomeAssistantConnectionError, LLMConnectionError
from core import config
from core.action_parser import parse_llm_response, execute_parsed_action

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

def manage_models_flow(available_models: list[str], current_active: list[str]):
    clear_screen()
    console.print("[bold white]ZARZĄDZANIE WIDOCZNYMI MODELAMI[/bold white]")
    console.print(Rule(style="dim"))
    
    choices = []
    for m in sorted(available_models):
        choices.append(questionary.Choice(title=m, value=m, checked=(m in current_active)))
        
    new_active = questionary.checkbox(
        "Zaznacz modele, które mają być widoczne w głównym menu (Spacja - zaznacz, Enter - zapisz):",
        choices=choices,
        style=custom_style
    ).ask()
    
    if new_active is not None:
        config.save_active_models(new_active)
        console.print("[green]Zapisano pomyślnie![/green]")
        console.input("\n[dim white]Naciśnij Enter, aby powrócić do menu...[/dim white]")

def options_flow():
    settings = config.load_settings()
    while True:
        clear_screen()
        console.print("[bold white]USTAWIENIA REGIS CORE[/bold white]")
        console.print(Rule(style="dim"))
        
        current_model = settings.get("selected_model")
        display_model = current_model if current_model else "Brak"
        current_temp = settings.get("temperature", 0.5)
        
        title_model  = f"{'Wybierz model docelowy':<26} | {display_model}"
        title_temp   = f"{'Zmień temperaturę modelu':<26} | {current_temp}"
        title_manage = f"{'Zarządzaj modelami':<26} | (Lista dla menu)"
        
        choice = questionary.select(
            "Opcje systemu:",
            choices=[
                questionary.Separator(" "),
                questionary.Choice(title=title_model, value="model"),
                questionary.Choice(title=title_temp, value="temp"),
                questionary.Choice(title=title_manage, value="manage"),
                questionary.Separator(" "),
                questionary.Choice(title="Wróć do menu głównego", value="back")
            ],
            style=custom_style
        ).ask()
        
        if choice == "back" or not choice:
            config.save_settings(settings)
            break
            
        if choice == "temp":
            temp_str = questionary.text(
                "Podaj nową temperaturę (np. 0.0 - 1.0):", 
                default=str(current_temp),
                style=custom_style
            ).ask()
            try:
                new_temp = float(temp_str)
                settings["temperature"] = new_temp
                config.save_settings(settings)
            except (ValueError, TypeError):
                console.print("[red]Nieprawidłowa wartość![/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
                
        elif choice == "manage":
            try:
                available_models = LLMEngine.get_available_models()
                active_models = config.load_active_models()
                valid_active = [m for m in active_models if m in available_models]
                manage_models_flow(available_models, valid_active)
            except LLMConnectionError as e:
                console.print(f"[red]Błąd serwera LLM: {e}[/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
            
        elif choice == "model":
            try:
                available_models = LLMEngine.get_available_models()
                if not available_models:
                    console.print("[red]Brak modeli w Ollama.[/red]")
                    console.input("\n[dim]Naciśnij Enter...[/dim]")
                    continue
                    
                active_models = config.load_active_models()
                valid_active = [m for m in active_models if m in available_models]
                
                if not valid_active:
                    console.print("[yellow]Brak widocznych modeli. Najpierw dodaj je w zarządzaniu modelami.[/yellow]")
                    console.input("\n[dim]Naciśnij Enter...[/dim]")
                    continue
                    
                model_choice = questionary.select(
                    "Wybierz model docelowy:",
                    choices=[questionary.Separator(" ")] + [questionary.Choice(title=m, value=m) for m in valid_active] + [questionary.Separator(" "), questionary.Choice(title="Anuluj", value="cancel")],
                    style=custom_style
                ).ask()
                
                if model_choice and model_choice != "cancel":
                    settings["selected_model"] = model_choice
                    config.save_settings(settings)
            except LLMConnectionError as e:
                console.print(f"[red]Błąd serwera LLM: {e}[/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")

def print_action_result(result):
    """Zajmuje się wyłącznie renderowaniem wyniku w terminalu."""
    if not result.is_valid:
        console.print(f"[red]BŁĄD: {result.error}[/red]")
        return
        
    if result.action != "none" and result.entity_id != "none":
        console.print(Rule("[dim]Wykryta Intencja (System)[/dim]", style="dim"))
        
        if isinstance(result.entity_id, list):
            entity_str = f"Wiele urządzeń ({len(result.entity_id)}x)"
        else:
            entity_str = str(result.entity_id)
            
        console.print(f"[dim] Akcja: {result.action} | Cel: {entity_str} | Param: {result.parameters}[/dim]")
        
        if result.ha_execution_attempted:
            if result.ha_success:
                console.print("[dim] ✓ Pomyślnie wysterowano sprzętem.[/dim]")
            else:
                if result.ha_error_msg:
                    console.print(f"[red] ✗ Błąd komunikacji: {result.ha_error_msg}[/red]")
                else:
                    console.print("[red] ✗ Odmowa ze strony sprzętu lub niewłaściwa encja.[/red]")
                    
        console.print(Rule(style="dim"))
        console.print()
            
    if result.reply:
        console.print(f"[bold white]Regis:[/bold white] {result.reply}")


def print_production_header(model_name: str):
    console.print(f"[bold white]REGIS CORE[/bold white] [dim]| Model: {model_name} | Komenda: 'wyjdz'[/dim]")
    console.print(Rule(style="dim"))

def run_production_loop(llm_engine: LLMEngine, ha_client: HomeAssistantClient):
    clear_screen()
    print_production_header(llm_engine.model_name)
    
    while True:
        try:
            user_input = console.input("\n[bold white]Ty:[/bold white] ")
            if user_input.lower() in ["wyjscie", "wyjdz", "exit", "quit"]:
                break
                
            if not user_input.strip():
                continue
                
            with console.status("[dim]Regis analizuje otoczenie...[/dim]", spinner="dots"):
                try:
                    current_state = ha_client.get_all_states()
                    raw_response = llm_engine.generate_response(user_input, current_state)
                    
                    parsed_result = parse_llm_response(raw_response)
                    parsed_result = execute_parsed_action(parsed_result, ha_client)
                    
                except (HomeAssistantConnectionError, LLMConnectionError) as e:
                    console.print(f"\n[red]Błąd systemu (Połączenie): {e}[/red]")
                    import logging
                    logging.exception("Błąd w trakcie analizy otoczenia/LLM.")
                    continue
            
            clear_screen()
            print_production_header(llm_engine.model_name)
            
            console.print(f"\n[bold white]Ty:[/bold white] {user_input}\n")
            
            print_action_result(parsed_result)
                
        except KeyboardInterrupt:
            console.print("\n[dim]Zamykam system Regis.[/dim]")
            break

def run_main_menu():
    """Główne menu zwracające wybór użytkownika, by plik główny mógł podjąć decyzję."""
    clear_screen()
    console.print("[bold white]REGIS CORE - MENU GŁÓWNE[/bold white]")
    console.print(Rule(style="dim"))
    
    mode_choice = questionary.select(
        "Wybierz tryb uruchomienia systemu:",
        choices=[
            questionary.Separator(" "),
            questionary.Choice(title="Uruchomienie standardowe (Produkcja)", value="prod"),
            questionary.Choice(title="Tryb debugowania jako LLM (Symulator)", value="debug"),
            questionary.Choice(title="Opcje", value="options"),
            questionary.Separator(" "),
            questionary.Choice(title="Wyjście", value="exit")
        ],
        style=custom_style
    ).ask()
    
    return mode_choice
