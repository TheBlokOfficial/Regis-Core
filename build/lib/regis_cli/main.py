import sys
import questionary
import subprocess
from regis_cli.ux import console, custom_style
from regis_cli.builders import build_portable_windows
from regis_cli.deployers import deploy_to_pi

def main():
    while True:
        console.clear()
        console.print("[header]Regis-Core | Menedżer Projektu[/header]\n")
        
        choice = questionary.select(
            "Wybierz akcję:",
            choices=[
                "[Zbuduj] Paczki Portable (Windows)",
                "[Wdróż] Serwer produkcyjny (Raspberry Pi)",
                "[Narzędzia] Uruchom testy",
                "[Wyjście] Zamknij panel"
            ],
            style=custom_style
        ).ask()

        if choice is None or "[Wyjście]" in choice:
            console.print("[info]Zamykanie...[/info]")
            sys.exit(0)
        elif "[Zbuduj]" in choice:
            build_portable_windows()
            console.input("\n[dim]Naciśnij Enter, aby kontynuować...[/dim]")
        elif "[Wdróż]" in choice:
            deploy_to_pi()
            console.input("\n[dim]Naciśnij Enter, aby kontynuować...[/dim]")
        elif "[Narzędzia]" in choice:
            console.print("\n[info]Uruchamianie testów (pytest)...[/info]\n")
            subprocess.run(["pytest"])
            console.input("\n[dim]Naciśnij Enter, aby kontynuować...[/dim]")

if __name__ == "__main__":
    main()
