# common.py

import os

def get_mkv_files(directory):
    """Get a list of all .mkv files in the specified directory."""
    return [f for f in os.listdir(directory) if f.lower().endswith('.mkv')]

def get_subdirectories(directory):
    """Get a list of subdirectories in the specified directory."""
    return [f for f in os.listdir(directory) if os.path.isdir(os.path.join(directory, f))]
