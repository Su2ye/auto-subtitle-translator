"""生成 ThinkSub 应用图标（纯 Python，不依赖 PySide6）"""
import struct
import zlib
from pathlib import Path


def make_png(size: int) -> bytes:
    """生成 Indigo 底色 + 白色对话气泡图标"""

    def pack_chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = b"".join([
        struct.pack(">I", size),
        struct.pack(">I", size),
        b"\x08\x02",
        b"\x00\x00\x00",
    ])

    raw_rows = []
    m = size // 8
    for y in range(size):
        raw_rows.append(b"\x00")  # filter none
        for x in range(size):
            # 气泡区域（圆角矩形 + 尾部三角）
            in_bubble = False
            bx, bw = m, size - 2 * m
            by_top, by_bot = m, m + size * 3 // 4
            if bx <= x < bx + bw and by_top <= y < by_bot:
                in_bubble = True
            # 尾巴三角
            cx = size // 2
            tail_h = size // 8
            tail_top = by_bot
            if y >= tail_top and abs(x - cx) < (size // 4) * (1 - (y - tail_top) / tail_h):
                in_bubble = True
            # 字幕线（灰色细线）
            on_line = False
            line_y = size // 3
            for i in range(3):
                ly = line_y + i * size // 6
                if abs(y - ly) <= 1 and size // 4 <= x < size * 3 // 4:
                    on_line = True

            if in_bubble:
                raw_rows[-1] += b"\xff\xff\xff\xff"  # 白色
            elif on_line:
                raw_rows[-1] += b"\xa0\xa0\xa0\xff"  # 灰色
            else:
                raw_rows[-1] += b"\x4f\x46\xe5\xff"  # Indigo

    raw_data = b"".join(raw_rows)
    idat = pack_chunk(b"IDAT", zlib.compress(raw_data))
    iend = pack_chunk(b"IEND", b"")

    return header + pack_chunk(b"IHDR", ihdr) + idat + iend


def main():
    out = Path("src/gui/resources")
    out.mkdir(parents=True, exist_ok=True)

    for sz in [16, 32, 48, 128, 256]:
        png = make_png(sz)
        (out / f"icon_{sz}.png").write_bytes(png)
        print(f"  {sz}x{sz}")

    # ICO（256x256 → width/height 填 0）
    png_data = make_png(256)
    ico = struct.pack("<HHH", 0, 1, 1)
    ico += struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png_data), 22)
    ico += png_data
    (out / "icon.ico").write_bytes(ico)
    print("  icon.ico")


if __name__ == "__main__":
    main()
