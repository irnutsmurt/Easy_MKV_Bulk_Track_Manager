# mediainfo.py
import pymediainfo
import os
import json
import re
import logging
import shutil
from datetime import datetime
from pymediainfo import MediaInfo
from tqdm import tqdm
from common import get_mkv_files, get_subdirectories  # Import from common.py
import directorynav  # Import directory navigation functions

# Directory to store JSON files
JSON_DIR = "json"

def get_media_files(directory, extensions=['.mkv', '.mp4', '.avi']):
    """Get a list of all media files in the specified directory."""
    return [f for f in os.listdir(directory) if os.path.splitext(f)[1].lower() in extensions]

def load_json(show_name):
    """Load the JSON file for a specific show if it exists."""
    json_file_path = os.path.join(JSON_DIR, f"{show_name}.json")
    if os.path.exists(json_file_path):
        with open(json_file_path, 'r') as file:
            return json.load(file)
    else:
        return {}

def save_json(show_name, data):
    """Save data to the JSON file for a specific show."""
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
    json_file_path = os.path.join(JSON_DIR, f"{show_name}.json")
    with open(json_file_path, 'w') as file:
        # Sort the data based on season and episode numbers if applicable
        sorted_data = {k: data[k] for k in sorted(data.keys(), key=lambda s: int(re.search(r'\d+', s).group()) if re.search(r'\d+', s) else 0)}
        json.dump(sorted_data, file, indent=4)

def extract_season_episode(file_name):
    """Extract season and episode from the filename."""
    match = re.search(r'[Ss](\d+)[Ee](\d+)', file_name)
    if match:
        season = int(match.group(1))
        episode = int(match.group(2))
        return season, episode
    return None, None

def create_backup_json(show_name):
    """Create a timestamped backup of the show's JSON file before making changes."""
    json_file_path = os.path.join(JSON_DIR, f"{show_name}.json")

    # Ensure the JSON_DIR exists
    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)
        logging.debug(f"Created JSON directory: {JSON_DIR}")

    if not os.path.exists(json_file_path):
        logging.warning(f"No JSON file found for {show_name} to backup.")
        return

    # Create a timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    backup_file_path = os.path.join(JSON_DIR, f"{show_name}_backup_{timestamp}.json")

    try:
        shutil.copyfile(json_file_path, backup_file_path)
        logging.info(f"Backup created: {backup_file_path}")
    except Exception as e:
        logging.error(f"Failed to create backup for {show_name}: {e}")

def restore_backup_json(show_name):
    """Restore the show's JSON file from the backup."""
    json_file_path = os.path.join(JSON_DIR, f"{show_name}.json")
    backup_file_path = os.path.join(JSON_DIR, f"{show_name}.backup.json")

    if not os.path.exists(backup_file_path):
        logging.error(f"No backup file found for {show_name}. Cannot restore.")
        return

    shutil.copyfile(backup_file_path, json_file_path)
    logging.info(f"Restored {json_file_path} from backup.")

def check_backup_exists(show_name):
    """Check if a backup JSON file exists for the show."""
    backup_file_path = os.path.join(JSON_DIR, f"{show_name}.backup.json")
    return os.path.exists(backup_file_path)

def gather_tracks(file_path):
    """Fetch all media information including multiple audio and text tracks."""
    media_info = MediaInfo.parse(file_path)
    tracks_info = {
        "general": [],
        "video": [],
        "audio": [],
        "text": []
    }

    for track in media_info.tracks:
        if track.track_type.lower() == "menu":
            continue  # Skip menu tracks

        track_type = track.track_type.lower()
        track_data = {
            "track_id": getattr(track, "track_id", None),  # Use real track ID if available
            "track_type": track_type,
            "duration": getattr(track, "duration", None),
            "file_size": getattr(track, "file_size", None),
            "overall_bit_rate": getattr(track, "overall_bit_rate", None),
            "width": getattr(track, "width", None),
            "height": getattr(track, "height", None),
            "frame_rate": getattr(track, "frame_rate", None),
            "codec": getattr(track, "codec", None),
            "channels": getattr(track, "channel_s", None),  # Handle channels correctly for audio
            "sampling_rate": getattr(track, "sampling_rate", None),
            "bit_rate": getattr(track, "bit_rate", None),
            "language": getattr(track, "language", 'und'),
            "track_name": getattr(track, "track_name", ""),  # Default to empty string if None
            "title": getattr(track, "title", ""),  # Default to empty string if None
            "forced": "Yes" if getattr(track, "forced", "No") == "Yes" else "No"  # Correct forced flag handling
        }

        if track_type == "general":
            tracks_info["general"].append(track_data)
        elif track_type == "video":
            tracks_info["video"].append(track_data)
        elif track_type == "audio":
            tracks_info["audio"].append(track_data)
        elif track_type == "text":
            tracks_info["text"].append(track_data)

    return tracks_info


def print_media_info(media_info, fields):
    """Print media info to the screen based on selected fields."""
    for track_type, tracks in media_info.items():
        if fields == "All Fields" or fields.lower() in track_type.lower():
            print(f"\n{track_type.capitalize()} Tracks:")
            for track in tracks:
                for key, value in track.items():
                    if value is not None:
                        print(f"  {key}: {value}")
                print("----------------------------------------")  # Separator for readability

