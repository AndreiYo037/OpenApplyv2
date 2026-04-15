"""Aggregate contact quality from top ranked contacts."""

from __future__ import annotations

from typing import Any, Dict, List


def compute_contact_quality(scored_contacts: List[Dict[str, Any]]) -> float:
    """Compute CONTACT_QUALITY (0-100) from top 2 contacts."""
    if not scored_contacts:
        return 0.0

    sorted_contacts = sorted(
        scored_contacts,
        key=lambda item: float(item.get("score", 0.0) or 0.0),
        reverse=True,
    )

    first = float(sorted_contacts[0].get("score", 0.0) or 0.0)
    if len(sorted_contacts) == 1:
        return round(max(0.0, min(first, 100.0)), 2)

    second = float(sorted_contacts[1].get("score", 0.0) or 0.0)
    quality = 0.7 * first + 0.3 * second
    return round(max(0.0, min(quality, 100.0)), 2)
