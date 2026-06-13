import os
import sqlite3

DB_PATH = "data/bot.db"

class Database:
    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self._conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS bindings (
                discord_id TEXT PRIMARY KEY,
                riot_name  TEXT NOT NULL,
                riot_tag   TEXT NOT NULL
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS riot_auth (
                discord_id    TEXT PRIMARY KEY,
                cookies_enc   TEXT NOT NULL,
                region        TEXT NOT NULL,
                created_at    INTEGER NOT NULL
            )
        """)
        self._conn.commit()

    def get_binding(self, discord_id: int):
        row = self._conn.execute(
            "SELECT riot_name, riot_tag FROM bindings WHERE discord_id = ?",
            (str(discord_id),)
        ).fetchone()
        if row:
            return row["riot_name"], row["riot_tag"]
        return None

    def set_binding(self, discord_id: int, riot_name: str, riot_tag: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO bindings (discord_id, riot_name, riot_tag) VALUES (?, ?, ?)",
            (str(discord_id), riot_name, riot_tag)
        )
        self._conn.commit()

    def delete_binding(self, discord_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM bindings WHERE discord_id = ?",
            (str(discord_id),)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def get_auth(self, discord_id: int):
        row = self._conn.execute(
            "SELECT cookies_enc, region, created_at FROM riot_auth WHERE discord_id = ?",
            (str(discord_id),)
        ).fetchone()
        if row:
            return row["cookies_enc"], row["region"], row["created_at"]
        return None

    def set_auth(self, discord_id: int, cookies_enc: str, region: str, created_at: int):
        self._conn.execute(
            "INSERT OR REPLACE INTO riot_auth (discord_id, cookies_enc, region, created_at) VALUES (?, ?, ?, ?)",
            (str(discord_id), cookies_enc, region, created_at)
        )
        self._conn.commit()

    def delete_auth(self, discord_id: int) -> bool:
        cur = self._conn.execute(
            "DELETE FROM riot_auth WHERE discord_id = ?",
            (str(discord_id),)
        )
        self._conn.commit()
        return cur.rowcount > 0

    def close(self):
        self._conn.close()
