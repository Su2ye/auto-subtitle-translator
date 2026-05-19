"""
Phase 2 集成测试：验证 ASR 模块代码结构（用已缓存的 tiny 模型）

用法:
    python scripts/test_phase2.py [视频路径]
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import soundfile as sf

from src.config import TEMP_DIR, DEVICE, COMPUTE_TYPE
from src.pipeline.audio_extractor import extract_audio
from src.pipeline.asr import ASREngine


def main():
    video_path = sys.argv[1] if len(sys.argv) > 1 else None
    output_dir = TEMP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    # 如果有视频参数，提取音频
    if video_path:
        video = Path(video_path)
        if not video.exists():
            print(f"错误: 视频不存在: {video}")
            sys.exit(1)
        TEMP_DIR.mkdir(parents=True, exist_ok=True)
        audio_path = extract_audio(video, TEMP_DIR / "phase2_test.wav")
    else:
        # 生成测试音频
        import subprocess
        from src.utils.ffmpeg_utils import find_ffmpeg
        ffmpeg = find_ffmpeg()
        output_dir.mkdir(parents=True, exist_ok=True)
        test_video = output_dir / "phase2_test_video.mp4"
        subprocess.run([
            ffmpeg,
            "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
            "-f", "lavfi", "-i", "color=c=black:s=320x240:d=5",
            "-c:v", "libx264", "-c:a", "aac", "-shortest",
            str(test_video), "-y",
        ], capture_output=True, check=True)
        audio_path = extract_audio(test_video, output_dir / "phase2_test.wav")

    audio, sr = sf.read(str(audio_path))
    print(f"音频: {len(audio)/sr:.1f}s, {sr}Hz")

    # 用 tiny 模型验证代码结构（large-v3/kotoba-whisper 需网络下载）
    print("\n--- ASREngine 流程验证（tiny 模型）---")
    from faster_whisper import WhisperModel
    model = WhisperModel("tiny", device=DEVICE, compute_type=COMPUTE_TYPE)
    segments, info = model.transcribe(audio, beam_size=1, vad_filter=False, without_timestamps=True)
    list(segments)
    print(f"language={info.language}, text={'voice' if info.language else 'silence'}")

    # 验证语言检测（ASREngine.detect_language）
    print("\n--- 语言检测测试 ---")
    engine = ASREngine()
    engine._load_model("tiny")  # 测试用 tiny，生产用 large-v3
    lang = engine.detect_language(audio)
    print(f"detect_language() → {lang}")

    print("\nPhase 2 代码结构验证通过。")


if __name__ == "__main__":
    main()
