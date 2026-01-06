import sys
import os
from PySide6.QtWidgets import QApplication
from src.ui import MainWindow

def main():
    app = QApplication(sys.argv)
    
    # Optional: Set app styling here
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
