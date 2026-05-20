"""QThread 工作线程 — 在后台运行管道"""

from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.pipeline.pipeline import PipelineRunner


class PipelineWorker(QThread):
    """后台处理线程"""
    progress = Signal(int, str)    # (百分比, 阶段描述)
    finished = Signal(dict)        # 结果字典
    error = Signal(str)            # 错误消息

    def __init__(self, video_path: str, output_dir: str,
                 output_type: str = "ass", mode: str = "quality",
                 language: str | None = None, burn: bool = False,
                 subtitle_position: str = "bottom"):
        super().__init__()
        self._video = Path(video_path)
        self._output = Path(output_dir)
        self._output_type = output_type
        self._mode = mode
        self._language = language
        self._burn = burn
        self._position = subtitle_position
        self._runner = PipelineRunner()

    def run(self):
        try:
            result = self._runner.run(
                self._video, self._output,
                self._output_type, self._mode,
                self._language, self._burn,
                progress_cb=self._on_progress,
                subtitle_position=self._position,
            )
            if result:
                self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

    def cancel(self):
        self._runner.cancel()

    def _on_progress(self, pct: int, msg: str):
        self.progress.emit(pct, msg)
