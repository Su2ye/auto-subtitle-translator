"""
Phase 5 集成测试：字幕烧录

用法:
    python scripts/test_phase5.py [视频路径]
"""

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import TEMP_DIR
from src.pipeline.subtitle_writer import write_ass
from src.pipeline.hard_sub import burn_subtitles
from src.utils.ffmpeg_utils import find_ffmpeg


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 1. 生成测试视频
    test_video = TEMP_DIR / "phase5_test_video.mp4"
    ffmpeg = find_ffmpeg()
    subprocess.run([
        ffmpeg,
        "-f", "lavfi", "-i", "sine=frequency=440:duration=3",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=3",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(test_video), "-y",
    ], capture_output=True, check=True)
    print(f"Test video: {test_video.stat().st_size} bytes")

    # 2. 生成测试字幕
    segments = [
        {"start": 0.5, "end": 2.5, "original": "Hello World",
         "chinese": "你好世界"},
    ]
    ass_path = TEMP_DIR / "phase5_test.ass"
    write_ass(segments, ass_path, video_width=320, video_height=240)
    print(f"ASS subtitle: {ass_path.stat().st_size} bytes")

    # 3. 烧录
    output = TEMP_DIR / "phase5_output.mp4"
    print(f"Burning subtitles...")
    result = burn_subtitles(test_video, ass_path, output, crf=23, preset="ultrafast")

    print(f"Output video: {result.stat().st_size} bytes")

    # 4. 验证
    if result.exists() and result.stat().st_size > 1000:
        print("Phase 5 硬字幕烧录验证通过")
    else:
        print("错误: 输出文件异常")

    # 清理
    for f in [test_video, ass_path, output]:
        f.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
