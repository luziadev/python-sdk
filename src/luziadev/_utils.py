from __future__ import annotations


def filter_none(params: dict) -> dict:
    """Remove keys with None values from a dictionary."""
    return {k: v for k, v in params.items() if v is not None}
