#!/bin/bash

# Build Script for macOS (Apple Silicon & Intel)
# Requires: python3, ffmpeg

echo "=== Building Loop Video Generator for macOS ==="

# 1. Install Dependencies
echo "Installing dependencies..."
pip3 install -r requirements.txt
pip3 install pyinstaller Pillow

# 2. Icon Conversion (SVG -> ICNS)
# macOS apps use .icns. We'll use a simple png fallback or try to make .icns if possible.
# For simplicity in this script, we will assume the SVG is sufficient or use a PNG for the internal icon.
# PyInstaller on Mac can handle .icns or .png often.

# 3. Build with PyInstaller
# Note: --windowed (noconsole) is preferred on Mac.

echo "Running PyInstaller..."
pyinstaller --noconsole --onefile --windowed \
            --name "LoopVideoGenerator" \
            --add-data "src/icons:src/icons" \
            --icon "src/icons/loop_app_icon.svg" \
            main.py

echo "Build complete! Check the 'dist' folder."
echo "You may need to grant permissions to the app in System Settings > Privacy & Security."
