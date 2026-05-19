"""FFmpeg 路径查找和基础验证"""

import json
import shutil
import subprocess
from pathlib import Path

from src.config import FFMPEG_BIN, FFPROBE_BIN

# Windows 系统默认 GBK，但 FFmpeg 输出是 UTF-8
SUBPROCESS_KWARGS = {"encoding": "utf-8", "errors": "replace", "text": True}

_winget_patterns = [
    "~/AppData/Local/Microsoft/WinGet/Links/ffmpeg.exe",
    "~/AppData/Local/Microsoft/WinGet/Packages/Gyan.FFmpeg_*/ffmpeg-*-full_build/bin/ffmpeg.exe",
]


def find_ffmpeg() -> str:
    """查找 FFmpeg 可执行文件，优先级：项目内置 > winget > 系统 PATH"""
    if FFMPEG_BIN and Path(FFMPEG_BIN).exists():
        return str(FFMPEG_BIN)

    for pattern in _winget_patterns:
        expanded = Path(pattern).expanduser()
        if "*" in str(expanded):
            candidates = list(expanded.parent.glob(expanded.name))
            if candidates:
                return str(candidates[0])
        elif expanded.exists():
            return str(expanded)

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    raise FileNotFoundError(
        "未找到 FFmpeg。请运行: winget install Gyan.FFmpeg\n"
        "或手动下载 ffmpeg.exe 放入项目的 ffmpeg/bin/ 目录。"
    )


def check_ffmpeg() -> bool:
    """验证 FFmpeg 是否可用"""
    try:
        ffmpeg = find_ffmpeg()
        result = subprocess.run(
            [ffmpeg, "-version"], capture_output=True, timeout=10,
            **SUBPROCESS_KWARGS,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_video_info(video_path: str | Path) -> dict:
    """获取视频基本信息（时长、分辨率、音频编码等）"""
    ffprobe = _find_ffprobe()

    result = subprocess.run(
        [
            ffprobe, "-v", "quiet", "-print_format", "json",
            "-show_format", "-show_streams", str(video_path),
        ],
        capture_output=True, timeout=30,
        **SUBPROCESS_KWARGS,
    )

    if result.returncode != 0:
        raise RuntimeError(f"无法读取视频信息: {result.stderr}")

    data = json.loads(result.stdout)

    info = {"filename": Path(video_path).name, "duration": 0, "resolution": "", "has_audio": False}

    fmt = data.get("format", {})
    info["duration"] = float(fmt.get("duration", 0))
    info["size_bytes"] = int(fmt.get("size", 0))

    for stream in data.get("streams", []):
        if stream["codec_type"] == "video":
            w = stream.get("width", 0)
            h = stream.get("height", 0)
            info["resolution"] = f"{w}×{h}"
        elif stream["codec_type"] == "audio":
            info["has_audio"] = True

    return info


def _find_ffprobe() -> str:
    """查找 ffprobe 可执行文件"""
    if Path(FFPROBE_BIN).exists():
        return str(FFPROBE_BIN)
    ffmpeg_path = find_ffmpeg()
    ffprobe_path = str(Path(ffmpeg_path).parent / "ffprobe.exe")
    if Path(ffprobe_path).exists():
        return ffprobe_path
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe
    raise FileNotFoundError("未找到 ffprobe")
