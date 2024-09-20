# mkvdefaults.py

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
    check_if_media_info_exists,
    check_all_media_info
)
import installmkvpropedit
from common import get_mkv_files, load_config, save_config
import getpass
import re
import sys
import directorynav

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')


def has_write_permission(file_path):
    """Check if the current user has write permissions for the file."""
    return os.access(file_path, os.W_OK)


def modify_mkv_track(file_path, track_id, flag_name, flag_value, dry_run=False, use_sudo=False, sudo_password=None):
    """Modify the MKV track's flag using mkvpropedit, with optional dry run and sudo."""
    installmkvpropedit.ensure_mkvpropedit_installed()

    if track_id is None:
        logging.error(f"Track ID is None for file {file_path}. Skipping modification.")
        return

    flag_value_str = "1" if flag_value else "0"
    command = ["mkvpropedit", file_path, "--edit", f"track:@{track_id}", "--set", f"{flag_name}={flag_value_str}"]

    if use_sudo:
        command.insert(0, "sudo")
        command.insert(1, "-S")

    if dry_run:
        logging.debug(f"[DRY RUN] Would execute: {' '.join(command)}")
        return

    try:
        logging.debug(f"Attempting to modify Track ID {track_id}: Setting {flag_name} to {flag_value}.")

        if use_sudo and sudo_password:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=f"{sudo_password}\n")
        else:
            result = subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout = result.stdout
            stderr = result.stderr

        logging.debug(f"Command output: {stdout}")
        logging.info(f"Track ID {track_id} {flag_name} set to {flag_value} in file {file_path}.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to modify the '{flag_name}' flag for track {track_id} in file {file_path}.")
        logging.debug(f"Error output: {e.stderr}")

        specific_error_pattern = re.compile(
            r"Error: Updating the 'Tracks' element failed\. Reason: The file could not be opened for writing\.",
            re.IGNORECASE
        )
        if specific_error_pattern.search(e.stderr):
            raise PermissionError("Permission denied while modifying MKV track.")
        else:
            logging.error(f"Error modifying track {track_id} in file {file_path}: {e.stderr}")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        logging.error(f"Error modifying track {track_id} in file {file_path}: {e}")

    if not dry_run and not use_sudo:
        update_media_info(os.path.basename(os.path.dirname(file_path)), file_path)


