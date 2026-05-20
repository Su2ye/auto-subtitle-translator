"""ThinkSub — 视频中文字幕生成工具"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEVICE, COMPUTE_TYPE  # 激活 CUDA DLL 路径
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QLockFile


def main():
    # 单实例锁
    lock = QLockFile(
        str(Path(__file__).resolve().parent.parent / "thinksub.lock")
    )
    if not lock.tryLock(100):
        QMessageBox.warning(None, "ThinkSub", "应用已在运行中。")
        return

    app = QApplication(sys.argv)
    app.setApplicationName("ThinkSub")

    # 启动动画
    from PySide6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
    from PySide6.QtGui import QPixmap, QIcon, QPainter, QColor, QPen, QBrush, QFont
    from PySide6.QtCore import Qt

    # 绘制闪屏背景（Indigo 底色 + 白色圆角卡片 + 图标 + 文字）
    px = QPixmap(480, 320)
    px.fill(QColor("#1E1E2E"))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)

    # 白色圆角卡片
    painter.setBrush(QColor("#2D2D3F"))
    painter.setPen(QPen(QColor("#3D3D5C"), 1))
    painter.drawRoundedRect(40, 40, 400, 240, 20, 20)

    # 蓝色 T 字母（代替图标）
    painter.setBrush(QColor("#4F46E5"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(190, 80, 100, 100, 16, 16)
    painter.setFont(QFont("Arial", 48, QFont.Bold))
    painter.setPen(QColor("#FFFFFF"))
    painter.drawText(190, 80, 100, 100, Qt.AlignCenter, "T")

    # 应用名称
    painter.setFont(QFont("Microsoft YaHei", 18, QFont.Bold))
    painter.setPen(QColor("#CDD6F4"))
    painter.drawText(40, 200, 400, 30, Qt.AlignCenter, "ThinkSub")
    # 副标题
    painter.setFont(QFont("Microsoft YaHei", 11))
    painter.setPen(QColor("#A6ADC8"))
    painter.drawText(40, 232, 400, 24, Qt.AlignCenter, "视频中文字幕生成工具")

    painter.end()

    splash = QSplashScreen(px)
    splash.show()
    app.processEvents()

    from src.gui.setup_wizard import check_models_ready, SetupWizard
    if not check_models_ready():
        splash.close()
        wizard = SetupWizard()
        if wizard.exec() != SetupWizard.Accepted:
            return

    from src.gui.main_window import MainWindow
    window = MainWindow()
    splash.finish(window)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
