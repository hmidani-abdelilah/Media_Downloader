#!/bin/bash

# -----------------------------------------------------------------------------
# Project: Media_Downloader
# Description: Professional installer script - installs dependencies from requirements.txt and sets up the application icon
# Author: Abdelilah Hmidani
# -----------------------------------------------------------------------------

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== Starting Media Downloader installation ===${NC}"

print_usage() {
    cat <<EOF
Usage: sudo ./installer.sh [OPTIONS]

Options:
  install             Install Media Downloader (default action)
  uninstall           Remove Media Downloader installation
  --uninstall         Alias for uninstall
  -h, --help          Show this help message and exit

Examples:
  sudo ./installer.sh
  sudo ./installer.sh uninstall
  sudo ./installer.sh --help
EOF
}

if [[ "$1" == "-h" || "$1" == "--help" || "$1" == "help" ]]; then
    print_usage
    exit 0
fi

# 1. Ensure script is run with sudo/root to install system packages
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}[ ERROR ] Please run the script as root (sudo ./installer.sh)${NC}"
    exit 1
fi

# Determine the real user to avoid permission issues with Python files and venv
REAL_USER=${SUDO_USER:-$USER}
USER_HOME=$(eval echo ~$REAL_USER)
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"



# Uninstall support
if [[ "$1" == "uninstall" || "$1" == "--uninstall" ]]; then
    DESKTOP_FILE="/usr/share/applications/media-downloader.desktop"
    APP_DIR="$CURRENT_DIR/Media_Downloader"
    VENV_DIR="$APP_DIR/venv"

    echo -e "${BLUE}[ UNINSTALL ] Removing Media Downloader installation...${NC}"

    if [ -f "$DESKTOP_FILE" ]; then
        rm -f "$DESKTOP_FILE"
        echo -e "${BLUE}[ UNINSTALL ] Removed desktop entry: $DESKTOP_FILE${NC}"
    else
        echo -e "${YELLOW}[ UNINSTALL ] Desktop entry not found: $DESKTOP_FILE${NC}"
    fi

    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
        echo -e "${BLUE}[ UNINSTALL ] Removed virtual environment: $VENV_DIR${NC}"
    else
        echo -e "${YELLOW}[ UNINSTALL ] Virtual environment not found: $VENV_DIR${NC}"
    fi

    if [ -d "$APP_DIR" ]; then
        rm -rf "$APP_DIR"
        echo -e "${BLUE}[ UNINSTALL ] Removed application directory: $APP_DIR${NC}"
    else
        echo -e "${YELLOW}[ UNINSTALL ] Application directory not found: $APP_DIR${NC}"
    fi

    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database /usr/share/applications
    fi

    echo -e "${GREEN}[ SUCCESS ] Uninstallation completed.${NC}"
    exit 0
fi

if [ -n "$1" ] && [[ "$1" != "install" ]]; then
    echo -e "${RED}[ ERROR ] Unknown option: $1${NC}"
    print_usage
    exit 1
fi

# 2. Detect distribution and install Python3 and FFmpeg
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    LIKE=$ID_LIKE
else
    echo -e "${RED}[ ERROR ] Unable to detect the operating system.${NC}"
    exit 1
fi

install_system_deps() {
    case "$OS" in
        ubuntu|debian|kali|raspbian|linuxmint)
            echo -e "${BLUE}[ INSTALL ] Updating packages and installing python3-venv and ffmpeg...${NC}"
            apt update -y
            apt install -y python3 python3-pip python3-venv ffmpeg git
            ;;
        fedora)
            echo -e "${BLUE}[ INSTALL ] Installing python3 and ffmpeg via DNF...${NC}"
            dnf install -y python3 python3-pip ffmpeg git
            ;;
        rhel|centos|rocky|almalinux)
            echo -e "${BLUE}[ INSTALL ] Enabling EPEL repository and installing dependencies...${NC}"
            if [ "$OS" != "fedora" ]; then
                dnf install -y epel-release || yum install -y epel-release
            fi
            dnf install -y python3 python3-pip ffmpeg git || yum install -y python3 python3-pip ffmpeg git
            ;;
        arch|manjaro|endeavouros|garuda)
            echo -e "${BLUE}[ INSTALL ] Updating repositories and installing python and ffmpeg via Pacman...${NC}"
            pacman -Sy --noconfirm --needed python python-pip ffmpeg git
            ;;
        *)
            if [[ "$LIKE" == *"arch"* ]]; then
                pacman -Sy --noconfirm --needed python python-pip ffmpeg git
            elif [[ "$LIKE" == *"debian"* || "$LIKE" == *"ubuntu"* ]]; then
                apt update -y && apt install -y python3 python3-pip python3-venv ffmpeg git
            elif [[ "$LIKE" == *"rhel"* || "$LIKE" == *"fedora"* ]]; then
                dnf install -y python3 python3-pip ffmpeg git || yum install -y python3 python3-pip ffmpeg git
            else
                echo -e "${RED}[ WARNING ] Distribution not automatically supported, please install Python and ffmpeg manually.${NC}"
            fi
            ;;
    esac
}
#change to current directory
CURRENT_DIR="$(dirname "${BASH_SOURCE[0]}")"

