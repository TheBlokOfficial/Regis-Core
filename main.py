import os
import logging
from core import config
from core.llm_engine import LLMEngine
from integrations.ha_client import HomeAssistantClient
from ui import cli

def setup_logging():
    log_file = os.path.join(config.DATA_DIR, "regis.log")
    if not os.path.exists(config.DATA_DIR):
        os.makedirs(config.DATA_DIR)
        
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8')
        ]
    )

def main():
    setup_logging()
    logging.info("Aplikacja Regis Core została uruchomiona.")
    
    while True:
        mode_choice = cli.run_main_menu()
        
        if mode_choice == "exit" or not mode_choice:
            cli.console.print("[red]Zamykam system Regis.[/red]")
            logging.info("Aplikacja Regis Core została zamknięta przez użytkownika.")
            return
            
        settings = config.load_settings()
        aliases = config.load_aliases()
        ha_client = HomeAssistantClient(
            url=settings.get("ha_url", "http://192.168.0.50:8123"),
            token=settings.get("ha_token", "TWÓJ_TOKEN_TUTAJ"),
            aliases=aliases
        )

        if mode_choice == "debug":
            cli.console.print("[yellow]Tryb symulatora został usunięty w nowej architekturze Agentic Tools.[/yellow]")
            cli.console.input("\n[dim]Naciśnij Enter...[/dim]")
            continue
            
        if mode_choice == "options":
            cli.options_flow()
            continue
            
        if mode_choice == "prod":
            selected_profile_id = settings.get("selected_profile")
            profiles = config.load_profiles()
            selected_profile = next((p for p in profiles if p["profile_id"] == selected_profile_id), None)
            
            if not selected_profile:
                cli.console.print("[red]Brak aktywnego profilu! Przejdź najpierw do Opcji, aby go ustawić.[/red]")
                cli.console.input("\n[dim]Naciśnij Enter...[/dim]")
                continue
                
            llm_engine = LLMEngine(
                model_name=selected_profile["model_name"],
                tier=selected_profile["tier"],
                temperature=selected_profile.get("temperature", 0.5),
                history_limit=settings.get("history_limit", 10)
            )
            
            cli.run_production_loop(llm_engine, ha_client, selected_profile["name"])

if __name__ == "__main__":
    main()
