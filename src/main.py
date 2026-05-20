"""ThinkSub — 视频中文字幕生成工具"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import DEVICE, COMPUTE_TYPE  # 激活 CUDA DLL 路径
from PySide6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("ThinkSub")

    from src.gui.setup_wizard import check_models_ready, SetupWizard
    if not check_models_ready():
        wizard = SetupWizard()
        if wizard.exec() != SetupWizard.Accepted:
            return

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
