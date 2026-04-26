from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import pymysql
import streamlit as st

from config import ALT_PLAYER_HEAD, BASE_DIR, DB_CONFIG, PLAYER_SKINS_DIR


FAVICON_URL = "https://raw.githubusercontent.com/aggthelegoman/minecraft_stats_webui/f6d5717cd40d338c151f178fb2c244cc1ae9d978/favicon.svg"
ADMIN_USERNAME = "minecraft_stats_webui_admin"
ADMIN_PASSWORD = "insecure_password_please_change_me"


st.set_page_config(page_title="Gardnercraft Server Stats", layout="wide", page_icon=FAVICON_URL)
if "auth" not in st.session_state:
    st.session_state["auth"] = False


def local_css(file_name: str | Path) -> None:
    css_path = Path(file_name)
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


local_css(BASE_DIR / "assets" / "styles.css")


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def get_player_names() -> list[str]:
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT p.name FROM players p ORDER BY p.name")
            return [row["name"] for row in cursor.fetchall()]
    finally:
        connection.close()


try:
    player_names = get_player_names()
    database_ready = True
    database_error = ""
except pymysql.Error as exc:
    player_names = []
    database_ready = False
    database_error = str(exc)


def ensure_database_ready() -> bool:
    if database_ready:
        return True
    st.error(f"Database connection failed: {database_error}")
    return False


def run_query(sql: str):
    try:
        connection = get_connection()
        with connection.cursor() as cursor:
            if not sql.strip():
                raise ValueError("Query cannot be blank.")
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.Error as exc:
        print(f"[ERROR] Database error: {exc}")
        return None
    except Exception as exc:
        print(f"[ERROR] Unexpected error executing query: {exc}")
        return None
    finally:
        if "connection" in locals() and connection.open:
            connection.close()


def make_head_image(username: str) -> str:
    skin_file_path = PLAYER_SKINS_DIR / f"{username}_head.png"

    if skin_file_path.exists():
        try:
            with skin_file_path.open("rb") as image_file:
                img_data = image_file.read()
            b64_encoded = base64.b64encode(img_data).decode("utf-8")
            return f"data:image/png;base64,{b64_encoded}"
        except Exception as exc:
            print(f"[WARN] Could not read skin file {skin_file_path}: {exc}")

    if ALT_PLAYER_HEAD.exists():
        try:
            with ALT_PLAYER_HEAD.open("rb") as image_file:
                img_data = image_file.read()
            b64_encoded = base64.b64encode(img_data).decode("utf-8")
            return f"data:image/png;base64,{b64_encoded}"
        except Exception as exc:
            print(f"[WARN] Could not read fallback skin {ALT_PLAYER_HEAD}: {exc}")

    return FAVICON_URL


