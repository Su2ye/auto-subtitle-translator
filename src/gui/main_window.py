"""ThinkSub 主窗口"""

from PySide6.QtWidgets import QMainWindow, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThinkSub")
        self.setMinimumSize(640, 600)
        self.resize(680, 720)

        label = QLabel("ThinkSub — 视频中文字幕生成工具", self)
        label.setAlignment(0x0084)  # Qt.AlignCenter
        self.setCentralWidget(label)
