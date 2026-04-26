# Minecraft Stats Web UI

A Streamlit app for browsing Minecraft server statistics stored in MariaDB.

This project is designed to work with [Minecraft Statistics to MySQL by RooByteNet](https://github.com/RooByteNet/Minecraft-Statistics-to-MySQL/tree/149b969df57100705fc13f70757629136c926a30). Point that plugin at a MariaDB database, then use this app to browse built-in leaderboards, inspect player stats, and run custom SQL queries.

## Features

- Streamlit web UI for Minecraft statistics
- Built-in leaderboards for play time, distance traveled, K/D ratio, and more
- Optional custom SQL page for admin use
- Player head images with a fallback placeholder
- Helper scripts for downloading Java and Floodgate/Bedrock skins

## Project Structure

```text
minecraft_stats_webui.py   Main Streamlit app
config.py                  Shared database and path configuration
assets/styles.css          Custom Streamlit styling
get_player_heads.py        Bulk download and crop player heads
skin_grabber.py            Download Java player skins
floodgate_skin_grabber.py  Download Floodgate/Bedrock player skins
player_skins/              Runtime skin image folder
```

## Requirements

- Python 3.10+
- MariaDB database populated by the Minecraft statistics plugin

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and set your database values:

```env
MARIADB_HOST=localhost
MARIADB_USER=root
MARIADB_PASSWORD=your_password_here
MARIADB_DATABASE=minecraft_stats
MARIADB_PORT=3306
```

This project reads configuration from environment variables. If you use a local `.env` loader or deployment platform secrets, keep `.env` out of Git.

## Running the App

```bash
streamlit run minecraft_stats_webui.py
```

## Generating Player Heads

To download player skins and generate cropped head icons:

```bash
python get_player_heads.py
```

Generated skins are stored in `player_skins/` and are ignored by `.gitignore`. The committed `alt_playerhead.png` file is used as the fallback image when a player skin is missing.

## Notes

- The default admin credentials in `minecraft_stats_webui.py` should be changed before deploying publicly.
- The app expects the database schema created by the RooByteNet plugin.
- The helper scripts depend on external APIs for skin downloads.

## Demo

A live demo was previously hosted at [stats.gardnercraft.dedyn.io](https://stats.gardnercraft.dedyn.io).
