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
        from faster_whisper.utils import download_model as download_whisper
        from huggingface_hub import snapshot_download
        import subprocess, sys

        MODELS_DIR.mkdir(parents=True, exist_ok=True)

        tasks: list[tuple] = []

        # ASR 模型：用 faster-whisper 的 download 函数
        if "ja" in self._langs:
            tasks.append(("asr", KOTOBA_WHISPER_MODEL, "日语 ASR"))
        if "en" in self._langs or "ko" in self._langs:
            tasks.append(("asr", WHISPER_MODEL, "英/韩 ASR"))

        # 翻译模型：用正确的 HF repo ID
        tasks.append(("translation", "facebook/nllb-200-distilled-600M", "翻译"))

        total = len(tasks)

        for i, (kind, repo, label) in enumerate(tasks):
            pct = int(i / total * 90)
            self.progress.emit(pct, f"下载 {label} ...")

            if kind == "asr":
                download_whisper(repo, output_dir=str(MODELS_DIR))
            else:
                out_dir = str(TRANSLATION_MODEL)
                if not TRANSLATION_MODEL.exists():
                    # 下载 HF 模型并转换（需要临时装 torch）
                    self.progress.emit(pct, f"下载 {label} (NLLB-200, 约1.2GB)")
                    self._ensure_converter_deps()
                    subprocess.run(
                        [sys.executable, "-m", "ctranslate2.converters.transformers",
                         "--model", repo, "--output_dir", out_dir,
                         "--quantization", "float16"],
                        check=True,
                    )
                    self._save_tokenizer(repo, out_dir)

        self.progress.emit(95, "保存配置...")
        self._save_config()
        self.progress.emit(100, "完成")

    def _ensure_converter_deps(self):
        import subprocess, sys
        try:
            import torch, transformers, sentencepiece  # noqa
        except ImportError:
            self.progress.emit(0, "安装转换依赖...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install",
                 "torch", "transformers", "sentencepiece", "-q"],
                check=True,
            )

    def _save_tokenizer(self, repo: str, out_dir: str):
        import os
        os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
        from transformers import NllbTokenizerFast
        tok = NllbTokenizerFast.from_pretrained(repo)
        tok.save_pretrained(out_dir)

    def _save_config(self):
        import json
        from src.config import SETTINGS_FILE
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(json.dumps({
            "installed_languages": self._langs,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


def check_models_ready() -> bool:
    """检查模型是否就绪（以 settings.json 为准）"""
    from src.config import SETTINGS_FILE
    return SETTINGS_FILE.exists() and TRANSLATION_MODEL.exists()


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
