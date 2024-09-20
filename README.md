# Easy MKV Bulk Forced/Default Audio or Subtitle change

## Overview

**MKV Audio Subtitle Changer** is a Python-based application designed to streamline the management and editing of MKV (Matroska Video) files. This tool allows users to effortlessly set forced or default audio and subtitle tracks, extract and display detailed media information, and maintain organized JSON files for data persistence. With a user-friendly, menu-driven interface, navigating through directories and performing bulk or individual file operations becomes intuitive and efficient.

## Features

- **Bulk Operations:** Set forced or default flags for audio and subtitle tracks across multiple MKV files simultaneously.
- **Individual File Editing:** Modify audio and subtitle tracks for specific MKV files as needed.
- **Media Information Extraction:** Retrieve comprehensive media details using the `pymediainfo` library.
- **JSON Data Management:** Automatically save and backup media information in structured JSON files.
- **Directory Navigation:** Easily browse and navigate through directories containing MKV files with a clear, menu-driven interface.
- **Backup & Restore:** Create timestamped backups of JSON data and restore them when necessary.
- **Progress Visualization:** Utilize progress bars for tracking the processing status of multiple files.

## Prerequisites

Before installing and running the application, ensure that your system meets the following requirements:

- **Operating System:** Windows, macOS, or Linux.
- **Python Version:** Python 3.6 or higher.
- **MediaInfo Library:** Required by the `pymediainfo` package to extract media information.

## Installation

