"""Audit helpers for processor subclasses."""

from __future__ import annotations


class AuditableMixin:
    """Adds a compact audit trail string."""

    def build_audit_prefix(self, *, processor: str, rule: str, priority: int) -> str:
        return f"[proc={processor}|rule={rule}|priority={priority}]"

