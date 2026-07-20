import os
import json
import questionary
from rich.console import Console
from rich.panel import Panel

from integrations import ha_client
from core import llm_engine

console = Console()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ACTIVE_MODELS_FILE = os.path.join(BASE_DIR, "data", "active_models.json")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_active_models():
    if not os.path.exists(ACTIVE_MODELS_FILE):
        return []
    with open(ACTIVE_MODELS_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def save_active_models(models):
    with open(ACTIVE_MODELS_FILE, "w", encoding="utf-8") as f:
        json.dump(models, f, indent=4)

def manage_models_flow(available_models, current_active):
    clear_screen()
    console.print(Panel.fit("[bold yellow]ZARZĄDZANIE WIDOCZNYMI MODELAMI[/bold yellow]", border_style="yellow"))
    
    choices = []
    for m in sorted(available_models):
        choices.append(questionary.Choice(title=m, value=m, checked=(m in current_active)))
        
    new_active = questionary.checkbox(
        "Zaznacz modele, które mają być widoczne w głównym menu (Spacja - zaznacz, Enter - zapisz):",
        choices=choices
    ).ask()
    
    if new_active is not None:
        save_active_models(new_active)
        console.print("[green]Zapisano pomyślnie![/green]")
        console.input("\n[dim white]Naciśnij Enter, aby powrócić do menu...[/dim white]")

def select_model_flow():
    while True:
        clear_screen()
        console.print(Panel.fit("[bold cyan]REGIS CORE - SYMULACJA LOKAJA[/bold cyan]", border_style="cyan"))
        console.print("[dim white]Sprawdzam listę dostępnych modeli w Ollama...[/dim white]")
        
        available_models = llm_engine.get_available_models()
        
        if not available_models:
            console.print("[bold red]Nie znaleziono żadnych modeli! Upewnij się, że serwer Ollama działa na localhost:11434.[/bold red]")
            return None
            
        active_models = load_active_models()
        
        # Filtrujemy tylko te zaznaczone, które wciąż fizycznie istnieją
        valid_active = [m for m in active_models if m in available_models]
        
        choices = []
        if valid_active:
            choices.append(questionary.Separator("--- Aktywne Modele ---"))
            for f in valid_active:
                choices.append(questionary.Choice(title=f"✓ {f}", value=f))
        else:
            choices.append(questionary.Separator("--- Brak aktywnych modeli (Przejdź do ustawień) ---"))
                
        choices.append(questionary.Separator("--- ⚙️ Ustawienia ---"))
        choices.append(questionary.Choice(title="⚙️ [Zarządzaj widocznymi modelami]", value="__MANAGE__"))
        choices.append(questionary.Choice(title="❌ [Wyjdź]", value="__EXIT__"))
            
        selected_value = questionary.select(
            "Wybierz model LLM, który ma pełnić rolę Regisa:",
            choices=choices
        ).ask()
        
        if selected_value == "__EXIT__" or not selected_value:
            return None
            
        if selected_value == "__MANAGE__":
            manage_models_flow(available_models, valid_active)
            continue
            
        return selected_value

def main():
    selected_model = select_model_flow()
    
    if not selected_model:
        console.print("[red]Zamykam system Regis.[/red]")
        return
        
    llm_engine.MODEL_NAME = selected_model
    
    clear_screen()
    header_panel = Panel(
        f"Model: [bold]{llm_engine.MODEL_NAME}[/bold] | Komenda: 'wyjdz'", 
        title="[cyan]REGIS CORE[/cyan]", 
        border_style="cyan"
    )
    console.print(header_panel)
    
    from rich.status import Status
    from rich.rule import Rule
    
    while True:
        try:
            user_input = console.input("\n[bold white]Ty:[/bold white] ")
            if user_input.lower() in ["wyjscie", "wyjdz", "exit", "quit"]:
                break
                
            if not user_input.strip():
                continue
                
            with console.status("[dim]Regis analizuje otoczenie...[/dim]", spinner="dots"):
                current_state = ha_client.get_all_states()
                response = llm_engine.generate_response(user_input, current_state)
            
            # Wyczyść ekran, by pokazać czystą interakcję
            clear_screen()
            console.print(header_panel)
            
            console.print(f"\n[bold white]Ty:[/bold white] {user_input}\n")
            
            if response.startswith("[BŁĄD]"):
                console.print(f"[red]{response}[/red]")
                continue
                
            try:
                action_data = json.loads(response)
                
                action = action_data.get("action", "none")
                entity_id = action_data.get("entity_id", "none")
                parameters = action_data.get("parameters", {})
                reply = action_data.get("reply", "")
                
                if action != "none" and entity_id != "none":
                    console.print(Rule("[dim]Wykryta Intencja (System)[/dim]", style="dim"))
                    
                    if isinstance(entity_id, list):
                        entity_str = f"Wiele urządzeń ({len(entity_id)}x)"
                    else:
                        entity_str = str(entity_id)
                        
                    console.print(f"[dim] Akcja: {action} | Cel: {entity_str} | Param: {parameters}[/dim]")
                    
                    success = ha_client.execute_action(action, entity_id, parameters)
                    if not success:
                        console.print("[red] ✗ Wystąpił błąd komunikacji ze sprzętem.[/red]")
                    else:
                        console.print("[dim] ✓ Pomyślnie wysterowano sprzętem.[/dim]")
                        
                    console.print(Rule(style="dim"))
                    console.print()
                        
                if reply:
                    console.print(f"[bold white]Regis:[/bold white] {reply}")
                    
            except json.JSONDecodeError:
                console.print(f"[red][BŁĄD PARSOWANIA JSON]:[/red]\n{response}")
                
        except KeyboardInterrupt:
            console.print("\n[dim]Zamykam system Regis.[/dim]")
            break

if __name__ == "__main__":
    main()
