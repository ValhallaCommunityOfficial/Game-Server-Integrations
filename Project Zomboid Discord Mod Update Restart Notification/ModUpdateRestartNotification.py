import time
import requests
import glob
import re
from datetime import datetime

# Made by KodeMan - https://www.thevalhallacommunity.com - Discord.gg/valhallacommunity

WAIT_SECONDS = 10  # Adjust as needed

log_directories = [
    ".cache/Logs/*DebugLog-server.txt", # Edit to full path of DebugLog-server.txt
    ".cache/Logs/*chat.txt" # Edit to full path of chat.txt
]

# Define your Discord webhook URL here
webhook_url = ''

mods_last_update = {}
last_read_positions = {}

# Keep track of sent notifications to avoid duplicates
notifications_sent = {
    'restart_countdown': set(),
    'server_live': False,
    'server_shutdown': False
}

# Function to extract mod ID from the log line
def extract_mod_id(line):
    mod_id_match = re.search(r'\((\d+)\)', line)
    if mod_id_match:
        return mod_id_match.group(1)
    return None

def post_to_discord(message):
    data = {
        'content': message
    }
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        print(f"Failed to send message to Discord: {response.status_code} {response.text}")

def read_log_file(log_file, last_position):
    lines = []
    try:
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            f.seek(last_position)
            lines = f.readlines()
            last_position = f.tell()
    except FileNotFoundError:
        pass
    return lines, last_position

def main():
    global last_read_positions, notifications_sent

    while True:
        for log_directory in log_directories:
            for log_file in glob.glob(log_directory):
                if log_file not in last_read_positions:
                    last_read_positions[log_file] = 0

                lines, last_read_positions[log_file] = read_log_file(log_file, last_read_positions[log_file])

                for line in lines:
                    if "has an update!" in line:
                        mod_name_match = re.search(r'Mod "(.+?)" \(\d+\) has an update!', line)
                        if mod_name_match:
                            mod_name = mod_name_match.group(1)
                            mod_id = extract_mod_id(line) # Extract the Mod ID
                            current_time = datetime.now()

                            # Check if the mod was updated within the last 20 minutes
                            last_update_time = mods_last_update.get(mod_name, datetime.min)
                            if (current_time - last_update_time).total_seconds() >= 20 * 60:
                                if mod_id:
                                    workshop_link = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
                                    post_to_discord(f'Mod "{mod_name}" has an update!\n{workshop_link}')
                                else:
                                    post_to_discord(f'Mod "{mod_name}" has an update! (Mod ID not found in log)')

                                mods_last_update[mod_name] = current_time

                    if "Detected outdated workshop item - restarting server in 5 minutes!" in line:
                        post_to_discord("Server will restart in 5 minutes.")

                    if "*** SERVER STARTED ****" in line:
                        if not notifications_sent['server_live']:
                            post_to_discord("Server is Live")
                            notifications_sent['server_live'] = True
                            notifications_sent['server_shutdown'] = False  # Reset shutdown notification

                    if "Core.quit" in line:
                        if not notifications_sent['server_shutdown']:
                            post_to_discord("Server has Shut Down")
                            notifications_sent['server_shutdown'] = True
                            notifications_sent['server_live'] = False  # Reset live notification

                    # Server restart countdown messages
                    countdown_match = re.search(r'Server restarting in (\d+) minute', line)
                    if countdown_match:
                        minutes = int(countdown_match.group(1))
                        if minutes > 0 and minutes not in notifications_sent['restart_countdown']:
                            post_to_discord(f"Server restarting in {minutes} minute.")
                            notifications_sent['restart_countdown'].add(minutes)
                    else:
                        countdown_match = re.search(r'Server restarting in (\d+) minutes', line)
                        if countdown_match:
                            minutes = int(countdown_match.group(1))
                            if minutes > 0 and minutes not in notifications_sent['restart_countdown']:
                                post_to_discord(f"Server restarting in {minutes} minutes.")
                                notifications_sent['restart_countdown'].add(minutes)

        time.sleep(WAIT_SECONDS)

if __name__ == "__main__":
    main()