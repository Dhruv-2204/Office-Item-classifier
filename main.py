import sys
import os
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow


def main():
    # Create necessary directories
    os.makedirs('input', exist_ok=True)
    os.makedirs('output', exist_ok=True)
    os.makedirs('snapshots', exist_ok=True)

    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("Office Object Detector")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("ObjectDetection")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()