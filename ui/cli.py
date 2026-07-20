import os
import questionary
from questionary import Style
from rich.console import Console
from rich.rule import Rule

import datetime
from integrations.ha_client import HomeAssistantClient
from core.llm_engine import LLMEngine
from core.exceptions import HomeAssistantConnectionError, LLMConnectionError
from core import config
from core.tools_registry import ToolsRegistry

console = Console()

custom_style = Style([
    ('qmark', 'fg:ansigray bold'),
    ('question', 'bold'),
    ('answer', 'fg:white bold'),
    ('pointer', 'fg:white bold'),
    ('highlighted', 'fg:white bold'),
    ('selected', 'fg:white bold'),
    ('separator', 'fg:ansigray'),
    ('instruction', 'fg:ansigray'),
    ('text', ''),
])

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header(title: str):
    clear_screen()
    console.print(f"[bold white]{title}[/bold white]")
    console.print(Rule(style="dim"))
    console.print("")

def manage_profiles_flow(available_models: list[str]):
    while True:
        print_header("ZARZĄDZANIE PROFILAMI MODELI")
        
        profiles = config.load_profiles()
        
        # Budujemy wspólną listę opcji
        choices = [
            questionary.Separator(" "),
            questionary.Choice(title="[+] Utwórz nowy profil", value="create")
        ]
        
        if profiles:
            choices.append(questionary.Separator(" "))
            choices.append(questionary.Separator("--- Istniejące profile ---"))
            for p in profiles:
                choices.append(questionary.Choice(title=f"{p['name']} ({p['model_name']} - {p['tier']})", value=p))
                
        choices.append(questionary.Separator(" "))
        choices.append(questionary.Choice(title="Wróć", value="back"))
        
        choice = questionary.select(
            "Wybierz profil do edycji lub utwórz nowy:",
            choices=choices,
            style=custom_style
        ).ask()
        
        if choice == "back" or not choice:
            return
            
        if choice == "create":
            if not available_models:
                console.print("[red]Brak zainstalowanych modeli w Ollama.[/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
                continue
                
            model_name = questionary.select(
                "Wybierz model bazowy dla profilu:",
                choices=[questionary.Separator(" ")] + available_models,
                style=custom_style
            ).ask()
            if not model_name: continue
            
            profile_name = questionary.text(
                "Podaj przyjazną nazwę profilu (np. 'Regis Zaufany'):",
                style=custom_style
            ).ask()
            if not profile_name: continue
            
            profile_id = profile_name.lower().replace(" ", "_")
            if any(p["profile_id"] == profile_id for p in profiles):
                console.print(f"[red]Błąd: Profil o nazwie '{profile_name}' (ID: {profile_id}) już istnieje![/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
                continue
            
            tier = questionary.select(
                "Przypisz klasę uprawnień (tier) do profilu:",
                choices=[questionary.Separator(" "), "basic", "advanced"],
                style=custom_style
            ).ask()
            if not tier: continue
            
            temp_str = questionary.text(
                "Podaj temperaturę modelu (np. 0.0 - 1.0):",
                default="0.5",
                style=custom_style
            ).ask()
            if not temp_str: continue
            
            try:
                temperature = float(temp_str)
            except ValueError:
                temperature = 0.5
            
            profiles.append({
                "profile_id": profile_id,
                "name": profile_name,
                "model_name": model_name,
                "tier": tier,
                "temperature": temperature
            })
            config.save_profiles(profiles)
            console.print("[green]Profil zapisany pomyślnie![/green]")
            console.input("\n[dim white]Naciśnij Enter...[/dim white]")
            
        else:
            # W tym przypadku `choice` to słownik wybranego profilu
            selected_profile = choice
            
            while True:
                print_header(f"EDYCJA PROFILU: {selected_profile['name']}")
                
                edit_choice = questionary.select(
                    "Wybierz właściwość do edycji lub akcję:",
                    choices=[
                        questionary.Separator(" "),
                        questionary.Choice(title=f"Nazwa: {selected_profile['name']}", value="name"),
                        questionary.Choice(title=f"Model: {selected_profile['model_name']}", value="model"),
                        questionary.Choice(title=f"Poziom (tier): {selected_profile['tier']}", value="tier"),
                        questionary.Choice(title=f"Temperatura: {selected_profile.get('temperature', 0.5)}", value="temp"),
                        questionary.Separator(" "),
                        questionary.Choice(title="Usuń profil", value="delete"),
                        questionary.Separator(" "),
                        questionary.Choice(title="Wróć", value="done")
                    ],
                    style=custom_style
                ).ask()
                
                if edit_choice == "done" or not edit_choice:
                    break
                    
                if edit_choice == "delete":
                    confirm = questionary.confirm(f"Czy na pewno chcesz usunąć profil '{selected_profile['name']}'?").ask()
                    if confirm:
                        profiles = [p for p in profiles if p["profile_id"] != selected_profile["profile_id"]]
                        config.save_profiles(profiles)
                        
                        settings = config.load_settings()
                        if settings.get("selected_profile") == selected_profile["profile_id"]:
                            settings["selected_profile"] = None
                            config.save_settings(settings)
                            
                        console.print("[green]Profil usunięto pomyślnie.[/green]")
                        console.input("\n[dim]Naciśnij Enter...[/dim]")
                        break # Wychodzi do menu wyboru profili
                            
                        if edit_choice == "name":
                            new_name = questionary.text(
                                "Podaj nową przyjazną nazwę profilu:",
                                default=selected_profile['name'],
                                style=custom_style
                            ).ask()
                            if not new_name or new_name == selected_profile['name']: continue
                            
                            new_id = new_name.lower().replace(" ", "_")
                            if new_id != selected_profile["profile_id"] and any(p["profile_id"] == new_id for p in profiles):
                                console.print(f"[red]Błąd: Profil o nazwie '{new_name}' już istnieje![/red]")
                                console.input("\n[dim]Naciśnij Enter...[/dim]")
                                continue
                                
                            if new_id != selected_profile["profile_id"]:
                                settings = config.load_settings()
                                if settings.get("selected_profile") == selected_profile["profile_id"]:
                                    settings["selected_profile"] = new_id
                                    config.save_settings(settings)
                                    
                            selected_profile["name"] = new_name
                            selected_profile["profile_id"] = new_id
                            config.save_profiles(profiles)
                            console.print("[green]Zapisano nową nazwę profilu.[/green]")
                            console.input("\n[dim]Naciśnij Enter...[/dim]")
                            
                        elif edit_choice == "model":
                            new_model = questionary.select(
                                "Wybierz nowy model bazowy:",
                                choices=[questionary.Separator(" ")] + available_models,
                                default=selected_profile['model_name'],
                                style=custom_style
                            ).ask()
                            if new_model and new_model != selected_profile["model_name"]:
                                selected_profile["model_name"] = new_model
                                config.save_profiles(profiles)
                                console.print("[green]Zapisano nowy model bazowy.[/green]")
                                console.input("\n[dim]Naciśnij Enter...[/dim]")
                                
                        elif edit_choice == "tier":
                            new_tier = questionary.select(
                                "Przypisz nową klasę uprawnień (tier):",
                                choices=[questionary.Separator(" "), "basic", "advanced"],
                                default=selected_profile['tier'],
                                style=custom_style
                            ).ask()
                            if new_tier and new_tier != selected_profile["tier"]:
                                selected_profile["tier"] = new_tier
                                config.save_profiles(profiles)
                                console.print("[green]Zapisano nową klasę uprawnień.[/green]")
                                console.input("\n[dim]Naciśnij Enter...[/dim]")
                                
                        elif edit_choice == "temp":
                            temp_str = questionary.text(
                                "Podaj nową temperaturę (np. 0.0 - 1.0):",
                                default=str(selected_profile.get('temperature', 0.5)),
                                style=custom_style
                            ).ask()
                            if temp_str:
                                try:
                                    new_temp = float(temp_str)
                                    selected_profile["temperature"] = new_temp
                                    config.save_profiles(profiles)
                                    console.print("[green]Zapisano nową temperaturę profilu.[/green]")
                                    console.input("\n[dim]Naciśnij Enter...[/dim]")
                                except ValueError:
                                    console.print("[red]Nieprawidłowa wartość![/red]")
                                    console.input("\n[dim]Naciśnij Enter...[/dim]")

def options_flow():
    settings = config.load_settings()
    while True:
        print_header("USTAWIENIA REGIS CORE")
        
        profiles = config.load_profiles()
        current_profile_id = settings.get("selected_profile")
        current_profile = next((p for p in profiles if p["profile_id"] == current_profile_id), None)
        
        display_profile = current_profile["name"] if current_profile else "Brak"
        
        title_profile = f"{'Wybierz aktywny profil':<26} | {display_profile}"
        title_manage = f"{'Zarządzaj profilami':<26} | (Kreator profili)"
        
        choice = questionary.select(
            "Opcje systemu:",
            choices=[
                questionary.Separator(" "),
                questionary.Choice(title=title_profile, value="profile"),
                questionary.Choice(title=title_manage, value="manage"),
                questionary.Separator(" "),
                questionary.Choice(title="Wróć do menu głównego", value="back")
            ],
            style=custom_style
        ).ask()
        
        if choice == "back" or not choice:
            config.save_settings(settings)
            break
            
        elif choice == "manage":
            try:
                available_models = LLMEngine.get_available_models()
                manage_profiles_flow(available_models)
            except LLMConnectionError as e:
                console.print(f"[red]Błąd serwera LLM: {e}[/red]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
            
        elif choice == "profile":
            profiles = config.load_profiles()
            if not profiles:
                console.print("[yellow]Brak utworzonych profili. Najpierw utwórz profil w Zarządzaniu profilami.[/yellow]")
                console.input("\n[dim]Naciśnij Enter...[/dim]")
                continue
                
            profile_choices = [questionary.Choice(title=f"{p['name']} ({p['model_name']})", value=p['profile_id']) for p in profiles]
            selected = questionary.select(
                "Wybierz profil do aktywacji:",
                choices=profile_choices + [questionary.Separator(" "), questionary.Choice(title="Anuluj", value="cancel")],
                style=custom_style
            ).ask()
            
            if selected and selected != "cancel":
                settings["selected_profile"] = selected
                config.save_settings(settings)

def print_production_header(model_name: str, tier: str, profile_name: str, temperature: float = 0.5):
    console.print(f"[bold white]REGIS CORE[/bold white] [dim]| Profil: {profile_name} | Model: {model_name} ({tier}) | Temp: {temperature}[/dim]\n[dim]Komendy: 'wyjdz' / 'reset' / 'tier' / 'temp' / 'profile'[/dim]")
    console.print(Rule(style="dim"))
    console.print("")

def run_production_loop(llm_engine: LLMEngine, ha_client: HomeAssistantClient, profile_name: str = "Brak profilu"):
    clear_screen()
    print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
    tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
    
    while True:
        try:
            user_input = console.input("\n[bold white]Ty:[/bold white] ")
            if user_input.lower() in ["wyjscie", "wyjdz", "exit", "quit"]:
                break
                
            if user_input.lower() in ["reset", "zapomnij"]:
                llm_engine.clear_history()
                clear_screen()
                print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
                console.print("\n[dim]Pamięć podręczna modelu została wyczyszczona.[/dim]")
                continue
                
            if user_input.lower().startswith("tier "):
                new_tier = user_input.split(" ")[1].lower().strip()
                if new_tier in ["basic", "advanced"]:
                    llm_engine.tier = new_tier
                    tools_registry = ToolsRegistry(ha_client, new_tier)
                    clear_screen()
                    print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
                    console.print(f"\n[green]Pomyślnie zmieniono poziom uprawnień (tier) na obecną sesję: {new_tier}[/green]")
                else:
                    console.print("\n[red]Nieznany poziom! Dostępne: basic, advanced.[/red]")
                continue
                
            if user_input.lower().startswith("temp "):
                try:
                    new_temp = float(user_input.split(" ")[1].strip())
                    if 0.0 <= new_temp <= 1.0:
                        llm_engine.temperature = new_temp
                        clear_screen()
                        print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
                        console.print(f"\n[green]Pomyślnie zmieniono temperaturę na obecną sesję: {new_temp}[/green]")
                    else:
                        console.print("\n[red]Podaj wartość temperatury między 0.0 a 1.0[/red]")
                except ValueError:
                    console.print("\n[red]Nieprawidłowa wartość temperatury![/red]")
                continue
                
            if user_input.lower() == "profile":
                profiles = config.load_profiles()
                if not profiles:
                    console.print("\n[yellow]Brak utworzonych profili.[/yellow]")
                    continue
                    
                profile_choices = [questionary.Separator(" ")] + [questionary.Choice(title=f"{p['name']} ({p['model_name']} - {p['tier']})", value=p) for p in profiles] + [questionary.Separator(" "), questionary.Choice(title="Anuluj", value="cancel")]
                selected = questionary.select(
                    "Wybierz profil do zmiany na obecną sesję:",
                    choices=profile_choices,
                    style=custom_style
                ).ask()
                
                if selected and selected != "cancel":
                    llm_engine.model_name = selected["model_name"]
                    llm_engine.tier = selected["tier"]
                    llm_engine.temperature = selected.get("temperature", 0.5)
                    profile_name = selected["name"]
                    tools_registry = ToolsRegistry(ha_client, llm_engine.tier)
                    
                    settings = config.load_settings()
                    settings["selected_profile"] = selected["profile_id"]
                    config.save_settings(settings)
                    
                    clear_screen()
                    print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
                    console.print(f"\n[green]Pomyślnie przełączono na profil: {profile_name}[/green]")
                else:
                    clear_screen()
                    print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
                continue
                
            if not user_input.strip():
                continue
                
            clear_screen()
            print_production_header(llm_engine.model_name, llm_engine.tier, profile_name, getattr(llm_engine, 'temperature', 0.5))
            
            for msg in llm_engine.history:
                if msg.get("is_internal"):
                    continue
                
                ts = msg.get("timestamp", "")
                ts_str = f"[dim green][{ts}][/dim green] " if ts else ""
                
                if msg["role"] == "user":
                    console.print(f"\n{ts_str}[bold white]Ty:[/bold white] {msg['content']}\n", highlight=False)
                elif msg["role"] == "assistant":
                    console.print(f"{ts_str}[bold white]Regis:[/bold white] {msg['content']}", highlight=False)
                elif msg["role"] == "tool_log":
                    console.print(f"{ts_str}[dim]{msg['content']}[/dim]", highlight=False)
                        
            now = datetime.datetime.now().strftime("%H:%M:%S")
            console.print(f"\n[dim green][{now}][/dim green] [bold white]Ty:[/bold white] {user_input}\n", highlight=False)
                
            status = console.status("[dim]Regis analizuje żądanie...[/dim]", spinner="dots")
            status.start()
            
            def status_update(msg_text):
                status.stop()
                ts_now = datetime.datetime.now().strftime("%H:%M:%S")
                console.print(f"[dim green][{ts_now}][/dim green] [dim]{msg_text}[/dim]", highlight=False)
                status.start()
                
            first_token_received = False
            
            def stream_update(token: str):
                nonlocal first_token_received
                if not first_token_received:
                    if not token.strip():
                        return
                    status.stop()
                    now_regis = datetime.datetime.now().strftime("%H:%M:%S")
                    console.print(f"[dim green][{now_regis}][/dim green] [bold white]Regis:[/bold white] ", end="", highlight=False)
                    first_token_received = True
                print(token, end="", flush=True)

            try:
                response_text = llm_engine.generate_response(user_input, tools_registry, status_update, stream_update)
            except (HomeAssistantConnectionError, LLMConnectionError) as e:
                status.stop()
                console.print(f"\n[red]Błąd systemu (Połączenie): {e}[/red]", highlight=False)
                import logging
                logging.exception("Błąd w trakcie analizy otoczenia/LLM.")
                continue
            finally:
                status.stop()
            
            if first_token_received:
                print()
                
        except KeyboardInterrupt:
            console.print("\n[dim]Zamykam system Regis.[/dim]")
            break

def run_main_menu():
    """Główne menu zwracające wybór użytkownika, by plik główny mógł podjąć decyzję."""
    print_header("REGIS CORE - MENU GŁÓWNE")
    
    mode_choice = questionary.select(
        "Wybierz tryb uruchomienia systemu:",
        choices=[
            questionary.Separator(" "),
            questionary.Choice(title="Uruchomienie standardowe (Produkcja)", value="prod"),
            questionary.Choice(title="Tryb debugowania jako LLM (Symulator)", value="debug"),
            questionary.Choice(title="Opcje", value="options"),
            questionary.Separator(" "),
            questionary.Choice(title="Wyjście", value="exit")
        ],
        style=custom_style
    ).ask()
    
    return mode_choice
