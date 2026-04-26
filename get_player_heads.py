from __future__ import annotations

import subprocess
import sys

import pymysql
from PIL import Image

from config import DB_CONFIG, PLAYER_SKINS_DIR


def get_player_names() -> list[str]:
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT p.name FROM players p ORDER BY p.name")
            return [row["name"] for row in cursor.fetchall()]
    finally:
        connection.close()


def crop_head(source_path, output_path) -> None:
    with Image.open(source_path) as image:
        head = image.crop((8, 8, 16, 16))
        head.save(output_path, "PNG")


def main() -> None:
    failed_player_skin_grab = []

    for player in get_player_names():
        is_floodgate_player = "." in player
        visible_name = player.replace(".", "")
        raw_skin_name = f".{visible_name}.png" if is_floodgate_player else f"{visible_name}.png"
        head_skin_name = f".{visible_name}_head.png" if is_floodgate_player else f"{visible_name}_head.png"
        raw_skin_path = PLAYER_SKINS_DIR / raw_skin_name
        head_skin_path = PLAYER_SKINS_DIR / head_skin_name

        if head_skin_path.exists():
            continue

        try:
            if not raw_skin_path.exists():
                script_name = "floodgate_skin_grabber.py" if is_floodgate_player else "skin_grabber.py"
                subprocess.run([sys.executable, script_name, visible_name], check=True)
            crop_head(raw_skin_path, head_skin_path)
        except Exception:
            player_type = "bedrock/floodgate" if is_floodgate_player else "java"
            failed_player_skin_grab.append(f"failed to download skin for {player_type} player {player}")

    for line in failed_player_skin_grab:
        print(line)


if __name__ == "__main__":
    main()
