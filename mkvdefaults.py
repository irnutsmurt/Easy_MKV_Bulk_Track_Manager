import os
import subprocess
import logging
from tqdm import tqdm
from mediainfo import (
    gather_tracks,
    update_media_info,
    create_backup_json,
    restore_backup_json,
    check_backup_exists,
    load_json,
    save_json,
    extract_season_episode
)
import installmkvpropedit
import json
from collections import Counter
import math
import directorynav
from common import get_mkv_files



def modify_mkv_track(file_path, track_id, flag_name, flag_value, dry_run=False):
    """Modify the MKV track's flag using mkvpropedit, with an optional dry run."""
    installmkvpropedit.ensure_mkvpropedit_installed()
    if track_id is None:
        logging.error(f"Track ID is None for file {file_path}. Skipping modification.")
        return
    flag_value_str = "1" if flag_value else "0"
    command = ["mkvpropedit", file_path, "--edit", f"track:@{track_id}", "--set", f"{flag_name}={flag_value_str}"]

    if dry_run:
        logging.info(f"[DRY RUN] Would execute: {' '.join(command)}")
    else:
        try:
            subprocess.run(command, check=True)
            logging.info(f"Track ID {track_id} {flag_name} set to {flag_value} in file {file_path}.")
        except subprocess.CalledProcessError:
            logging.error(f"Failed to modify the '{flag_name}' flag for track {track_id} in file {file_path}.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

        # Update the JSON after modification
        update_media_info(os.path.basename(os.path.dirname(file_path)), file_path)


def edit_mkv_file(file_path, dry_run=False):
    """Provide menu options to edit a single MKV file."""
    installmkvpropedit.ensure_mkvpropedit_installed()
    logging.info(f"Loading media info for {file_path}")
    show_name = os.path.basename(os.path.dirname(file_path))
    create_backup_json(show_name)  # Create a backup before making changes

    while True:
        media_info = update_media_info(show_name, file_path)
        tracks_info = gather_tracks(file_path)

        # Collect available tracks
        audio_tracks = tracks_info.get("audio", [])
        text_tracks = tracks_info.get("text", [])

        print("\nMKV Edit Menu:")
        print("1. Modify audio tracks")
        print("2. Modify subtitle tracks")
        print("3. Return to previous menu")
        choice = input("\nEnter your choice: ")

        if choice == '1':
            selected_track = select_track(audio_tracks, "audio")
            if selected_track:
                modify_tracks(file_path, selected_track, 'audio', dry_run)
        elif choice == '2':
            selected_track = select_track(text_tracks, "subtitle")
            if selected_track:
                modify_tracks(file_path, selected_track, 'text', dry_run)
        elif choice == '3':
            return
        else:
            logging.error("Invalid choice. Please select a valid option.")


def select_track(tracks, track_type):
    """Allow the user to select one track to modify."""
    if not tracks:
        logging.info(f"No {track_type} tracks found.")
        return None

    while True:
        print(f"\nAvailable {track_type.capitalize()} Tracks:")
        valid_tracks = []
        for idx, track in enumerate(tracks):
            track_id = track.get('track_id')
            if track_id is None:
                continue  # Skip tracks without valid track_id
            language = track.get('language', 'und')
            title = track.get('title', '')
            forced = track.get('forced', 'No')
            track_info = f"Track ID: {track_id}, Language: {language}, Title: {title}, Forced: {forced}"
            print(f"{len(valid_tracks) + 1}. {track_info}")
            valid_tracks.append(track)

        if not valid_tracks:
            logging.info(f"No valid {track_type} tracks with track IDs found.")
            return None

        try:
            selection = input(f"\nEnter the number of the {track_type} track to set as forced (1-{len(valid_tracks)}), or '0' to cancel: ").strip()
            if selection == '0':
                return None
            index = int(selection) - 1
            if 0 <= index < len(valid_tracks):
                selected_track = valid_tracks[index]
                return selected_track
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(valid_tracks)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")


def modify_tracks(file_path, selected_track, track_type, dry_run):
    """Modify the selected track and reset others of the same type."""
    flag_name = 'flag-forced'
    flag_value = True

    # Collect all tracks of the same type
    tracks_info = gather_tracks(file_path)
    all_tracks = tracks_info.get(track_type, [])

    # Prepare changes
    changes = []
    for track in all_tracks:
        track_id = track.get('track_id')
        if track_id is None:
            logging.warning(f"Track ID is None for track: {track}. Skipping this track.")
            continue  # Skip tracks without a valid track_id
        if track == selected_track:
            new_forced = 'Yes'
        else:
            new_forced = 'No' if track.get('forced', 'No') == 'Yes' else track.get('forced', 'No')
        changes.append({
            'track_id': track_id,
            'before': track,
            'after': {**track, 'forced': new_forced}
        })

    # Show before and after changes for relevant tracks
    print("\nChanges to be made:")
    for change in changes:
        if change['before'] == selected_track or (change['before'].get('forced', 'No') == 'Yes' and change['after']['forced'] == 'No'):
            track_id = change['track_id']
            print(f"\nTrack ID {track_id}:")
            print("Before:")
            print(json.dumps(change['before'], indent=4))
            print("After:")
            print(json.dumps(change['after'], indent=4))

    proceed = input("Do you want to proceed with these changes? (y/n): ").strip().lower()
    if proceed != 'y':
        logging.info("Operation cancelled by user.")
        return

    # Apply changes
    for change in changes:
        track_id = change['track_id']
        forced_value = True if change['after']['forced'] == 'Yes' else False
        modify_mkv_track(file_path, track_id, flag_name, forced_value, dry_run)


def work_in_current_directory(directory):
    """Provide options to work with files in the current directory."""
    while True:
        mkv_files = get_mkv_files(directory)  # Now correctly imported
        if not mkv_files:
            logging.info("No MKV files found in this directory.")
            return

        show_name = os.path.basename(directory)
        backup_exists = check_backup_exists(show_name)

        print("\nOptions:")
        print("1. Bulk set forced audio for files")
        print("2. Bulk set forced subtitle for files")
        print("3. Set forced audio for a single file")
        print("4. Set forced subtitle for a single file")
        print("5. Refresh media info")
        if backup_exists:
            print("6. Restore previous changes back")
            print("7. Return to previous menu")
            print("8. Return to main menu")
        else:
            print("6. Return to previous menu")
            print("7. Return to main menu")

        choice = input("\nEnter your choice: ")

        if choice == '1':
            bulk_set_forced_flag(directory, mkv_files, 'audio')
        elif choice == '2':
            bulk_set_forced_flag(directory, mkv_files, 'subtitle')
        elif choice == '3':
            select_and_edit_single_file(directory, mkv_files, 'audio')
        elif choice == '4':
            select_and_edit_single_file(directory, mkv_files, 'subtitle')
        elif choice == '5':
            refresh_media_info(show_name, directory)
        elif (choice == '6' and backup_exists):
            restore_previous_changes(directory)
        elif (choice == '6' and not backup_exists) or (choice == '7' and backup_exists):
            return
        elif (choice == '7' and not backup_exists) or (choice == '8' and backup_exists):
            return  # Return to main menu
        else:
            logging.error("Invalid choice. Please select a valid option.")


def edit_mkv_files_menu():
    """Main menu for editing MKV files."""
    from main import load_config  # Import here to avoid circular import
    config = load_config()
    directory = config.get('media_directory', '')
    if not os.path.isdir(directory):
        logging.error(f"Configured media directory '{directory}' not found.")
        return

    # Pass only the directory to media_action
    directorynav.navigate_and_browse(directory, media_action=work_in_current_directory)

def bulk_modify_files(directory, mkv_files, selected_track_info, track_type, dry_run=False):
    """Modify the forced flag for the selected track across multiple MKV files."""
    flag_name = 'flag-forced'

    # Display a summary of the changes to be made
    print(f"\nBulk {'Dry Run' if dry_run else 'Execution'}: Setting '{flag_name}' for {track_type} tracks.")

    for file_name in tqdm(mkv_files, desc="Processing MKV files"):
        file_path = os.path.join(directory, file_name)
        show_name = os.path.basename(directory)

        # Ensure media info is up to date
        media_info = update_media_info(show_name, file_path)
        tracks_info = gather_tracks(file_path)

        # Get all tracks of the specified type
        tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

        # Identify the track to force and others to reset
        for track in tracks:
            if (track.get('language') == selected_track_info['language'] and
                track.get('title') == selected_track_info['title']):
                # This is the track to set as forced
                flag_value = True
            else:
                # Reset other tracks' forced flag
                flag_value = False

            track_id = track.get('track_id')
            if track_id is not None:
                modify_mkv_track(file_path, track_id, flag_name, flag_value, dry_run)
            else:
                logging.warning(f"Track ID missing for track: {track}")

def bulk_set_forced_flag(directory, mkv_files, track_type):
    """Bulk set the forced flag for a specific track type in multiple files."""
    # Display a message and initialize a progress bar
    total_files = len(mkv_files)
    print(f"\nReviewing all {total_files} files...")

    # Initialize variables
    track_collections = []
    show_name = os.path.basename(directory)
    show_data = load_json(show_name)
    updated_json = False

    # Use tqdm for the progress bar
    with tqdm(total=total_files, desc="Reviewing files") as progress_bar:
        for file_name in mkv_files:
            file_path = os.path.join(directory, file_name)
            file_base_name = os.path.basename(file_path)
            season, episode = extract_season_episode(file_base_name)

            # Determine season and episode keys
            if season is None:
                season_key = "No Season"
                episode_key = file_base_name
            else:
                season_key = f"Season {season}"
                episode_key = f"s{season:02}e{episode:02}"

            # Check if media info exists in JSON
            if season_key in show_data and episode_key in show_data[season_key]:
                media_info = show_data[season_key][episode_key]["media_info"]
            else:
                # If not in JSON, parse the file and update JSON
                media_info = gather_tracks(file_path)
                if season_key not in show_data:
                    show_data[season_key] = {}
                show_data[season_key][episode_key] = {
                    "filename": file_base_name,
                    "media_info": media_info
                }
                updated_json = True

            # Collect track information based on track_type
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
            for track in tracks:
                if track.get('track_id') is None:
                    continue  # Skip tracks without track_id
                language = track.get('language', 'und')
                title = track.get('title', '')
                track_info = {'language': language, 'title': title}
                track_collections.append(json.dumps(track_info))

            progress_bar.update(1)

    # Save updated JSON if necessary
    if updated_json:
        save_json(show_name, show_data)

    # Count occurrences of each track
    track_counter = Counter(track_collections)
    sorted_tracks = track_counter.most_common()
    total_files = len(mkv_files)

    # Pagination settings
    page_size = 10
    total_pages = math.ceil(len(sorted_tracks) / page_size)
    current_page = 1

    while True:
        start_index = (current_page - 1) * page_size
        end_index = start_index + page_size
        page_tracks = sorted_tracks[start_index:end_index]

        print(f"\nAvailable Tracks (Page {current_page}/{total_pages}):")
        for idx, (track_json, count) in enumerate(page_tracks, start=1):
            track_info = json.loads(track_json)
            language = track_info['language']
            title = track_info['title']
            print(f"{idx}. Language: {language}, Title: {title} ({count}/{total_files})")

        # Pagination options
        print("\nOptions:")
        if current_page > 1:
            print("n. Previous page")
        if current_page < total_pages:
            print("m. Next page")
        print("0. Return to previous menu")

        selection = input("\nEnter the number of the track to set as forced, or choose an option: ").strip()

        if selection == '0':
            return
        elif selection.lower() == 'n' and current_page > 1:
            current_page -= 1
        elif selection.lower() == 'm' and current_page < total_pages:
            current_page += 1
        else:
            try:
                index = int(selection) - 1
                if 0 <= index < len(page_tracks):
                    selected_track_json, _ = page_tracks[index]
                    selected_track_info = json.loads(selected_track_json)
                    # Present options to the user
                    while True:
                        print("\nOptions:")
                        print("1. Perform a dry run")
                        print("2. Execute change")
                        print("3. Cancel and return to previous menu")
                        print("4. Return to main menu")
                        action = input("\nEnter your choice: ").strip()
                        if action == '1':
                            bulk_modify_files(directory, mkv_files, selected_track_info, track_type, dry_run=True)
                            return
                        elif action == '2':
                            bulk_modify_files(directory, mkv_files, selected_track_info, track_type, dry_run=False)
                            return
                        elif action == '3':
                            return
                        elif action == '4':
                            return  # Return to main menu
                        else:
                            logging.error("Invalid choice. Please select a valid option.")
                else:
                    logging.error("Invalid selection. Please enter a valid number.")
            except ValueError:
                logging.error("Invalid input. Please enter a valid number or option.")
