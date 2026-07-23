import sys
import os

# Gwarancja dla PyInstaller, że uwzględni wszystkie podmoduły
import regis_node.node
import regis_node.satellite
import regis_node.wizard
import regis_node.tray

def main():
    # Obsługa trybów uruchomieniowych podprocesów (uruchamiane przez tray app)
    if "--worker" in sys.argv:
        from regis_node.node import start
        start()
        return
    if "--satellite" in sys.argv:
        from regis_node.satellite import main as sat_main
        sat_main()
        return
    if "--wizard" in sys.argv:
        from regis_node.wizard import run_wizard
        run_wizard()
        return

    # Uruchomienie domyślne - główny proces aplikacji Tray
    data_dir = "data"
    settings_path = os.path.join(data_dir, "settings.json")
    
    # Jeżeli nie ma ustawień, uruchamiamy wizard konfiguracyjny (czeka na skończenie)
    if not os.path.exists(settings_path):
        from regis_node.wizard import run_wizard
        run_wizard()
        
    # Jeżeli po wizardzie settings.json wciąż nie ma, znaczy że proces został przerwany
    if not os.path.exists(settings_path):
        print("Brak pliku settings.json. Zamykanie.")
        sys.exit(1)
        
    # Ukryj konsole Windows zanim pojawi sie ikona w pasku
    if sys.platform == "win32":
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
            
    # Uruchamiamy panel w Tray'u
    from regis_node.tray import run_tray
    run_tray()

if __name__ == "__main__":
    main()
