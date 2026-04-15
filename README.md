# OpenApplyv2 Decision Engine

Production-oriented single-job decision engine that evaluates:

1. Job-to-CV match quality
2. Reachable contact quality (via TinyFish-based discovery)

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

## TinyFish Integration Note

`enrichment/contact_scraper.py` contains `_tinyfish_fetch_text(...)` as the integration seam.
Replace that stub with your TinyFish client call in your runtime environment.
