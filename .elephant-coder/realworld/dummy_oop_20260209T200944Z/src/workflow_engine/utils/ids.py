"""ID helper functions."""

from __future__ import annotations

from datetime import datetime, timezone
from random import randint


def make_ticket_id(channel: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    suffix = randint(1000, 9999)
    clean = "".join(ch for ch in channel.lower() if ch.isalnum()) or "generic"
    return f"{clean}-{stamp}-{suffix}"