def bulk_modify_files(directory, mkv_files, selected_track_info, track_type, flag_name, dry_run=False, use_sudo=False, sudo_password=None):
    """Modify the flag for the selected track across multiple MKV files."""
    print(f"\nBulk {'Dry Run' if dry_run else 'Execution'}: Setting '{flag_name}' for {track_type.capitalize()} tracks.")

    for file_path in tqdm(mkv_files, desc="Processing MKV files"):
        show_name = os.path.basename(directory)

        try:
            media_info = update_media_info(show_name, file_path)
            tracks_info = gather_tracks(file_path)

            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

            for track in tracks:
                track_id = track.get('track_id')
                if track_id is None:
                    logging.warning(f"Track ID missing for track: {track}")
                    continue

                is_selected_track = (
                    (track.get('language', 'und').lower().strip() == selected_track_info['language'].lower().strip()) and
                    ((track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip())
                )

                if flag_name == 'flag-forced':
                    desired_flag = True if is_selected_track else False
                elif flag_name == 'flag-default':
                    desired_flag = True if is_selected_track else False
                else:
                    desired_flag = None

                if desired_flag is None:
                    continue

                current_flag = track.get(flag_name, False)
                if current_flag == desired_flag:
                    logging.debug(f"Track ID {track_id} already has {flag_name} set to {desired_flag}. Skipping modification.")
                    continue

                try:
                    modify_mkv_track(file_path, track_id, flag_name, desired_flag, dry_run, use_sudo, sudo_password)
                except PermissionError:
                    logging.error(f"Permission denied for file '{file_path}'.")
                    if not use_sudo:
                        response = input(f"Do you want to use sudo to modify '{file_path}'? (y/n): ").strip().lower()
                        if response == 'y':
                            sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
                            try:
                                modify_mkv_track(file_path, track_id, flag_name, desired_flag, dry_run, use_sudo=True, sudo_password=sudo_password_input)
                            except PermissionError:
                                logging.error(f"Failed to modify '{file_path}' even with sudo.")
                            except Exception as e:
                                logging.error(f"An unexpected error occurred while modifying '{file_path}': {e}")
                    else:
                        logging.error(f"Cannot modify '{file_path}' without sufficient permissions.")
        except PermissionError:
            logging.error(f"Permission denied for file '{file_path}'.")
        except Exception as e:
            logging.error(f"An unexpected error occurred while processing file '{file_path}': {e}")


def bulk_set_forced_flag(directory, mkv_files, track_type):
    """Bulk set the forced flag for a specific track type in multiple files."""
    print(f"\nBulk Set Forced {track_type.capitalize()} Tracks")

    unique_tracks = {}
    print("\nCollecting unique tracks across all MKV files...")
    for file_name in tqdm(mkv_files, desc="Scanning MKV files"):
        file_path = os.path.join(directory, file_name)
        show_name = os.path.basename(directory)
        media_info = check_if_media_info_exists(show_name, file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

        for track in tracks:
            language = (track.get('language', 'und') or '').lower().strip()
            title = (track.get('title') or '').lower().strip()
            key = (language, title)
            if key not in unique_tracks:
                unique_tracks[key] = {
                    'language': track.get('language', 'und'),
                    'title': track.get('title', ''),
                    'count': 1
                }
            else:
                unique_tracks[key]['count'] += 1

    if not unique_tracks:
        logging.info(f"No {track_type} tracks found to set as forced.")
        return

    unique_tracks_list = list(unique_tracks.values())

    print("\nAvailable Tracks to Set as Forced:")
    for idx, track in enumerate(unique_tracks_list, start=1):
        language = track['language']
        title = track['title']
        count = track['count']
        print(f"{idx}. Language: {language}, Title: {title} ({count} MKV file{'s' if count !=1 else ''})")

    while True:
        try:
            selection = int(input(f"\nSelect the track to set as forced (1-{len(unique_tracks_list)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(unique_tracks_list):
                selected_track_info = {
                    'language': unique_tracks_list[selection - 1]['language'],
                    'title': unique_tracks_list[selection - 1]['title']
                }
                selected_track_count = unique_tracks_list[selection - 1]['count']
                print(f"\nYou have selected to set the following track as forced:")
                print(f"Language: {selected_track_info['language']}, Title: {selected_track_info['title']} ({selected_track_count} MKV file{'s' if selected_track_count !=1 else ''})")
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(unique_tracks_list)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    files_with_track = []
    files_without_track = []

    print(f"\nScanning MKV files for the selected track...")
    for file_name in tqdm(mkv_files, desc="Scanning files"):
        file_path = os.path.join(directory, file_name)
        media_info = check_if_media_info_exists(os.path.basename(directory), file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)

    print(f"\nFound {len(files_with_track)} file{'s' if len(files_with_track)!=1 else ''} with the selected track and {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} without it.")

    if files_without_track:
        print(f"\nThe following {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} do not contain the selected track and will be skipped:")
        for file_path in files_without_track[:10]:
            print(f"- {os.path.basename(file_path)}")
        if len(files_without_track) > 10:
            print(f"...and {len(files_without_track) - 10} more.")

    files_requiring_sudo = [f for f in files_with_track if not has_write_permission(f)]
    sudo_password_input = None

    if files_requiring_sudo:
        response = input(f"\n{len(files_requiring_sudo)} file{'s' if len(files_requiring_sudo)!=1 else ''} are not writable. Do you want to provide a sudo password to modify them? (y/n): ").strip().lower()
        if response == 'y':
            sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
        else:
            logging.error("Cannot modify the non-writable files without sudo. Skipping them.")
            files_with_track = [f for f in files_with_track if has_write_permission(f)]
            if not files_with_track:
                logging.info("No writable files left to modify. Aborting bulk operation.")
                return

    while True:
        print("\nOptions:")
        print("1. Perform a Dry Run")
        print("2. Execute Changes")
        print("3. Return to Previous Menu")
        print("4. Return to Main Menu")

        option = input("\nEnter your choice: ").strip()

        if option == '1':
            print("\nPerforming a dry run to simulate the changes...")
            try:
                bulk_modify_files(directory, files_with_track, selected_track_info, track_type, flag_name='flag-forced', dry_run=True, use_sudo=False)
                print("\nDry run completed successfully. No changes have been made.")
            except PermissionError:
                logging.error("Permission denied during dry run.")
            except Exception as e:
                logging.error(f"An unexpected error occurred during dry run: {e}")
            break
        elif option == '2':
            create_backup_json(os.path.basename(directory))
            logging.debug(f"Backup of JSON data created for show '{os.path.basename(directory)}'.")

            print("\nExecuting changes...")
            try:
                writable_files = [f for f in files_with_track if has_write_permission(f)]
                if writable_files:
                    bulk_modify_files(directory, writable_files, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=False)

                if sudo_password_input and files_requiring_sudo:
                    bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)

                print("\nBulk modification completed successfully.")
            except PermissionError:
                response = input("Permission denied while modifying some files. Would you like to use sudo to modify the remaining files? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
                        bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)
                        print("\nBulk modification with sudo completed successfully.")
                    except Exception as e:
                        logging.error(f"An error occurred while using sudo: {e}")
                else:
                    logging.error("Bulk modification aborted due to permission issues.")
            break
        elif option == '3':
            return
        elif option == '4':
            return
        else:
            logging.error("Invalid choice. Please select a valid option.")


def bulk_set_default_flag(directory, mkv_files, track_type):
    """Bulk set the default flag for a specific track type in multiple files."""
    print(f"\nBulk Set Default {track_type.capitalize()} Tracks")

    unique_tracks = {}
    print("\nCollecting unique tracks across all MKV files...")
    for file_name in tqdm(mkv_files, desc="Scanning MKV files"):
        file_path = os.path.join(directory, file_name)
        show_name = os.path.basename(directory)
        media_info = check_if_media_info_exists(show_name, file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

        for track in tracks:
            language = (track.get('language', 'und') or '').lower().strip()
            title = (track.get('title') or '').lower().strip()
            key = (language, title)
            if key not in unique_tracks:
                unique_tracks[key] = {
                    'language': track.get('language', 'und'),
                    'title': track.get('title', ''),
                    'count': 1
                }
            else:
                unique_tracks[key]['count'] += 1

    if not unique_tracks:
        logging.info(f"No {track_type} tracks found to set as default.")
        return

    unique_tracks_list = list(unique_tracks.values())

    print("\nAvailable Tracks to Set as Default:")
    for idx, track in enumerate(unique_tracks_list, start=1):
        language = track['language']
        title = track['title']
        count = track['count']
        print(f"{idx}. Language: {language}, Title: {title} ({count} MKV file{'s' if count !=1 else ''})")

    while True:
        try:
            selection = int(input(f"\nSelect the track to set as default (1-{len(unique_tracks_list)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(unique_tracks_list):
                selected_track_info = {
                    'language': unique_tracks_list[selection - 1]['language'],
                    'title': unique_tracks_list[selection - 1]['title']
                }
                selected_track_count = unique_tracks_list[selection - 1]['count']
                print(f"\nYou have selected to set the following track as default:")
                print(f"Language: {selected_track_info['language']}, Title: {selected_track_info['title']} ({selected_track_count} MKV file{'s' if selected_track_count !=1 else ''})")
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(unique_tracks_list)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    files_with_track = []
    files_without_track = []

    print(f"\nScanning MKV files for the selected track...")
    for file_name in tqdm(mkv_files, desc="Scanning files"):
        file_path = os.path.join(directory, file_name)
        media_info = check_if_media_info_exists(os.path.basename(directory), file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)

    print(f"\nFound {len(files_with_track)} file{'s' if len(files_with_track)!=1 else ''} with the selected track and {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} without it.")

    if files_without_track:
        print(f"\nThe following {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} do not contain the selected track and will be skipped:")
        for file_path in files_without_track[:10]:
            print(f"- {os.path.basename(file_path)}")
        if len(files_without_track) > 10:
            print(f"...and {len(files_without_track) - 10} more.")

    files_requiring_sudo = [f for f in files_with_track if not has_write_permission(f)]
    sudo_password_input = None

    if files_requiring_sudo:
        response = input(f"\n{len(files_requiring_sudo)} file{'s' if len(files_requiring_sudo)!=1 else ''} are not writable. Do you want to provide a sudo password to modify them? (y/n): ").strip().lower()
        if response == 'y':
            sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
        else:
            logging.error("Cannot modify the non-writable files without sudo. Skipping them.")
            files_with_track = [f for f in files_with_track if has_write_permission(f)]
            if not files_with_track:
                logging.info("No writable files left to modify. Aborting bulk operation.")
                return

    while True:
        print("\nOptions:")
        print("1. Perform a Dry Run")
        print("2. Execute Changes")
        print("3. Return to Previous Menu")
        print("4. Return to Main Menu")

        option = input("\nEnter your choice: ").strip()

        if option == '1':
            print("\nPerforming a dry run to simulate the changes...")
            try:
                bulk_modify_files(directory, files_with_track, selected_track_info, track_type, flag_name='flag-default', dry_run=True, use_sudo=False)
                print("\nDry run completed successfully. No changes have been made.")
            except PermissionError:
                logging.error("Permission denied during dry run.")
            except Exception as e:
                logging.error(f"An unexpected error occurred during dry run: {e}")
            break
        elif option == '2':
            create_backup_json(os.path.basename(directory))
            logging.debug(f"Backup of JSON data created for show '{os.path.basename(directory)}'.")

            print("\nExecuting changes...")
            try:
                writable_files = [f for f in files_with_track if has_write_permission(f)]
                if writable_files:
                    bulk_modify_files(directory, writable_files, selected_track_info, track_type, flag_name='flag-default', dry_run=False, use_sudo=False)

                if sudo_password_input and files_requiring_sudo:
                    bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-default', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)

                print("\nBulk modification completed successfully.")
            except PermissionError:
                response = input("Permission denied while modifying some files. Would you like to use sudo to modify the remaining files? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
                        bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-default', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)
                        print("\nBulk modification with sudo completed successfully.")
                    except Exception as e:
                        logging.error(f"An error occurred while using sudo: {e}")
                else:
                    logging.error("Bulk modification aborted due to permission issues.")
            break
        elif option == '3':
            return
        elif option == '4':
            return
        else:
            logging.error("Invalid choice. Please select a valid option.")


def bulk_set_default_and_forced_flag(directory, mkv_files, track_type):
    """Bulk set both default and forced flags for a specific track type in multiple files."""
    print(f"\nBulk Set Both Default and Forced {track_type.capitalize()} Tracks")

    unique_tracks = {}
    print("\nCollecting unique tracks across all MKV files...")
    for file_name in tqdm(mkv_files, desc="Scanning MKV files"):
        file_path = os.path.join(directory, file_name)
        show_name = os.path.basename(directory)
        media_info = check_if_media_info_exists(show_name, file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

        for track in tracks:
            language = (track.get('language', 'und') or '').lower().strip()
            title = (track.get('title') or '').lower().strip()
            key = (language, title)
            if key not in unique_tracks:
                unique_tracks[key] = {
                    'language': track.get('language', 'und'),
                    'title': track.get('title', ''),
                    'count': 1
                }
            else:
                unique_tracks[key]['count'] += 1

    if not unique_tracks:
        logging.info(f"No {track_type} tracks found to set as default and forced.")
        return

    unique_tracks_list = list(unique_tracks.values())

    print("\nAvailable Tracks to Set as Default and Forced:")
    for idx, track in enumerate(unique_tracks_list, start=1):
        language = track['language']
        title = track['title']
        count = track['count']
        print(f"{idx}. Language: {language}, Title: {title} ({count} MKV file{'s' if count !=1 else ''})")

    while True:
        try:
            selection = int(input(f"\nSelect the track to set as default and forced (1-{len(unique_tracks_list)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(unique_tracks_list):
                selected_track_info = {
                    'language': unique_tracks_list[selection - 1]['language'],
                    'title': unique_tracks_list[selection - 1]['title']
                }
                selected_track_count = unique_tracks_list[selection - 1]['count']
                print(f"\nYou have selected to set the following track as default and forced:")
                print(f"Language: {selected_track_info['language']}, Title: {selected_track_info['title']} ({selected_track_count} MKV file{'s' if selected_track_count !=1 else ''})")
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(unique_tracks_list)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    files_with_track = []
    files_without_track = []

    print(f"\nScanning MKV files for the selected track...")
    for file_name in tqdm(mkv_files, desc="Scanning files"):
        file_path = os.path.join(directory, file_name)
        media_info = check_if_media_info_exists(os.path.basename(directory), file_name)
        if media_info:
            tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)
        else:
            tracks_info = gather_tracks(file_path)
            tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])
            has_track = any(
                (track.get('language', 'und') or '').lower().strip() == selected_track_info['language'].lower().strip() and
                (track.get('title') or '').lower().strip() == selected_track_info['title'].lower().strip()
                for track in tracks
            )
            if has_track:
                files_with_track.append(file_path)
            else:
                files_without_track.append(file_path)

    print(f"\nFound {len(files_with_track)} file{'s' if len(files_with_track)!=1 else ''} with the selected track and {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} without it.")

    if files_without_track:
        print(f"\nThe following {len(files_without_track)} file{'s' if len(files_without_track)!=1 else ''} do not contain the selected track and will be skipped:")
        for file_path in files_without_track[:10]:
            print(f"- {os.path.basename(file_path)}")
        if len(files_without_track) > 10:
            print(f"...and {len(files_without_track) - 10} more.")

    files_requiring_sudo = [f for f in files_with_track if not has_write_permission(f)]
    sudo_password_input = None

    if files_requiring_sudo:
        response = input(f"\n{len(files_requiring_sudo)} file{'s' if len(files_requiring_sudo)!=1 else ''} are not writable. Do you want to provide a sudo password to modify them? (y/n): ").strip().lower()
        if response == 'y':
            sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
        else:
            logging.error("Cannot modify the non-writable files without sudo. Skipping them.")
            files_with_track = [f for f in files_with_track if has_write_permission(f)]
            if not files_with_track:
                logging.info("No writable files left to modify. Aborting bulk operation.")
                return

    while True:
        print("\nOptions:")
        print("1. Perform a Dry Run")
        print("2. Execute Changes")
        print("3. Return to Previous Menu")
        print("4. Return to Main Menu")

        option = input("\nEnter your choice: ").strip()

        if option == '1':
            print("\nPerforming a dry run to simulate the changes...")
            try:
                bulk_modify_files(directory, files_with_track, selected_track_info, track_type, flag_name='flag-forced', dry_run=True, use_sudo=False)
                print("\nDry run completed successfully. No changes have been made.")
            except PermissionError:
                logging.error("Permission denied during dry run.")
            except Exception as e:
                logging.error(f"An unexpected error occurred during dry run: {e}")
            break
        elif option == '2':
            create_backup_json(os.path.basename(directory))
            logging.debug(f"Backup of JSON data created for show '{os.path.basename(directory)}'.")

            print("\nExecuting changes...")
            try:
                writable_files = [f for f in files_with_track if has_write_permission(f)]
                if writable_files:
                    bulk_modify_files(directory, writable_files, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=False)

                if sudo_password_input and files_requiring_sudo:
                    bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)

                print("\nBulk modification completed successfully.")
            except PermissionError:
                response = input("Permission denied while modifying some files. Would you like to use sudo to modify the remaining files? (y/n): ").strip().lower()
                if response == 'y':
                    try:
                        sudo_password_input = getpass.getpass(prompt="Enter sudo password: ")
                        bulk_modify_files(directory, files_requiring_sudo, selected_track_info, track_type, flag_name='flag-forced', dry_run=False, use_sudo=True, sudo_password=sudo_password_input)
                        print("\nBulk modification with sudo completed successfully.")
                    except Exception as e:
                        logging.error(f"An error occurred while using sudo: {e}")
                else:
                    logging.error("Bulk modification aborted due to permission issues.")
            break
        elif option == '3':
            return
        elif option == '4':
            return
        else:
            logging.error("Invalid choice. Please select a valid option.")


def select_and_edit_single_file_default(directory, mkv_files, track_type):
    """Set the default flag for a specific track in a single MKV file."""
    print(f"\nSet Default '{track_type.capitalize()}' Track for a Single File")

    if not mkv_files:
        logging.info("No MKV files found in this directory.")
        return

    print("\nAvailable MKV Files:")
    for idx, file_name in enumerate(mkv_files, start=1):
        print(f"{idx}. {file_name}")

    while True:
        try:
            selection = int(input(f"\nSelect a file to modify (1-{len(mkv_files)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(mkv_files):
                selected_file = mkv_files[selection - 1]
                file_path = os.path.join(directory, selected_file)
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(mkv_files)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    media_info = check_if_media_info_exists(os.path.basename(directory), selected_file)
    if media_info:
        tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
    else:
        tracks_info = gather_tracks(file_path)
        tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

    if not tracks:
        logging.info(f"No {track_type} tracks found in '{selected_file}'.")
        return

    print(f"\nAvailable {track_type.capitalize()} Tracks in '{selected_file}':")
    for idx, track in enumerate(tracks, start=1):
        language = track.get('language', 'und')
        title = track.get('title', 'No Title')
        is_default = track.get('flag-default', False)
        print(f"{idx}. Track ID: {track.get('track_id')}, Language: {language}, Title: {title}, Default: {is_default}")

    while True:
        try:
            track_selection = int(input(f"\nSelect a track to set as default (1-{len(tracks)}), or 0 to cancel: "))
            if track_selection == 0:
                return
            if 1 <= track_selection <= len(tracks):
                selected_track = tracks[track_selection - 1]
                track_id = selected_track.get('track_id')
                if track_id is None:
                    logging.warning("Selected track does not have a valid Track ID.")
                    return
                desired_flag = True
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(tracks)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    try:
        if not selected_track.get('flag-default', False):
            modify_mkv_track(file_path, track_id, 'flag-default', True)
        else:
            logging.info(f"Track ID {track_id} is already set as default.")

        for track in tracks:
            if track.get('track_id') != track_id and track.get('flag-default', False):
                modify_mkv_track(file_path, track.get('track_id'), 'flag-default', False)

        print(f"\nDefault flag set successfully for Track ID {track_id} in '{selected_file}'.")
    except Exception as e:
        logging.error(f"An error occurred while setting default flags: {e}")


def select_and_edit_single_file_default_and_forced(directory, mkv_files, track_type):
    """Set both default and forced flags for a specific track in a single MKV file."""
    print(f"\nSet Both Default and Forced '{track_type.capitalize()}' Track for a Single File")

    if not mkv_files:
        logging.info("No MKV files found in this directory.")
        return

    print("\nAvailable MKV Files:")
    for idx, file_name in enumerate(mkv_files, start=1):
        print(f"{idx}. {file_name}")

    while True:
        try:
            selection = int(input(f"\nSelect a file to modify (1-{len(mkv_files)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(mkv_files):
                selected_file = mkv_files[selection - 1]
                file_path = os.path.join(directory, selected_file)
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(mkv_files)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    media_info = check_if_media_info_exists(os.path.basename(directory), selected_file)
    if media_info:
        tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
    else:
        tracks_info = gather_tracks(file_path)
        tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

    if not tracks:
        logging.info(f"No {track_type} tracks found in '{selected_file}'.")
        return

    print(f"\nAvailable {track_type.capitalize()} Tracks in '{selected_file}':")
    for idx, track in enumerate(tracks, start=1):
        language = track.get('language', 'und')
        title = track.get('title', 'No Title')
        is_default = track.get('flag-default', False)
        is_forced = track.get('flag-forced', False)
        print(f"{idx}. Track ID: {track.get('track_id')}, Language: {language}, Title: {title}, Default: {is_default}, Forced: {is_forced}")

    while True:
        try:
            track_selection = int(input(f"\nSelect a track to set as default and forced (1-{len(tracks)}), or 0 to cancel: "))
            if track_selection == 0:
                return
            if 1 <= track_selection <= len(tracks):
                selected_track = tracks[track_selection - 1]
                track_id = selected_track.get('track_id')
                if track_id is None:
                    logging.warning("Selected track does not have a valid Track ID.")
                    return
                desired_flag_default = True
                desired_flag_forced = True
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(tracks)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    try:
        if not selected_track.get('flag-default', False):
            modify_mkv_track(file_path, track_id, 'flag-default', True)
        else:
            logging.info(f"Track ID {track_id} is already set as default.")

        if not selected_track.get('flag-forced', False):
            modify_mkv_track(file_path, track_id, 'flag-forced', True)
        else:
            logging.info(f"Track ID {track_id} is already set as forced.")

        for track in tracks:
            if track.get('track_id') != track_id:
                if track.get('flag-default', False):
                    modify_mkv_track(file_path, track.get('track_id'), 'flag-default', False)
                if track.get('flag-forced', False):
                    modify_mkv_track(file_path, track.get('track_id'), 'flag-forced', False)

        print(f"\nDefault and Forced flags set successfully for Track ID {track_id} in '{selected_file}'.")
    except Exception as e:
        logging.error(f"An error occurred while setting default and forced flags: {e}")


def select_and_edit_single_file(directory, mkv_files, track_type):
    """Set the forced flag for a specific track in a single MKV file."""
    print(f"\nSet Forced '{track_type.capitalize()}' Track for a Single File")

    if not mkv_files:
        logging.info("No MKV files found in this directory.")
        return

    print("\nAvailable MKV Files:")
    for idx, file_name in enumerate(mkv_files, start=1):
        print(f"{idx}. {file_name}")

    while True:
        try:
            selection = int(input(f"\nSelect a file to modify (1-{len(mkv_files)}), or 0 to cancel: "))
            if selection == 0:
                return
            if 1 <= selection <= len(mkv_files):
                selected_file = mkv_files[selection - 1]
                file_path = os.path.join(directory, selected_file)
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(mkv_files)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    media_info = check_if_media_info_exists(os.path.basename(directory), selected_file)
    if media_info:
        tracks = media_info.get(track_type if track_type != 'subtitle' else 'text', [])
    else:
        tracks_info = gather_tracks(file_path)
        tracks = tracks_info.get(track_type if track_type != 'subtitle' else 'text', [])

    if not tracks:
        logging.info(f"No {track_type} tracks found in '{selected_file}'.")
        return

    print(f"\nAvailable {track_type.capitalize()} Tracks in '{selected_file}':")
    for idx, track in enumerate(tracks, start=1):
        language = track.get('language', 'und')
        title = track.get('title', 'No Title')
        is_forced = track.get('flag-forced', False)
        print(f"{idx}. Track ID: {track.get('track_id')}, Language: {language}, Title: {title}, Forced: {is_forced}")

    while True:
        try:
            track_selection = int(input(f"\nSelect a track to set as forced (1-{len(tracks)}), or 0 to cancel: "))
            if track_selection == 0:
                return
            if 1 <= track_selection <= len(tracks):
                selected_track = tracks[track_selection - 1]
                track_id = selected_track.get('track_id')
                if track_id is None:
                    logging.warning("Selected track does not have a valid Track ID.")
                    return
                desired_flag = True
                break
            else:
                logging.error(f"Invalid selection. Please enter a number between 1 and {len(tracks)}.")
        except ValueError:
            logging.error("Invalid input. Please enter a valid number.")

    try:
        if not selected_track.get('flag-forced', False):
            modify_mkv_track(file_path, track_id, 'flag-forced', True)
        else:
            logging.info(f"Track ID {track_id} is already set as forced.")

        for track in tracks:
            if track.get('track_id') != track_id and track.get('flag-forced', False):
                modify_mkv_track(file_path, track.get('track_id'), 'flag-forced', False)

        print(f"\nForced flag set successfully for Track ID {track_id} in '{selected_file}'.")
    except Exception as e:
        logging.error(f"An error occurred while setting forced flags: {e}")

def work_in_current_directory(directory):
    """Provide options to work with files in the current directory."""
    while True:
        mkv_files = get_mkv_files(directory)
        if not mkv_files:
            logging.info("No MKV files found in this directory.")
            return "main_menu"  # Return signal to main menu

        show_name = os.path.basename(directory)
        backup_exists = check_backup_exists(show_name)

        print("\nOptions:")
        print("1. Bulk set forced audio for files")
        print("2. Bulk set forced subtitle for files")
        print("3. Bulk set default audio for files")
        print("4. Bulk set default subtitle for files")
        print("5. Set forced audio for a single file")
        print("6. Set forced subtitle for a single file")
        print("7. Set default audio for a single file")
        print("8. Set default subtitle for a single file")
        print("9. Bulk set both default and forced audio for files")
        print("10. Bulk set both default and forced subtitle for files")
        print("11. Set both default and forced audio for a single file")
        print("12. Set both default and forced subtitle for a single file")
        print("13. Refresh media info")
        if backup_exists:
            print("14. Restore previous changes back")
            print("15. Return to previous menu")
        else:
            print("14. Return to previous menu")

        print("0. Return to main menu")  # Option 0 to return to main menu

        choice = input("\nEnter your choice: ").strip()

        if choice == '0':
            logging.debug("User selected to return to main menu.")
            return "main_menu"  # Return signal to main menu
        elif choice == '1':
            bulk_set_forced_flag(directory, mkv_files, 'audio')
        elif choice == '2':
            bulk_set_forced_flag(directory, mkv_files, 'subtitle')
        elif choice == '3':
            bulk_set_default_flag(directory, mkv_files, 'audio')
        elif choice == '4':
            bulk_set_default_flag(directory, mkv_files, 'subtitle')
        elif choice == '5':
            select_and_edit_single_file(directory, mkv_files, 'audio')
        elif choice == '6':
            select_and_edit_single_file(directory, mkv_files, 'subtitle')
        elif choice == '7':
            select_and_edit_single_file_default(directory, mkv_files, 'audio')
        elif choice == '8':
            select_and_edit_single_file_default(directory, mkv_files, 'subtitle')
        elif choice == '9':
            bulk_set_default_and_forced_flag(directory, mkv_files, 'audio')
        elif choice == '10':
            bulk_set_default_and_forced_flag(directory, mkv_files, 'subtitle')
        elif choice == '11':
            select_and_edit_single_file_default_and_forced(directory, mkv_files, 'audio')
        elif choice == '12':
            select_and_edit_single_file_default_and_forced(directory, mkv_files, 'subtitle')
        elif choice == '13':
            refresh_media_info(show_name, directory)
        elif (choice == '14' and backup_exists):
            restore_backup_json(show_name)
        elif (choice == '14' and not backup_exists) or (choice == '15' and backup_exists):
            return  # Return to previous menu
        else:
            logging.error("Invalid choice. Please select a valid option.")


def refresh_media_info(show_name, directory):
    """Refresh media information by reprocessing all MKV files in the directory."""
    media_files = get_mkv_files(directory)
    fields = "All Fields"
    check_all_media_info(directory, media_files, show_name, fields)
    print("\nMedia information refreshed successfully.")

def edit_mkv_files_menu():
    """Main menu for editing MKV files."""
    config = load_config()
    directory = config.get('media_directory', '')
    if not os.path.isdir(directory):
        logging.error(f"Configured media directory '{directory}' not found.")
        return

    result = directorynav.navigate_and_browse(directory, media_action=work_in_current_directory)

    if result == "main_menu":
        logging.debug("Propagating 'main_menu' signal to main.py")
        return "main_menu"  # <-- Propagate the signal to main.py
    else:
        logging.debug(f"Received result from navigate_and_browse: {result}")
        return




