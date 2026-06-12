import os
import json

DEFAULT_REGION = "ap"
SETTINGS_PATH = "data/guild_settings.json"

class GuildSettings:
    def __init__(self):
        self._data: dict = {}
        os.makedirs("data", exist_ok=True)
        self._load()

    def _load(self):
        if os.path.exists(SETTINGS_PATH):
            try:
                with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                    self._data = json.load(f)
            except Exception:
                self._data = {}

    def _save(self):
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def get_region(self, guild_id) -> str:
        if guild_id is None:
            return DEFAULT_REGION
        return self._data.get(str(guild_id), {}).get("region", DEFAULT_REGION)

    def set_region(self, guild_id, region: str):
        self._data.setdefault(str(guild_id), {})["region"] = region
        self._save()