def display_leaderboard(query: str) -> None:
    if not query.strip():
        st.info("Please enter a valid SQL query.")
        return

    results = run_query(query)
    if results is None:
        st.error("Failed to execute query. Check your connection or syntax.")
        return

    st.markdown("### Query Results")

    if len(results) == 0:
        st.info("No results returned from the database.")
        return

    if not ALT_PLAYER_HEAD.exists():
        st.warning(f"Missing fallback placeholder: {ALT_PLAYER_HEAD}")

    df = pd.DataFrame(results)

    if len(df.columns) > 0:
        head_icons = df.iloc[:, 0].apply(make_head_image).tolist()
    else:
        head_icons = [None] * len(results)

    df.insert(0, "head_icon", head_icons)

    st.data_editor(
        df,
        column_config={
            "head_icon": st.column_config.ImageColumn(
                label="Player Head",
                width="small",
                help="Player skin head icon with fallback to alt_playerhead.png",
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

    st.markdown(f"**Rows Returned:** {len(results)}")


def intro() -> None:
    st.write("# Welcome to Minecraft Statistics Web UI")
    st.sidebar.success("Select a page from the sidebar.")
    st.markdown('<div class="hero-panel">', unsafe_allow_html=True)
    st.markdown(
        """
        Browse server leaderboards, inspect player statistics, and run custom SQL queries
        against a Minecraft statistics database.
        """
    )
    st.markdown("</div>", unsafe_allow_html=True)
    if not ensure_database_ready():
        st.info("Set the MariaDB environment variables before using the app.")


def leaderboard() -> None:
    if not ensure_database_ready():
        return

    def causes_of_death():
        return "SELECT stat_key, SUM(stat_value) AS total_kills FROM player_stats_killed_by GROUP BY stat_key ORDER BY total_kills DESC"

    def player_play_time():
        return "SELECT p.name, c.stat_value / 72000 AS hours_played FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key = 'minecraft:play_time' ORDER BY hours_played DESC;"

    def statistics_for_a_player():
        player_name = st.selectbox("Players", options=player_names, key="player_filter")
        st.write("This leaderboard shows detailed stats for a single player, similar to the in-game statistics view.")
        return f"SELECT p.name, m.stat_key, m.stat_value FROM players p JOIN player_stats_mined m ON p.uuid = m.uuid WHERE p.name = '{player_name}' ORDER BY m.stat_value DESC;"

    def distance_traveled_by():
        distance_scales = {
            "Kilometers (1000 Blocks)": 100000,
            "Miles": 160934.4,
            "Chunks": 160,
            "Meters (Blocks)": 100,
        }
        scale = st.selectbox("Units", distance_scales.keys(), key="distance_units")
        if st.checkbox("totals", key="distance_totals_toggle"):
            distance_stats_totals = {
                "Total of all distances": [
                    f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:aviate_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:minecart_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_under_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_on_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:swim_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:boat_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:strider_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:sprint_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:fall_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:fly_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:crouch_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:climb_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:horse_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:pig_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:happy_ghast_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:nautilus_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_one_cm', 'aviate_one_cm', 'minecart_one_cm', 'walk_under_water_one_cm', 'walk_on_water_one_cm', 'swim_one_cm', 'boat_one_cm', 'strider_one_cm', 'sprint_one_cm', 'fall_one_cm', 'fly_one_cm', 'crouch_one_cm', 'climb_one_cm', 'horse_one_cm', 'pig_one_cm', 'happy_ghast_one_cm', 'nautilus_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;",
                    "Sum of all tracked travel methods.",
                ],
                "Total on Foot": [
                    f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:sprint_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:crouch_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_one_cm', 'sprint_one_cm', 'crouch_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;",
                    "Total distance walking, sprinting, and crouching.",
                ],
                "Total Distance in Water": [
                    f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_under_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_on_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:swim_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_under_water_one_cm', 'walk_on_water_one_cm', 'swim_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;",
                    "Total distance traveled in water, excluding boats and nautilus.",
                ],
                "Total Distance Ridden on Mobs": [
                    f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:strider_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:horse_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:pig_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:happy_ghast_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:nautilus_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:strider_one_cm', 'horse_one_cm', 'pig_one_cm', 'happy_ghast_one_cm', 'nautilus_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;",
                    "Total distance from rideable mobs.",
                ],
                "Total Distance in Vehicles": [
                    f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:minecart_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:boat_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:minecart_one_cm', 'boat_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;",
                    "Total distance traveled by boat and minecart.",
                ],
            }
            total_distance_key = st.selectbox("Total Distances", distance_stats_totals.keys(), key="distance_totals_select")
            st.write(f"Explanation: {distance_stats_totals[total_distance_key][1]}")
            return distance_stats_totals[total_distance_key][0]

        distance_stats = {
            "Distance By Elytra": ["minecraft:aviate_one_cm", "The total distance traveled by elytra."],
            "Distance by Minecart": ["minecraft:minecart_one_cm", "The total distance traveled by minecart."],
            "Distance Walked": ["minecraft:walk_one_cm", "The total distance walked."],
            "Distance Walked Under Water": ["minecraft:walk_under_water_one_cm", "The total distance covered while the player's head is underwater."],
            "Distance Walked on Water": ["minecraft:walk_on_water_one_cm", "The total distance covered while the player's head is not underwater."],
            "Distance Swam": ["minecraft:swim_one_cm", "The total distance covered with sprint-swimming."],
            "Distance Traveled by Boat": ["minecraft:boat_one_cm", "The total distance traveled by boat."],
            "Distance Traveled on Strider": ["minecraft:strider_one_cm", "The total distance traveled on strider."],
            "Distance Sprinted": ["minecraft:sprint_one_cm", "The total distance sprinted."],
            "Distance Fallen": ["minecraft:fall_one_cm", "The total distance fallen, excluding jumping."],
            "Distance Flown": ["minecraft:fly_one_cm", "Distance traveled upward and forward while airborne."],
            "Distance Walked while Crouching": ["minecraft:crouch_one_cm", "The total distance traveled while sneaking."],
            "Distance Climbed": ["minecraft:climb_one_cm", "The total distance traveled up ladders or vines."],
            "Distance Traveled on Horse": ["minecraft:horse_one_cm", "The total distance traveled on horse and similar mobs."],
            "Distance by Pig": ["minecraft:pig_one_cm", "The total distance traveled on pig."],
            "Distance by Happy Ghast": ["minecraft:happy_ghast_one_cm", "The total distance traveled by Happy Ghast."],
            "Distance by Nautilus": ["minecraft:nautilus_one_cm", "The total distance traveled by nautilus."],
        }
        distance_key = st.selectbox("Distance traveled by", distance_stats.keys(), key="distance_metric")
        st.write(f"Explanation: {distance_stats[distance_key][1]}")
        return f"SELECT p.name, c.stat_value / {distance_scales[scale]} AS distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key = '{distance_stats[distance_key][0]}' ORDER BY distance_traveled DESC;"

    def kdr():
        return "SELECT p.name, ROUND(CAST(c.stat_value AS FLOAT) / NULLIF(d.stat_value, 0), 2) AS KD_Ratio, c.stat_value AS Player_Kills, d.stat_value AS Player_Deaths FROM players p JOIN player_stats_killed c ON p.uuid = c.uuid JOIN player_stats_killed_by d ON p.uuid = d.uuid WHERE c.stat_key = 'minecraft:player' AND d.stat_key = 'minecraft:player' ORDER BY KD_Ratio DESC;"

    leaderboards = {
        "Player causes of death from mobs": causes_of_death,
        "Player Play Time": player_play_time,
        "Statistics for a player": statistics_for_a_player,
        "Distances by player": distance_traveled_by,
        "Kill Death Ratio": kdr,
    }
    st.markdown("# Leaderboards")
    query = st.selectbox("Choose a leaderboard", leaderboards.keys(), key="leaderboard_select")
    if st.session_state["auth"]:
        st.code(leaderboards[query](), language="sql")
        display_leaderboard(leaderboards[query]())
    else:
        display_leaderboard(leaderboards[query]())


def custom_sql_queries() -> None:
    st.markdown("# Custom SQL Queries")
    if not ensure_database_ready():
        return
    if st.session_state["auth"]:
        default_query = """SELECT stat_key, SUM(stat_value) AS total_kills
FROM player_stats_killed_by
GROUP BY stat_key
ORDER BY total_kills DESC;"""
        query = st.text_area("Type your SQL query here", value=default_query, height=200, key="custom_sql_input")
        display_leaderboard(query)
    else:
        st.write("Please authenticate to run custom SQL queries. Built-in leaderboards are still available.")


def authentication() -> None:
    st.markdown("# Authentication")
    st.write("Authenticate to use custom SQL queries and view raw query text for the built-in leaderboards.")
    username = st.text_input("Username", key="auth_username")
    password = st.text_input("Password", type="password", key="auth_password")
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        st.session_state["auth"] = True

    st.write(f"Authenticated: {st.session_state['auth']}")


page_names_to_funcs = {
    "Home": intro,
    "Leaderboards": leaderboard,
    "Custom SQL Queries": custom_sql_queries,
    "Authentication": authentication,
}

page_name = st.sidebar.selectbox("Choose a page", page_names_to_funcs.keys(), key="page_nav")
page_names_to_funcs[page_name]()
