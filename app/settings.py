"""Kullanıcı ayarları (JSON olarak %APPDATA%/ZOYMediaTool içinde saklanır)."""
import json
import os
import threading

from .paths import DATA_DIR, DEFAULT_OUTPUT_DIR

_FILE = os.path.join(DATA_DIR, "settings.json")
_lock = threading.Lock()

DEFAULTS = {
    "theme": "win2000",          # win2000 | xp-dark | xp-luna
    "output_dir": DEFAULT_OUTPUT_DIR,
    "open_folder_when_done": False,
    "username": os.environ.get("USERNAME", "Kullanıcı"),
}


def load() -> dict:
    data = dict(DEFAULTS)
    try:
        with open(_FILE, "r", encoding="utf-8") as f:
            data.update(json.load(f))
    except Exception:
        pass
    return data


def save(new_values: dict) -> dict:
    with _lock:
        data = load()
        data.update({k: v for k, v in new_values.items() if k in DEFAULTS})
        with open(_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
