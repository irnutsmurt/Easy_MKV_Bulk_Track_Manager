# directorynav.py

import os
import logging
from common import get_mkv_files, get_subdirectories

def navigate_and_browse(current_directory, media_action=None, on_exit=None):
    """Navigate through directories and provide options to work with MKV files."""
    previous_directory = os.path.dirname(current_directory)

    while True:
        subdirectories = get_subdirectories(current_directory)
        mkv_files = get_mkv_files(current_directory)
        mkv_file_count = len(mkv_files)

        print(f"\nCurrent Directory: {current_directory}")
        options = []
        index = 1  # Start indexing from 1 since 0 is reserved

        # List subdirectories
        if subdirectories:
            print("\nSubdirectories:")
            for subdir in subdirectories:
                print(f"{index}. {subdir}")
                options.append(('dir', os.path.join(current_directory, subdir)))
                index += 1

        # List MKV files
        if mkv_file_count > 0:
            print(f"{index}. List {mkv_file_count} MKV files")
            options.append(('list_mkv', current_directory))
            index += 1
            print(f"{index}. Work in current directory")
            options.append(('work_current', current_directory))
            index += 1

        print(f"{index}. Move to previous directory")
        options.append(('previous', previous_directory))
        index += 1

        print("0. Return to main menu")  # Option 0 to return to main menu

        choice = input("\nEnter your choice: ").strip()

        if choice == '0':
            logging.debug("User selected to return to main menu.")
            return "main_menu"  # Return the signal to propagate upwards

        try:
            choice = int(choice)
            if 1 <= choice <= len(options):
                option_type, option_value = options[choice - 1]
                if option_type == 'dir':
                    # Navigate into the selected subdirectory
                    result = navigate_and_browse(option_value, media_action, on_exit)
                    if result == "main_menu":
                        return "main_menu"  # Propagate the signal upwards
                elif option_type == 'list_mkv':
                    if media_action:
                        result = media_action(option_value)
                        if result == "main_menu":
                            return "main_menu"  # Propagate the signal upwards
                elif option_type == 'work_current':
                    if media_action:
                        result = media_action(option_value)
                        if result == "main_menu":
                            return "main_menu"  # Propagate the signal upwards
                elif option_type == 'previous':
                    if os.path.isdir(option_value):
                        current_directory = option_value
                    else:
                        print("No previous directory.")
            else:
                print("Invalid choice. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

# Helper functions (Assuming these are defined elsewhere in common.py)
def get_subdirectories(directory):
    """Retrieve a list of subdirectories in the given directory."""
    try:
        return [name for name in os.listdir(directory)
                if os.path.isdir(os.path.join(directory, name))]
    except Exception as e:
        logging.error(f"Error accessing subdirectories in '{directory}': {e}")
        return []
