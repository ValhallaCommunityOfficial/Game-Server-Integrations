import os
import time
import glob
from zomboid_rcon import ZomboidRCON

# Define your server RCON connection details
server_ip = '' # Adjust as needed
server_port = 25574  # Adjust as needed
rcon_password = '' # Adjust as needed

# Define the path to the new players text file
new_players_file = '/home/ubuntu/newplayers.txt' # Adjust as needed, this will keep track of players who received welcome pack.

# Define the path to the PerkLog directory
perklog_directory = '/var/lib/pterodactyl/volumes/f715d160-b70b-4bd9-80e0-f8bc04247261/.cache/Logs/' # Adjust as needed, path to PerkLog.txt

# Initialize the RCON client
rcon = ZomboidRCON(ip=server_ip, port=server_port, password=rcon_password)

# Define the welcome pack items
welcome_pack_items = [
    'PinkSlip.91geoMetro 1',
    'Base.ToiletPaper 1',
    'Base.CopperCoin 100',
    'Base.Crisps3 1',
    'Base.HandAxe 1',
    'MoreSmokes.JointsPackSourDiesel 1',
    'Base.PopBottle 1',
    'Base.Jacket_Padded 1',
    'Base.Trousers_Padded 1',
    'Base.Screwdriver 1',
    'Base.Pillow 1'
]

# Function to read and store new players
def get_new_players():
    try:
        with open(new_players_file, 'r') as file:
            return set(file.read().splitlines())
    except FileNotFoundError:
        return set()

# Function to add a player to the new players list
def add_new_player(player_name):
    new_players = get_new_players()
    new_players.add(player_name)
    with open(new_players_file, 'w') as file:
        file.write('\n'.join(new_players))

# Function to check if a player is new
def is_new_player(player_name):
    # Remove the hyphen if present and check if the player is new
    cleaned_name = player_name.lstrip('-')
    return cleaned_name not in get_new_players()

# Function to check if a player has survived for 0 hours
def has_survived_0_hours(player_name):
    perklog_files = glob.glob(os.path.join(perklog_directory, '*PerkLog.txt'))
    if perklog_files:
        latest_perklog = max(perklog_files, key=os.path.getctime)
        try:
            with open(latest_perklog, 'r') as file:
                lines = file.readlines()
                for line in lines:
                    if '[Hours Survived: 0]' in line and player_name in line:
                        return True
        except FileNotFoundError:
            print(f"PerkLog file not found: {latest_perklog}")
    else:
        print("No PerkLog files found.")
    return False

# Function to give a welcome pack to a new player with retries
def give_welcome_pack(player_name):
    if is_new_player(player_name) and has_survived_0_hours(player_name):
        # Wait for 5 minutes (300 seconds) before giving the welcome pack
        print(f"Waiting for 30 seconds before giving the welcome pack to {player_name}")
        time.sleep(30)

        max_retries = 3
        retries = 0

        while retries < max_retries:
            for item in welcome_pack_items:
                # Wrap player names with spaces in quotations
                formatted_player_name = f'"{player_name}"' if ' ' in player_name else player_name
                # Execute the additem command for each item in the welcome pack
                result = rcon.additem(formatted_player_name, item)
                if not result.successful:
                    print(f"Failed to give item {item} to {player_name}: {result.response}")
                    retries += 1
                    if retries < max_retries:
                        print(f"Retrying ({retries}/{max_retries})...")
                        time.sleep(60)  # Wait for 60 seconds before retrying
                    else:
                        print(f"Max retries reached. Giving up on {player_name}.")
                        break
            else:
                print(f"Welcome pack given to {player_name}")
                add_new_player(player_name)
                break
    else:
        print(f"{player_name} is not a new player or has not survived for 0 hours")

# Main loop to continuously check for new players and monitor the PerkLog file
while True:
    player_names = set()
    for perklog_file in glob.glob(os.path.join(perklog_directory, '*PerkLog.txt')):
        with open(perklog_file, 'r') as file:
            lines = file.readlines()
            for line in lines:
                if '[Hours Survived: 0]' in line:
                    parts = line.split(']')
                    if len(parts) > 2:
                        player_name = parts[2].strip('[]')
                        player_names.add(player_name)

    for player_name in player_names:
        give_welcome_pack(player_name)
    
    # Wait for a specified time (e.g., 60 seconds) before checking again
    time.sleep(60)
