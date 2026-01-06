Loop Video Generator - macOS Instructions
=======================================

Building from Source
--------------------
Since this app was developed on Windows, you will need to build the Mac executable yourself using the provided script.

1.  **Prerequisites**:
    -   Python 3.10+ installed.
    -   FFmpeg installed (e.g., `brew install ffmpeg`).

2.  **Build**:
    Open a terminal in this directory and run:
    ```bash
    chmod +x build_mac.sh
    ./build_mac.sh
    ```

3.  **Run**:
    The app will be in the `dist` folder.
    -   You might see a "Unidentified Developer" warning.
    -   Go to **System Settings > Privacy & Security** and click "Open Anyway".

Hardware Acceleration
---------------------
The app supports `h264_videotoolbox` for fast hardware encoding on Apple Silicon (M1/M2/M3) and Intel Macs. Select "Auto-Detect" or "Apple Silicon" in the dropdown.
