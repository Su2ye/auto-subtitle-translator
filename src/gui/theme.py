"""ThinkSub 深色主题 — Catppuccin Mocha 风格"""

DARK_STYLE = """
QMainWindow {
    background-color: #1E1E2E;
}
QWidget {
    color: #CDD6F4;
    font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
    font-size: 13px;
}
QLabel#TitleLabel {
    font-size: 20px;
    font-weight: bold;
    color: #CDD6F4;
    padding: 8px 0;
}
QLabel#DropHint {
    font-size: 15px;
    color: #A6ADC8;
}
QFrame#DropZone {
    border: 2px dashed #585B70;
    border-radius: 12px;
    background-color: #2D2D3F;
}
QFrame#DropZone:hover {
    border-color: #89B4FA;
    background-color: #333350;
}
QFrame#InfoCard {
    background-color: #2D2D3F;
    border: 1px solid #3D3D5C;
    border-radius: 8px;
    padding: 12px;
}
QGroupBox {
    border: 1px solid #3D3D5C;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
}
QRadioButton, QCheckBox {
    spacing: 6px;
}
QComboBox {
    background-color: #2D2D3F;
    border: 1px solid #3D3D5C;
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 120px;
}
QComboBox::drop-down {
    border: none;
}
QPushButton#PrimaryBtn {
    background-color: #89B4FA;
    color: #1E1E2E;
    border: none;
    border-radius: 8px;
    padding: 10px 32px;
    font-size: 14px;
    font-weight: bold;
}
QPushButton#PrimaryBtn:hover {
    background-color: #9DC4FB;
}
QPushButton#PrimaryBtn:disabled {
    background-color: #585B70;
    color: #A6ADC8;
}
QPushButton#SecondaryBtn {
    background-color: transparent;
    color: #CDD6F4;
    border: 1px solid #585B70;
    border-radius: 8px;
    padding: 8px 20px;
}
QPushButton#SecondaryBtn:hover {
    border-color: #89B4FA;
    color: #89B4FA;
}
QProgressBar {
    border: none;
    border-radius: 4px;
    background-color: #45475A;
    height: 8px;
    text-align: center;
}
QProgressBar::chunk {
    background-color: #89B4FA;
    border-radius: 4px;
}
QProgressBar#progressError {
    color: #F38BA8;
    background-color: #F38BA8;
}
"""
