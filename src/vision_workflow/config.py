"""运行时设置（环境变量 / .env）。"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="VISION_WORKFLOW_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = "dev"
    log_level: str = "INFO"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    dir: str = "logs"


class RuntimeConfig(BaseModel):
    app: dict[str, Any] = Field(default_factory=dict)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    root_dir: Path = ROOT_DIR

    def resolve_path(self, path: str | Path) -> Path:
        p = Path(path)
        if p.is_absolute():
            return p
        return (self.root_dir / p).resolve()


@lru_cache(maxsize=1)
def get_settings(_config_path: str | None = None) -> RuntimeConfig:
    env = AppSettings()
    return RuntimeConfig(
        app={"name": "vision-workflow", "env": env.env},
        logging=LoggingConfig(level=env.log_level, dir="logs"),
        root_dir=ROOT_DIR,
    )


def reload_settings(config_path: str | None = None) -> RuntimeConfig:
    get_settings.cache_clear()
    return get_settings(config_path)
