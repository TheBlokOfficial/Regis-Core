import os
import json
import socket
import questionary

def run_wizard():
    print("\n" + "="*50)
    print("      Regis Node: Konfiguracja Początkowa")
    print("="*50 + "\n")
    
    instance_name = questionary.text(
        "Nazwa tej instancji:", 
        default=f"Node-{socket.gethostname()}"
    ).ask()
    
    room = questionary.text(
        "Pokój (np. salon):", 
        default="salon"
    ).ask()
    
    controller_url = questionary.text(
        "URL Kontrolera (wpisz 'auto' dla wykrywania po UDP):", 
        default="auto"
    ).ask()
    
    active_tier = questionary.select(
        "Wybierz Tier modelu LLM (poziom inteligencji):",
        choices=["butler (1.5B)", "regis (14B)", "prime (32B)"],
        default="regis (14B)"
    ).ask()
    
    # Wyciąganie samego klucza np "regis"
    active_tier = active_tier.split(" ")[0]
    
    print("\nUsługi w tle:")
    run_worker = questionary.confirm("Uruchamiać Worker (LLM) automatycznie?", default=True).ask()
    run_satellite = questionary.confirm("Uruchamiać Satellite (Mikrofon) automatycznie?", default=False).ask()
    
    settings = {
        "instance_name": instance_name,
        "room": room,
        "controller_url": controller_url,
        "active_tier": active_tier,
        "worker_port": 8001,
        "worker_host": "0.0.0.0",
        "autostart_worker": run_worker,
        "autostart_satellite": run_satellite
    }
    
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    settings_path = os.path.join(data_dir, "settings.json")
    
    with open(settings_path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)
        
    print(f"\n[OK] Konfiguracja zapisana w {settings_path}")
    print("[OK] Uruchamianie aplikacji w System Tray...\n")

if __name__ == "__main__":
    run_wizard()
