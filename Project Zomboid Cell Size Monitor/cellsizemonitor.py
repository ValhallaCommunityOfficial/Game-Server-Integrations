import os
import json
import re
import requests
import time
from collections import defaultdict

# Made by KodeMan - https://www.thevalhallacommunity.com - Discord.gg/valhallacommunity

def monitor_cell_sizes(save_folder, cache_file="cell_size_cache.json", log_file="ENTER_PATH_FOR_NEW_LOG_FILE_CREATION", webhook_url="ENTER_YOUR_DISCORD_WEBHOOK_HERE"): # EDIT THIS AS NEEDED
    cell_cache = defaultdict(int)
    chunk_cache = {}

    pattern = re.compile(r"map_(\d+)_(\d+)\.bin")

    for filename in os.listdir(save_folder):
        match = pattern.match(filename)
        if match:
            x, y = map(int, match.groups())
            cell_x, cell_y = x // 30, y // 30
            cell_key = f"{cell_x}_{cell_y}"
            filepath = os.path.join(save_folder, filename)
            size_bytes = os.path.getsize(filepath)
            size_mb = size_bytes / (1024 * 1024) 
            cell_cache[cell_key] += size_mb
            chunk_cache[filepath] = size_bytes / 1024  # Store chunk size in KB

    # Sort cells and chunks by size (descending)
    sorted_cells = sorted(cell_cache.items(), key=lambda item: item[1], reverse=True)
    sorted_chunks = sorted(chunk_cache.items(), key=lambda item: item[1], reverse=True)

    # Log top 10 largest cells and chunks to file
    with open(log_file, "w") as f:
        f.write("Top 10 Largest Cells (MB):\n")
        for cell_key, size_mb in sorted_cells[:10]:
            f.write(f"Cell {cell_key}: {size_mb:.2f} MB\n")

        f.write("\nTop 10 Largest Chunks (KB):\n")
        for chunk_path, size_kb in sorted_chunks[:10]:
            f.write(f"{chunk_path.split('/')[-1]}: {size_kb:.2f} KB\n")

    # Post top 10 largest cells and chunks to Discord webhook
    top_cells_message = "Top 10 Largest Cells (MB):\n" + "\n".join(
        f"Cell {cell_key}: {size_mb:.2f} MB" for cell_key, size_mb in sorted_cells[:10]
    )
    top_chunks_message = "Top 10 Largest Chunks (KB):\n" + "\n".join(
        f"{chunk_path.split('/')[-1]}: {size_kb:.2f} KB" for chunk_path, size_kb in sorted_chunks[:10]
    )
    requests.post(webhook_url, json={"content": top_cells_message + "\n\n" + top_chunks_message})

    # Save updated cell cache (optional)
    with open(cache_file, "w") as f:
        json.dump(cell_cache, f)  # Only save cell cache

# --- Main Execution ---
save_folder = "/var/lib/pterodactyl/volumes/f715d160-b70b-4bd9-80e0-f8bc04247261/.cache/Saves/Multiplayer/test/" # Replace with path to your zomboid server save file
webhook_url = ""  # Replace with your actual webhook URL

while True:
    monitor_cell_sizes(save_folder, webhook_url=webhook_url)
    time.sleep(10800)  # Sleep for 30 minutes
