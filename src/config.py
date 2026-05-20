"""
ThinkSub 全局配置

所有路径、模型名、阈值集中管理，不在模块中散布硬编码值。
"""

import ctypes
import os
import sys
from pathlib import Path


def _setup_cuda_dlls() -> bool:
    """将 nvidia DLL 目录加入搜索路径（pip 安装或系统 CUDA Toolkit）"""
    # pip 安装的 nvidia-* 在 venv/Lib/site-packages 下
    project_root = Path(__file__).resolve().parent.parent
    site_packages = project_root / "venv" / "Lib" / "site-packages"
    if not site_packages.is_dir():
        # 非开发环境（PyInstaller 打包后），从 python 所在路径找
        site_packages = Path(sys.executable).parent.parent / "Lib" / "site-packages"

    for d in site_packages.glob("nvidia/*/bin"):
        os.add_dll_directory(str(d))

    # 系统 CUDA Toolkit
    cuda_root = Path("C:/Program Files/NVIDIA GPU Computing Toolkit/CUDA")
    if cuda_root.is_dir():
        for ver_dir in sorted(cuda_root.iterdir(), reverse=True):
            cuda_bin = ver_dir / "bin"
            if cuda_bin.is_dir():
                os.add_dll_directory(str(cuda_bin))
                break

    for lib in ("cublas64_12.dll", "cublas64_11.dll"):
        try:
            ctypes.CDLL(lib)
            return True
        except OSError:
            continue
    return False


_IS_CUDA = _setup_cuda_dlls()

# ---- 路径 ----
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ---- 用户数据 ----
APPDATA_DIR = Path(os.getenv("APPDATA", "")) / "ThinkSub"

# 模型存到 APPDATA（exe 和源码共用，持久保留），可通过 settings 自定义
def _get_models_dir():
    try:
        import json
        sf = APPDATA_DIR / "settings.json"
        if sf.exists():
            custom = json.loads(sf.read_text("utf-8")).get("model_path")
            if custom:
                return Path(custom)
    except Exception:
        pass
    return APPDATA_DIR / "models"

MODELS_DIR = _get_models_dir()

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

# 翻译模型（HuggingFace 格式，NLLB-200 一个模型覆盖全部语言）
TRANSLATION_MODEL = MODELS_DIR / "nllb-200-hf"

# NLLB-200 语言码映射（ISO 639-1 → BCP-47）
NLLB_LANG_CODES = {
    "ja": "jpn_Jpan",
    "en": "eng_Latn",
    "ko": "kor_Hang",
}
NLLB_TARGET_LANG = "zho_Hans"

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

SETTINGS_FILE = APPDATA_DIR / "settings.json"
TEMP_DIR = Path(os.getenv("TEMP", "/tmp")) / "thinksub"

# ---- HF 镜像 ----
HF_ENDPOINT = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
