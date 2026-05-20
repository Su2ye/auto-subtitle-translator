"""ASR 模块 — 多模型路由器"""

from dataclasses import dataclass

import numpy as np
from faster_whisper import WhisperModel

from src.config import (
    DEVICE,
    COMPUTE_TYPE,
    WHISPER_MODEL,
    WHISPER_FAST_MODEL,
    KOTOBA_WHISPER_MODEL,
    SUPPORTED_LANGUAGES,
    QUALITY_ASR_BEAM_SIZE,
    FAST_ASR_BEAM_SIZE,
    LANGUAGE_DETECT_SECONDS,
    SAMPLE_RATE,
)


@dataclass
class ASRSegment:
    start: float
    end: float
    text: str


@dataclass
class ASRResult:
    language: str
    segments: list[ASRSegment]
    text: str


def _find_model_dir(name: str, root: "Path") -> str | None:
    """在 root 及其子目录中查找匹配模型的目录"""
    from pathlib import Path
    root = Path(root)
    if not root.is_dir():
        return None
    # 直接匹配
    direct = root / name
    if direct.is_dir():
        return str(direct)
    # 搜索子目录（HF cache 格式：org--repo）
    for d in root.iterdir():
        if d.is_dir() and (name in d.name or d.name.endswith(name)):
            return str(d)
    return None


class ASREngine:
    """多语言 ASR 引擎"""

    def __init__(self, fast_mode: bool = False):
        self._fast_mode = fast_mode
        self._model: WhisperModel | None = None
        self._model_name: str | None = None

    def transcribe(self, audio: np.ndarray, language: str | None = None) -> ASRResult:
        if language is not None and language not in SUPPORTED_LANGUAGES:
            raise ValueError(f"不支持的语言: {language}")

        audio = audio.squeeze().astype(np.float32)
        self._load_model(self._pick_model(language))

        beam_size = FAST_ASR_BEAM_SIZE if self._fast_mode else QUALITY_ASR_BEAM_SIZE

        raw_segments, info = self._model.transcribe(
            audio,
            language=language,
            task="transcribe",
            beam_size=beam_size,
            vad_filter=True,
            condition_on_previous_text=False,
        )

        segments = [
            ASRSegment(start=s.start, end=s.end, text=s.text.strip())
            for s in raw_segments
        ]
        return ASRResult(
            language=info.language,
            segments=segments,
            text=" ".join(s.text for s in segments),
        )

    def detect_language(self, audio: np.ndarray) -> str:
        if self._model is None:
            self._load_model(WHISPER_MODEL)
        samples = int(LANGUAGE_DETECT_SECONDS * SAMPLE_RATE)
        audio_clip = audio[:samples].astype(np.float32)

        segments, info = self._model.transcribe(
            audio_clip, beam_size=1, vad_filter=False, without_timestamps=True
        )
        list(segments)
        detected = info.language
        return detected if detected in SUPPORTED_LANGUAGES else "uncertain"

    def _load_model(self, model_name: str) -> None:
        if self._model_name == model_name:
            return
        if self._model is not None:
            del self._model
        # 先查 MODELS_DIR（含子目录），找不到用 HF 缓存
        from src.config import MODELS_DIR
        local = _find_model_dir(model_name, MODELS_DIR)
        if local:
            model_name = local
        self._model = WhisperModel(
            model_name, device=DEVICE, compute_type=COMPUTE_TYPE
        )
        self._model_name = model_name

    def _pick_model(self, language: str | None) -> str:
        if language == "ja":
            return KOTOBA_WHISPER_MODEL
        if self._fast_mode and language in ("en", "ko"):
            return WHISPER_FAST_MODEL
        return WHISPER_MODEL
