from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QApplication
import sys
import os

app = QApplication(sys.argv)

icon_path = "src/icons/loop_app_icon.svg"
png_path = "src/icons/loop_app_icon.png"
ico_path = "src/icons/loop_app_icon.ico"

# Load SVG
pixmap = QIcon(icon_path).pixmap(256, 256)
pixmap.save(png_path, "PNG")

# For ICO, we can try to rely on PyInstaller doing PNG->ICO, 
# or if we have Pillow, we can do:
from PIL import Image
img = Image.open(png_path)
img.save(ico_path)

print(f"Created {png_path} and {ico_path}")
