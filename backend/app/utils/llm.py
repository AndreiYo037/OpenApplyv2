"""OpenAI helper utilities."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from openai import OpenAI


def extract_json_object(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
        return payload if isinstance(payload, dict) else {}
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                payload = json.loads(text[start : end + 1])
                return payload if isinstance(payload, dict) else {}
            except json.JSONDecodeError:
                return {}
    return {}


def run_openai_json(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini") -> Dict[str, Any]:
    """Execute OpenAI call and return parsed JSON object."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    content = response.choices[0].message.content or ""
    parsed = extract_json_object(content)
    if not parsed:
        raise RuntimeError("Model output was not valid JSON")
    return parsed
