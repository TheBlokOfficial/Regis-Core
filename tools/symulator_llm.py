import sys
import os
import json

# Dodanie katalogu głównego do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations import ha_client
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

from rich.rule import Rule

def main():
    while True:
        try:
            clear_screen()
            header_panel = Panel(
                "[dim]Jesteś modelem LLM. Analizujesz poniższy stan i zwracasz JSON komendy.[/dim]\n[dim]Wpisz 'wyjdz' aby zakończyć symulację.[/dim]", 
                title="[yellow]SYMULATOR LLM (WIZARD OF OZ)[/yellow]", 
                border_style="yellow"
            )
            console.print(header_panel)
            
            console.print(Rule("[dim]Bieżący Stan Home Assistant[/dim]", style="dim"))
            current_state = ha_client.get_all_states()
            
            syntax = Syntax(json.dumps(current_state, indent=2), "json", theme="ansi_dark", line_numbers=False)
            console.print(syntax)
            
            console.print(Rule(style="dim"))
            console.print("[dim]Przykładowy JSON: {\"action\": \"turn_on\", \"entity_id\": \"light.biurko\", \"parameters\": {}}[/dim]\n")
            
            user_json_str = console.input("[bold white]Twój JSON (jako LLM):[/bold white] ")
            
            if user_json_str.strip().lower() in ['wyjdz', 'wyjscie', 'exit', 'quit']:
                break
                
            if not user_json_str.strip():
                continue
                
            try:
                action_data = json.loads(user_json_str)
                action = action_data.get("action", "none")
                entity_id = action_data.get("entity_id", "none")
                parameters = action_data.get("parameters", {})
                reply = action_data.get("reply", "")
                
                console.print()
                console.print(Rule("[dim]Próba Wykonania (Symulator)[/dim]", style="dim"))
                
                if action != "none" and entity_id != "none":
                    if isinstance(entity_id, list):
                        entity_str = f"Wiele urządzeń ({len(entity_id)}x)"
                    else:
                        entity_str = str(entity_id)
                        
                    console.print(f"[dim] Akcja: {action} | Cel: {entity_str} | Param: {parameters}[/dim]")
                    
                    success = ha_client.execute_action(action, entity_id, parameters)
                    if success:
                        console.print("[dim] ✓ Pomyślnie wysterowano sprzętem (API).[/dim]")
                    else:
                        console.print("[red] ✗ Wystąpił błąd komunikacji ze sprzętem (API).[/red]")
                else:
                    console.print("[dim] Brak fizycznej akcji na urządzeniach.[/dim]")
                    
                console.print(Rule(style="dim"))
                
                if reply:
                    console.print(f"\n[bold white]Odpowiedź Regisa (Syntezator mowy):[/bold white] {reply}")
                    
            except json.JSONDecodeError:
                console.print("\n[red][BŁĄD SYNTAKTYCZNY]: Nieprawidłowy format JSON.[/red]")
                
            console.input("\n[dim]Naciśnij Enter, aby przeładować stan i kontynuować...[/dim]")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
