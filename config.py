import os
from pathlib import Path

import pymysql.cursors


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
PLAYER_SKINS_DIR = BASE_DIR / "player_skins"
ALT_PLAYER_HEAD = PLAYER_SKINS_DIR / "alt_playerhead.png"


DB_CONFIG = {
    "host": os.getenv("MARIADB_HOST", "127.0.0.1"),
    "port": int(os.getenv("MARIADB_PORT", "3306")),
    "user": os.getenv("MARIADB_USER", "root"),
    "password": os.getenv("MARIADB_PASSWORD", "your_password_here"),
    "database": os.getenv("MARIADB_DATABASE", "minecraft_stats"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}
