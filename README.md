Minecraft Stats Webui

This project is built on [RootByteNet's Minecraft Statistics to MySQL](https://github.com/RooByteNet/Minecraft-Statistics-to-MySQL/tree/149b969df57100705fc13f70757629136c926a30). Set it up for your server from the instructions there and have it post to a [MariaDB](https://mariadb.org/) database, then edit the python file and put in your connection info and deploy this python [streamlit](https://streamlit.io/) page online with docker or streamlit cloud.

You can check out a demo that pulls data from my personal minecraft server [here](https://stats.gardnercraft.dedyn.io)

There are still a lot of bugs and features I am still working on, so any help is appreciated. Here are some of the features in the works:
- more leaderboards
- fixing the current leaderboards (I'm really bad at sql and some might be broken)
- advancement leaderboards and tracker
- better website UI
- not having database connection details hardcoded in the python files
- adding this repository, MariaDB, and [Minecraft Statistics to MySQL](https://github.com/RooByteNet/Minecraft-Statistics-to-MySQL/tree/149b969df57100705fc13f70757629136c926a30) into a single docker container for easier setup
- setup tutorials

I also recently added support where leaderboards displaying players will show the player head. This will work if you use the included get_player_heads.py (which also needs skin_grabber.py and floodgate_skin_grabber.py). And yes, this script can get player heads for players on the server using geyser and floodgate. If a player head/skin cant be found, the minecraft_stats_webui.py page uses either alt_playerhead.png or the site favicon if alt_playerhead.png is missing. Also, please feel free to use your own alt_playerhead.png file. It just needs to be an 8x8 pixel png image.
