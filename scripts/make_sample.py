"""生成一张占位模板图（可按需裁剪替换）。"""

from pathlib import Path

from PIL import Image, ImageDraw


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "ming_jiang_sha" / "demo.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (120, 40), color=(24, 48, 72))
    draw = ImageDraw.Draw(img)
    draw.rectangle((2, 2, 117, 37), outline=(90, 180, 255), width=2)
    draw.text((16, 12), "demo", fill=(240, 248, 255))
    img.save(out)
    print(f"created: {out}")


if __name__ == "__main__":
    main()
