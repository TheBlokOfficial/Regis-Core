import os
import shutil
import subprocess
from regis_cli.ux import console

def build_portable_windows():
    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[header]      Kompilacja aplikacji brzegowych (Windows)[/header]")
    console.print(f"[header]                [Portable App Mode][/header]")
    console.print(f"[header]========================================================[/header]\n")

    modules = [
        {"name": "regis-satellite", "folder": "Regis-Satellite", "script": "src/regis_satellite/main.py", "title": "Regis Satellite", "profile": "satellite"},
        {"name": "regis-worker", "folder": "Regis-Worker", "script": "src/regis_worker/node.py", "title": "Regis Worker", "profile": "worker"},
        {"name": "regis-terminal", "folder": "Regis-Terminal", "script": "src/regis_terminal/main.py", "title": "Regis Terminal", "profile": "terminal"},
    ]

    for i, mod in enumerate(modules, 1):
        console.print(f"[info][{i}/3] Budowanie {mod['name']}...[/info]")
        
        cmd = [
            "pyinstaller", "--paths", "src", "--name", mod["name"],
            "--onedir", "--clean", mod["script"]
        ]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode != 0:
            console.print(f"[error]Błąd kompilacji {mod['name']}![/error]")
            continue

        dist_app = os.path.join("dist", mod["folder"])
        data_dir = os.path.join(dist_app, "data")
        system_dir = os.path.join(dist_app, "system")
        
        os.makedirs(data_dir, exist_ok=True)
        
        src_system = os.path.join("dist", mod["name"])
        if os.path.exists(system_dir):
            shutil.rmtree(system_dir)
        if os.path.exists(src_system):
            shutil.move(src_system, system_dir)

        bat_content = f"""@echo off
title {mod['title']}
cd /d "%~dp0"
system\\{mod['name']}.exe
if %errorlevel% neq 0 pause
"""
        with open(os.path.join(dist_app, "Uruchom.bat"), "w", encoding="utf-8") as f:
            f.write(bat_content)

        with open(os.path.join(dist_app, ".env"), "w", encoding="utf-8") as f:
            f.write(f"ACTIVE_PROFILE={mod['profile']}\n")

        settings_file = os.path.join(data_dir, f"settings.{mod['profile']}.json")
        with open(settings_file, "w", encoding="utf-8") as f:
            if mod["profile"] == "worker":
                f.write('{\n    "controller_url": "auto",\n    "worker_port": 8001,\n    "worker_host": "0.0.0.0",\n    "active_tier": "regis"\n}\n')
            else:
                f.write('{\n    "controller_url": "auto",\n    "server_url": "auto"\n}\n')

    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[success]SUKCES! Gotowe pakiety (Portable App) znajduja sie w 'dist\\'.[/success]")
    console.print(f"[info]Kazda z nich posiada juz swoj katalog 'data/' oraz[/info]")
    console.print(f"[info]ukryte biblioteki w folderze 'system/'.[/info]")
    console.print(f"[info]Uruchamiaj je klikajac 'Uruchom.bat'.[/info]")
    console.print(f"[header]========================================================[/header]\n")

def build_wheel():
    console.print(f"[info]Rozpoczynam budowanie paczki .whl (Linux/Raspberry)...[/info]")
    cmd = ["python", "-m", "build", "--wheel"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode == 0:
        console.print("[success]Paczka .whl wygenerowana pomyślnie![/success]")
        return True
    else:
        console.print(f"[error]Błąd podczas budowania paczki .whl:[/error]")
        console.print(result.stdout.decode('utf-8'))
        return False
