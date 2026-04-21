import pymysql
import os
import subprocess
from PIL import Image

#please put in the same database connection information from the minecraft_stats_web_ui.py file
DB_CONFIG = {
    'host': os.getenv('MARIADB_HOST', '<put your database ip here>'),
    'port': int(os.getenv('MARIADB_PORT', '<put your database port here, usually defaults to 3306>')),
    'user': os.getenv('MARIADB_USER', '<put your database user here, minecraft stats to mysql default to "minecraft_user">'),
    'password': os.getenv('MARIADB_PASSWORD', '<put your database password here>'),
    'database': os.getenv('MARIADB_DATABASE', '<put your database name here, minecraft stats to mysql defaults to "minecraft_stats">'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor,
    }

def get_player_names():
    """Fetch all player usernames from players table using MariaDB."""
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            query = "SELECT p.name FROM players p"
            cursor.execute(query)
            players = [row["name"] for row in cursor.fetchall()]
        return players
    finally:
        connection.close()

players = get_player_names()
failed_player_skin_grab = []

for player in players:
    if not "." in player:
        if not os.path.exists(f"player_skins/{player}.png"):
            try:
                subprocess.run(["python","skin_grabber.py",player],check=True)
                img = Image.open(f"player_skins/{player}.png")
                res = img.crop((8, 8, 16, 16))
                res.save(f"player_skins/{player}_head.png","PNG")
            except:
                failed_player_skin_grab.append(f"failed to download skin for java player {player}")
    else:
        if not os.path.exists(f"player_skins/.{player}.png"):
            player = player.replace(".","")
            try:
                subprocess.run(["python","floodgate_skin_grabber.py",player],check=True)
                img = Image.open(f"player_skins/.{player}.png")
                res = img.crop((8, 8, 16, 16))
                # res = img.resize((16,16), resample=Image.BOX) #for scaling but it aint workin
                res.save(f"player_skins/.{player}_head.png","PNG")
            except:
                failed_player_skin_grab.append(f"failed to download skin for bedrock/floodgate player .{player}")

if failed_player_skin_grab != []:
    for line in failed_player_skin_grab:
        print(line)