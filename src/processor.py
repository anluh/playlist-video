import os
import subprocess
import logging
from PySide6.QtCore import QThread, Signal

class RenderThread(QThread):
    progress_update = Signal(str)
    progress_value = Signal(int)       # Current Task (0-100)
    progress_batch = Signal(int)       # Batch Progress (0-100)
    finished = Signal(bool, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_running = True

    def run(self):
        mode = self.settings.get('mode', 'single') # 'single' or 'batch'
        gpu_encoder = self.settings.get('gpu_encoder', 'libx264')
        separate_files = self.settings.get('separate_files', False)
        playlist_repeat = self.settings.get('playlist_repeat', 1)
        
        try:
            if mode == 'batch':
                batch_root = self.settings.get('batch_root')
                output_root = self.settings.get('output_path') # In batch mode, this is a folder
                self._run_batch_mode(batch_root, output_root, gpu_encoder, separate_files, playlist_repeat)
            else:
                # Single Mode
                output_path = self.settings.get('output_path')
                video_path = self.settings.get('video_path')
                audio_paths = self.settings.get('audio_paths')
                
                if not audio_paths:
                    self.finished.emit(False, "No audio files selected.")
                    return

                if separate_files:
                    # In single mode, output_path is a Folder if separate_files is True
                    # Repeat not supported in separate files mode
                    self._render_separate(output_path, video_path, audio_paths, gpu_encoder)
                else:
                    # In single mode, output_path is a File
                    self._render_single(output_path, video_path, audio_paths, gpu_encoder, repeat_count=playlist_repeat)

        except Exception as e:
            self.finished.emit(False, str(e))

    def _run_batch_mode(self, batch_root, output_root, gpu_encoder, separate_files, repeat_count):
        # Scan Input Folders
        subfolders = [f.path for f in os.scandir(batch_root) if f.is_dir()]
        total_folders = len(subfolders)
        
        if total_folders == 0:
            self.finished.emit(False, "No subfolders found in the selected batch root.")
            return

        video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
        audio_exts = ('.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg')

        success_count = 0
        
        for i, folder in enumerate(subfolders):
            folder_name = os.path.basename(folder)
            self.progress_update.emit(f"Processing Folder {i+1}/{total_folders}: {folder_name}")
            self.progress_batch.emit(int(((i) / total_folders) * 100)) # Start of this folder
            
            # Discovery
            video_path = None
            audio_paths = []
            
            for root, dirs, files in os.walk(folder):
                for f in files:
                    f_lower = f.lower()
                    path = os.path.join(root, f)
                    if not video_path and f_lower.endswith(video_exts):
                        video_path = path
                    elif f_lower.endswith(audio_exts):
                        audio_paths.append(path)
            
            if not video_path:
                self.progress_update.emit(f"Skipping {folder_name}: No video found.")
                continue
            if not audio_paths:
                self.progress_update.emit(f"Skipping {folder_name}: No audio found.")
                continue
            
            # Sort Audio
            audio_paths.sort(key=lambda p: os.path.basename(p).lower())
            
            # Process
            if separate_files:
                # Create subfolder in output for this project
                project_out_dir = os.path.join(output_root, folder_name)
                os.makedirs(project_out_dir, exist_ok=True)
                
                # Render Separate Tracks
                self._render_separate(project_out_dir, video_path, audio_paths, gpu_encoder, batch_prefix=f"[{i+1}/{total_folders}] ")
            else:
                # Combined Mode -> One file named FolderName.mp4
                output_file = os.path.join(output_root, f"{folder_name}.mp4")
                # For combined mode, this single file represents 100% of the CURRENT task
                # Passed repeat_count
                self._render_single(output_file, video_path, audio_paths, gpu_encoder, batch_mode=True, progress_scale=100, repeat_count=repeat_count)
            
            success_count += 1
            
        self.progress_batch.emit(100)
        self.finished.emit(True, f"Batch Processing Complete! Processed {success_count}/{total_folders} folders.")

    def _run_ffmpeg(self, cmd, total_duration=None, progress_offset=0, progress_scale=100):
        # Startup info to hide console window
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            startupinfo=startupinfo
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # Parse time=00:00:00.00
                if total_duration and "time=" in line:
                    try:
                        # Extract time string
                        idx = line.find("time=")
                        time_str = line[idx+5:idx+16] # 00:00:00.00
                        # Convert to seconds
                        h, m, s = time_str.split(':')
                        current_seconds = float(h) * 3600 + float(m) * 60 + float(s)
                        
                        relative_percent = (current_seconds / total_duration) * 100
                        relative_percent = min(max(relative_percent, 0), 100)
                        
                        # Scale to global progress
                        # global = offset + (relative * scale / 100)
                        final_percent = progress_offset + (relative_percent * progress_scale / 100)
                        self.progress_value.emit(int(final_percent))
                    except:
                        pass
        
        return process.returncode == 0

    def _render_separate(self, output_dir, video_path, audio_paths, gpu_encoder, batch_prefix=""):
        from src.utils import get_media_duration
        
        total_tracks = len(audio_paths)
        # We divide the 100% progress bar into chunks for each track
        chunk_size = 100 / total_tracks
        
        for i, audio_path in enumerate(audio_paths):
            track_name = os.path.splitext(os.path.basename(audio_path))[0]
            track_name_safe = "".join([c for c in track_name if c not in '<>:"/\\|?*']).strip()
            
            output_file = os.path.join(output_dir, f"{track_name_safe}.mp4")
            
            self.progress_update.emit(f"{batch_prefix}Rendering track {i+1}/{total_tracks}: {track_name}...")
            
            # Get duration for progress calc
            duration = get_media_duration(audio_path)
            
            cmd = ['ffmpeg', '-y']
            cmd.extend(['-stream_loop', '-1', '-i', video_path])
            cmd.extend(['-i', audio_path])
            cmd.extend(['-map', '0:v', '-map', '1:a'])
            
            if 'nvenc' in gpu_encoder:
                cmd.extend(['-c:v', gpu_encoder, '-preset', 'p4', '-tune', 'hq'])
            elif 'amf' in gpu_encoder:
                cmd.extend(['-c:v', gpu_encoder, '-quality', 'balanced'])
            else:
                cmd.extend(['-c:v', 'libx264', '-preset', 'medium'])
                
            cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
            cmd.extend(['-shortest'])
            cmd.append(output_file)
            
            # Pass duration and offsets to run_ffmpeg
            current_offset = i * chunk_size
            self._run_ffmpeg(cmd, total_duration=duration, progress_offset=current_offset, progress_scale=chunk_size)

    def _render_single(self, output_path, video_path, audio_paths, gpu_encoder, batch_mode=False, progress_offset=0, progress_scale=100, repeat_count=1):
        from src.utils import get_media_duration
        
        # Apply Repetition
        final_audio_paths = []
        for _ in range(repeat_count):
            final_audio_paths.extend(audio_paths)
        
        # Calculate total duration for progress
        total_duration = 0
        for p in final_audio_paths:
            d = get_media_duration(p)
            if d: total_duration += d

        # Construct FFmpeg command
        cmd = ['ffmpeg', '-y']
        
        # Input 0: Video (Looped)
        cmd.extend(['-stream_loop', '-1', '-i', video_path])
        
        # Inputs 1..N: Audio files (Multiplied)
        for audio in final_audio_paths:
            cmd.extend(['-i', audio])
        
        # Build Filter Complex
        filter_complex = []
        
        # Audio Concatenation
        # Note: Input 0 is video. Audio inputs start at 1.
        audio_inputs = "".join([f"[{i+1}:a]" for i in range(len(final_audio_paths))])
        filter_complex.append(f"{audio_inputs}concat=n={len(final_audio_paths)}:v=0:a=1[outa]")
        
        # Map video and audio
        cmd.extend(['-filter_complex', ";".join(filter_complex)])
        cmd.extend(['-map', '0:v', '-map', '[outa]'])
        
        # Encoding settings
        if 'nvenc' in gpu_encoder:
            cmd.extend(['-c:v', gpu_encoder, '-preset', 'p4', '-tune', 'hq'])
        elif 'amf' in gpu_encoder:
            cmd.extend(['-c:v', gpu_encoder, '-quality', 'balanced'])
        else:
            cmd.extend(['-c:v', 'libx264', '-preset', 'medium'])
            
        cmd.extend(['-c:a', 'aac', '-b:a', '192k'])
        
        # Cut video to shortest stream
        cmd.extend(['-shortest'])
        
        # Output
        cmd.append(output_path)
        
        log_msg = f"Starting render: {os.path.basename(output_path)}"
        self.progress_update.emit(log_msg)
        
        success = self._run_ffmpeg(cmd, total_duration=total_duration, progress_offset=progress_offset, progress_scale=progress_scale)
        
        if success:
            # Create the Track List Text File
            # Only list the unique tracks (1 iteration), not the repeats
            self._create_tracklist(output_path, audio_paths)
            if not batch_mode:
                self.progress_value.emit(100)
                self.finished.emit(True, "Render Complete!")
        else:
            if not batch_mode:
                self.finished.emit(False, "FFmpeg validation failed.")
            else:
                self.progress_update.emit(f"Failed to render: {os.path.basename(output_path)}")


    def _create_tracklist(self, output_video_path, audio_paths):
        """Creates a timestamped text file next to the video."""
        from src.utils import get_media_duration
        
        txt_path = os.path.splitext(output_video_path)[0] + ".txt"
        current_time = 0.0
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            for path in audio_paths:
                name = os.path.basename(path)
                # Format MM:SS or HH:MM:SS
                m, s = divmod(int(current_time), 60)
                h, m = divmod(m, 60)
                if h > 0:
                    time_str = f"{h:02d}:{m:02d}:{s:02d}"
                else:
                    time_str = f"{m:02d}:{s:02d}"
                
                f.write(f"{time_str} - {name}\n")
                
                duration = get_media_duration(path)
                if duration:
                    current_time += duration
