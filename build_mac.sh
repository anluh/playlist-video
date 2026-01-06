#!/bin/bash

# Build Script for macOS (Apple Silicon & Intel)
# Requires: python3, ffmpeg

echo "=== Building Loop Video Generator for macOS ==="

# 1. Create Virtual Environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# 2. Activate Virtual Environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 3. Install Dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller Pillow

# 4. Icon Conversion (SVG -> ICNS)
# macOS apps use .icns. We'll use a simple png fallback or try to make .icns if possible.
# For simplicity in this script, we will assume the SVG is sufficient or use a PNG for the internal icon.
# PyInstaller on Mac can handle .icns or .png often.

# 5. Build with PyInstaller
# Note: --windowed (noconsole) is preferred on Mac.

echo "Running PyInstaller..."
pyinstaller --noconsole --onefile --windowed \
            --name "LoopVideoGenerator" \
            --add-data "src/icons:src/icons" \
            --icon "src/icons/loop_app_icon.png" \
            main.py

# 6. Deactivate Virtual Environment
deactivate

echo ""
echo "Build complete! Check the 'dist' folder."
echo "You may need to grant permissions to the app in System Settings > Privacy & Security."