# clone repository and navigate to it
if [ ! -d "Media_Downloader" ]; then
    echo -e "${BLUE}[ CLONE ] Cloning the Media_Downloader repository...${NC}"
    cd "$CURRENT_DIR"
    su - "$REAL_USER" -c "git clone https://github.com/hmidani-abdelilah/Media_Downloader.git $(pwd)/Media_Downloader"
    cd Media_Downloader
else
    echo -e "${BLUE}[ INFO ] Media_Downloader directory already exists, updating repository...${NC}"
    cd Media_Downloader
    su - "$REAL_USER" -c "cd $(pwd) && git pull origin main"
fi

# Install system dependencies (Python3, pip, ffmpeg) based on the detected distribution
install_system_deps

# 3. Set up the virtual environment and install requirements.txt
APP_DIR="$(pwd)"
VENV_DIR="$APP_DIR/venv"
REQ_FILE="$APP_DIR/requirements.txt"

if [ ! -f "$REQ_FILE" ]; then
    echo -e "${RED}[ ERROR ] requirements.txt not found in the project folder!${NC}"
    exit 1
fi

echo -e "${BLUE}[ SETUP ] Creating the Python virtual environment...${NC}"
# Create the virtual environment as the normal user to avoid permission issues
su - "$REAL_USER" -c "python3 -m venv $VENV_DIR"

echo -e "${BLUE}[ INSTALL ] Installing dependencies from requirements.txt...${NC}"
# Activate the environment and install actual repository dependencies as the normal user
su - "$REAL_USER" -c "$VENV_DIR/bin/pip install --upgrade pip"
su - "$REAL_USER" -c "$VENV_DIR/bin/pip install -r $REQ_FILE"


# pause for testing
# if [ -n "$DISPLAY" ]; then
#     read -n 1 -s -r -p "Press any key to continue with system dependencies installation..."
#     echo
#     echo -e "${BLUE}[ TEST ] Running the GUI application for a quick display test...${NC}"
#     su - "$REAL_USER" -c "DISPLAY=$DISPLAY $VENV_DIR/bin/python3 $APP_DIR/app.py"
# else
#     echo -e "${YELLOW}[ SKIP ] No DISPLAY available; skipping GUI test run.${NC}"
# fi


# 4. Configure the icon path and main script
MAIN_SCRIPT="$APP_DIR/app.py"

# Check repository icon (logo.png or icon.png or use system icon fallback)
if [ -f "$APP_DIR/logo.png" ]; then
    ICON_PATH="$APP_DIR/logo.png"
elif [ -f "$APP_DIR/icon.png" ]; then
    ICON_PATH="$APP_DIR/icon.png"
else
    ICON_PATH="video-player" # default system icon when no icon file exists
fi

# 5. Create and install the Desktop entry (.desktop)
DESKTOP_FILE="/usr/share/applications/media-downloader.desktop"
echo -e "${BLUE}[ SETUP ] Creating desktop entry at $DESKTOP_FILE...${NC}"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Downloader
Comment=Download videos and audio from the internet using CustomTkinter & yt-dlp
Exec="$VENV_DIR/bin/python3" "$MAIN_SCRIPT"
Icon=$ICON_PATH
Terminal=false
Categories=Network;Utility;
StartupNotify=true
EOF

# Set permissions for the shortcut file so it appears in the menu immediately
chmod 644 "$DESKTOP_FILE"

# update desktop database to recognize the new entry (optional but can help with some desktop environments)
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database /usr/share/applications
fi


echo -e "${GREEN}[ SUCCESS ] Installation completed successfully! requirements.txt was installed and the icon was configured.${NC}"
