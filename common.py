# common.py

import os
import json

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from the JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_config(config):
    """Save configuration to the JSON file."""
    with open(CONFIG_FILE, 'w') as file:
        json.dump(config, file, indent=4)

def get_mkv_files(directory):
    """Get a list of all .mkv files in the specified directory."""
    return [f for f in os.listdir(directory) if f.lower().endswith('.mkv')]

def get_subdirectories(directory):
    """Get a list of subdirectories in the specified directory."""
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
