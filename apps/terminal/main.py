import os
import logging
from core import config
from core.llm_engine import LLMEngine
from integrations.ha_client import HomeAssistantClient
from apps.terminal import cli

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


        if mode_choice == "prod":
            active_tier = settings.get("active_tier", "butler")
            
            # Konfiguracja per tier
            tier_config = {
                "butler": {
                    "model": "qwen2.5:1.5b-instruct",
                    "temperature": 0.1,
                    "display_name": "Lokaj"
                },
                "regis": {
                    "model": "qwen2.5:14b-instruct",
                    "temperature": 0.1,
                    "display_name": "Regis"
                },
                "prime": {
                    "model": "qwen2.5:32b-instruct",
                    "temperature": 0.1,
                    "display_name": "Regis Prime"
                }
            }
            
            tier_cfg = tier_config.get(active_tier, tier_config["butler"])
            model_name = settings.get("selected_model", tier_cfg["model"])
            temperature = tier_cfg["temperature"]
            display_name = tier_cfg["display_name"]
                
            llm_engine = LLMEngine(
                model_name=model_name,
                tier=active_tier,
                temperature=temperature,
                history_limit=settings.get("history_limit", 20)
            )
            
            cli.run_production_loop(llm_engine, ha_client, display_name)
            
        elif mode_choice == "remote":
            from core.remote_client import RemoteClient
            client = RemoteClient(base_url="http://192.168.0.119:8000")
            cli.run_remote_loop(client)


if __name__ == "__main__":
    main()
