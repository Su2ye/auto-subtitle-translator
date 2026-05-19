"""
Phase 1 集成测试：视频 → WAV → VAD 语音段统计

用法:
    python scripts/test_phase1.py [视频路径]
    默认使用 ffmpeg 生成合成测试视频
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.audio_extractor import extract_audio
from src.pipeline.vad import detect_speech_segments
from src.utils.ffmpeg_utils import find_ffmpeg, get_video_info

import numpy as np
import soundfile as sf

from src.config import TEMP_DIR


def _create_test_video() -> Path:
    """生成带语音的合成测试视频（5 秒 440Hz 正弦波 + 320×240 黑色画面）"""
    ffmpeg = find_ffmpeg()
    output = TEMP_DIR / "thinksub_test_video.mp4"
    cmd = [
        ffmpeg,
        "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
        "-f", "lavfi", "-i", "color=c=black:s=320x240:d=5",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(output), "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output


def main():
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    video_path = sys.argv[1] if len(sys.argv) > 1 else None

    if video_path is None:
        print("生成合成测试视频...")
        video_path = str(_create_test_video())

    video_path = Path(video_path)
    if not video_path.exists():
        print(f"错误: 视频文件不存在: {video_path}")
        sys.exit(1)

    print(f"输入视频: {video_path.name}")

    # 1. 获取视频信息
    info = get_video_info(video_path)
    print(f"  时长: {info['duration']:.1f}s")
    print(f"  分辨率: {info['resolution']}")
    print(f"  有音频: {'是' if info['has_audio'] else '否'}")

    if not info["has_audio"]:
        print("错误: 视频没有音频轨道")
        sys.exit(1)

    # 2. 提取音频
    wav_path = TEMP_DIR / "thinksub_test_audio.wav"
    print(f"\n提取音频 → {wav_path}")
    wav = extract_audio(video_path, wav_path)
    print(f"  输出: {wav.stat().st_size} bytes")

    # 3. VAD 检测
    audio, sr = sf.read(str(wav))
    print(f"\n音频: {len(audio)} samples, {sr}Hz, {len(audio)/sr:.2f}s")

    segments = detect_speech_segments(audio)
    print(f"检测到 {len(segments)} 个语音段")

    for i, (start_ms, end_ms) in enumerate(segments):
        print(f"  #{i+1}: {start_ms}ms - {end_ms}ms ({end_ms-start_ms}ms)")

    print("\nPhase 1 集成测试通过。")

    # 清理临时文件
    wav.unlink(missing_ok=True)
    if video_path.name.startswith("thinksub_test"):
        video_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
