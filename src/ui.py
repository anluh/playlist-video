
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QListWidget, QLabel, QFileDialog, 
    QMessageBox, QProgressBar, QAbstractItemView,
    QFrame, QComboBox, QCheckBox, QTabWidget, QLineEdit, QSpinBox,
    QSizePolicy, QGridLayout, QStyleOption, QStyle
)
from PySide6.QtCore import Qt, QMimeData, Signal, QSize
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont, QPainter, QColor, QPen, QIcon
from src.utils import detect_gpu
from src.processor import RenderThread

# === MATERIAL DESIGN STYLESHEET ===
STYLESHEET = """
    QMainWindow { background-color: #121212; color: #E0E0E0; font-family: 'Segoe UI', sans-serif; }
    
    /* Typography */
    QLabel { color: #E0E0E0; font-size: 13px; }
    QLabel#header { font-size: 15px; font-weight: bold; color: #FFFFFF; }
    QLabel#caption { font-size: 11px; color: #9E9E9E; }
    
    /* Cards */
    QFrame#card { 
        background-color: #1E1E1E; 
        border-radius: 8px; 
        border: 1px solid #333333; 
    }
    
    /* Tabs */
    QTabWidget::pane { border: none; }
    QTabBar::tab { 
        background: transparent; 
        color: #9E9E9E; 
        padding: 8px 16px; 
        font-size: 13px;
        font-weight: 500;
        border-bottom: 2px solid transparent;
    }
    QTabBar::tab:selected { 
        color: #4285F4; 
        border-bottom: 2px solid #4285F4; 
    }
    QTabBar::tab:hover { color: #E0E0E0; }
    
    /* Inputs */
    QLineEdit, QComboBox, QSpinBox {
        background-color: #2C2C2C;
        border: 1px solid #444;
        border-radius: 4px;
        padding: 5px 10px;
        color: #FFF;
        font-size: 13px;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #4285F4;
    }

    /* ComboBox */
    QComboBox {
        padding-right: 20px;
    }
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 25px;
        border-left: 1px solid #444;
        border-top-right-radius: 4px;
        border-bottom-right-radius: 4px;
        background-color: #333;
    }
    QComboBox::down-arrow {
        image: url({icon_arrow_down});
        width: 14px; height: 14px;
    }

    /* SpinBox */
    QSpinBox {
        padding-right: 15px;
    }
    QSpinBox:focus {
        border: 1px solid #444;
    }
    QSpinBox:disabled {
        background-color: #202020;
        color: #555;
        border: 1px solid #333;
    }
    QSpinBox::up-button {
        subcontrol-origin: border;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #444;
        border-bottom: 1px solid #444;
        background-color: #333;
        border-top-right-radius: 4px;
    }
    QSpinBox::down-button {
        subcontrol-origin: border;
        subcontrol-position: bottom right;
        width: 20px;
        border-left: 1px solid #444;
        background-color: #333;
        border-bottom-right-radius: 4px;
        border-top: none;
    }
    QSpinBox::up-button:hover, QSpinBox::down-button:hover {
        background-color: #444;
    }
    QSpinBox::up-arrow {
        image: url({icon_arrow_up});
        width: 10px; height: 10px;
    }
    QSpinBox::down-arrow {
        image: url({icon_arrow_down});
        width: 10px; height: 10px;
    }

    /* Checkbox */
    QCheckBox { 
        color: #E0E0E0; 
        spacing: 8px; 
        font-size: 15px; /* Bigger Text */
    }
    QCheckBox::indicator { 
        width: 20px; height: 20px; /* Bigger Box */
    }
    QCheckBox::indicator:unchecked {
        image: url({icon_check_unchecked});
    }
    QCheckBox::indicator:checked { 
        image: url({icon_check_checked});
    }
    /* Buttons */
    QPushButton {
        background-color: #333;
        color: #E0E0E0;
        border-radius: 4px;
        padding: 6px 14px;
        font-weight: 500;
        border: none;
    }
    QPushButton:hover { background-color: #444; }
    
    /* Action Buttons (Primary) */
    QPushButton#primary {
        background-color: #4285F4;
        color: #FFF;
    }
    QPushButton#primary:hover { background-color: #5B95F5; }
    
    /* Header Tool Buttons */
    QPushButton#tool {
        background-color: transparent;
        color: #8AB4F8;
        border: 1px solid #334;
        padding: 4px 10px;
    }
    QPushButton#tool:hover { background-color: #2D3A4B; }
    
    /* Render Button (Success) */
    QPushButton#success {
        background-color: #0F9D58;
        color: #FFF;
        font-weight: bold;
        font-size: 14px;
        border-radius: 6px;
    }
    QPushButton#success:hover { background-color: #13B264; }
    QPushButton#success:disabled { background-color: #333; color: #777; }
    
    /* Progress Bar */
    QProgressBar {
        border: none;
        background-color: #333;
        border-radius: 4px;
        height: 6px;
        text-align: center;
        color: transparent; 
    }
    QProgressBar::chunk {
        background-color: #4285F4;
        border-radius: 4px;
    }
"""

