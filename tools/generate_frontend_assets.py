"""Generate local PNG assets for the 空空如也GameHub frontend."""

from __future__ import annotations

import math
import struct
import zlib
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
COVER_DIR = ROOT_DIR / "frontend" / "public" / "assets" / "covers"
AD_DIR = ROOT_DIR / "frontend" / "public" / "assets" / "ads"


Color = tuple[int, int, int]


def main() -> None:
    """Generate cover and ad placeholder images."""
    COVER_DIR.mkdir(parents=True, exist_ok=True)
    AD_DIR.mkdir(parents=True, exist_ok=True)

    cover_specs = [
        ("game-placeholder.png", (14, 20, 31), (45, 212, 191), "placeholder"),
    ]
    for filename, start_color, end_color, motif in cover_specs:
        write_png(
            COVER_DIR / filename,
            720,
            960,
            make_cover_pixels(720, 960, start_color, end_color, motif),
        )

    ad_specs = [
        ("home-top.png", 1200, 280, (12, 18, 28), (45, 212, 191), "banner"),
        ("sidebar.png", 520, 720, (24, 20, 36), (244, 114, 182), "side"),
    ]
    for filename, width, height, start_color, end_color, motif in ad_specs:
        write_png(
            AD_DIR / filename,
            width,
            height,
            make_cover_pixels(width, height, start_color, end_color, motif),
        )


def make_cover_pixels(
    width: int,
    height: int,
    start_color: Color,
    end_color: Color,
    motif: str,
) -> list[list[Color]]:
    """Create stylized cover pixels using deterministic geometry."""
    pixels: list[list[Color]] = []
    for y in range(height):
        row: list[Color] = []
        vertical_ratio = y / max(height - 1, 1)
        for x in range(width):
            horizontal_ratio = x / max(width - 1, 1)
            color = blend(start_color, end_color, vertical_ratio * 0.74)
            color = add_noise(color, x, y, amount=10)
            color = apply_vignette(color, horizontal_ratio, vertical_ratio)
            color = apply_motif(color, x, y, width, height, motif)
            row.append(color)
        pixels.append(row)
    return pixels


def apply_motif(
    color: Color,
    x: int,
    y: int,
    width: int,
    height: int,
    motif: str,
) -> Color:
    """Apply a theme-specific geometric motif."""
    center_x = width / 2
    center_y = height / 2

    if motif == "stars":
        orbit = abs(math.sin((x + y) / 58))
        if (x * 17 + y * 29) % 251 == 0:
            return lighten(color, 82)
        if abs(math.hypot(x - center_x, y - center_y) - height * 0.24) < 3:
            return lighten(color, int(45 * orbit))

    if motif == "city":
        if y > height * 0.48 and x % 95 < 45:
            color = darken(color, 18)
        if y > height * 0.56 and (x // 22 + y // 28) % 7 == 0:
            return lighten(color, 70)

    if motif == "workshop":
        gear_radius = height * 0.18
        distance = math.hypot(x - center_x, y - height * 0.42)
        if abs(distance - gear_radius) < 8:
            return lighten(color, 58)
        if x % 90 < 8 or y % 120 < 8:
            color = lighten(color, 18)

    if motif == "paper":
        fold = abs(x - (width * 0.28 + y * 0.18))
        if fold < 5:
            return lighten(color, 75)
        if (x + y) % 140 < 6:
            color = lighten(color, 16)

    if motif == "arena":
        ring_distance = math.hypot(x - center_x, y - center_y)
        if abs(ring_distance - height * 0.22) < 5:
            return lighten(color, 72)
        if abs(x - center_x) < 5 or abs(y - center_y) < 5:
            color = lighten(color, 32)

    if motif == "waves":
        wave = math.sin(x / 32 + y / 90)
        if abs(wave) < 0.08:
            return lighten(color, 58)
        if abs(math.sin((x + y) / 44)) < 0.03:
            color = lighten(color, 24)

    if motif == "placeholder":
        if x % 96 < 5 or y % 96 < 5:
            color = lighten(color, 18)
        ring_distance = math.hypot(x - center_x, y - height * 0.38)
        if abs(ring_distance - height * 0.18) < 7:
            return lighten(color, 66)

    if motif in {"banner", "side", "feed"}:
        diagonal = (x + y * 1.35) % 180
        if diagonal < 18:
            color = lighten(color, 32)
        if abs(math.sin(x / 44) + math.cos(y / 38)) < 0.08:
            color = lighten(color, 26)

    return color


def write_png(path: Path, width: int, height: int, pixels: list[list[Color]]) -> None:
    """Write RGB pixels to a PNG file."""
    raw_rows = []
    for row in pixels:
        raw_rows.append(b"\x00" + b"".join(bytes(pixel) for pixel in row))
    raw_data = b"".join(raw_rows)
    compressed_data = zlib.compress(raw_data, level=9)
    png_data = b"".join(
        [
            b"\x89PNG\r\n\x1a\n",
            make_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)),
            make_chunk(b"IDAT", compressed_data),
            make_chunk(b"IEND", b""),
        ]
    )
    path.write_bytes(png_data)


def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Create a PNG chunk with CRC."""
    checksum = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", checksum)


def blend(start_color: Color, end_color: Color, ratio: float) -> Color:
    """Blend two RGB colors."""
    safe_ratio = max(0.0, min(ratio, 1.0))
    return tuple(
        int(start + (end - start) * safe_ratio)
        for start, end in zip(start_color, end_color)
    )


def add_noise(color: Color, x: int, y: int, amount: int) -> Color:
    """Add deterministic texture noise."""
    noise = ((x * 37 + y * 17 + x * y) % (amount * 2 + 1)) - amount
    return clamp_color(tuple(channel + noise for channel in color))


def apply_vignette(color: Color, x_ratio: float, y_ratio: float) -> Color:
    """Darken image edges to keep foreground UI readable."""
    distance = math.hypot(x_ratio - 0.5, y_ratio - 0.48)
    darken_amount = int(max(0.0, distance - 0.18) * 95)
    return darken(color, darken_amount)


def lighten(color: Color, amount: int) -> Color:
    """Lighten an RGB color by amount."""
    return clamp_color(tuple(channel + amount for channel in color))


def darken(color: Color, amount: int) -> Color:
    """Darken an RGB color by amount."""
    return clamp_color(tuple(channel - amount for channel in color))


def clamp_color(color: tuple[int, int, int]) -> Color:
    """Clamp an RGB color into byte range."""
    return tuple(max(0, min(255, channel)) for channel in color)


if __name__ == "__main__":
    main()
