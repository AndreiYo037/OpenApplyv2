"""Contact ranking service (LLM + fallback)."""

from __future__ import annotations

from typing import Any, Dict, List

from app.utils.llm import run_openai_json


def _fallback_rank(contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    def order_key(item: Dict[str, Any]) -> tuple[int, float]:
        source = item.get("source")
        role = str(item.get("role", "")).lower()
        if source == "job_description":
            priority = 0
        elif "hiring manager" in role or "manager" in role:
            priority = 1
        else:
            priority = 2
        return (priority, -float(item.get("confidence", 0.0) or 0.0))

    sorted_contacts = sorted(contacts, key=order_key)
    return sorted_contacts[:10]


def rank_contacts(job: Dict[str, Any], contacts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not contacts:
        return []

    fallback = _fallback_rank(contacts)
    system = """Rank contacts for outreach.

Priority:
1) job_description recruiters
2) hiring managers
3) others

Return STRICT JSON:
{"top_contacts": [contact_objects_in_best_order_max_10]}
"""
    try:
        output = run_openai_json(system, str({"job": job, "contacts": contacts}))
        ranked = output.get("top_contacts", [])
        if not isinstance(ranked, list):
            return fallback
        cleaned = [c for c in ranked if isinstance(c, dict)]
        return cleaned[:10] if cleaned else fallback
    except Exception:
        return fallback
