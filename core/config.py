import os
import json
from typing import Any

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
ALIASES_FILE = os.path.join(DATA_DIR, "aliases.json")

def load_settings() -> dict[str, Any]:
    """Ładuje główne ustawienia programu z fallbackiem na wartości domyślne.
    
    Returns:
        dict[str, Any]: Słownik z konfiguracją systemu.
    """
    default_settings = {
        "active_tier": "butler", 
        "history_limit": 10,
        "ha_url": "http://192.168.0.50:8123",
        "ha_token": "TWÓJ_TOKEN_TUTAJ"
    }
    if not os.path.exists(SETTINGS_FILE):
        return default_settings
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        try:
            settings = json.load(f)
            return {**default_settings, **settings}
        except json.JSONDecodeError:
            return default_settings

def save_settings(settings: dict[str, Any]) -> None:
    """Zapisuje ustawienia do pliku konfiguracyjnego.
    
    Args:
        settings (dict[str, Any]): Aktualny stan konfiguracji do zapisu.
    """
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)

def load_aliases() -> dict[str, str]:
    """Ładuje zdefiniowane w pliku aliasy nazw urządzeń HA.
    
    Returns:
        dict[str, str]: Słownik mapujący np. "light.xyz" -> "Lampa".
    """
    if not os.path.exists(ALIASES_FILE):
        return {}
    with open(ALIASES_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

