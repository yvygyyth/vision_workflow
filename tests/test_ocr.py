"""区域截图 / OCR。"""

from pathlib import Path

from PIL import Image

from vision_workflow.vision.capture import grab_region
from vision_workflow.vision.ocr import image_to_text


def test_grab_region_uses_fit_and_bbox(monkeypatch) -> None:
    captured: dict = {}

    def fake_grab(bbox=None):
        captured["bbox"] = bbox
        return Image.new("RGB", (bbox[2] - bbox[0], bbox[3] - bbox[1]), color=(1, 2, 3))

    monkeypatch.setattr(
        "vision_workflow.display.cached_template_scale",
        lambda: 2.0,
    )
    monkeypatch.setattr("PIL.ImageGrab.grab", fake_grab)

    img = grab_region((10, 20, 30, 40), region_fit=True)
    assert captured["bbox"] == (20, 40, 80, 120)
    assert img.size == (60, 80)


def test_grab_region_raw(monkeypatch) -> None:
    captured: dict = {}

    def fake_grab(bbox=None):
        captured["bbox"] = bbox
        return Image.new("RGB", (10, 10), color=(0, 0, 0))

    monkeypatch.setattr("PIL.ImageGrab.grab", fake_grab)
    grab_region((1, 2, 3, 4), region_fit=False)
    assert captured["bbox"] == (1, 2, 4, 6)


def test_image_to_text_joins_blocks(monkeypatch) -> None:
    class _Out:
        txts = ("左慈", "赠礼")

    calls: list[dict] = []

    def fake_engine(arr, **kwargs):
        calls.append(kwargs)
        return _Out()

    monkeypatch.setattr("vision_workflow.vision.ocr._get_engine", lambda: fake_engine)

    text = image_to_text(Image.new("RGB", (8, 8), color=(255, 255, 255)))
    assert text == "左慈赠礼"
    assert calls == [{"use_det": False}]


def test_image_to_text_use_det_true(monkeypatch) -> None:
    class _Out:
        txts = ("马超赠礼",)

    calls: list[dict] = []

    def fake_engine(arr, **kwargs):
        calls.append(kwargs)
        return _Out()

    monkeypatch.setattr("vision_workflow.vision.ocr._get_engine", lambda: fake_engine)
    assert image_to_text(Image.new("RGB", (4, 4)), use_det=True) == "马超赠礼"
    assert calls == [{"use_det": True}]


def test_image_to_text_empty(monkeypatch) -> None:
    class _Out:
        txts = ()

    monkeypatch.setattr(
        "vision_workflow.vision.ocr._get_engine",
        lambda: (lambda arr, **kwargs: _Out()),
    )
    assert image_to_text(Image.new("RGB", (4, 4))) == ""


def test_image_to_text_from_path(monkeypatch, tmp_path: Path) -> None:
    path = tmp_path / "a.png"
    Image.new("RGB", (4, 4), color=(10, 10, 10)).save(path)

    class _Out:
        txts = ("ok",)

    monkeypatch.setattr(
        "vision_workflow.vision.ocr._get_engine",
        lambda: (lambda arr, **kwargs: _Out()),
    )
    assert image_to_text(path) == "ok"
