# MKV Audio Subtitle Changer

## Overview

**MKV Audio Subtitle Changer** is a Python-based application designed to simplify the management and editing of MKV (Matroska Video) files. This tool allows users to effortlessly set forced or default audio and subtitle tracks, extract and display detailed media information, and maintain organized JSON files for data persistence. With a user-friendly, menu-driven interface, navigating through directories and performing bulk or individual file operations becomes intuitive and efficient.

## Features

- **Bulk Operations:** Set forced or default flags for audio and subtitle tracks across multiple MKV files simultaneously.
- **Individual File Editing:** Modify audio and subtitle tracks for specific MKV files as needed.
- **Media Information Extraction:** Retrieve comprehensive media details using the `pymediainfo` library.
- **JSON Data Management:** Automatically save and backup media information in structured JSON files.
- **Directory Navigation:** Easily browse and navigate through directories containing MKV files with a clear, menu-driven interface.
- **Backup & Restore:** Create timestamped backups of JSON data and restore them when necessary.
- **Progress Visualization:** Utilize progress bars for tracking the processing status of multiple files.
- **Automatic Dependency Checking:** Ensure that `mkvpropedit` is installed, and attempt installation if missing.

## Prerequisites

Before installing and running the application, ensure that your system meets the following requirements:

- **Operating System:** Windows, macOS, or Linux.
- **Python Version:** Python 3.6 or higher.
- **MKVToolNix (`mkvpropedit`):** Used for editing MKV files.

## Installation

### 1. Clone the Repository

First, clone the repository to your local machine using Git:

```bash
git clone https://github.com/yourusername/MKV-Audio-Subtitle-Changer.git
cd MKV-Audio-Subtitle-Changer/mkvscripts
```

*Replace `yourusername` with your actual GitHub username.*

### 2. Install MKVToolNix (`mkvpropedit`)

The application requires `mkvpropedit` for editing MKV files.

- **Linux/macOS:**
  - The application will attempt to install `mkvpropedit` automatically if it's not found on your system.
- **Windows:**
  - Download and install `MKVToolNix` from the official website: [https://mkvtoolnix.download/downloads.html#windows](https://mkvtoolnix.download/downloads.html#windows)
  - Ensure that `mkvpropedit` is accessible in your system's PATH.

### 3. (Optional) Set Up a Python Virtual Environment

Creating a virtual environment is recommended to manage dependencies without affecting your global Python installation.

1. **Create a Virtual Environment:**

   ```bash
   python3 -m venv venv
   ```

2. **Activate the Virtual Environment:**

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

## Usage

### 1. Run the Application

Execute the `main.py` script to start the application:

```bash
python main.py
```

### 2. Automatic Dependency Checking

Upon running, the application will:

1. **Check for `mkvpropedit`:**
   - If `mkvpropedit` is **installed**, the application proceeds to the main menu.
   - If **not installed**:
     - **Linux/macOS:** The application will attempt to install `mkvpropedit` automatically using the appropriate package manager (`apt`, `pacman`, `dnf`, or `brew`).
     - **Windows:** You will be prompted to manually download and install `MKVToolNix` from [https://mkvtoolnix.download/downloads.html#windows](https://mkvtoolnix.download/downloads.html#windows).

2. **Proceed or Exit:**
   - **Successful Installation:** Continues to the main menu.
   - **Failed Installation or User Declines:** Logs an error and exits the application.

### 3. Main Menu Options

After ensuring all dependencies are met, the main menu provides several options:

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

### 4. Navigating and Editing MKV Files

1. **Select "Edit MKV Files":**
   - From the main menu, choose the option to **Edit MKV Files** (e.g., option `3`).

2. **MKV Editing Menu:**
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

### 5. Checking Media Information

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

### 6. Backup and Restore

- **Backup:**
  - Before making changes to the JSON data, a timestamped backup is automatically created.

- **Restore:**
  - From the **Edit MKV Files** menu, select the option to **Restore previous changes** if a backup exists.

## Directory Structure

```plaintext
MKV-Audio-Subtitle-Changer/
│
├── mkvscripts/
│   ├── main.py
│   ├── mediainfo.py
│   ├── mkvdefaults.py
│   ├── directorynav.py
│   ├── common.py
│   ├── installmkvpropedit.py
│   ├── requirements.txt
│   └── json/                   # Directory where JSON files are stored
│
├── README.md
└── LICENSE
```

## Dependencies

The application relies on the following external Python packages:

- **[pymediainfo](https://pypi.org/project/pymediainfo/):**
  - **Purpose:** A Python wrapper for the MediaInfo library, used to extract detailed media information from video and audio files.
  - **Note:** `pymediainfo` does not require installing the MediaInfo library separately.

- **[tqdm](https://pypi.org/project/tqdm/):**
  - **Purpose:** Provides progress bars for Python loops and processes, enhancing user experience by visualizing operation progress.

- **[distro](https://pypi.org/project/distro/):**
  - **Purpose:** Detects the Linux distribution, enabling OS-specific installation commands for dependencies like `mkvpropedit`.

These dependencies are listed in the `requirements.txt` file and can be installed using `pip`.

### `requirements.txt`

```plaintext
distro==1.9.0
pymediainfo==6.1.0
tqdm==4.66.5
```

*Note: Adjust the versions based on your project's compatibility and testing.*

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
     git push origin feature/YourFeatureName
     ```

5. **Create a Pull Request:**
   - Navigate to the original repository and create a pull request from your forked branch.

## License

This project is licensed under the [GNU General Public License v3.0](LICENSE).

## Contact

For any questions, issues, or suggestions, please open an issue in the repository.

---

*Thank you for using MKV Audio Subtitle Changer! We hope it enhances your media management experience.*
