"""
ThinkSub 全局配置

所有路径、模型名、阈值集中管理，不在模块中散布硬编码值。
"""

import ctypes
import os
from pathlib import Path


def _cuda_available() -> bool:
    """检测 CUDA 运行时是否可用"""
    try:
        ctypes.CDLL("cublas64_12.dll")
        return True
    except OSError:
        pass
    try:
        ctypes.CDLL("cublas64_11.dll")
        return True
    except OSError:
        pass
    return False


_IS_CUDA = _cuda_available()

# ---- 路径 ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
FFMPEG_DIR = PROJECT_ROOT / "ffmpeg"
FFMPEG_BIN = FFMPEG_DIR / "bin" / "ffmpeg.exe"
FFPROBE_BIN = FFMPEG_DIR / "bin" / "ffprobe.exe"

# ---- 语言 ----
SUPPORTED_LANGUAGES = ("ja", "en", "ko")

# ---- 模型 ----
# 语言检测 + 英/韩 ASR
WHISPER_MODEL = "large-v3"
# 快速模式英/韩
WHISPER_FAST_MODEL = "medium"
# 日语专用 ASR（CTranslate2 格式）
KOTOBA_WHISPER_MODEL = "kotoba-tech/kotoba-whisper-v2.0-faster"

# 翻译模型（CTranslate2 格式，本地路径）
TRANSLATION_MODELS = {
    "en": MODELS_DIR / "opus-mt-en-zh-faster",
    "ja": MODELS_DIR / "opus-mt-ja-zh-faster",
    "ko": MODELS_DIR / "opus-mt-ko-zh-faster",
}

# ---- 处理参数 ----
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.3
MIN_SPEECH_DURATION_MS = 500
MAX_SPEECH_GAP_MS = 400
LANGUAGE_DETECT_SECONDS = 30

QUALITY_ASR_BEAM_SIZE = 5
FAST_ASR_BEAM_SIZE = 2

# ---- 硬件 ----
DEVICE = "cuda" if _IS_CUDA else "cpu"
COMPUTE_TYPE = "float16" if _IS_CUDA else "int8"

# ---- 用户数据 ----
APPDATA_DIR = Path(os.getenv("APPDATA", "")) / "ThinkSub"
SETTINGS_FILE = APPDATA_DIR / "settings.json"
TEMP_DIR = Path(os.getenv("TEMP", "/tmp")) / "thinksub"

# ---- HF 镜像 ----
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
