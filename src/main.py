"""ThinkSub — 视频中文字幕生成工具"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEVICE, COMPUTE_TYPE  # 激活 CUDA DLL 路径
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QLockFile, QPropertyAnimation, QEasingCurve


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

    from src.gui.setup_wizard import check_models_ready, SetupWizard
    if not check_models_ready():
        wizard = SetupWizard()
        if wizard.exec() != SetupWizard.Accepted:
            return

    from src.gui.main_window import MainWindow
    window = MainWindow()

    # 启动淡入动画
    window.setWindowOpacity(0.0)
    window.show()
    anim = QPropertyAnimation(window, b"windowOpacity")
    anim.setDuration(400)
    anim.setStartValue(0.0)
    anim.setEndValue(1.0)
    anim.setEasingCurve(QEasingCurve.OutCubic)
    anim.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
