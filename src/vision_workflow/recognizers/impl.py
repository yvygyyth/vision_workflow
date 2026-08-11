"""内置识图器实现。"""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PIL import Image

from vision_workflow.models import IntentType, RecognitionResult
from vision_workflow.recognizers import BaseRecognizer, register_recognizer

logger = logging.getLogger(__name__)


def _validate_image(image_path: Path) -> None:
    if not image_path.exists():
        raise FileNotFoundError(f"图片不存在: {image_path}")
    if not image_path.is_file():
        raise ValueError(f"路径不是文件: {image_path}")
    # 用 Pillow 做一次可读性校验
    with Image.open(image_path) as img:
        img.verify()


def _parse_intent(value: str) -> IntentType:
    try:
        return IntentType(value)
    except ValueError:
        return IntentType.UNKNOWN


@register_recognizer("mock")
class MockRecognizer(BaseRecognizer):
    """本地联调用：不调用外部模型，按配置返回固定意图。"""

    def recognize(self, image_path: Path) -> RecognitionResult:
        _validate_image(image_path)
        intent = _parse_intent(str(self.options.get("default_intent", "notify")))
        payload = dict(self.options.get("default_payload") or {})
        confidence = float(self.options.get("confidence", 0.95))
        text = str(self.options.get("default_text") or f"mock intent={intent.value}")
        return RecognitionResult(
            image_path=str(image_path),
            text=text,
            intent=intent,
            confidence=confidence,
            payload=payload,
            raw={"mode": "mock"},
            recognizer=self.name,
        )


@register_recognizer("rule")
class RuleRecognizer(BaseRecognizer):
    """基于图片旁路文本 / sidecar JSON / 文件名规则的轻量识别。

    约定：
    - 同名 .txt：OCR 文本（可手工放置）
    - 同名 .json：直接给出 intent/payload
    - 否则用文件名关键词 + keyword_rules 推断
    """

    def recognize(self, image_path: Path) -> RecognitionResult:
        _validate_image(image_path)

        sidecar_json = image_path.with_suffix(".json")
        if sidecar_json.exists():
            data = json.loads(sidecar_json.read_text(encoding="utf-8"))
            intent = _parse_intent(str(data.get("intent", "unknown")))
            return RecognitionResult(
                image_path=str(image_path),
                text=str(data.get("text", "")),
                intent=intent,
                confidence=float(data.get("confidence", 0.9)),
                payload=dict(data.get("payload") or {}),
                raw={"source": "sidecar_json", "data": data},
                recognizer=self.name,
            )

        text = ""
        sidecar_txt = image_path.with_suffix(".txt")
        if sidecar_txt.exists():
            text = sidecar_txt.read_text(encoding="utf-8").strip()
        else:
            text = image_path.stem

        intent, confidence, payload = self._match_rules(text)
        return RecognitionResult(
            image_path=str(image_path),
            text=text,
            intent=intent,
            confidence=confidence,
            payload=payload,
            raw={"source": "rule", "matched_text": text},
            recognizer=self.name,
        )

    def _match_rules(self, text: str) -> tuple[IntentType, float, dict[str, Any]]:
        rules = list(self.options.get("keyword_rules") or [])
        lower = text.lower()

        # URL 优先
        urls = re.findall(r"https?://[^\s]+", text)
        if urls:
            return IntentType.OPEN_URL, 0.9, {"url": urls[0]}

        for rule in rules:
            keywords = [str(k) for k in rule.get("keywords") or []]
            if any(k.lower() in lower for k in keywords):
                intent = _parse_intent(str(rule.get("intent", "unknown")))
                payload = dict(rule.get("payload") or {})
                if intent == IntentType.OPEN_URL and "url" not in payload:
                    payload["url"] = "https://example.com"
                if intent == IntentType.SAVE_FILE and "filename" not in payload:
                    payload["filename"] = "recognized.txt"
                    payload["content"] = text
                if intent == IntentType.NOTIFY and "message" not in payload:
                    payload["message"] = text
                return intent, 0.75, payload

        return IntentType.NOTIFY, 0.4, {"message": f"未能匹配明确意图，原文: {text}"}


@register_recognizer("openai")
class OpenAIVisionRecognizer(BaseRecognizer):
    """调用 OpenAI 兼容视觉接口。未安装 openai 或缺少密钥时给出明确错误。"""

    SYSTEM_PROMPT = (
        "你是识图执行助手。分析图片内容，输出严格 JSON（不要 markdown）："
        '{"intent":"open_url|save_file|click_button|notify|unknown",'
        '"confidence":0.0到1.0,'
        '"text":"图片中的关键文本",'
        '"payload":{...}}。'
        "open_url 的 payload 需含 url；save_file 需含 filename/content；"
        "notify 需含 message；click_button 需含 target。"
    )

    def recognize(self, image_path: Path) -> RecognitionResult:
        _validate_image(image_path)
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError(
                "未安装 openai，请执行: pip install -e \".[openai]\""
            ) from exc

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("缺少环境变量 OPENAI_API_KEY")

        base_url = os.getenv("OPENAI_BASE_URL") or None
        model = str(self.options.get("model") or os.getenv("OPENAI_VISION_MODEL") or "gpt-4o-mini")

        client = OpenAI(api_key=api_key, base_url=base_url)
        import base64

        mime = "image/png" if image_path.suffix.lower() == ".png" else "image/jpeg"
        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")

        resp = client.chat.completions.create(
            model=model,
            temperature=float(self.options.get("temperature", 0.1)),
            max_tokens=int(self.options.get("max_tokens", 512)),
            messages=[
                {"role": "system", "content": self.SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "请识别该图片并给出可执行意图。"},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"},
                        },
                    ],
                },
            ],
            response_format={"type": "json_object"},
        )

        content = resp.choices[0].message.content or "{}"
        data = json.loads(content)
        intent = _parse_intent(str(data.get("intent", "unknown")))
        payload = dict(data.get("payload") or {})

        # 简单校验 open_url
        if intent == IntentType.OPEN_URL and "url" in payload:
            parsed = urlparse(str(payload["url"]))
            if parsed.scheme not in {"http", "https"}:
                intent = IntentType.UNKNOWN

        return RecognitionResult(
            image_path=str(image_path),
            text=str(data.get("text", "")),
            intent=intent,
            confidence=float(data.get("confidence", 0.0)),
            payload=payload,
            raw={"model": model, "response": data},
            recognizer=self.name,
        )
