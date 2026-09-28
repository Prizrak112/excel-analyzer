"""
Защита приложения: пароль, хеширование, привязка к машине.
"""

import os
import json
import hashlib
import subprocess
import platform
from pathlib import Path
from datetime import datetime


# ============================================================
# Пути
# ============================================================

CONFIG_DIR = Path.home() / ".excel-analyzer"
CONFIG_DIR.mkdir(exist_ok=True)
SECURITY_FILE = CONFIG_DIR / "security.json"
LICENSE_FILE = CONFIG_DIR / "license.json"


# ============================================================
# Хеширование пароля
# ============================================================

SALT = "ea_2026_v1_x9k2m"


def hash_password(password: str, salt: str = SALT) -> str:
    """SHA-256 хеш пароля с солью."""
    data = (salt + password).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def verify_password(password: str, stored_hash: str) -> bool:
    """Проверить пароль против сохранённого хеша."""
    return hash_password(password) == stored_hash


# ============================================================
# Стабильный machine_id — источники
# ============================================================

def _get_machine_guid() -> str | None:
    """
    Основной источник: MachineGuid из реестра Windows.
    HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
    Генерируется один раз при установке Windows, не меняется
    при смене сети, переименовании ПК, обновлениях.
    """
    if platform.system() != "Windows":
        return None
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        )
        value, _ = winreg.QueryValueEx(key, "MachineGuid")
        winreg.CloseKey(key)
        return str(value).strip() if value else None
    except Exception:
        return None


def _get_volume_serial() -> str | None:
    """
    Резерв: серийный номер тома C:.
    Стабилен до переустановки Windows / форматирования диска.
    """
    if platform.system() != "Windows":
        return None
    try:
        result = subprocess.run(
            ["cmd", "/c", "vol", "C:"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        # vol C: выводит строку вида: "Серийный номер тома: XXXX-XXXX"
        for line in result.stdout.splitlines():
            parts = line.split()
            for p in parts:
                if len(p) == 9 and p[4] == "-":
                    return p.strip()
    except Exception:
        pass
    return None


def _get_cpu_id() -> str | None:
    """
    Резерв: ProcessorId процессора.
    Меняется только при замене CPU.
    """
    if platform.system() != "Windows":
        return None
    try:
        result = subprocess.run(
            ["wmic", "cpu", "get", "ProcessorId"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        lines = [l.strip() for l in result.stdout.splitlines() if l.strip()]
        if len(lines) >= 2:
            return lines[1]
    except Exception:
        pass
    return None


# ============================================================
# Хранилище безопасности
# ============================================================

class SecurityStore:
    """Хранилище пароля и настроек безопасности."""

    def __init__(self):
        self._data = self._load()

    def _load(self) -> dict:
        if SECURITY_FILE.exists():
            try:
                with open(SECURITY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        with open(SECURITY_FILE, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    # ---------- Пароль ----------

    def has_password(self) -> bool:
        """Установлен ли пароль?"""
        return "password_hash" in self._data

    def set_password(self, password: str):
        """Установить пароль (сохраняется только хеш)."""
        self._data["password_hash"] = hash_password(password)
        self._data["password_set_at"] = datetime.now().isoformat()
        self._save()

    def check_password(self, password: str) -> bool:
        """Проверить пароль."""
        stored = self._data.get("password_hash")
        if not stored:
            return False
        return verify_password(password, stored)

    def reset_password(self):
        """Удалить пароль (для отладки)."""
        self._data.pop("password_hash", None)
        self._save()

    # ---------- Привязка к ПК ----------

    def get_machine_id(self) -> str:
        """
        Стабильный уникальный ID машины (16 символов).

        Приоритет источников:
          1. MachineGuid (реестр Windows) — самый стабильный
          2. Серийный номер тома C:
          3. ProcessorId CPU
          4. Fallback: hostname + platform (крайний случай)

        ВАЖНО: MAC-адрес (uuid.getnode) НЕ используется —
        он меняется при смене Wi-Fi/Ethernet/VPN.
        """
        sources = []

        guid = _get_machine_guid()
        if guid:
            sources.append(f"guid:{guid}")

        serial = _get_volume_serial()
        if serial:
            sources.append(f"vol:{serial}")

        cpu = _get_cpu_id()
        if cpu:
            sources.append(f"cpu:{cpu}")

        # Fallback — только если ни один источник не сработал
        if not sources:
            sources.append(f"node:{platform.node()}")
            sources.append(f"plat:{platform.platform()}")

        raw = "|".join(sources).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()[:16]

    def has_license(self) -> bool:
        """Есть ли файл лицензии?"""
        return LICENSE_FILE.exists()

    def create_license(self):
        """Создать лицензию для текущей машины."""
        license_data = {
            "machine_id": self.get_machine_id(),
            "created_at": datetime.now().isoformat(),
            "hostname": platform.node(),
            "os": platform.system() + " " + platform.release(),
        }
        with open(LICENSE_FILE, "w", encoding="utf-8") as f:
            json.dump(license_data, f, indent=2)

    def verify_license(self) -> bool:
        """Проверить, что лицензия подходит этой машине."""
        if not LICENSE_FILE.exists():
            return False

        try:
            with open(LICENSE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("machine_id") == self.get_machine_id()
        except Exception:
            return False

    def delete_license(self):
        """Удалить лицензию."""
        if LICENSE_FILE.exists():
            LICENSE_FILE.unlink()

    # ---------- Логи попыток ----------

    def log_failed_attempt(self):
        """Записать неудачную попытку входа."""
        attempts = self._data.get("failed_attempts", [])
        attempts.append({
            "time": datetime.now().isoformat(),
            "machine_id": self.get_machine_id(),
        })
        self._data["failed_attempts"] = attempts[-100:]
        self._save()

    def get_failed_attempts(self) -> list:
        """Получить список неудачных попыток."""
        return self._data.get("failed_attempts", [])

    def clear_failed_attempts(self):
        """Очистить логи попыток."""
        self._data["failed_attempts"] = []
        self._save()


# ============================================================
# Глобальный экземпляр
# ============================================================

_security = None


def get_security() -> SecurityStore:
    """Получить глобальный экземпляр SecurityStore."""
    global _security
    if _security is None:
        _security = SecurityStore()
    return _security