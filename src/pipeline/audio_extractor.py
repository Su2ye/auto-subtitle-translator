"""从视频中提取音频为 16kHz 单声道 WAV"""

import os
import subprocess
import tempfile
from pathlib import Path

from src.config import SAMPLE_RATE
from src.utils.ffmpeg_utils import find_ffmpeg


def extract_audio(video_path: str | Path, output_path: str | Path | None = None) -> Path:
    """
    从视频中提取音频。

    Args:
        video_path: 输入视频文件路径
        output_path: 输出 WAV 路径，为 None 时自动生成临时文件

    Returns:
        输出的 WAV 文件路径
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")

    if output_path is None:
        fd, temp_name = tempfile.mkstemp(suffix=".wav", prefix="thinksub_")
        os.close(fd)
        output_path = Path(temp_name)
    else:
        output_path = Path(output_path)

    ffmpeg = find_ffmpeg()

    cmd = [
        ffmpeg,
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", str(SAMPLE_RATE),
        "-ac", "1",
        "-y",
        str(output_path),
    ]

    result = subprocess.run(
        cmd, capture_output=True, timeout=300,
        encoding="utf-8", errors="replace", text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg 音频提取失败:\n{result.stderr}")

    return output_path
