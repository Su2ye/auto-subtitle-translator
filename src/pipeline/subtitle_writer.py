"""字幕文件生成 — 双语 SRT / ASS"""

from pathlib import Path

# ASS 样式定义（设计规范）
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
Style: Original,Arial,16,&H00CCCCCC,&H00000000,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1,0,2,40,40,80,1
Style: Chinese,Microsoft YaHei,26,&H00FFFFFF,&H00000000,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,1.5,0.5,2,40,40,40,0

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def _format_time(seconds: float, ass: bool = False) -> str:
    """秒数 → 时间戳字符串"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    if ass:
        return f"{h:01d}:{m:02d}:{s:02d}.{ms:02d}"  # ASS 用百分秒
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(segments: list[dict], output_path: str | Path) -> Path:
    """
    生成 SRT 双语字幕文件。

    Args:
        segments: [{"start": float, "end": float, "original": str, "chinese": str}, ...]
        output_path: 输出 .srt 文件路径
    """
    output_path = Path(output_path)
    lines = []

    for i, seg in enumerate(segments, 1):
        start = _format_time(seg["start"])
        end = _format_time(seg["end"])
        text = f"{seg['original']} | {seg['chinese']}"
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    output_path.write_text("".join(lines), encoding="utf_8_sig")
    return output_path


def write_ass(segments: list[dict], output_path: str | Path,
              video_width: int = 1920, video_height: int = 1080) -> Path:
    """
    生成 ASS 双语字幕文件（原文灰色小字 + 中文白色大字描边）。

    Args:
        segments: [{"start": float, "end": float, "original": str, "chinese": str}, ...]
        output_path: 输出 .ass 文件路径
        video_width: 视频宽度（用于 PlayResX）
        video_height: 视频高度（用于 PlayResY）
    """
    output_path = Path(output_path)

    header = ASS_STYLE_HEADER.replace(
        "PlayResX: 1920\nPlayResY: 1080",
        f"PlayResX: {video_width}\nPlayResY: {video_height}",
    )

    events = []
    for seg in segments:
        start = _format_time(seg["start"], ass=True)
        end = _format_time(seg["end"], ass=True)
        # \N 是 ASS 换行符
        original = _escape_ass(seg["original"])
        chinese = _escape_ass(seg["chinese"])
        combined = f"{{\\rOriginal}}{original}{{\\N}}{{\\rChinese}}{chinese}"
        events.append(f"Dialogue: 0,{start},{end},Chinese,,0,0,0,,{combined}")

    content = header + "\n".join(events) + "\n"
    output_path.write_text(content, encoding="utf_8_sig")  # UTF-8 BOM
    return output_path


def _escape_ass(text: str) -> str:
    """转义 ASS 特殊字符"""
    # \N 是换行，需要先将文本中的反斜杠转义
    text = text.replace("\\", "\\\\")
    # ASS 的 {} 用于样式控制
    text = text.replace("{", "\\{").replace("}", "\\}")
    return text


def write_subtitles(segments: list[dict], output_path: str | Path,
                    fmt: str = "ass", **kwargs) -> Path:
    """
    生成字幕文件，自动根据扩展名或 fmt 参数选择格式。

    Args:
        segments: 双语片段列表
        output_path: 输出路径
        fmt: "srt" | "ass"
        **kwargs: 传递给具体 writer 的额外参数
    """
    output_path = Path(output_path)
    ext = output_path.suffix.lower()

    if fmt == "srt" or ext == ".srt":
        return write_srt(segments, output_path)
    elif fmt == "ass" or ext == ".ass":
        return write_ass(segments, output_path, **kwargs)
    else:
        raise ValueError(f"不支持的字幕格式: {fmt}，请使用 srt 或 ass")
