import os
import glob
import subprocess
from regis_cli.ux import console
from regis_cli.builders import build_wheel

def deploy_to_pi():
    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[header]      Deployment na serwer główny (Raspberry Pi)[/header]")
    console.print(f"[header]========================================================[/header]\n")

    if not build_wheel():
        return

    # Znajdź plik .whl
    wheels = glob.glob("dist/*.whl")
    if not wheels:
        console.print("[error]Nie znaleziono pliku .whl w folderze dist/.[/error]")
        return
    
    wheel_path = wheels[0]
    wheel_name = os.path.basename(wheel_path)

    console.print(f"[info]Wysyłanie pliku {wheel_name} przez SCP na malinkę...[/info]")
    scp_cmd = ["scp", wheel_path, f"theblok@192.168.0.119:~/{wheel_name}"]
    result = subprocess.run(scp_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        console.print(f"[error]Błąd podczas wysyłania przez SCP:[/error]")
        console.print(result.stdout.decode('utf-8'))
        return
    console.print("[success]Plik przesłany pomyślnie.[/success]")

    console.print(f"[info]Instalacja paczki i restart usług na malince...[/info]")
    ssh_cmd = [
        "ssh", "theblok@192.168.0.119",
        f"cd ~/regis-core ; rm -rf regis_controller/ regis_worker/ regis_satellite/ regis_terminal/ core/ integrations/ ; source .venv/bin/activate ; pip install --force-reinstall ~/{wheel_name} ; rm ~/{wheel_name} ; sudo systemctl daemon-reload ; sudo systemctl restart regis.service regis-worker.service"
    ]
    result = subprocess.run(ssh_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        console.print(f"[error]Błąd podczas instalacji na malince:[/error]")
        console.print(result.stdout.decode('utf-8'))
        return

    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[success]SUKCES! Aplikacja zostala zainstalowana i zrestartowana.[/success]")
    console.print(f"[header]========================================================[/header]\n")
