from src.utils import detect_gpu, get_ffmpeg_path

def test_environment():
    print("Testing Environment...")
    ffmpeg = get_ffmpeg_path()
    if ffmpeg:
        print(f"[OK] FFmpeg found at: {ffmpeg}")
    else:
        print("[FAIL] FFmpeg NOT found.")
    
    gpu = detect_gpu()
    print(f"[OK] Detected GPU Encoder: {gpu}")

if __name__ == "__main__":
    test_environment()
