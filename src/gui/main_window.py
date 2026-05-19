"""ThinkSub 主窗口"""

import time
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QWidget,
    QLabel, QPushButton, QProgressBar,
    QGroupBox, QRadioButton, QComboBox, QCheckBox,
    QFrame, QFileDialog, QMessageBox,
)

from src.config import TEMP_DIR
from src.gui.theme import DARK_STYLE
from src.gui.worker import PipelineWorker


WINDOW_W = 640
WINDOW_H = 680


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ThinkSub — 视频中文字幕生成")
        self.setMinimumSize(500, 600)
        self.resize(WINDOW_W, WINDOW_H)
        self.setAcceptDrops(True)

        self._video_path: Path | None = None
        self._worker: PipelineWorker | None = None
        self._start_time = None

        self._init_ui()
        self.setStyleSheet(DARK_STYLE)

    # ---- UI 构建 ----

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 16, 24, 20)
        layout.setSpacing(16)

        layout.addWidget(self._title_label())
        layout.addWidget(self._drop_zone())
        layout.addWidget(self._info_card())
        layout.addWidget(self._settings_group())
        layout.addWidget(self._progress_section())
        layout.addWidget(self._action_bar())
        layout.addStretch()

    def _title_label(self) -> QLabel:
        lbl = QLabel("ThinkSub")
        lbl.setObjectName("TitleLabel")
        return lbl

    def _drop_zone(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("DropZone")
        frame.setMinimumHeight(140)
        v = QVBoxLayout(frame)
        v.setAlignment(Qt.AlignCenter)
        self._drop_hint = QLabel("拖拽视频文件到此处\n或点击选择文件")
        self._drop_hint.setObjectName("DropHint")
        self._drop_hint.setAlignment(Qt.AlignCenter)
        v.addWidget(self._drop_hint)
        frame.mousePressEvent = self._on_click_select
        return frame

    def _info_card(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("InfoCard")
        v = QVBoxLayout(frame)
        self._info_name = QLabel("未选择视频")
        self._info_detail = QLabel("")
        self._info_detail.setStyleSheet("color: #A6ADC8;")
        v.addWidget(self._info_name)
        v.addWidget(self._info_detail)
        return frame

    def _settings_group(self) -> QGroupBox:
        g = QGroupBox("处理设置")
        v = QVBoxLayout(g)

        # 输出类型
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("输出类型:"))
        self._radio_sub = QRadioButton("字幕文件")
        self._radio_burn = QRadioButton("字幕 + 烧录")
        self._radio_sub.setChecked(True)
        h1.addWidget(self._radio_sub)
        h1.addWidget(self._radio_burn)
        h1.addStretch()
        v.addLayout(h1)

        # 模式
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("处理模式:"))
        self._radio_quality = QRadioButton("高质量")
        self._radio_fast = QRadioButton("快速")
        self._radio_quality.setChecked(True)
        h2.addWidget(self._radio_quality)
        h2.addWidget(self._radio_fast)
        h2.addStretch()
        v.addLayout(h2)

        # 语言
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("源语言:"))
        self._combo_lang = QComboBox()
        self._combo_lang.addItems(["自动检测", "日语", "英语", "韩语"])
        h3.addWidget(self._combo_lang)
        h3.addStretch()
        v.addLayout(h3)

        return g

    def _progress_section(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setVisible(False)
        v.addWidget(self._progress_bar)

        self._progress_label = QLabel("")
        self._progress_label.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        v.addWidget(self._progress_label)

        return w

    def _action_bar(self) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w)
        h.setContentsMargins(0, 0, 0, 0)

        self._time_label = QLabel("")
        self._time_label.setStyleSheet("color: #A6ADC8;")
        h.addWidget(self._time_label)

        h.addStretch()

        self._cancel_btn = QPushButton("取消")
        self._cancel_btn.setObjectName("SecondaryBtn")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._on_cancel)
        h.addWidget(self._cancel_btn)

        self._start_btn = QPushButton("开始处理")
        self._start_btn.setObjectName("PrimaryBtn")
        self._start_btn.clicked.connect(self._on_start)
        self._start_btn.setEnabled(False)
        h.addWidget(self._start_btn)

        return w

    # ---- 拖拽 ----

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self._drop_hint.setText("松开以导入视频")

    def dragLeaveEvent(self, event):
        self._drop_hint.setText("拖拽视频文件到此处\n或点击选择文件")

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = Path(url.toLocalFile())
            if path.suffix.lower() in (".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm"):
                self._load_video(path)
                return
        self._drop_hint.setText("不支持的格式")

    def _on_click_select(self, _):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择视频", "",
            "视频文件 (*.mp4 *.mkv *.avi *.mov *.wmv *.flv *.webm);;所有文件 (*)"
        )
        if path:
            self._load_video(Path(path))

    # ---- 视频加载 ----

    def _load_video(self, path: Path):
        from src.utils.ffmpeg_utils import get_video_info
        self._video_path = path
        try:
            info = get_video_info(path)
            self._info_name.setText(f"{path.name}")
            size_gb = info.get("size_bytes", 0) / 1e9
            mins = int(info["duration"] // 60)
            secs = int(info["duration"] % 60)
            self._info_detail.setText(
                f"时长 {mins}:{secs:02d}  |  "
                f"{info['resolution']}  |  "
                f"{size_gb:.1f} GB  |  "
                f"{'有音频' if info['has_audio'] else '无音频'}"
            )
            self._start_btn.setEnabled(info["has_audio"])
            if not info["has_audio"]:
                self._info_detail.setText(self._info_detail.text() + " — 无法处理")
        except Exception as e:
            self._info_name.setText(f"{path.name} (读取失败)")
            self._info_detail.setText(str(e))
            self._start_btn.setEnabled(False)

        self._drop_hint.setText("")

    # ---- 处理控制 ----

    def _on_start(self):
        if not self._video_path:
            return

        lang_map = {"自动检测": None, "日语": "ja", "英语": "en", "韩语": "ko"}
        lang = lang_map.get(self._combo_lang.currentText())
        mode = "fast" if self._radio_fast.isChecked() else "quality"
        burn = self._radio_burn.isChecked()

        output_dir = self._video_path.parent
        TEMP_DIR.mkdir(parents=True, exist_ok=True)

        self._worker = PipelineWorker(
            str(self._video_path), str(output_dir),
            output_type="ass", mode=mode, language=lang, burn=burn,
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)

        self._set_running(True)
        self._progress_bar.setValue(0)
        self._start_time = time.time()
        self._worker.start()

    def _on_cancel(self):
        if self._worker:
            self._worker.cancel()
            self._progress_label.setText("已取消")
            self._set_running(False)

    def _on_progress(self, pct: int, msg: str):
        self._progress_bar.setValue(pct)
        self._progress_label.setText(msg)

    def _on_finished(self, result: dict):
        self._set_running(False)
        elapsed = time.time() - self._start_time if self._start_time else 0
        self._time_label.setText(f"耗时 {int(elapsed//60)} 分 {int(elapsed%60)} 秒")

        sub = result.get("subtitle")
        vid = result.get("video")
        msg = "处理完成！"
        if sub:
            msg += f"\n字幕: {Path(sub).name}"
        if vid:
            msg += f"\n视频: {Path(vid).name}"
        QMessageBox.information(self, "完成", msg)

    def _on_error(self, msg: str):
        self._set_running(False)
        QMessageBox.warning(self, "错误", msg)

    def _set_running(self, running: bool):
        self._start_btn.setEnabled(not running)
        self._cancel_btn.setVisible(running)
        self._progress_bar.setVisible(running)
        if not running:
            self._progress_label.setText("")
