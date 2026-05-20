"""硬字幕烧录 — FFmpeg subtitles 滤镜"""

import shutil
import subprocess
import tempfile
from pathlib import Path

from src.utils.ffmpeg_utils import find_ffmpeg

DEFAULT_CRF = 18
DEFAULT_PRESET = "medium"


def burn_subtitles(
    video_path: str | Path,
    ass_path: str | Path,
    output_path: str | Path,
    crf: int = DEFAULT_CRF,
    preset: str = DEFAULT_PRESET,
) -> Path:
    """
    将 ASS 字幕烧录到视频中。

    Args:
        video_path: 原始视频路径
        ass_path: ASS 字幕文件路径
        output_path: 输出 MP4 路径
        crf: H.264 CRF，17-23 推荐，越小质量越高
        preset: x264 编码预设
    """
    video_path = Path(video_path)
    ass_path = Path(ass_path)
    output_path = Path(output_path)

    if not video_path.exists():
        raise FileNotFoundError(f"视频文件不存在: {video_path}")
    if not ass_path.exists():
        raise FileNotFoundError(f"字幕文件不存在: {ass_path}")

    ffmpeg = find_ffmpeg()

    # subtitles 滤镜有路径解析问题（: 被解释为参数分隔符）
    # 解决：将 ass 复制到临时目录，用不含特殊字符的简短路径
    tmp_ass = Path(tempfile.gettempdir()) / f"thinksub_{ass_path.name}"
    shutil.copy2(ass_path, tmp_ass)

    try:
        cmd = [
            ffmpeg,
            "-i", str(video_path),
            "-vf", f"subtitles={tmp_ass.name}",
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "copy",
            "-y",
            str(output_path),
        ]

        result = subprocess.run(
            cmd, capture_output=True, timeout=3600,
            encoding="utf-8", errors="replace", text=True,
            cwd=str(tmp_ass.parent),
        )

        if result.returncode != 0:
            err = result.stderr
            # 查找关键错误行
            for line in err.splitlines():
                if "Error" in line or "error" in line or "failed" in line.lower():
                    raise RuntimeError(f"FFmpeg 烧录失败: {line.strip()}")
            raise RuntimeError(f"FFmpeg 烧录失败 (返回码={result.returncode})\n{err[-300:]}")
    finally:
        tmp_ass.unlink(missing_ok=True)

    return output_path
