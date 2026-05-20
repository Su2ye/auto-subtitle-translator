"""语言检测 — 使用 Whisper 内置分类头"""

import numpy as np
from faster_whisper import WhisperModel

from src.config import (
    DEVICE,
    COMPUTE_TYPE,
    MODELS_DIR,
    WHISPER_MODEL,
    SUPPORTED_LANGUAGES,
    LANGUAGE_DETECT_SECONDS,
    SAMPLE_RATE,
)


def detect_language(
    audio: np.ndarray,
    detect_duration: float = LANGUAGE_DETECT_SECONDS,
) -> str:
    """
    检测音频语言（自动加载 large-v3 模型）。

    Returns:
        "ja" | "en" | "ko" | "uncertain"
    """
    from src.pipeline.asr import _find_model_dir
    model_name = _find_model_dir(WHISPER_MODEL, MODELS_DIR) or WHISPER_MODEL
    model = WhisperModel(model_name, device=DEVICE, compute_type=COMPUTE_TYPE)

    try:
        audio = audio.squeeze()
        samples = int(detect_duration * SAMPLE_RATE)
        audio_clip = audio[:samples].astype(np.float32)

        segments, info = model.transcribe(
            audio_clip,
            beam_size=1,
            vad_filter=False,
            without_timestamps=True,
        )
        list(segments)
        detected = info.language
        return detected if detected in SUPPORTED_LANGUAGES else "uncertain"
    except Exception:
        return "uncertain"
    finally:
        del model
