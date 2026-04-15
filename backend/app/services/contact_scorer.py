"""Contact scoring service."""

from __future__ import annotations

from typing import Any, Dict, List


def compute_contact_score(contacts: List[Dict[str, Any]]) -> float:
    if not contacts:
        return 0.0

    def confidence(item: Dict[str, Any]) -> float:
        return max(0.0, min(float(item.get("confidence", 0.0) or 0.0), 1.0))

    top = contacts[:2]
    if len(top) == 1:
        confidence_component = confidence(top[0])
    else:
        confidence_component = 0.7 * confidence(top[0]) + 0.3 * confidence(top[1])

    channel_component = 0.0
    if any(c.get("linkedin_url") for c in contacts):
        channel_component += 0.5
    if any(c.get("email") for c in contacts):
        channel_component += 0.5

    role_component = 0.0
    role_text = " ".join(str(c.get("role", "")).lower() for c in top)
    if any(token in role_text for token in ("recruiter", "hiring manager", "talent", "manager")):
        role_component = 1.0

    score = 0.7 * confidence_component + 0.2 * channel_component + 0.1 * role_component
    return min(score, 1.0)
