import json
import logging
from time import sleep, time
from zomboid_rcon import ZomboidRCON

# Made by KodeMan - https://www.thevalhallacommunity.com - Discord.gg/valhallacommunity

# Configuration
SERVER_IP = '' # Edit as needed
SERVER_PORT = 25574 # RCON PORT - Edit as needed
SERVER_PASSWORD = '' # RCON PASSWORD - Edit as needed

REWARDS = [
    {'item': 'Base.CopperCoin', 'quantity': 50, 'interval': 3600},  # Hourly reward - Edit as needed
    {'item': 'Base.EventCoin', 'quantity': 1, 'interval': 10800}    # 3-hour reward - Edit as needed
]

CHECK_INTERVAL = 300  # Check for eligible players every 5 minutes
MAX_RETRIES = 5       # Maximum number of retries for giving items
RETRY_DELAY = 5       # Delay between retries (in seconds)
PLAYTIME_DATA_FILE = "player_data.json"

# Logging Setup
logging.basicConfig(filename='zomboid_rewards.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Helper Functions
def load_playtime_data():
    try:
        with open(PLAYTIME_DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logging.warning("Playtime data file not found or corrupted. Starting fresh.")
        return {}

def save_playtime_data(player_data):
    with open(PLAYTIME_DATA_FILE, "w") as file:
        json.dump(player_data, file, indent=4)

# Main Script Logic
def main():
    rcon_client = None
    player_data = load_playtime_data()

    while True:
        try:
            if rcon_client is None:
                rcon_client = ZomboidRCON(SERVER_IP, SERVER_PORT, SERVER_PASSWORD)
                logging.info("Established RCON connection.")

            # Check the RCON connection
            if rcon_client.help().successful:
                player_list_result = rcon_client.players()

                if player_list_result.successful:
                    player_names = [
                        name.strip('- ') for name in player_list_result.response.split('\n')
                        if name.strip('- ') and not name.startswith("Players connected")
                    ]

                    for player_name in player_names:
                        player_data.setdefault(player_name, {'connect_time': time(), 'rewards': {}})
                        playtime = int(time() - player_data[player_name]['connect_time'])

                        for reward in REWARDS:
                            item_name = reward['item']
                            last_reward_time = player_data[player_name]['rewards'].get(item_name, 0)
                            if playtime >= reward['interval'] and playtime - last_reward_time >= reward['interval']:
                                for attempt in range(MAX_RETRIES):
                                    give_item_result = rcon_client.additem(f'"{player_name}"', f"{item_name} {reward['quantity']}")
                                    if give_item_result.successful:
                                        logging.info(f"Gave {reward['quantity']} {item_name} to {player_name} (playtime: {playtime} seconds)")
                                        player_data[player_name]['rewards'][item_name] = playtime
                                        break
                                    else:
                                        logging.error(f"Failed to give item (attempt {attempt + 1}): {give_item_result.error}")
                                        sleep(RETRY_DELAY)
                                else:
                                    logging.error(f"Maximum retries reached for giving item to {player_name}")

            else:
                raise ConnectionError("RCON connection is not active.")

            save_playtime_data(player_data)
        except KeyboardInterrupt:
            logging.info("Script terminated by user.")
            break
        except ConnectionError as e:
            logging.error(f"Connection error: {e}. Attempting to reconnect in {RETRY_DELAY} seconds...")
            sleep(RETRY_DELAY)
            rcon_client = None
        except Exception as e:
            logging.critical(f"Unexpected error: {e}", exc_info=True)
            if rcon_client:
                rcon_client.close()
                rcon_client = None
        finally:
            sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