### 1. Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/yourusername/MKVAudioSubtitleChanger.git
cd MKVAudioSubtitleChanger/mkvscripts
```

*Replace `yourusername` with your actual GitHub username.*

### 2. Install the MediaInfo Library

The application relies on the MediaInfo library to extract media details. Install it based on your operating system:

- **Ubuntu/Debian:**

  ```bash
  sudo apt-get update
  sudo apt-get install mediainfo
  ```

- **macOS (using Homebrew):**

  ```bash
  brew install mediainfo
  ```

- **Windows:**

  1. Download the [MediaInfo DLL](https://mediaarea.net/en/MediaInfo/Download/Windows).
  2. Install it and ensure that the DLL is accessible in your system's PATH or placed in the same directory as your Python scripts.

### 3. Set Up a Python Virtual Environment (Optional but Recommended)

Creating a virtual environment helps manage dependencies without affecting your global Python installation.

```bash
python3 -m venv venv
```

Activate the virtual environment:

- **Linux/macOS:**

  ```bash
  source venv/bin/activate
  ```

- **Windows:**

  ```bash
  venv\Scripts\activate
  ```

### 4. Install Python Dependencies

With the virtual environment activated (if you chose to use one), install the required Python packages:

```bash
pip install -r requirements.txt
```

### 5. Verify Installation

Ensure that all dependencies are installed correctly by running:

```bash
pip list
```

You should see `pymediainfo` and `tqdm` listed among the installed packages.

## Usage

### 1. Configure Settings

Before using the application, configure your media directory where your MKV files are stored.

1. **Run the Application:**

   ```bash
   python main.py
   ```

2. **Configure Media Directory:**

   - From the **Main Menu**, select the option to **Configure Settings** (usually option `4`).
   - Enter the path to your media directory when prompted.
   - Example:

     ```
     Enter the path to your media directory: /path/to/your/media/files
     ```

### 2. Main Menu Options

After configuring settings, the main menu provides several options:

1. **Browse Media in Stored Directory:**
   - Navigate through your configured media directory.
   - Perform media info checks or edit MKV files.

2. **Check Media Info in a Custom Directory:**
   - Specify a different directory to check media information.

3. **Edit MKV Files:**
   - Access the MKV editing submenu to set audio and subtitle flags.

4. **Configure Settings:**
   - Modify your media directory or other settings.

5. **Exit:**
   - Close the application.

### 3. Navigating and Editing MKV Files

1. **Select "Edit MKV Files":**
   - From the main menu, choose the option to **Edit MKV Files** (e.g., option `3`).

2. **Directory Navigation Menu:**
   - **Options:**
     - **1-15:** Various operations related to setting audio and subtitle flags.
     - **0:** **Return to Main Menu**.
   
   - **Example Menu:**

     ```
     Options:
     1. Bulk set forced audio for files
     2. Bulk set forced subtitle for files
     ...
     14. Return to previous menu
     0. Return to main menu
     ```

3. **Perform Operations:**
   - Select the desired operation by entering the corresponding number.
   - For example, to bulk set forced audio for all MKV files, enter `1`.

4. **Return to Main Menu:**
   - At any point, select **option `0`** to return to the main menu.

### 4. Checking Media Information

1. **Select "Browse Media in Stored Directory" or "Check Media Info in a Custom Directory":**
   - Choose the appropriate option from the main menu.

2. **Media Info Menu:**
   - **Options:**
     - **1:** Check media info for a specific file.
     - **2:** Check media info for all files.
     - **3:** Return to previous directory.
     - **4:** Return to main menu.

3. **Viewing Media Info:**
   - Choose to check info for a specific file or all files.
   - Media information will be **displayed on the screen** and **saved** to the corresponding JSON file in the `json` directory.

### 5. Backup and Restore

- **Backup:**
  - Before making changes to the JSON data, a timestamped backup is automatically created.
  
- **Restore:**
  - From the **Edit MKV Files** menu, select the option to **Restore previous changes** if a backup exists.

## Directory Structure

```plaintext
MKVAudioSubtitleChanger/
│
├── mkvscripts/
│   ├── main.py
│   ├── mediainfo.py
│   ├── mkvdefaults.py
│   ├── directorynav.py
│   ├── common.py
│   ├── requirements.txt
│   └── json/                   # Directory where JSON files are stored
│
├── README.md
└── LICENSE
```

## Dependencies

The application relies on the following external Python packages:

- **[pymediainfo](https://pypi.org/project/pymediainfo/):**
  - **Purpose:** A Python wrapper for the MediaInfo library, used to extract media information from video and audio files.
  
- **[tqdm](https://pypi.org/project/tqdm/):**
  - **Purpose:** Provides progress bars for Python loops, enhancing the user experience by visualizing the progress of operations.

These dependencies are listed in the `requirements.txt` file and can be installed using `pip`.

## `requirements.txt`

For your convenience, here's the `requirements.txt` file containing all necessary Python packages:

```plaintext
pymediainfo==5.0.0
tqdm==4.64.0
```

*Note: The versions specified are examples. Adjust them based on your project's compatibility and testing.*

## Troubleshooting

### Common Issues

1. **`TypeError` When Selecting Browse Media:**
   - **Error Message:**
     ```
     TypeError: browse_directory.<locals>.<lambda>() missing 1 required positional argument: 'mkv_files'
     ```
   - **Cause:** Mismatch in the number of arguments expected by the lambda function in `mediainfo.py` and those provided by `directorynav.py`.
   - **Solution:** Ensure that the lambda function in `mediainfo.py` matches the expected signature.

2. **MediaInfo Library Not Found:**
   - **Symptom:** Errors related to the `pymediainfo` package not finding the MediaInfo library.
   - **Solution:** Verify that the MediaInfo library is installed and accessible in your system's PATH. Reinstall if necessary.

3. **No MKV Files Found:**
   - **Symptom:** The application logs indicate no MKV files are found in the specified directory.
   - **Solution:** Ensure that the media directory is correctly configured and contains MKV files.

### Debugging Tips

- **Enable Detailed Logging:**
  - The application uses the `logging` module to provide debug and error messages.
  - Review the logs to identify the source of issues.
  
- **Verify JSON Files:**
  - Check the `json` directory to ensure that JSON files are being created and updated correctly.
  
- **Check File Permissions:**
  - Ensure that the application has the necessary permissions to read from and write to the media and JSON directories.

## Contributing

Contributions are welcome! If you'd like to enhance the application, fix bugs, or add new features, please follow these steps:

1. **Fork the Repository:**
   - Click the "Fork" button at the top-right corner of the repository page.

2. **Create a New Branch:**
   - Navigate to your forked repository and create a new branch for your feature or bug fix.
   
   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes:**
   - Make your changes and commit them with clear messages.
   
   ```bash
   git commit -m "Add feature XYZ"
   ```

4. **Push to Your Fork:**
   
   ```bash
   git push ori# Easy-MKV-Bulk-Forced-Audio-or-Subtitle
There is a lot of options out there for setting default audio and subtitles for mkv files but they're all either command line, require you to know the track order, or can only be used for 1 mkv file at a time. Instead of guessing, this will allow anyone with at least a minor understanding of python to do it on there own.
gin feature/YourFeatureName
   ```

5. **Create a Pull Request:**
   - Navigate to the original repository and create a pull request from your forked branch.

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any questions, issues, or suggestions, please open an issue in the repository or contact [your-email@example.com](mailto:your-email@example.com).

---

*Thank you for using MKV Audio Subtitle Changer! We hope it enhances your media management experience.*
