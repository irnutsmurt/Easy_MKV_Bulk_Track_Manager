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
        index = 1

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

        print(f"{index}. Return to main menu")
        options.append(('main_menu', None))

        choice = input("\nEnter your choice: ")

        try:
            choice = int(choice)
            if 1 <= choice <= len(options):
                option_type, option_value = options[choice - 1]
                if option_type == 'dir':
                    navigate_and_browse(option_value, media_action, on_exit)
                elif option_type == 'list_mkv':
                    if media_action:
                        media_action(option_value)
                elif option_type == 'work_current':
                    if media_action:
                        media_action(option_value)
                elif option_type == 'previous':
                    if os.path.isdir(option_value):
                        current_directory = option_value
                    else:
                        print("No previous directory.")
                elif option_type == 'main_menu':
                    if on_exit:
                        on_exit()
                    return
            else:
                print("Invalid choice. Please select a valid option.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
