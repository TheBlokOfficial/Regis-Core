import sys
import os
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations.ha_client import HomeAssistantClient
from core.exceptions import HomeAssistantConnectionError
from core.action_parser import parse_llm_response, execute_parsed_action
from core import config
from core.llm_engine import SYSTEM_PROMPT
from ui.cli import console, clear_screen, print_action_result, print_production_header

from rich.rule import Rule

def main(ha_client: HomeAssistantClient):
    settings = config.load_settings()
    model_name = settings.get("selected_model", "WIZARD OF OZ")
    
    while True:
        try:
            clear_screen()
            print_production_header(f"{model_name} (Symulator)")
            
            try:
                current_state = ha_client.get_all_states()
                system_p = SYSTEM_PROMPT.replace("{ha_state}", json.dumps(current_state, indent=2))
                console.print(f"\n[dim]{system_p}[/dim]\n")
            except HomeAssistantConnectionError as e:
                console.print(f"[red]Błąd połączenia z HA: {e}[/red]")
            
            console.print(Rule(style="dim"))
            
            user_json_str = console.input("\n[bold white]Ty:[/bold white] ")
            
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
