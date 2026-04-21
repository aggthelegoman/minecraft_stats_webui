import streamlit as st
import pymysql.cursors
import os

favicon = "https://raw.githubusercontent.com/aggthelegoman/minecraft_stats_webui/f6d5717cd40d338c151f178fb2c244cc1ae9d978/favicon.svg" #if you'd link to use a different favicon, put the link here. This is sometimes used for several placeholder icons in addition to the site favicon
st.set_page_config(page_title="Gardnercraft Server Stats", layout="wide", page_icon=favicon)
if "auth" not in st.session_state:
    st.session_state["auth"] = False

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

#gets list of all player usernames
player_names = get_player_names()

def display_leaderboard(query):
    import pandas as pd
    import base64

    def run_query(sql: str): #Execute raw SQL and return results as list of dicts.
        try:
            connection = pymysql.connect(**DB_CONFIG)
            with connection.cursor() as cursor:
                # Validate query is not empty
                if not sql.strip():
                    raise ValueError("Query cannot be blank.")
                # Execute the query (safe to run any valid SQL)
                cursor.execute(sql)
                # Get all results
                results = cursor.fetchall()
                return results
        except pymysql.Error as e:
            print(f"[ERROR] Database error: {e}")
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error executing query: {e}")
            return None
        finally:
            if 'connection' in locals() and connection.open:
                connection.close()

    if not query.strip():
        st.info("⚠️ Please enter a valid SQL query.")
        return

    # === Execute & Show Results ===
    results = run_query(query)
    if results is None:
        st.error("❌ Failed to execute query. Check your connection or syntax.")
        return

    # === Display Table with Player Head Icons (Safe, Local Only) ===
    st.markdown("### 📊 Query Results")

    # If empty result set
    if len(results) == 0:
        st.info("🔍 No results returned from the database.")
        return

    # Convert to DataFrame and ensure columns are strings so we can use them directly
    df = pd.DataFrame(results)

    # === Step: Build Image Column for Player Heads with Fallback ===
    SKIN_DIR = "player_skins"  # Root directory of player heads (must contain both <username>_head.png AND alt_playerhead.png)
    
    # Confirm fallback image exists in folder
    FALLBACK_FILE = os.path.join(SKIN_DIR, "alt_playerhead.png")
    if not os.path.exists(FALLBACK_FILE):
        st.warning(f"⚠️ Missing fallback placeholder: {FALLBACK_FILE}. Generated one automatically.")
        # Optionally generate one here? Not needed unless requested — just skip for now
        pass

    def make_head_image(username):
        """Generate a data URL from the local image <username>_head.png, or alt_playerhead.png if missing."""
        skin_file_path = os.path.join(SKIN_DIR, f"{username}_head.png")
        
        # Try main head first — if it exists
        if os.path.exists(skin_file_path):
            try:
                with open(skin_file_path, 'rb') as image_file:
                    img_data = image_file.read()
                b64_encoded = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{b64_encoded}"
            except Exception as e:
                print(f"[WARN] Could not read skin file {skin_file_path}: {e}")
        
        # Else fallback to alt_playerhead.png
        fallback_url = os.path.join(SKIN_DIR, "alt_playerhead.png")
        if os.path.exists(fallback_url):
            try:
                with open(fallback_url, 'rb') as image_file:
                    img_data = image_file.read()
                b64_encoded = base64.b64encode(img_data).decode('utf-8')
                return f"data:image/png;base64,{b64_encoded}"
            except Exception as e:
                print(f"[WARN] Could not read fallback skin {fallback_url}: {e}")
        
        # Final fallback: generic placeholder
        return favicon

    # Add new column to df with image URLs
    # df['head_icon'] = df.iloc[:, 0].apply(make_head_image) if len(df.columns) > 0 else [None] * len(results)

    # Assuming df already exists and has at least one column
    if len(df.columns) > 0:
        # Extract values from the original leftmost column (index 0)
        head_icons = df.iloc[:, 0].apply(make_head_image).tolist()
    else:
        head_icons = [None] * len(results)

    # Now insert 'head_icon' as the first column
    df.insert(0, 'head_icon', head_icons)



    # Now render using st.data_editor + ImageColumn (best for custom formatting)
    st.data_editor(
        df,
        column_config={
            "head_icon": st.column_config.ImageColumn(
                label="Player Head",
                width="small",  # Scales to ~75px — fits nicely beside names
                help="Icon of the player's skin head (fallback: alt_playerhead.png)"
            ),
        },
        hide_index=True,
        use_container_width=True,
    )

    # Footer info
    if len(results) > 0:
        st.markdown(f"📊 **Rows Returned:** {len(results)}")

# End of display leaderboard function

def intro():
    st.write("# Welcome to minecraft statistics webui! 👋")
    st.sidebar.success("Select an option above.")

    st.markdown(
        """
        Welcome to minecraft statistics webui. View personal player statistics, or view server leaderboards for player statistics.
    """
    )

