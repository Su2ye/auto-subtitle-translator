"""ThinkSub 主窗口"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow, QLabel

WINDOW_MIN_WIDTH = 640
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 680
WINDOW_DEFAULT_HEIGHT = 720


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThinkSub")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)

        label = QLabel("ThinkSub", self)
        label.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(label)
