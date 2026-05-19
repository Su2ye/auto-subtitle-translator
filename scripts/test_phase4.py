"""
Phase 4 集成测试：字幕文件生成

用法:
    python scripts/test_phase4.py
"""

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.subtitle_writer import write_srt, write_ass, write_subtitles


def main():
    segments = [
        {"start": 1.5, "end": 4.0, "original": "Hello, how are you?",
         "chinese": "您好,您好吗?"},
        {"start": 4.5, "end": 7.2, "original": "Machine learning is changing",
         "chinese": "机器学习正在改变世界."},
        {"start": 8.0, "end": 10.5, "original": "今日はいい天気ですね。",
         "chinese": "今天天气很好."},
    ]

    d = Path(tempfile.gettempdir()) / "thinksub"

    # SRT
    srt = write_srt(segments, d / "test.srt")
    content = srt.read_text("utf-8-sig")
    checks = [
        ("SRT timestamp format", "00:00:01,500" in content),
        ("Has original text", "Hello" in content),
        ("Has Chinese text", "您" in content),
        ("Bilingual separator", "|" in content),
    ]
    for name, ok in checks:
        print(f"  SRT {name}: {ok}")

    # ASS
    ass = write_ass(segments, d / "test.ass")
    content_ass = ass.read_text("utf-8-sig")
    checks_ass = [
        ("ASS header", "[Script Info]" in content_ass),
        ("Original style", "Style: Original" in content_ass),
        ("Chinese style", "Style: Chinese" in content_ass),
        ("Chinese text", "今天天气很好" in content_ass),
        ("ASS newline", r"{\N}" in content_ass),
        ("Dialogue events", "Dialogue:" in content_ass),
        ("UTF-8 BOM", ass.read_bytes()[:3] == b"\xef\xbb\xbf"),
    ]
    for name, ok in checks_ass:
        print(f"  ASS {name}: {ok}")

    # Auto format selection
    srt2 = write_subtitles(segments, d / "auto.srt")
    ass2 = write_subtitles(segments, d / "auto.ass")
    print(f"  Auto SRT: {'OK' if srt2.suffix == '.srt' else 'FAIL'}")
    print(f"  Auto ASS: {'OK' if ass2.suffix == '.ass' else 'FAIL'}")

    # Cleanup
    for f in [srt, ass, srt2, ass2]:
        f.unlink(missing_ok=True)

    all_srt = all(ok for _, ok in checks)
    all_ass = all(ok for _, ok in checks_ass)
    if all_srt and all_ass:
        print("\nPhase 4 字幕生成验证通过")
    else:
        print("\n有检查项失败")


if __name__ == "__main__":
    main()
