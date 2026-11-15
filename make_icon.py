"""Gera o icone .ico do app (circulo azul + 'V')."""
import os
import sys

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets", "icon.ico")


def build(size=256):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pad = size * 0.03
    d.ellipse((pad, pad, size - pad, size - pad), fill="#1f6feb")
    s = size / 64.0
    d.polygon([(18 * s, 20 * s), (46 * s, 20 * s), (32 * s, 47 * s)], fill="#ffffff")
    return img


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    img = build(256)
    img.save(OUT, format="ICO", sizes=[(256, 256), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("icone:", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
