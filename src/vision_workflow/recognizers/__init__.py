"""识图器抽象与注册。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from vision_workflow.models import RecognitionResult


class BaseRecognizer(ABC):
    name: str = "base"

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abstractmethod
    def recognize(self, image_path: Path) -> RecognitionResult:
        raise NotImplementedError


_REGISTRY: dict[str, type[BaseRecognizer]] = {}


def register_recognizer(name: str):
    def decorator(cls: type[BaseRecognizer]):
        cls.name = name
        _REGISTRY[name] = cls
        return cls

    return decorator


def get_recognizer(name: str, options: dict[str, Any] | None = None) -> BaseRecognizer:
    if name not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY)) or "(empty)"
        raise KeyError(f"未知识图器: {name}，可选: {available}")
    return _REGISTRY[name](options=options)


def list_recognizers() -> list[str]:
    return sorted(_REGISTRY)
