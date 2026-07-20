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

def main():
    while True:
        try:
            clear_screen()
            console.print(Panel.fit("[bold magenta]SYMULATOR LLM (WIZARD OF OZ DEBUGGER)[/bold magenta]\n[white]Ty jesteś modelem językowym! Widzisz na żywo JSON z urządzeniami i musisz zwrócić komendę, by je wysterować.[/white]", border_style="magenta"))
            
            console.print("\n[bold cyan]--- BIEŻĄCY STAN HOME ASSISTANT ---[/bold cyan]")
            current_state = ha_client.get_all_states()
            
            syntax = Syntax(json.dumps(current_state, indent=2), "json", theme="monokai", line_numbers=True)
            console.print(syntax)
            
            console.print("[dim white]Instrukcja: Wpisz czysty JSON, np:[/dim white]")
            console.print('[dim white]{"action": "turn_on", "entity_id": "light.biurko", "parameters": {"brightness_pct": 50}}[/dim white]')
            console.print("[dim white]Wpisz 'wyjdz' aby zakończyć.[/dim white]\n")
            
            user_json_str = console.input("[bold green][Twój JSON (jako LLM)]:[/bold green] ")
            
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
                
                console.print(f"\n[magenta]---> PRÓBA WYKONANIA PRZEZ ha_client.py <---[/magenta]")
                console.print(f"[magenta]Wywoływana Akcja:[/magenta] {action} | [magenta]Urządzenie:[/magenta] {entity_id} | [magenta]Parametry:[/magenta] {parameters}")
                
                if action != "none" and entity_id != "none":
                    success = ha_client.execute_action(action, entity_id, parameters)
                    if success:
                        console.print("[bold green][WYNIK API]: SUKCES! Narzędzie zadziałało poprawnie.[/bold green]")
                    else:
                        console.print("[bold red][WYNIK API]: PORAŻKA! Funkcja execute_action zwróciła False.[/bold red]")
                else:
                    console.print("[bold yellow][WYNIK API]: Brak akcji na urządzeniach.[/bold yellow]")
                    
                if reply:
                    console.print(f"\n🔊 [bold cyan][GŁOŚNIK (To słyszy człowiek)]:[/bold cyan] {reply}")
                    
            except json.JSONDecodeError:
                console.print("\n[bold red][BŁĄD SYNTAKTYCZNY]: To co wpisałeś, to nie jest kod JSON! Brakuje cudzysłowów lub klamry.[/bold red]")
                
            console.input("\n[dim white]Naciśnij Enter, aby przeładować stan HA i kontynuować...[/dim white]")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()