class FileListWidget(QListWidget):
    """Custom ListWidget to handle file drops."""
    files_dropped = Signal(list)
    video_dropped = Signal(str)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        # Default dashed style
        self.setStyleSheet("""
            QListWidget { 
                background-color: #1E1E1E; 
                border: 2px dashed #444; 
                border-radius: 6px; 
                color: #E0E0E0; 
                outline: 0;
            }
            QListWidget::item { padding: 8px; border-radius: 4px; background: #252525; margin: 2px; }
            QListWidget::item:selected { background-color: #3D4C63; color: #8AB4F8; }
            QListWidget::item:focus { outline: none; }
        """)

    def set_solid_style(self):
        self.setStyleSheet("""
            QListWidget { 
                background-color: #1E1E1E; 
                border: 1px solid #333; 
                border-radius: 6px; 
                color: #E0E0E0; 
                outline: 0;
            }
            QListWidget::item { padding: 8px; border-radius: 4px; background: #252525; margin: 2px; }
            QListWidget::item:selected { background-color: #3D4C63; color: #8AB4F8; }
            QListWidget::item:focus { outline: none; }
        """)

    def set_dashed_style(self):
        self.setStyleSheet("""
            QListWidget { 
                background-color: #1E1E1E; 
                border: 2px dashed #444; 
                border-radius: 6px; 
                color: #E0E0E0; 
                outline: 0;
            }
            QListWidget::item { padding: 8px; border-radius: 4px; background: #252525; margin: 2px; }
            QListWidget::item:selected { background-color: #3D4C63; color: #8AB4F8; }
            QListWidget::item:focus { outline: none; }
        """)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.count() == 0:
            painter = QPainter(self.viewport())
            painter.setPen(QPen(QColor("#666"), 1))
            painter.setFont(QFont("Segoe UI", 12))
            text = "Drag & Drop Audio/Video Files Here"
            
            # Center Text
            rect = self.viewport().rect()
            painter.drawText(rect, Qt.AlignCenter, text)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
            
            audio_files = []
            found_video = None
            
            video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
            audio_exts = ('.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg')

            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    # Recurse directory
                    for root, dirs, filenames in os.walk(path):
                        for f in filenames:
                            f_lower = f.lower()
                            full_path = os.path.join(root, f)
                            if f_lower.endswith(audio_exts):
                                audio_files.append(full_path)
                            elif f_lower.endswith(video_exts) and not found_video:
                                found_video = full_path
                else:
                    path_lower = path.lower()
                    if path_lower.endswith(audio_exts):
                        audio_files.append(path)
                    elif path_lower.endswith(video_exts) and not found_video:
                        found_video = path
            
            if found_video:
                self.video_dropped.emit(found_video)

            if audio_files:
                self.files_dropped.emit(audio_files)
        else:
            super().dropEvent(event)

class DropLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setPlaceholderText("C:/Path/To/Root/Folder (Drop Here)")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.setDropAction(Qt.CopyAction)
            event.accept()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                path = urls[0].toLocalFile()
                if os.path.isdir(path):
                    self.setText(path)
                    event.accept()
        else:
            super().dropEvent(event)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Loop Video Playlist Generator")
        self.resize(850, 650)
        
        # Resolve Icons
        icon_dir = os.path.join(os.path.dirname(__file__), 'icons')
        # Ensure forward slashes for Qt
        icon_dir = icon_dir.replace('\\', '/')
        
        icon_arrow_down = f"{icon_dir}/arrow_down.svg"
        icon_arrow_up = f"{icon_dir}/arrow_up.svg"
        icon_check_checked = f"{icon_dir}/check_checked.svg"
        icon_check_unchecked = f"{icon_dir}/check_unchecked.svg"
        
        self.setWindowIcon(QIcon(f"{icon_dir}/loop_app_icon.svg"))
        
        formatted_style = STYLESHEET.replace("{icon_arrow_down}", icon_arrow_down) \
                                    .replace("{icon_arrow_up}", icon_arrow_up) \
                                    .replace("{icon_check_checked}", icon_check_checked) \
                                    .replace("{icon_check_unchecked}", icon_check_unchecked)
        
        self.setStyleSheet(formatted_style)
        
        # Single Mode Data
        self.video_path = None
        self.audio_files = []
        
        # UI Setup
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.tabBar().setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.tabs)
        
        # Tab 1: Single Folder
        self.tab_single = QWidget()
        self.init_single_tab()
        self.tabs.addTab(self.tab_single, "SINGLE FOLDER")
        
        # Tab 2: Multi Folder
        self.tab_batch = QWidget()
        self.init_batch_tab()
        self.tabs.addTab(self.tab_batch, "MULTI FOLDER")
        
        # === SETTINGS CARD ===
        settings_card = QFrame()
        settings_card.setObjectName("card")
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setSpacing(10)
        settings_layout.setContentsMargins(15, 15, 15, 15)
        
        # Settings Grid
        grid = QGridLayout()
        grid.setVerticalSpacing(10)
        grid.setHorizontalSpacing(20)
        
        # 1. GPU
        lbl_enc = QLabel("Encoder Strategy")
        lbl_enc.setObjectName("caption")
        self.combo_gpu = QComboBox()
        self.combo_gpu.addItems([
            "Auto-Detect", 
            "CPU (libx264)", 
            "NVIDIA (h264_nvenc)", 
            "AMD (h264_amf)", 
            "Intel (h264_qsv)",
            "Apple Silicon (h264_videotoolbox)"
        ])
        self.combo_gpu.setCursor(Qt.PointingHandCursor)
        grid.addWidget(lbl_enc, 0, 0)
        grid.addWidget(self.combo_gpu, 1, 0)
        
        # 2. Options
        lbl_opt = QLabel("Output Options")
        lbl_opt.setObjectName("caption")
        grid.addWidget(lbl_opt, 0, 1)
        
        opts_layout = QHBoxLayout()
        self.chk_separate = QCheckBox("Separate File per Track")
        self.chk_separate.setCursor(Qt.PointingHandCursor)
        self.spin_repeat = QSpinBox()
        self.spin_repeat.setRange(1, 10)
        self.spin_repeat.setPrefix("Loop: ")
        self.spin_repeat.setSuffix("x")
        self.spin_repeat.setValue(1)
        self.chk_separate.stateChanged.connect(self.toggle_repeat_input)
        
        opts_layout.addWidget(self.chk_separate)
        opts_layout.addWidget(self.spin_repeat)
        grid.addLayout(opts_layout, 1, 1)
        
        settings_layout.addLayout(grid)
        
        # Render Button
        settings_layout.addSpacing(5)
        self.btn_render = QPushButton("RENDER VIDEO")
        self.btn_render.setObjectName("success")
        self.btn_render.setMinimumHeight(44)
        self.btn_render.setCursor(Qt.PointingHandCursor)
        self.btn_render.clicked.connect(self.start_render)
        settings_layout.addWidget(self.btn_render)
        
        # Progress Bars (No Text Label)
        progress_layout = QVBoxLayout()
        self.bar_current = QProgressBar()
        self.bar_current.setVisible(False)
        self.bar_batch = QProgressBar()
        self.bar_batch.setVisible(False)
        progress_layout.addWidget(self.bar_current)
        progress_layout.addWidget(self.bar_batch)
        
        settings_layout.addLayout(progress_layout)
        
        main_layout.addWidget(settings_card)
        
        # Initial Logic
        self.list_audio.files_dropped.connect(self.add_audio_files)
        self.list_audio.video_dropped.connect(self.set_video)
        self.detected_encoder = detect_gpu()
        self.status_bar = self.statusBar() # Keep status bar for small logs
        self.status_bar.showMessage(f"System ready. GPU: {self.detected_encoder}")


    def init_single_tab(self):
        layout = QVBoxLayout(self.tab_single)
        layout.setSpacing(15)
        layout.setContentsMargins(5, 15, 5, 5)
        
        # Card 1: Video (Compact)
        card_video = QFrame()
        card_video.setObjectName("card")
        v_layout = QVBoxLayout(card_video)
        v_layout.setContentsMargins(15, 10, 15, 10)
        
        # Header Row: Title + Stretch + Buttons
        header_row = QHBoxLayout()
        lbl_v = QLabel("Background Video Loop")
        lbl_v.setObjectName("header")
        
        btn_browse = QPushButton("Browse")
        btn_browse.setObjectName("tool")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self.select_video)
        
        btn_clear_v = QPushButton("Clear")
        btn_clear_v.setObjectName("tool")
        btn_clear_v.setCursor(Qt.PointingHandCursor)
        btn_clear_v.clicked.connect(self.clear_video)
        
        header_row.addWidget(lbl_v)
        header_row.addStretch()
        header_row.addWidget(btn_browse)
        header_row.addWidget(btn_clear_v)
        
        v_layout.addLayout(header_row)
        
        # Content Row: Status Label
        self.lbl_video = QLabel("No Video Selected")
        self.lbl_video.setStyleSheet("color: #666; font-style: italic;")
        v_layout.addWidget(self.lbl_video)
        
        layout.addWidget(card_video)
        
        # Card 2: Audio
        card_audio = QFrame()
        card_audio.setObjectName("card")
        a_layout = QVBoxLayout(card_audio)
        a_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with Tools
        a_header = QHBoxLayout()
        lbl_a = QLabel("Audio Playlist")
        lbl_a.setObjectName("header")
        
        btn_add = QPushButton("+ Add Files")
        btn_add.setObjectName("tool")
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.clicked.connect(self.browse_audio)
        
        btn_folder = QPushButton("+ Folder")
        btn_folder.setObjectName("tool")
        btn_folder.setCursor(Qt.PointingHandCursor)
        btn_folder.clicked.connect(self.browse_folder)
        
        btn_clear = QPushButton("Clear")
        btn_clear.setObjectName("tool")
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.clicked.connect(self.clear_audio)
        
        a_header.addWidget(lbl_a)
        a_header.addStretch()
        a_header.addWidget(btn_add)
        a_header.addWidget(btn_folder)
        a_header.addWidget(btn_clear)
        a_layout.addLayout(a_header)
        
        # Unified List/Drop Widget
        self.list_audio = FileListWidget()
        a_layout.addWidget(self.list_audio)
        
        layout.addWidget(card_audio)

    def init_batch_tab(self):
        layout = QVBoxLayout(self.tab_batch)
        layout.setContentsMargins(5, 15, 5, 5)
        
        card_batch = QFrame()
        card_batch.setObjectName("card")
        b_layout = QVBoxLayout(card_batch)
        
        lbl_b = QLabel("Batch Processing Mode")
        lbl_b.setObjectName("header")
        b_layout.addWidget(lbl_b)
        
        b_layout.addWidget(QLabel("Select a root folder containing multiple project subfolders."))
        
        batch_input_layout = QHBoxLayout()
        self.line_batch_input = DropLineEdit()
        self.line_batch_input.setPlaceholderText("C:/Path/To/Root/Folder (Drop Here)")
        self.line_batch_input.setReadOnly(True)
        
        btn_browse = QPushButton("Select Folder")
        btn_browse.setObjectName("primary")
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.clicked.connect(self.browse_batch_root)
        
        batch_input_layout.addWidget(self.line_batch_input)
        batch_input_layout.addWidget(btn_browse)
        
        b_layout.addLayout(batch_input_layout)
        b_layout.addStretch()
        
        layout.addWidget(card_batch)
        layout.addStretch()

    # ... [Logic Methods] ...
    def select_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Background Video", "", "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if path:
            self.set_video(path)

    def set_video(self, path):
        self.tabs.setCurrentIndex(0) 
        self.video_path = path
        self.lbl_video.setText(f"{os.path.basename(path)}")
        self.lbl_video.setStyleSheet("color: #4285F4; font-weight: bold;")
        
    def clear_video(self):
        self.video_path = None
        self.lbl_video.setText("No Video Selected")
        self.lbl_video.setStyleSheet("color: #666; font-style: italic;")

    def browse_audio(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", "", "Audio Files (*.mp3 *.wav *.aac *.flac)")
        if paths:
            self.add_audio_files(paths)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            audio_files = []
            video_found = None
            video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
            audio_exts = ('.mp3', '.wav', '.aac', '.m4a', '.flac', '.ogg')

            for root, dirs, filenames in os.walk(folder):
                for f in filenames:
                    f_lower = f.lower()
                    full_path = os.path.join(root, f)
                    if f_lower.endswith(audio_exts):
                        audio_files.append(full_path)
                    elif f_lower.endswith(video_exts) and not video_found:
                        video_found = full_path
            
            if video_found:
                self.set_video(video_found)

            if audio_files:
                self.add_audio_files(audio_files)

    def add_audio_files(self, paths):
        new_added = False
        for path in paths:
            if path not in self.audio_files:
                self.audio_files.append(path)
                new_added = True
        
        if new_added:
            self.audio_files.sort(key=lambda p: os.path.basename(p).lower())
            self.list_audio.clear()
            for path in self.audio_files:
                self.list_audio.addItem(os.path.basename(path))
            
            # Switch to solid style once files exist
            if len(self.audio_files) > 0:
                self.list_audio.set_solid_style()

    def remove_audio(self):
        # We need this method if we add a 'Selected Remove' button, currently I only added Clear All in new UI. 
        pass

    def clear_audio(self):
        self.list_audio.clear()
        self.audio_files = []
        self.list_audio.set_dashed_style()

    def browse_batch_root(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Root Batch Folder")
        if folder:
            self.line_batch_input.setText(folder)

    def toggle_repeat_input(self):
        is_separate = self.chk_separate.isChecked()
        self.spin_repeat.setDisabled(is_separate)
        
    def start_render(self):
        current_tab_index = self.tabs.currentIndex()
        settings = {}
        
        choice = self.combo_gpu.currentIndex()
        if choice == 0: encoder = self.detected_encoder
        elif choice == 1: encoder = "libx264"
        elif choice == 2: encoder = "h264_nvenc"
        elif choice == 3: encoder = "h264_amf"
        elif choice == 4: encoder = "h264_qsv"
        elif choice == 5: encoder = "h264_videotoolbox"
        else: encoder = "libx264"
        
        sep_files = self.chk_separate.isChecked()

        common_settings = {
            "gpu_encoder": encoder,
            "separate_files": sep_files,
            "playlist_repeat": self.spin_repeat.value()
        }
        
        if current_tab_index == 0:
            # === SINGLE MODE ===
            if not self.audio_files:
                QMessageBox.warning(self, "Missing Audio", "Please add at least one audio file.")
                return

            if sep_files:
                if not self.video_path:
                    QMessageBox.warning(self, "Missing Video", "Cannot use 'Separate File per Track' without a video background.\n\nPlease add a video or uncheck 'Separate File per Track' for Audio Only output.")
                    return

                out_path = QFileDialog.getExistingDirectory(self, "Select Output Folder")
                if not out_path: return
            else:
                # If No Video -> Audio Only (.mp3)
                if not self.video_path:
                    out_path, _ = QFileDialog.getSaveFileName(self, "Save Audio As", "output.mp3", "MP3 Audio (*.mp3)")
                else:
                    out_path, _ = QFileDialog.getSaveFileName(self, "Save Video As", "output.mp4", "MP4 Video (*.mp4)")
                
                if not out_path: return
            
            # Reconstruct ordered list
            ordered_audio = []
            for index in range(self.list_audio.count()):
                item = self.list_audio.item(index)
                name = item.text()
                for p in self.audio_files:
                    if os.path.basename(p) == name:
                        ordered_audio.append(p)
                        break
            
            settings = common_settings
            settings["mode"] = "single"
            settings["output_path"] = out_path
            settings["video_path"] = self.video_path
            settings["audio_paths"] = ordered_audio

        else:
            # === BATCH MODE ===
            batch_root = self.line_batch_input.text()
            if not batch_root or not os.path.isdir(batch_root):
                QMessageBox.warning(self, "Invalid Input", "Please select a valid Batch Root folder.")
                return
            
            # --- VALIDATION STEP ---
            video_exts = ('.mp4', '.mov', '.avi', '.mkv', '.webm')
            subfolders = [f.path for f in os.scandir(batch_root) if f.is_dir()]
            
            folders_no_video = []
            
            for folder in subfolders:
                has_video = False
                for root, dirs, files in os.walk(folder):
                    for f in files:
                        if f.lower().endswith(video_exts):
                            has_video = True
                            break
                    if has_video: break
                
                if not has_video:
                    folders_no_video.append(os.path.basename(folder))
            
            # Logic Rule: If Separate Video Checked AND No Video in folder -> Alert & Stop
            if sep_files:
                if folders_no_video:
                    msg = "The following folders have NO VIDEO, but 'Separate File per Track' is checked:\n\n"
                    msg += "\n".join(folders_no_video[:10])
                    if len(folders_no_video) > 10: msg += "\n..."
                    msg += "\n\nCannot proceed in Separate File mode without a video source for every folder."
                    QMessageBox.critical(self, "Batch Error", msg)
                    return
            else:
                # Logic Rule: If Combined Mode AND No Video -> Warn & Continue?
                if folders_no_video:
                    msg = "The following folders have NO VIDEO and will be rendered as AUDIO ONLY (.mp3):\n\n"
                    msg += "\n".join(folders_no_video[:10])
                    if len(folders_no_video) > 10: msg += "\n..."
                    msg += "\n\nDo you want to continue?"
                    
                    reply = QMessageBox.question(self, "Missing Videos", msg, 
                                                 QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    
                    if reply == QMessageBox.No:
                        return

            out_path = QFileDialog.getExistingDirectory(self, "Select Output Folder for Batch")
            if not out_path: return
            
            settings = common_settings
            settings["mode"] = "batch"
            settings["batch_root"] = batch_root
            settings["output_path"] = out_path

        self.thread = RenderThread(settings)
        self.thread.progress_update.connect(self.update_progress_text)
        self.thread.progress_value.connect(self.bar_current.setValue) 
        self.thread.progress_batch.connect(self.bar_batch.setValue)
        self.thread.finished.connect(self.render_finished)
        
        self.btn_render.setEnabled(False)
        self.btn_render.setText("RENDERING...")
        self.bar_current.setVisible(True)
        self.bar_current.setValue(0)
        this_green = "#0F9D58"
        self.bar_current.setStyleSheet(f"QProgressBar::chunk {{ background-color: {this_green}; }}")
        
        if current_tab_index == 1: 
            self.bar_batch.setVisible(True)
            self.bar_batch.setValue(0)
        else:
            self.bar_batch.setVisible(False)
            
        self.thread.start()

    def update_progress_text(self, msg):
        self.status_bar.showMessage(msg)

    def render_finished(self, success, message):
        self.btn_render.setEnabled(True)
        self.btn_render.setText("RENDER VIDEO")
        self.bar_current.setVisible(False)
        self.bar_batch.setVisible(False)
        self.status_bar.showMessage("Ready")
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