def check_if_media_info_exists(show_name, file_name):
    """Check if media info for a specific file is already in the JSON file."""
    season, episode = extract_season_episode(file_name)
    show_data = load_json(show_name)

    if season is None:
        # Handle non-seasoned episodes (No Season)
        return show_data.get("No Season", {}).get(file_name, {}).get("media_info")

    season_key = f"Season {season}"
    episode_key = f"s{season:02}e{episode:02}"

    if season_key in show_data and episode_key in show_data[season_key]:
        return show_data[season_key][episode_key]["media_info"]
    return None

def update_media_info(show_name, file_path):
    """Check and update the JSON file with media info for a specific episode."""
    file_name = os.path.basename(file_path)
    season, episode = extract_season_episode(file_name)

    show_data = load_json(show_name)

    if season is None:
        media_info = gather_tracks(file_path)
        if "No Season" not in show_data:
            show_data["No Season"] = {}
        show_data["No Season"][file_name] = {
            "filename": file_name,
            "media_info": media_info
        }
        save_json(show_name, show_data)
        return media_info

    season_key = f"Season {season}"
    episode_key = f"s{season:02}e{episode:02}"

    media_info = gather_tracks(file_path)

    if season_key not in show_data:
        show_data[season_key] = {}

    show_data[season_key][episode_key] = {
        "filename": file_name,
        "media_info": media_info
    }

    save_json(show_name, show_data)
    return media_info

def check_and_print_media_info(show_name, file_path, fields):
    """Check if media info exists in the JSON. If not, process the file and add it to JSON."""
    file_name = os.path.basename(file_path)

    media_info = check_if_media_info_exists(show_name, file_name)

    if media_info:
        logging.info(f"Media info for {file_name} found in JSON file.")
    else:
        logging.info(f"Processing {file_name} and adding media info to JSON file.")
        media_info = update_media_info(show_name, file_path)

    # Print the media info to the screen
    print_media_info(media_info, fields)

def check_all_media_info(directory, media_files, show_name, fields):
    """Check media info for all media files in the specified directory."""
    total_files = len(media_files)
    with tqdm(total=total_files, desc="Processing files", unit="file") as progress_bar:
        for file_name in media_files:
            file_path = os.path.join(directory, file_name)
            check_and_print_media_info(show_name, file_path, fields)
            progress_bar.update(1)
    logging.info("All media info has been processed.")

def select_media_info_fields(main_menu=False):
    """Menu to select which media info fields to display."""
    while True:
        print("\nSelect which fields to display:")
        print("1. General")
        print("2. Video")
        print("3. Audio")
        print("4. Text")
        print("5. All Fields")
        print("6. Return to previous menu")
        print("0. Return to main menu")

        choice = input("\nEnter your choice: ").strip()

        if choice == '1':
            return "general"
        elif choice == '2':
            return "video"
        elif choice == '3':
            return "audio"
        elif choice == '4':
            return "text"
        elif choice == '5':
            return "All Fields"
        elif choice == '6' and not main_menu:
            return "previous"
        elif choice == '0' or (choice == '6' and main_menu):
            return "main_menu"
        else:
            logging.error("Invalid choice. Please select a valid option.")

def browse_directory(directory, show_name=None):
    """Allows the user to browse a directory, checking for subdirectories or MKV files."""
    directorynav.navigate_and_browse(
        directory,
        media_action=lambda current_dir: browse_media_menu(current_dir, get_mkv_files(current_dir), show_name),
        on_exit=lambda: "main_menu"
    )

def browse_media_menu(current_directory, mkv_files, show_name=None):
    """Display media-related actions for MKV files."""
    if not mkv_files:
        logging.info("No MKV files found.")
        return

    print(f"\n1. Check media info for a specific file")
    print("2. Check media info for all files")
    print("3. Return to previous directory")
    print("4. Return to main menu")

    choice = input("\nEnter your choice: ").strip()

    if choice == '1':
        # List MKV files
        print("\nList of files:")
        for idx, file_name in enumerate(mkv_files, start=1):
            print(f"{idx}. {file_name}")

        try:
            file_idx = int(input(f"\nEnter the file number (1-{len(mkv_files)}): ").strip())
            if 1 <= file_idx <= len(mkv_files):
                file_path = os.path.join(current_directory, mkv_files[file_idx - 1])
                # Show granular field menu
                fields = select_media_info_fields()
                if fields == "main_menu":
                    return "main_menu"
                elif fields == "previous":
                    return
                check_and_print_media_info(show_name or os.path.basename(current_directory), file_path, fields)
            else:
                logging.error(f"Invalid file number. Please enter a number between 1 and {len(mkv_files)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid file number.")

    elif choice == '2':
        # Show granular field menu
        fields = select_media_info_fields()
        if fields == "main_menu":
            return "main_menu"
        elif fields == "previous":
            return
        check_all_media_info(current_directory, mkv_files, show_name or os.path.basename(current_directory), fields)

    elif choice == '3':
        return  # Return to the previous directory

    elif choice == '4':
        return "main_menu"  # Indicate to caller to return to main menu

    else:
        logging.error("Invalid choice. Please select a valid option.")
