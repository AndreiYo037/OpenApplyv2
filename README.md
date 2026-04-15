# OpenApplyv2 Internship Conversion Engine

OpenApplyv2 is designed as an internship conversion engine for Singapore undergraduates.
It is not a job browsing tool. It scores whether an opportunity is worth pursuing, identifies who matters,
and generates context-aware outreach that is ready to send.

## Product Moats

1. **Decision Layer**: Decide who matters, not just show people.
   - Enforces hard constraints on actionability.
   - Discards opportunities with weak fit or unreliable contact coverage.
2. **Personalization Layer**: Generate context-aware outreach.
   - Combines company signals, contact signals, and user signals.
   - Localizes company intelligence and contact discovery to Singapore.

## Input

```python
{
  "job_text": str,
  "user_profile": {
    "skills": list[str],
    "experience": str,
    "education": str,
    "projects": list[str]
  }
}
```

## Output

```python
{
  "title": str,
  "company": str,
  "job_fit": float,
  "contact_score": float,
  "final_score": float,
  "actionable": bool,
  "discard_reason": str | None,
  "company_signals": [str],
  "contacts": [
    {
      "name": str,
      "role": str,
      "linkedin_url": str | None,
      "email": str | None
    }
  ]
}
```

## Module Layout

- `ingestion/parser.py`: Lightweight job text parsing
- `ranking/job_matcher.py`: Job fit scoring
- `enrichment/contact_scraper.py`: TinyFish-only contact discovery
- `ranking/contact_scorer.py`: Contact quality scoring
- `ranking/decision_engine.py`: Pipeline orchestration
- `main.py`: Public entrypoint (`run_decision_engine`)

## Run Example

```python
from main import run_decision_engine

payload = {
    "job_text": "Senior Backend Engineer at Acme. Skills: Python, SQL, AWS.",
    "user_profile": {
        "skills": ["Python", "SQL", "Docker"],
        "experience": "Built backend APIs and data pipelines.",
        "education": "BSc Computer Science",
        "projects": ["Recommendation service"]
    }
}

print(run_decision_engine(payload))
```

## Singapore Localization

- Contact discovery uses Singapore-scoped TinyFish search.
- Company intelligence is generated from Singapore-relevant public signals.
- Outreach strategy is tuned for Singapore internship context.
