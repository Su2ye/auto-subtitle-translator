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
