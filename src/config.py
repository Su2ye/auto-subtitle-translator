"""
ThinkSub 全局配置

所有路径、模型名、阈值集中管理，不在模块中散布硬编码值。
"""

import os
from pathlib import Path

# ---- 路径 ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
FFMPEG_DIR = PROJECT_ROOT / "ffmpeg"
FFMPEG_BIN = FFMPEG_DIR / "bin" / "ffmpeg.exe"
FFPROBE_BIN = FFMPEG_DIR / "bin" / "ffprobe.exe"

# ---- 模型 ----
# 语言检测 + 英/韩 ASR
WHISPER_MODEL = "large-v3"

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
SILENCE_THRESHOLD = 0.3        # VAD 静音判定阈值 (0-1)
MIN_SPEECH_DURATION_MS = 500   # 最短有效语音段 (ms)
MAX_SPEECH_GAP_MS = 400        # 最大句间间隔 (ms)，超过则切分
LANGUAGE_DETECT_SECONDS = 30   # 语言检测用前 N 秒音频

# 高质量模式
QUALITY_ASR_BEAM_SIZE = 5
# 快速模式
FAST_ASR_BEAM_SIZE = 2

# ---- 硬件 ----
DEVICE = "cuda"
COMPUTE_TYPE = "float16"       # GPU 用 float16, CPU 降级时用 int8

# ---- 用户数据 ----
APPDATA_DIR = Path(os.getenv("APPDATA", "")) / "ThinkSub"
SETTINGS_FILE = APPDATA_DIR / "settings.json"
TEMP_DIR = Path(os.getenv("TEMP", "/tmp")) / "thinksub"

# ---- HF 镜像 ----
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
