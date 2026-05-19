"""
Phase 3 集成测试：翻译模块（NLLB-200）

用法:
    python scripts/test_phase3.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.pipeline.translator import Translator, translate_segments


def main():
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    t = Translator()
    print("Translator (NLLB-200) loaded\n")

    tests = [
        ("en", "Hello, how are you?", "英→中"),
        ("en", "Machine learning is changing the world.", "英→中 长句"),
        ("ja", "こんにちは、お元気ですか？", "日→中"),
        ("ja", "今日はいい天気ですね。", "日→中 日常"),
        ("ko", "안녕하세요?", "韩→中"),
        ("ko", "오늘 날씨가 좋네요.", "韩→中 日常"),
    ]

    passed = 0
    for lang, text, desc in tests:
        result = t.translate(text, lang)
        ok = bool(result.strip()) and len(result) < len(text) * 3
        status = "OK" if ok else "FAIL"
        if ok:
            passed += 1
        print(f"  {status} [{lang}] {desc}")
        print(f"    原文: {text}")
        print(f"    译文: {result}\n")

    # 批量翻译（同语言）
    print("--- translate_segments ---")
    segs = [
        {"start": 0.0, "end": 2.0, "text": "Hello"},
        {"start": 2.0, "end": 4.0, "text": "Good morning"},
        {"start": 4.0, "end": 6.0, "text": "Thank you"},
    ]
    result = translate_segments(segs, "en")
    for s in result:
        print(f"  [{s['start']}s-{s['end']}s] {s['original']} → {s['chinese']}")
    print(f"  translate_segments OK: {len(result)} segments")

    print(f"\n{passed}/{len(tests)} 通过")
    if passed == len(tests):
        print("Phase 3 翻译模块验证通过")


if __name__ == "__main__":
    main()
