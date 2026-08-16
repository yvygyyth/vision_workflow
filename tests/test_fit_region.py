"""region 显示缩放。"""

from vision_workflow.display import fit_region


def test_fit_region_scales_all_components(monkeypatch) -> None:
    monkeypatch.setattr(
        "vision_workflow.display.cached_template_scale",
        lambda: 1.5,
    )
    assert fit_region((100, 200, 300, 40)) == (150, 300, 450, 60)


def test_fit_region_raw_passthrough(monkeypatch) -> None:
    monkeypatch.setattr(
        "vision_workflow.display.cached_template_scale",
        lambda: 2.0,
    )
    assert fit_region((10, 20, 30, 40), fit=False) == (10, 20, 30, 40)
