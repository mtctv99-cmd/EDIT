from PyQt5.QtCore import QSettings

APP_ORG = "MyCompany"
APP_NAME = "StoryEditor"

class Settings:
    @staticmethod
    def _s():
        return QSettings(APP_ORG, APP_NAME)

    @staticmethod
    def get_recent():
        s = Settings._s()
        return s.value("recent_files", []) or []

    @staticmethod
    def add_recent(path):
        s = Settings._s()
        recent = s.value("recent_files", []) or []
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        s.setValue("recent_files", recent[:10])

    @staticmethod
    def save_api_config(cfg: dict):
        s = Settings._s()
        s.setValue("api_config", cfg)

    @staticmethod
    def load_api_config() -> dict:
        s = Settings._s()
        return s.value("api_config", {}) or {}

    @staticmethod
    def save_prompts(prompts: list):
        s = Settings._s()
        s.setValue("prompts", prompts)

    @staticmethod
    def load_prompts() -> list:
        s = Settings._s()
        return s.value("prompts", []) or []

    @staticmethod
    def get_last_dir(key: str) -> str:
        s = Settings._s()
        return s.value(f"last_dir/{key}", "")

    @staticmethod
    def set_last_dir(key: str, path: str):
        s = Settings._s()
        s.setValue(f"last_dir/{key}", path)

    @staticmethod
    def clear_recent():
        s = Settings._s()
        s.setValue("recent_files", [])

    @staticmethod
    def remove_recent(path):
        s = Settings._s()
        recent = s.value("recent_files", []) or []
        if path in recent:
            recent.remove(path)
            s.setValue("recent_files", recent)
