"""Minimal OpenRouter client for Elephant Coder."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib import error, request


@dataclass
class OpenRouterResult:
    """Normalized OpenRouter response."""

    content: str
    usage: dict[str, int]
    estimated_cost_usd: float
    raw: dict[str, Any]


class OpenRouterError(RuntimeError):
    """OpenRouter request error."""


class OpenRouterClient:
    """HTTP client for OpenRouter chat completions."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://openrouter.ai/api/v1",
        app_name: str = "elephant-coder",
    ):
        if not api_key.strip():
            raise OpenRouterError("OPENROUTER_API_KEY is empty.")
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.app_name = app_name

    def chat_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        max_tokens: int,
        temperature: float = 0.2,
        timeout_sec: int = 60,
    ) -> OpenRouterResult:
        """Send chat completion request."""
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            method="POST",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/grillcheese-ai/grilly",
                "X-Title": self.app_name,
            },
        )
        try:
            with request.urlopen(req, timeout=timeout_sec) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
        except error.HTTPError as exc:
            raw = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            raise OpenRouterError(f"HTTP {exc.code}: {raw or exc.reason}") from exc
        except error.URLError as exc:
            raise OpenRouterError(f"Network error: {exc.reason}") from exc
        except TimeoutError as exc:
            raise OpenRouterError("OpenRouter request timed out.") from exc

        choices = data.get("choices") or []
        if not choices:
            raise OpenRouterError("No choices returned from OpenRouter.")

        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()

        usage_raw = data.get("usage") or {}
        usage = {
            "prompt_tokens": int(usage_raw.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage_raw.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage_raw.get("total_tokens", 0) or 0),
        }
        if usage["total_tokens"] == 0:
            usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]

        estimated_cost_usd = 0.0
        for key in ("cost", "total_cost", "estimated_cost"):
            val = usage_raw.get(key)
            if val is not None:
                try:
                    estimated_cost_usd = float(val)
                except (TypeError, ValueError):
                    estimated_cost_usd = 0.0
                break

        return OpenRouterResult(
            content=content,
            usage=usage,
            estimated_cost_usd=estimated_cost_usd,
            raw=data,
        )
