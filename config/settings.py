"""
Глобальные настройки приложения.
Хранятся в ~/.excel-analyzer/settings.json
"""

import json
from pathlib import Path


SETTINGS_DIR = Path.home() / ".excel-analyzer"
SETTINGS_DIR.mkdir(exist_ok=True)
SETTINGS_FILE = SETTINGS_DIR / "settings.json"


class Settings:
    """Глобальные настройки приложения."""
    
    DEFAULTS = {
        "theme": "light",
        "language": "ru",
        "autosave": True,
        "autosave_interval": 300,
    }
    
    def __init__(self):
        self._data = self._load()
    
    def _load(self) -> dict:
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    result = dict(self.DEFAULTS)
                    result.update(data)
                    return result
            except Exception:
                return dict(self.DEFAULTS)
        return dict(self.DEFAULTS)
    
    def _save(self):
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[Settings] Ошибка сохранения: {e}")
    
    def get(self, key: str, default=None):
        return self._data.get(key, default)
    
    def set(self, key: str, value):
        self._data[key] = value
        self._save()
    
    # ---------- Тема ----------
    
    def get_theme_name(self) -> str:
        return self.get("theme", "light")
    
    def set_theme_name(self, name: str):
        self.set("theme", name)


_settings = None


def get_settings() -> Settings:
    """Глобальный экземпляр настроек."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings