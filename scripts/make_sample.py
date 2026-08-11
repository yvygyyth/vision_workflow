"""生成一张联调用示例图。"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "data" / "samples" / "demo.png"
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (640, 360), color=(24, 48, 72))
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 600, 320), outline=(90, 180, 255), width=3)
    draw.text((80, 140), "Vision Workflow Demo", fill=(240, 248, 255))
    draw.text((80, 190), "intent: open_url", fill=(180, 220, 255))
    img.save(out)

    # rule 识图器可读的 sidecar
    sidecar = out.with_suffix(".json")
    sidecar.write_text(
        '{\n  "intent": "notify",\n  "confidence": 0.92,\n'
        '  "text": "demo image",\n  "payload": {"message": "示例识图成功"}\n}\n',
        encoding="utf-8",
    )
    print(f"created: {out}")
    print(f"created: {sidecar}")


if __name__ == "__main__":
    main()
