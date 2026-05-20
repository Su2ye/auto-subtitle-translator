"""生成 ThinkSub 应用图标 — 蓝色大写 T"""

import struct
import zlib
from pathlib import Path


def make_png(size: int) -> bytes:
    """生成蓝色圆角方形 + 白色 T 的 PNG"""

    def pack_chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", size, size) + b"\x08\x02\x00\x00\x00"

    raw_rows = []
    m = size // 6
    t_bar_top = m * 2
    t_bar_bot = t_bar_top + m
    t_stem_left = size // 2 - m // 2
    t_stem_right = size // 2 + m // 2
    t_stem_bot = size - m

    for y in range(size):
        raw_rows.append(b"\x00")  # filter byte
        for x in range(size):
            # 圆角方形蓝色背景
            in_bg = True
            r = size // 8
            if x < r and y < r and (x - r) ** 2 + (y - r) ** 2 > r * r:
                in_bg = False
            if x >= size - r and y < r and (x - (size - r - 1)) ** 2 + (y - r) ** 2 > r * r:
                in_bg = False
            if x < r and y >= size - r and (x - r) ** 2 + (y - (size - r - 1)) ** 2 > r * r:
                in_bg = False
            if x >= size - r and y >= size - r and (x - (size - r - 1)) ** 2 + (y - (size - r - 1)) ** 2 > r * r:
                in_bg = False

            # T 字母区域
            in_t = False
            # 横杠
            if t_bar_top <= y < t_bar_bot and m <= x < size - m:
                in_t = True
            # 竖杠
            if t_stem_left <= x < t_stem_right and t_bar_bot <= y < t_stem_bot:
                in_t = True

            if in_t:
                raw_rows[-1] += b"\xff\xff\xff\xff"  # 白色 T
            elif in_bg:
                raw_rows[-1] += b"\x1e\x66\xf5\xff"  # 蓝色底
            else:
                raw_rows[-1] += b"\x00\x00\x00\x00"  # 透明

    raw_data = b"".join(raw_rows)
    idat = pack_chunk(b"IDAT", zlib.compress(raw_data))
    iend = pack_chunk(b"IEND", b"")

    return header + pack_chunk(b"IHDR", ihdr) + idat + iend


def main():
    out = Path("src/gui/resources")
    out.mkdir(parents=True, exist_ok=True)

    for sz in [16, 32, 48, 128, 256]:
        b = make_png(sz)
        (out / f"icon_{sz}.png").write_bytes(b)
        print(f"  {sz}x{sz}")

    # ICO
    png = make_png(256)
    ico = struct.pack("<HHH", 0, 1, 1)
    ico += struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png), 22)
    ico += png
    (out / "icon.ico").write_bytes(ico)
    print("  icon.ico")


if __name__ == "__main__":
    main()
