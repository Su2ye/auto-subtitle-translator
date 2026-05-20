"""生成蓝色 T 图标的 base64 编码（用于代码内嵌）"""

import base64
import struct
import zlib


def make_png(size: int) -> bytes:
    def pack_chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    header = b"\x89PNG\r\n\x1a\n"
    ihdr = struct.pack(">II", size, size) + b"\x08\x02\x00\x00\x00"
    raw_rows = []
    m = size // 6
    bar_top = m * 2
    bar_bot = bar_top + m
    stem_left = size // 2 - m // 2
    stem_right = size // 2 + m // 2
    stem_bot = size - m

    for y in range(size):
        raw_rows.append(b"\x00")
        for x in range(size):
            in_t = (bar_top <= y < bar_bot and m <= x < size - m) or \
                   (stem_left <= x < stem_right and bar_bot <= y < stem_bot)
            if in_t:
                raw_rows[-1] += b"\xff\xff\xff\xff"
            else:
                raw_rows[-1] += b"\x3b\x82\xf6\xff"

    raw_data = b"".join(raw_rows)
    idat = pack_chunk(b"IDAT", zlib.compress(raw_data))
    iend = pack_chunk(b"IEND", b"")
    return header + pack_chunk(b"IHDR", ihdr) + idat + iend


def main():
    png = make_png(256)
    b64 = base64.b64encode(png).decode("ascii")
    print(f"T_ICON_B64 = \"\"\"\\\n{b64}\"\"\"")
    print(f"\n# Length: {len(b64)} chars")


if __name__ == "__main__":
    main()
