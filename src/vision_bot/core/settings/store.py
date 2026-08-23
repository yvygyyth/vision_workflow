"""设置读写：项目根 match_settings.json。"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from vision_bot.core.paths import project_root
from vision_bot.core.settings.match import MatchSettings

logger = logging.getLogger(__name__)

_SETTINGS_NAME = "match_settings.json"
_cache: MatchSettings | None = None


def settings_path() -> Path:
    return project_root() / _SETTINGS_NAME


def default_match_settings() -> MatchSettings:
    return MatchSettings()


def get_match_settings() -> MatchSettings:
    global _cache
    if _cache is None:
        _cache = load_match_settings()
    return _cache


def reload_match_settings() -> MatchSettings:
    global _cache
    _cache = load_match_settings()
    return _cache


def load_match_settings() -> MatchSettings:
    path = settings_path()
    if not path.exists():
        return default_match_settings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return MatchSettings.from_dict(data if isinstance(data, dict) else None)
    except Exception as exc:
        logger.warning("读取设置失败，使用默认: %s", exc)
        return default_match_settings()


def save_match_settings(settings: MatchSettings) -> MatchSettings:
    global _cache
    validated = settings.validate()
    path = settings_path()
    path.write_text(
        json.dumps(validated.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    _cache = validated
    try:
        from vision_bot.core.display import clear_display_cache

        clear_display_cache()
    except Exception:
        pass
    return validated
