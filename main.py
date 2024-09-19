# main.py

import os
import sys
import json
import logging

# Import functions from other modules
import mediainfo
import mkvdefaults
import installmkvpropedit

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Path to the configuration file
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

def configure_settings():
    """Configure settings such as media directory."""
    config = load_config()
    while True:
        print("\nSettings Menu")
        print("1. Set media directory")
        print("2. Return to main menu")

        choice = input("\nEnter your choice: ")

        if choice == '1':
            directory = input("Enter the path to your media directory: ").strip()
            if os.path.isdir(directory):
                config['media_directory'] = directory
                save_config(config)
                logging.info(f"Media directory set to '{directory}'.")
            else:
                logging.error(f"Directory '{directory}' does not exist.")
        elif choice == '2':
            return
        else:
            logging.error("Invalid choice. Please select a valid option.")

def menu():
    """Display the main menu."""
    # Ensure mkvpropedit is installed before proceeding
    if not installmkvpropedit.ensure_mkvpropedit_installed():
        sys.exit(1)

    while True:
        config = load_config()
        print("\nMain Menu")
        if 'media_directory' in config:
            print("1. Browse media in stored directory")
        print("2. Check media info in a custom directory")
        print("3. Edit MKV files")
        print("4. Configure settings")
        print("5. Exit")

        choice = input("\nEnter your choice: ")

        if choice == '1' and 'media_directory' in config:
            # Browse media in the stored directory
            media_directory = config['media_directory']
            if os.path.isdir(media_directory):
                result = mediainfo.browse_directory(media_directory)
                if result == "main_menu":
                    continue  # Return to the main menu
            else:
                logging.error(f"Stored media directory '{media_directory}' not found.")

        elif choice == '2':
            directory = input("Enter the directory to check for media files: ").strip()

            if not os.path.isdir(directory):
                logging.error(f"Directory '{directory}' not found. Please try again.")
                continue

            result = mediainfo.browse_directory(directory)
            if result == "main_menu":
                continue  # Return to the main menu

        elif choice == '3':
            mkvdefaults.edit_mkv_files_menu()

        elif choice == '4':
            configure_settings()

        elif choice == '5':
            logging.info("Exiting program.")
            sys.exit(0)

        else:
            logging.error("Invalid choice. Please enter a valid option.")

if __name__ == "__main__":
    menu()
