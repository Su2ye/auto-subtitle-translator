"""处理管道编排 — 协调各模块完成完整处理"""

from pathlib import Path

import numpy as np
import soundfile as sf

from src.pipeline.audio_extractor import extract_audio
from src.pipeline.vad import detect_speech_segments
from src.pipeline.asr import ASREngine
from src.pipeline.translator import get_translator, translate_segments
from src.pipeline.subtitle_writer import write_subtitles
from src.pipeline.hard_sub import burn_subtitles
from src.utils.ffmpeg_utils import get_video_info
from src.config import SUPPORTED_LANGUAGES


class PipelineRunner:
    """管道编排器，提供进度回调"""

    def __init__(self):
        self._asr = None
        self._progress_cb = None
        self._cancel_flag = False

    def run(
        self,
        video_path: Path,
        output_dir: Path,
        output_type: str,       # "srt" | "ass" | "both"
        mode: str,              # "quality" | "fast"
        language: str | None,   # "ja" | "en" | "ko" | None (auto)
        burn: bool = False,
        progress_cb=None,
    ) -> dict:
        """
        执行完整处理管道。

        Returns:
            {"subtitle": Path, "video": Path | None, "language": str, "duration_s": float}
        """
        self._progress_cb = progress_cb
        self._cancel_flag = False
        fast = mode == "fast"

        self._report(0, "读取视频信息...")
        info = get_video_info(video_path)
        if not info["has_audio"]:
            raise RuntimeError("视频没有音频轨道")

        self._report(5, "提取音频...")
        audio_path = output_dir / f"{video_path.stem}_audio.wav"
        audio_path = extract_audio(video_path, audio_path)
        if self._cancel_flag:
            return {}

        audio, sr = sf.read(str(audio_path))
        audio = audio.astype(np.float32)

        self._report(15, "检测语音段...")
        segments = detect_speech_segments(audio)
        if not segments:
            raise RuntimeError("未检测到语音内容")
        if self._cancel_flag:
            return {}

        self._report(20, "语音识别中...")
        self._asr = ASREngine(fast_mode=fast)

        if language is None:
            lang = self._asr.detect_language(audio)
        else:
            lang = language
        if lang not in SUPPORTED_LANGUAGES:
            raise RuntimeError(f"无法识别语言: {lang}，请手动指定")
        if self._cancel_flag:
            return {}

        self._report(40, f"语音识别中 ({lang})...")
        result = self._asr.transcribe(audio, language=lang)
        if self._cancel_flag:
            return {}

        self._report(65, "翻译中...")
        bilingual = translate_segments(
            [{"start": s.start, "end": s.end, "text": s.text}
             for s in result.segments],
            lang,
        )
        if self._cancel_flag:
            return {}

        self._report(80, "生成字幕文件...")
        # 从 "1920×1080" 解析宽高
        res = info.get("resolution", "1920×1080")
        try:
            w, h = res.split("×")
            vw, vh = int(w), int(h)
        except (ValueError, AttributeError):
            vw, vh = 1920, 1080

        sub_output = output_dir / f"{video_path.stem}.ass"
        sub_output = write_subtitles(bilingual, sub_output, fmt="ass",
                                     video_width=vw, video_height=vh)
        if output_type == "srt":
            sub_output = write_subtitles(bilingual,
                                         output_dir / f"{video_path.stem}.srt",
                                         fmt="srt")
        if self._cancel_flag:
            return {}

        result = {"subtitle": sub_output, "video": None,
                  "language": lang, "duration_s": info["duration"]}

        if burn:
            self._report(90, "烧录字幕...")
            video_out = output_dir / f"{video_path.stem}_sub.mp4"
            result["video"] = burn_subtitles(video_path, sub_output, video_out)
            if self._cancel_flag:
                return {}

        self._report(100, "完成")
        audio_path.unlink(missing_ok=True)
        return result

    def cancel(self):
        self._cancel_flag = True

    def _report(self, pct: int, msg: str):
        if self._progress_cb:
            self._progress_cb(pct, msg)
