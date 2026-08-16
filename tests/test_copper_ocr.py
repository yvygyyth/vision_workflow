"""铜币 OCR 解析。"""

from vision_workflow.apps.ming_jiang_sha.parts.qian_li_dan_qi.utils.bag import (
    parse_copper_text,
)


def test_parse_copper_plain() -> None:
    assert parse_copper_text("1234") == 1234


def test_parse_copper_with_comma() -> None:
    assert parse_copper_text("1,234") == 1234
    assert parse_copper_text("1，234") == 1234


def test_parse_copper_ocr_noise() -> None:
    assert parse_copper_text("O12l") == 121
    assert parse_copper_text("铜币 56") == 56


def test_parse_copper_empty() -> None:
    assert parse_copper_text("") is None
    assert parse_copper_text("abc") is None
