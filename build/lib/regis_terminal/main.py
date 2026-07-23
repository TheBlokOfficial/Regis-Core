import os
import sys

# Wymuszenie kodowania UTF-8 w konsoli Windows dla biblioteki rich
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import logging
from core import config
from core.llm_engine import LLMEngine
from integrations.ha_client import HomeAssistantClient
from regis_terminal import cli

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
            import atexit
            from core.remote_client import RemoteClient
            server_url = settings.get("server_url", settings.get("controller_url", "http://127.0.0.1:8000"))
            
            has_errors = False
            if server_url == "auto":
                from regis_terminal.cli import console
                console.print("\n[dim]Wyszukiwanie kontrolera w sieci lokalnej (Auto-Discovery)... Proszę czekać.[/dim]")
                from core.discovery import discover_controller
                try:
                    server_url = discover_controller()
                    console.print(f"[green]Odnaleziono kontroler: {server_url}[/green]")
                except Exception as e:
                    logging.warning(f"Auto-Discovery zawiodło: {e}")
                    console.print("[yellow]Nie odnaleziono kontrolera (timeout). Używam domyślnego adresu http://127.0.0.1:8000[/yellow]")
                    server_url = "http://127.0.0.1:8000"
                    has_errors = True
                    
            satellite_id = settings.get("worker_id", "terminal-dev")  # reużywamy worker_id jako ID terminala
            terminal_room = settings.get("terminal_room", None)

            # Rejestracja Terminala jako Satelity w Kontrolerze
            registration_payload = {
                "id": satellite_id,
                "room": terminal_room,
                "type": "terminal",
                "capabilities": ["text"],
                "wakeword_local": False,
            }
            try:
                import requests as _req
                console.print(f"[dim]Rejestracja terminala w kontrolerze ({server_url})...[/dim]")
                resp = _req.post(f"{server_url}/v1/satellites/register", json=registration_payload, timeout=5)
                if resp.ok:
                    logging.info(f"Terminal '{satellite_id}' zarejestrowany jako satelita (pokój={terminal_room}).")
                else:
                    logging.warning(f"Rejestracja satelity zwróciła {resp.status_code}. Kontynuuję.")
                    has_errors = True
            except Exception as e:
                logging.warning(f"Nie udało się zarejestrować terminala jako satelity: {e}. Kontynuuję.")
                console.print("[red]Błąd rejestracji w kontrolerze (Kontroler jest offline?).[/red]")
                has_errors = True

            if has_errors:
                from regis_terminal.cli import console
                console.input("\n[dim]Naciśnij Enter, aby wejść do trybu awaryjnego (urządzenie może nie działać prawidłowo)...[/dim]")

            def _unregister_satellite():
                try:
                    import requests as _req
                    _req.delete(f"{server_url}/v1/satellites/{satellite_id}", timeout=5)
                    logging.info(f"Terminal '{satellite_id}' wyrejestrowany z Kontrolera.")
                except Exception:
                    pass

            atexit.register(_unregister_satellite)

            client = RemoteClient(base_url=server_url, satellite_id=satellite_id)
            cli.run_remote_loop(client)


if __name__ == "__main__":
    main()
