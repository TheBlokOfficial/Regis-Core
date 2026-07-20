import sys
import os
import json

# Dodanie katalogu głównego do ścieżki
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from integrations import ha_client
from core import llm_engine
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

console = Console()

def show_exact_context():
    console.print("[yellow]Pobieram stan z Home Assistanta na żywo...[/yellow]\n")
    current_state = ha_client.get_all_states()
    
    final_prompt = llm_engine.SYSTEM_PROMPT.replace("{ha_state}", json.dumps(current_state, indent=2, ensure_ascii=False))
    
    console.print(Panel.fit("[bold cyan]OTO DOKŁADNY TEKST, KTÓRY CZYTA LLM (SYSTEM PROMPT)[/bold cyan]", border_style="cyan"))
    
    syntax = Syntax(final_prompt, "markdown", theme="monokai", word_wrap=True)
    console.print(syntax)
    
    console.print("\n[bold magenta][Podsumowanie]: Jak widzisz, Model dostaje potężny kawał tekstu za każdym naciśnięciem Enter![/bold magenta]")

if __name__ == "__main__":
    show_exact_context()
