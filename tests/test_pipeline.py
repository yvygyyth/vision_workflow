"""流水线基础测试。"""

from pathlib import Path

from PIL import Image

from vision_workflow.config import reload_settings
from vision_workflow.models import ActionStatus, IntentType
from vision_workflow.pipeline import Pipeline


def _make_image(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (64, 64), color=(10, 20, 30)).save(path)


def test_mock_pipeline_dry_run(tmp_path: Path) -> None:
    img = tmp_path / "a.png"
    _make_image(img)

    cfg = reload_settings()
    cfg.pipeline.recognizer = "mock"
    cfg.pipeline.dry_run = True
    cfg.recognizers["mock"] = {
        "default_intent": "notify",
        "default_payload": {"message": "hello"},
        "confidence": 0.99,
    }

    result = Pipeline(cfg).run(img)
    assert result.success
    assert result.recognition is not None
    assert result.recognition.intent == IntentType.NOTIFY
    assert result.action is not None
    assert result.action.status == ActionStatus.DRY_RUN


def test_rule_sidecar_json(tmp_path: Path) -> None:
    img = tmp_path / "b.png"
    _make_image(img)
    img.with_suffix(".json").write_text(
        '{"intent":"save_file","confidence":0.88,'
        '"text":"hello","payload":{"filename":"out.txt","content":"hi"}}',
        encoding="utf-8",
    )

    cfg = reload_settings()
    cfg.pipeline.recognizer = "rule"
    cfg.pipeline.dry_run = False
    cfg.actions["save_file"] = {
        "enabled": True,
        "output_dir": str(tmp_path / "out"),
    }

    result = Pipeline(cfg).run(img)
    assert result.success
    assert result.action is not None
    assert result.action.status == ActionStatus.SUCCESS
    assert (tmp_path / "out" / "out.txt").read_text(encoding="utf-8") == "hi"


def test_low_confidence_skips(tmp_path: Path) -> None:
    img = tmp_path / "c.png"
    _make_image(img)

    cfg = reload_settings()
    cfg.pipeline.recognizer = "mock"
    cfg.pipeline.min_confidence = 0.9
    cfg.recognizers["mock"] = {
        "default_intent": "notify",
        "default_payload": {"message": "x"},
        "confidence": 0.2,
    }

    result = Pipeline(cfg).run(img)
    assert not result.success
    assert "置信度" in result.message
