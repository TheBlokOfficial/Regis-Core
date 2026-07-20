import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.ha_client import HomeAssistantClient
from core.exceptions import HomeAssistantConnectionError
from core.action_parser import parse_llm_response, execute_parsed_action
from ui.cli import console, clear_screen, print_action_result

from rich.panel import Panel
from rich.syntax import Syntax
from rich.rule import Rule

def main(ha_client: HomeAssistantClient):
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
            try:
                current_state = ha_client.get_all_states()
                syntax = Syntax(json.dumps(current_state, indent=2), "json", theme="ansi_dark", line_numbers=False)
                console.print(syntax)
            except HomeAssistantConnectionError as e:
                console.print(f"[red]Błąd połączenia z HA: {e}[/red]")
                current_state = {}
            
            console.print(Rule(style="dim"))
            console.print("[dim]Przykładowy JSON: {\"action\": \"turn_on\", \"entity_id\": \"light.biurko\", \"parameters\": {}}[/dim]\n")
            
            user_json_str = console.input("[bold white]Twój JSON (jako LLM):[/bold white] ")
            
            if user_json_str.strip().lower() in ['wyjdz', 'wyjscie', 'exit', 'quit']:
                break
                
            if not user_json_str.strip():
                continue
                
            console.print()
            console.print(Rule("[dim]Próba Wykonania (Symulator)[/dim]", style="dim"))
            
            parsed_result = parse_llm_response(user_json_str)
            parsed_result = execute_parsed_action(parsed_result, ha_client)
            
            print_action_result(parsed_result)
                
            console.input("\n[dim]Naciśnij Enter, aby przeładować stan i kontynuować...[/dim]")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    dummy_client = HomeAssistantClient("http://localhost:8123", "dummy", {})
    main(dummy_client)
