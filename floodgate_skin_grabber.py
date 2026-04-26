from __future__ import annotations

import sys

import requests

from config import PLAYER_SKINS_DIR


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit("Usage: floodgate_skin_grabber.py <gamertag-without-leading-dot>")

    username = sys.argv[1]
    url = f"https://mcprofile.io/api/v1/bedrock/gamertag/{username}"

    response = requests.get(url, timeout=20)
    if response.status_code != 200:
        raise SystemExit(f"Did not receive HTTP 200 from {url}")

    data = response.json()
    image = requests.get(data["skin"], timeout=20).content
    output_path = PLAYER_SKINS_DIR / f".{username}.png"
    output_path.write_bytes(image)


if __name__ == "__main__":
    main()
