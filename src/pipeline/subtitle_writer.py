"""字幕文件生成 — 双语 SRT / ASS"""

import re
from pathlib import Path

ASS_STYLE_HEADER = """[Script Info]
Title: ThinkSub
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Chinese,Arial,30,&H00FFFFFF,&H00000000,&H000000FF,&H80000000,0,0,0,0,100,100,0,0,1,2,0,2,60,60,50,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_time(seconds: float, ass: bool = False) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    if ass:
        return f"{h:01d}:{m:02d}:{s:02d}.{ms:02d}"
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments: list[dict], output_path: str | Path) -> Path:
    output_path = Path(output_path)
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_time(seg["start"])
        end = _format_time(seg["end"])
        text = f"{seg['original']}\n{seg['chinese']}"
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    output_path.write_text("".join(lines), encoding="utf_8_sig")
    return output_path


def write_ass(segments: list[dict], output_path: str | Path,
              video_width: int = 1920, video_height: int = 1080,
              position: str = "bottom") -> Path:
    output_path = Path(output_path)

    header = ASS_STYLE_HEADER.replace(
        "PlayResX: 1920\nPlayResY: 1080",
        f"PlayResX: {video_width}\nPlayResY: {video_height}",
    )

    v_margin = video_height // 12
    header = re.sub(
        r"Style: Chinese,.*",
        f"Style: Chinese,Arial,30,&H00FFFFFF,&H00000000,&H000000FF,&H80000000,"
        f"0,0,0,0,100,100,0,0,1,2,0,2,60,60,{v_margin},0",
        header,
    )

    events = []
    for seg in segments:
        start = _format_time(seg["start"], ass=True)
        end = _format_time(seg["end"], ass=True)
        original = _escape_ass(seg["original"])
        chinese = _escape_ass(seg["chinese"])
        # 原文 22px 灰色在上，\N 换行，中文 30px 白色在下
        text = (
            f"{{\\fs22\\c&HCCCCCC&}}{original}"
            f"\\N"
            f"{{\\fs30\\c&HFFFFFF&\\3c&H000000&}}{chinese}"
        )
        events.append(f"Dialogue: 0,{start},{end},Chinese,,0,0,0,,{text}")

    content = header + "\n".join(events) + "\n"
    output_path.write_text(content, encoding="utf_8_sig")
    return output_path


def _escape_ass(text: str) -> str:
    text = text.replace("\\", "\\\\")
    text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def write_subtitles(segments: list[dict], output_path: str | Path,
                    fmt: str = "ass", **kwargs) -> Path:
    output_path = Path(output_path)
    ext = output_path.suffix.lower()
    if fmt == "srt" or ext == ".srt":
        return write_srt(segments, output_path)
    elif fmt == "ass" or ext == ".ass":
        return write_ass(segments, output_path, **kwargs)
    else:
        raise ValueError(f"不支持的字幕格式: {fmt}，请使用 srt 或 ass")
