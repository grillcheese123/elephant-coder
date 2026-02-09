"""Common message template helper."""

from __future__ import annotations


class MessageTemplate:
    """Simple formatter for channel payload text."""

    def __init__(self, channel: str):
        self.channel = channel

    def render(self, content: str) -> str:
        return f"{self.channel}:{content}"

