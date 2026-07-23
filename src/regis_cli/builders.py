import os
import shutil
import subprocess
from regis_cli.ux import console

def build_portable_windows():
    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[header]      Kompilacja aplikacji brzegowych (Windows)[/header]")
    console.print(f"[header]                [Portable App Mode][/header]")
    console.print(f"[header]========================================================[/header]\n")

    console.print(f"[info]Budowanie regis-node...[/info]")
    
    import sys
    cmd = [
        sys.executable, "-m", "PyInstaller", "--paths", "src", "--name", "regis-node",
        "--distpath", "build_dist", "--onedir", "--clean", "src/regis_node/main.py"
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if result.returncode != 0:
        console.print(f"[error]Błąd kompilacji regis-node![/error]")
        return

    dist_app = os.path.join("dist", "Regis-Node")
    data_dir = os.path.join(dist_app, "data")
    system_dir = os.path.join(dist_app, "system")
    
    os.makedirs(data_dir, exist_ok=True)
    
    src_system = os.path.join("build_dist", "regis-node")
    if os.path.exists(system_dir):
        shutil.rmtree(system_dir)
    if os.path.exists(src_system):
        shutil.move(src_system, system_dir)

    bat_content = """@echo off
title Regis Node
cd /d "%~dp0"
system\\regis-node.exe
"""
    with open(os.path.join(dist_app, "Uruchom.bat"), "w", encoding="utf-8") as f:
        f.write(bat_content)

    console.print(f"\n[header]========================================================[/header]")
    console.print(f"[success]SUKCES! Gotowy pakiet (Portable App) znajduje sie w 'dist\\Regis-Node\\'.[/success]")
    console.print(f"[info]Aplikacja posiada juz swoj katalog 'data/' oraz[/info]")
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
