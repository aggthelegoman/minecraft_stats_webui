import requests
import sys

# this uses the api found at:
# https://mcprofile.io/

#usage:
# floodgate_skin_grabber.py <username>
# the username must have the "." omitted for it to work

url =  f"https://mcprofile.io/api/v1/bedrock/gamertag/{sys.argv[1]}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    image = requests.get(data['skin']).content
    f = open(f'player_skins/.{sys.argv[1]}.png','wb')
    f.write(image)
    f.close()
else:
    print("Did not receive http code 200, image failed to download")
