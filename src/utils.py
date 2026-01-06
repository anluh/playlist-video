import shutil
import subprocess
import json
import logging
import platform

def get_ffmpeg_path():
    """Check if ffmpeg is available in system PATH."""
    return shutil.which("ffmpeg")

def get_ffprobe_path():
    """Check if ffprobe is available in system PATH."""
    return shutil.which("ffprobe")

def get_media_duration(file_path):
    """
    Get the duration of a media file using ffprobe.
    Returns float duration in seconds, or None if failed.
    """
    ffprobe = get_ffprobe_path()
    if not ffprobe:
        logging.error("ffprobe not found.")
        return None

    try:
        cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            file_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except Exception as e:
        logging.error(f"Error getting duration for {file_path}: {e}")
        return None

def detect_gpu():
    """
    Detects available hardware acceleration methods for FFmpeg.
    Returns a preferred video codec string for FFmpeg (e.g., 'h264_nvenc', 'h264_amf', or 'libx264').
    """
    system = platform.system()
    if system != "Windows":
        return "libx264" # Fallback for non-windows for this MVP

    try:
        import wmi
        w = wmi.WMI()
        for gpu in w.Win32_VideoController():
            name = gpu.Name.lower()
            if "nvidia" in name:
                # Check if ffmpeg supports nvenc
                if _check_encoder("h264_nvenc"):
                    return "h264_nvenc"
            elif "amd" in name or "radeon" in name:
                if _check_encoder("h264_amf"):
                    return "h264_amf"
            elif "intel" in name:
                if _check_encoder("h264_qsv"):
                    return "h264_qsv"
    except ImportError:
        logging.warning("WMI module not found, skipping detailed GPU check.")
    except Exception as e:
        logging.error(f"GPU detection failed: {e}")

    return "libx264"

def _check_encoder(encoder_name):
    """Verifies if the local FFmpeg supports the given encoder."""
    ffmpeg = get_ffmpeg_path()
    if not ffmpeg:
        return False
    
    try:
        # ffmpeg -encoders
        cmd = [ffmpeg, "-v", "error", "-encoders"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return encoder_name in result.stdout
    except:
        return False
