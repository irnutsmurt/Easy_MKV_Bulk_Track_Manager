# installmkvpropedit.py

import shutil
import subprocess
import platform
import logging

# Try to import 'distro' for Linux distribution detection
try:
    import distro
except ImportError:
    distro = None

def is_mkvpropedit_installed():
    """Check if mkvpropedit is installed."""
    return shutil.which("mkvpropedit") is not None

def install_mkvtoolnix():
    """Attempt to install MKVToolNix based on the detected OS."""
    os_type = platform.system()

    if os_type == "Linux":
        if not distro:
            logging.error("The 'distro' package is required to detect Linux distributions.")
            logging.info("Please install 'distro' via 'pip install distro' and rerun the script.")
            return False
        distro_name = distro.id().lower()

        try:
            if "ubuntu" in distro_name or "debian" in distro_name:
                logging.info("Installing MKVToolNix on Ubuntu/Debian...")
                subprocess.run(["sudo", "apt", "update"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", "mkvtoolnix"], check=True)

            elif "arch" in distro_name:
                logging.info("Installing MKVToolNix on Arch Linux...")
                subprocess.run(["sudo", "pacman", "-S", "--noconfirm", "mkvtoolnix-cli"], check=True)

            elif "fedora" in distro_name or "redhat" in distro_name:
                logging.info("Installing MKVToolNix on Fedora/Red Hat...")
                subprocess.run(["sudo", "dnf", "install", "-y", "mkvtoolnix"], check=True)

            else:
                logging.error(f"Unsupported Linux distribution: {distro_name}. Please install MKVToolNix manually.")
                return False

        except subprocess.CalledProcessError as e:
            logging.error(f"Installation failed: {e}")
            return False

    elif os_type == "Darwin":
        logging.info("Installing MKVToolNix on macOS...")
        try:
            subprocess.run(["brew", "install", "mkvtoolnix"], check=True)
        except subprocess.CalledProcessError:
            logging.error("Homebrew not found. Please install Homebrew and try again.")
            return False

    elif os_type == "Windows":
        logging.info("Please download and install MKVToolNix from the official website: https://mkvtoolnix.download/downloads.html#windows")
        return False  # Cannot automate installation on Windows securely

    else:
        logging.error(f"Unsupported operating system: {os_type}. Please install MKVToolNix manually.")
        return False

    return is_mkvpropedit_installed()

def ensure_mkvpropedit_installed():
    """Ensure mkvpropedit is installed, otherwise prompt for installation."""
    if not is_mkvpropedit_installed():
        logging.info("The mkvpropedit tool is required but not installed.")
        install_choice = input("Would you like to attempt to install MKVToolNix now? (y/n): ").strip().lower()

        if install_choice == 'y':
            success = install_mkvtoolnix()
            if success:
                logging.info("MKVToolNix installed successfully.")
                return True
            else:
                logging.error("Failed to install MKVToolNix. Please install it manually and rerun the script.")
                return False
        else:
            logging.error("MKVToolNix is required to proceed. Exiting.")
            return False
    else:
        logging.debug("MKVToolNix (mkvpropedit) is installed and ready to use.")
        return True
