import sys
import os
import json
import subprocess
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw

worker_process = None
satellite_process = None

def get_settings():
    settings_path = os.path.join("data", "settings.json")
    if os.path.exists(settings_path):
        with open(settings_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def create_default_icon():
    # Tworzenie prostej kwadratowej ikony 64x64
    image = Image.new('RGB', (64, 64), color=(40, 40, 40))
    dc = ImageDraw.Draw(image)
    dc.rectangle((16, 16, 48, 48), fill=(0, 120, 215))
    return image

def get_executable_command(sub_mode):
    # Jeśli program to .exe wygenerowany przez PyInstaller
    if getattr(sys, 'frozen', False):
        return [sys.executable, sub_mode]
    else:
        # Jesli odpalane ze skryptu main.py
        return [sys.executable, "-m", "regis_node.main", sub_mode]

def start_worker():
    global worker_process
    if worker_process is None or worker_process.poll() is not None:
        cmd = get_executable_command("--worker")
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        worker_process = subprocess.Popen(cmd, **kwargs)

def stop_worker():
    global worker_process
    if worker_process is not None:
        worker_process.terminate()
        worker_process.wait()
        worker_process = None

def start_satellite():
    global satellite_process
    if satellite_process is None or satellite_process.poll() is not None:
        cmd = get_executable_command("--satellite")
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW
        # Uzywamy stdin=PIPE po to zeby w razie czego satellite.py zablokowalo sie na input(), a nie sypnelo EOFError 
        satellite_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, **kwargs)

def stop_satellite():
    global satellite_process
    if satellite_process is not None:
        satellite_process.terminate()
        satellite_process.wait()
        satellite_process = None

def toggle_worker(icon, item):
    if is_worker_running():
        stop_worker()
    else:
        start_worker()

def toggle_satellite(icon, item):
    if is_satellite_running():
        stop_satellite()
    else:
        start_satellite()

def is_worker_running():
    return worker_process is not None and worker_process.poll() is None

def is_satellite_running():
    return satellite_process is not None and satellite_process.poll() is None

def run_wizard_from_tray(icon, item):
    cmd = get_executable_command("--wizard")
    # Z oknem konsoli
    subprocess.Popen(cmd)

# Autostart Windows
import winreg

AUTOSTART_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "RegisNode"

def is_autostart_enabled():
    if sys.platform != "win32":
        return False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False

def toggle_autostart(icon, item):
    if sys.platform != "win32":
        return
    enabled = is_autostart_enabled()
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY, 0, winreg.KEY_SET_VALUE)
        if enabled:
            winreg.DeleteValue(key, APP_NAME)
        else:
            # Wskazuje na obecny plik (exe jezeli pyinstaller, albo script)
            path = sys.executable
            if getattr(sys, 'frozen', False):
                # wrap in quotes if spaces
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{path}"')
            else:
                main_py = os.path.abspath(sys.argv[0])
                winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{path}" "{main_py}"')
        winreg.CloseKey(key)
    except Exception as e:
        print(f"Błąd zmiany autostartu: {e}")

def quit_panel(icon, item):
    icon.stop()

def quit_all(icon, item):
    stop_worker()
    stop_satellite()
    icon.stop()

def get_menu():
    settings = get_settings()
    name = settings.get("instance_name", "Regis Node")
    return pystray.Menu(
        item(lambda text: f"Regis Node — {name}", lambda: None, enabled=False),
        pystray.Menu.SEPARATOR,
        item(lambda text: "Worker LLM: " + ("Uruchomiony" if is_worker_running() else "Zatrzymany"), toggle_worker, checked=lambda item: is_worker_running()),
        item(lambda text: "Satellite: " + ("Uruchomiony" if is_satellite_running() else "Zatrzymany"), toggle_satellite, checked=lambda item: is_satellite_running()),
        pystray.Menu.SEPARATOR,
        item("Autostart przy logowaniu", toggle_autostart, checked=lambda item: is_autostart_enabled()),
        item("Konfiguracja...", run_wizard_from_tray),
        pystray.Menu.SEPARATOR,
        item("Zamknij panel (procesy działają)", quit_panel),
        item("Zamknij wszystko", quit_all),
    )

def run_tray():
    settings = get_settings()
    if settings.get("autostart_worker"):
        start_worker()
    if settings.get("autostart_satellite"):
        start_satellite()

    icon = pystray.Icon("regis_node", create_default_icon(), "Regis Node", menu=get_menu())
    icon.run()

if __name__ == "__main__":
    run_tray()
