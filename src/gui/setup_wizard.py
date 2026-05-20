"""首次运行模型下载向导"""

from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QCheckBox, QProgressBar, QPushButton,
)

from src.config import (
    MODELS_DIR, WHISPER_MODEL, KOTOBA_WHISPER_MODEL,
    TRANSLATION_MODEL,
)


class DownloadWorker(QThread):
    """后台下载模型"""
    progress = Signal(int, str)   # (pct, msg)
    finished = Signal(bool, str)  # (ok, error_msg)

    def __init__(self, languages: list[str]):
        super().__init__()
        self._langs = languages

    def run(self):
        try:
            self._download()
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, str(e))

    def _download(self):
        import os
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        from huggingface_hub import snapshot_download

        tasks: list[tuple[str, str | None]] = []
        # ASR models
        if "ja" in self._langs:
            tasks.append((KOTOBA_WHISPER_MODEL, "日语 ASR"))
        if "en" in self._langs or "ko" in self._langs:
            if "en" in self._langs and "ko" not in self._langs:
                pass  # label below
            tasks.append((WHISPER_MODEL, "英/韩 ASR"))

        # Translation model (shared)
        tasks.append((TRANSLATION_MODEL.name, "翻译"))

        total = len(tasks)
        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        for i, (repo, label) in enumerate(tasks):
            pct = int(i / total * 90)
            self.progress.emit(pct, f"下载 {label} ({repo})")
            snapshot_download(repo, local_dir=str(MODELS_DIR),
                              max_workers=4)

        self.progress.emit(95, "保存配置...")
        self._save_config()
        self.progress.emit(100, "完成")

    def _save_config(self):
        import json
        from src.config import SETTINGS_FILE
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({
            "installed_languages": self._langs,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def check_models_ready() -> bool:
    """检查模型是否就绪"""
    return TRANSLATION_MODEL.exists() and (MODELS_DIR / "silero_vad.onnx").exists()


class SetupWizard(QDialog):
    """首次运行：语言选择 + 模型下载"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ThinkSub — 首次设置")
        self.setFixedSize(440, 360)
        self._init_ui()

    def _init_ui(self):
        v = QVBoxLayout(self)
        v.setSpacing(16)
        v.setContentsMargins(24, 20, 24, 20)

        title = QLabel("欢迎使用 ThinkSub")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #CDD6F4;")
        v.addWidget(title)

        v.addWidget(QLabel("请选择需要翻译的语言，应用将自动下载所需模型："))
        v.addWidget(QLabel("（下载约 2-4 GB，支持断点续传）"))

        self._cb_ja = QCheckBox("日语")
        self._cb_en = QCheckBox("英语")
        self._cb_ko = QCheckBox("韩语")
        self._cb_ja.setChecked(True)
        for cb in [self._cb_ja, self._cb_en, self._cb_ko]:
            v.addWidget(cb)

        self._size_label = QLabel("预计下载: 2.7 GB")
        self._size_label.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        v.addWidget(self._size_label)

        self._progress = QProgressBar()
        self._progress.setVisible(False)
        v.addWidget(self._progress)

        self._status = QLabel("")
        self._status.setStyleSheet("color: #A6ADC8; font-size: 11px;")
        v.addWidget(self._status)

        v.addStretch()

        btn_row = QHBoxLayout()
        self._btn = QPushButton("开始下载")
        self._btn.setObjectName("PrimaryBtn")
        self._btn.clicked.connect(self._on_start)
        btn_row.addStretch()
        btn_row.addWidget(self._btn)
        v.addLayout(btn_row)

        # 更新大小提示
        self._cb_ja.toggled.connect(self._update_size)
        self._cb_en.toggled.connect(self._update_size)
        self._cb_ko.toggled.connect(self._update_size)

    def _update_size(self):
        ja = self._cb_ja.isChecked()
        en = self._cb_en.isChecked()
        ko = self._cb_ko.isChecked()
        if not (ja or en or ko):
            self._size_label.setText("请至少选择一种语言")
            self._btn.setEnabled(False)
            return
        self._btn.setEnabled(True)
        gb = 0
        if ja:
            gb += 1.5  # kotoba-whisper
        if en or ko:
            gb += 3.0  # large-v3 (shared)
        gb += 1.2  # NLLB-200 translation
        self._size_label.setText(f"预计下载: {gb:.1f} GB")

    def _on_start(self):
        langs = []
        if self._cb_ja.isChecked():
            langs.append("ja")
        if self._cb_en.isChecked():
            langs.append("en")
        if self._cb_ko.isChecked():
            langs.append("ko")
        if not langs:
            return

        self._progress.setVisible(True)
        self._btn.setEnabled(False)
        self._cb_ja.setEnabled(False)
        self._cb_en.setEnabled(False)
        self._cb_ko.setEnabled(False)

        self._worker = DownloadWorker(langs)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, pct: int, msg: str):
        self._progress.setValue(pct)
        self._status.setText(msg)

    def _on_finished(self, ok: bool, error: str):
        if ok:
            self.accept()
        else:
            self._status.setText(f"下载失败: {error}")
            self._btn.setEnabled(True)
            self._btn.setText("重试")