def leaderboard():
    #code to generate leaderboards
    def causes_of_death():
        return("SELECT stat_key, SUM(stat_value) AS total_kills FROM player_stats_killed_by GROUP BY stat_key ORDER BY total_kills DESC")
    def player_play_time():
        return("SELECT p.name, c.stat_value / 72000 as hours_played FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key = 'minecraft:play_time' ORDER BY hours_played DESC;")
    def statistics_for_a_player(): #this leaderboard is probably a little broken
        PlayerName = st.selectbox("Players",options=player_names)
        st.write("This leaderboard allows you to view the statistics for an individual player, and is similar to what the player would see in the statistics menu inside the pause menu. There is a high chance it is broken")
        return(f"SELECT p.name, m.stat_key, m.stat_value FROM players p JOIN player_stats_mined m ON p.uuid = m.uuid WHERE p.name = '{PlayerName}' ORDER BY m.stat_value DESC;")
    def distance_traveled_by():
        distance_scales = {"Kilometers (1000 Blocks)":100000,"Miles (for you silly americans)":160934.4,"Chunks":160,"Meters (Blocks)":100}
        scale = st.selectbox("Units", distance_scales.keys())
        if st.checkbox("totals"):
            distance_stats_totals = {"Total of all distances":[f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:aviate_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:minecart_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_under_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_on_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:swim_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:boat_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:strider_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:sprint_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:fall_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:fly_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:crouch_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:climb_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:horse_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:pig_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:happy_ghast_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:nautilus_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_one_cm', 'aviate_one_cm','minecart_one_cm', 'walk_under_water_one_cm','walk_on_water_one_cm', 'swim_one_cm','boat_one_cm', 'strider_one_cm','sprint_one_cm','fall_one_cm', 'fly_one_cm', 'crouch_one_cm','climb_one_cm', 'horse_one_cm', 'pig_one_cm','happy_ghast_one_cm', 'nautilus_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;","Sum of all the methods of travel"],"Total on Foot":[f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:sprint_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:crouch_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_one_cm','sprint_one_cm','crouch_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;","Total distance walking, sprinting, and crouching (excluding walking in water)"],"Total Distance in Water":[f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:walk_under_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:walk_on_water_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:swim_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:walk_under_water_one_cm','walk_on_water_one_cm', 'swim_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;","Total of all distance traveled in water (excludes riding Nautilus and Boats)"],"Total Distance Ridden on Mobs":[f"SELECT p.name,ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:strider_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:horse_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:pig_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:happy_ghast_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:nautilus_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:strider_one_cm','horse_one_cm','pig_one_cm','happy_ghast_one_cm','nautilus_one_cm')GROUP BY p.name ORDER BY total_distance_traveled DESC;","Total distance from riding Horses, Pigs, Happy Ghasts, Striders, and Nautilus"],"Total Distance in Vehicles":[f"SELECT p.name, ROUND(SUM(CASE WHEN c.stat_key = 'minecraft:minecart_one_cm' THEN c.stat_value ELSE 0 END + CASE WHEN c.stat_key = 'minecraft:boat_one_cm' THEN c.stat_value ELSE 0 END) / {distance_scales[scale]}, 2) AS total_distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key IN ('minecraft:minecart_one_cm','boat_one_cm') GROUP BY p.name ORDER BY total_distance_traveled DESC;","Total Distance Traveled by Boat and Minecart"]}
            total_distance_key = st.selectbox("Total Distances;", distance_stats_totals.keys())
            st.write(f"Explaination: {distance_stats_totals[total_distance_key][1]}")
            return(distance_stats_totals[total_distance_key][0])

        else:
            #descriptions pulled from https://minecraft.wiki/w/Statistics#List_of_custom_statistic_names
            distance_stats = {"Distance By Elytra":["minecraft:aviate_one_cm","The total distance traveled by Elytra."],"Distance by Minecart":["minecraft:minecart_one_cm","The total distance traveled by minecarts."],"Distance Walked":["minecraft:walk_one_cm","The total distance walked."],"Distance Walked Under Water":["minecraft:walk_under_water_one_cm","The total distance covered in any direction while the player's head is underwater."],"Distance Walked on Water (Jesus Leaderboard)":["minecraft:walk_on_water_one_cm","The total distance covered in any direction while the player's head is not underwater (sorry its not really a Jesus leaderboard)."],"Distance Swam":["minecraft:swim_one_cm","The total distance covered with sprint-swimming."],"Distance Traveled by Boat":["minecraft:boat_one_cm","The distance traveled by boats (unfortunately there is no way to distinguish between boats on ice and boats on water)"],"Distance Traveled on Strider":["minecraft:strider_one_cm","The total distance traveled by striders via saddles."],"Distance Sprinted":["minecraft:sprint_one_cm","The total distance sprinted"],"Distance Fallen":["minecraft:fall_one_cm","The total distance fallen, excluding jumping. If the player falls more than one block, the entire jump is counted."],"Distance Flown":["minecraft:fly_one_cm","Distance traveled upward and forward at the same time, while more than one block above the ground."],"Distance Walked while Crouching":["minecraft:crouch_one_cm","The total distance traveled while sneaking and not in water."],"Distance Climbed":["minecraft:climb_one_cm","The total distance traveled up ladders or vines."],"Distance Traveled on Horse":["minecraft:horse_one_cm","The total distance traveled by horses (might also include other rideable mobs like camels, mules, donkeys, and skeleton horses)."],"Distance by Pig":["minecraft:pig_one_cm","The total distance traveled by pigs via saddles."],"Distance by Happy Ghast":["minecraft:happy_ghast_one_cm","The total distance traveled by Happy Ghast"],"Distance by Nautilus":["minecraft:nautilus_one_cm","The total distance traveled by nautilus"]}
            # unused dictionary definitions for mobs that are rideable but don't appear to be tracked
            # {"Distance by Skeleton Horse":["minecraft:skeleton_horse_one_cm","this one might be broken, or included in distance by horse"],"Distance by Donkey":["minecraft:donkey_one_cm","this one might be broken"],"Distance by Mule":["minecraft:mule_one_cm","this one might be broken"],"Distance Traveled on Camel":["minecraft:camel_one_cm","this one might be broken"]
            distance_key = st.selectbox("Distance traveled by", distance_stats.keys())
            st.write(f"Explaination: {distance_stats[distance_key][1]}")
            return(f"SELECT p.name, c.stat_value / {distance_scales[scale]} as distance_traveled FROM players p JOIN player_stats_custom c ON p.uuid = c.uuid WHERE c.stat_key = '{distance_stats[distance_key][0]}' ORDER BY distance_traveled DESC;")

    def kdr():
        return("SELECT p.name, ROUND(CAST(c.stat_value AS FLOAT) / NULLIF(d.stat_value, 0), 2) AS KD_Ratio, c.stat_value AS Player_Kills, d.stat_value AS Player_Deaths FROM players p JOIN player_stats_killed c ON p.uuid = c.uuid JOIN player_stats_killed_by d ON p.uuid = d.uuid WHERE c.stat_key = 'minecraft:player' AND d.stat_key = 'minecraft:player' ORDER BY KD_Ratio DESC;")

    leaderboards = {
    "Player causes of death from mobs":causes_of_death,
    "Player Play Time":player_play_time,
    "Statistics for a player":statistics_for_a_player,
    "Distances by player":distance_traveled_by,
    "Kill Death Ratio":kdr
    }
    st.markdown(f"# {list(page_names_to_funcs.keys())[1]}")
    query = st.selectbox("Choose a leaderboard", leaderboards.keys())
    if st.session_state["auth"]:
        st.write(query)
    display_leaderboard(leaderboards[query]())


#leaderboard for player with most kills
#SELECT p.name, c.stat_value as Player_Kills FROM players p JOIN player_stats_killed c ON p.uuid = c.uuid WHERE c.stat_key = 'minecraft:player' ORDER BY Player_Kills DESC;


def custom_sql_queries():
    st.markdown(f'# {list(page_names_to_funcs.keys())[2]}')
    if st.session_state["auth"]:
        DEFAULT_QUERY = """SELECT stat_key, SUM(stat_value) AS total_kills
FROM player_stats_killed_by
GROUP BY stat_key
ORDER BY total_kills DESC;"""
        # --- Input Field ---
        query = st.text_area("Type Your SQL Query Here", value=DEFAULT_QUERY, height=200)
        display_leaderboard(query)
    else:
        st.write("Please authenticate to make custom leaderboards. Otherwise enjoy the pre built leaderboards on the leaderboards page")

def authentication():
    st.markdown(f"# {list(page_names_to_funcs.keys())[3]}")
    st.write("Authenticate to use queries on the custom sql queries page, and see the query values for the pre-built leaderboards. Type your credentials here, and submit with CTRL Enter")
    username = st.text_input("Username")
    password = st.text_input("Password",type="password")
    if username == "minecraft_stats_webui_admin" and password == "insecure_password_please_change_me":  #please define a new admin username and password here
        st.session_state["auth"] = True

    st.write(f"Authenticated: {st.session_state["auth"]}")

page_names_to_funcs = {
    "—": intro,
    "Leaderboards": leaderboard,
    "Custom Sql queries": custom_sql_queries,
    "Authentication": authentication
}

page_name = st.sidebar.selectbox("Choose a demo", page_names_to_funcs.keys())
page_names_to_funcs[page_name]()
