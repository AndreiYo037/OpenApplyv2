# OpenApplyv2 Internship Conversion Engine

OpenApplyv2 helps Singapore undergraduates decide whether to pursue an internship, identify the right people to reach out to, and generate personalized outreach that is ready to send.

Unlike job browsing tools that optimize for volume, OpenApplyv2 optimizes for conversion quality: stronger fit, better contact targeting, and clearer next actions.

## Main Goal

Increase internship conversion outcomes by combining:
- **Fit quality**: Is this role realistically worth your effort?
- **Contact quality**: Who can influence your application outcome?
- **Outreach quality**: What message should you send first?

## Product Moats

1. **Decision Layer**: Decide who matters, not just show people.
   - Enforces hard constraints on actionability.
   - Filters out low-fit roles and weak-contact opportunities.
2. **Personalization Layer**: Generate context-aware outreach.
   - Combines company signals, contact signals, and user signals.
   - Tailored for Singapore internship context.

## Input

```python
{
  "job_text": str,
  "cv_text": str
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
  "decision": str,
  "actionable": bool,
  "discard_reason": str | None,
  "company_signals": [str],
  "job_summary": str,
  "required_skills": [str],
  "action_plan": str,
  "contacts": [
    {
      "id": str,
      "name": str,
      "role": str | None,
      "role_type": str | None,
      "influence_level": float | None,
      "linkedin_url": str | None,
      "email": str | None,
      "source": str,
      "confidence": float,
      "search_hint": str
    }
  ]
}
```

## Module Layout

- `backend/app/main.py`: FastAPI app entrypoint
- `backend/app/routes/evaluate.py`: Main scoring endpoint (`/evaluate`)
- `backend/app/routes/generate_message.py`: On-demand outreach endpoint (`/generate_message`)
- `backend/app/services/job_parser.py`: Job text parsing + recruiter extraction
- `backend/app/services/cv_parser.py`: CV text parsing
- `backend/app/services/job_matcher.py`: Job fit scoring
- `backend/app/services/contact_scraper.py`: Singapore-focused contact discovery
- `backend/app/services/contact_merger.py`: Merge + dedupe contacts
- `backend/app/services/contact_ranker.py`: Prioritize high-value contacts
- `backend/app/services/contact_scorer.py`: Contact quality scoring
- `backend/app/services/company_intel.py`: Singapore company/job signal extraction
- `backend/app/services/strategy_generator.py`: Outreach strategy + message generation
- `backend/app/services/decision_engine.py`: End-to-end orchestration
- `frontend/src/App.tsx`: Main UI workflow
- `frontend/src/api/client.ts`: API client for evaluate/message calls

## End-to-End Flow

1. User submits **job description + CV text** from the frontend.
2. Backend parses job context (title/company/requirements/keywords/contacts).
3. Backend parses CV into structured profile features.
4. Job fit score is computed from skills, requirements, and text overlap.
5. Contacts are discovered (Singapore-focused), merged, and deduplicated.
6. Contacts are ranked by influence/relevance and scored for outreach quality.
7. Company intelligence is generated from Singapore-relevant signals.
8. Strategy engine generates contact-first action guidance.
9. Final decision score and actionable recommendation are returned.
10. User can generate a role-aware personalized message per contact on demand.

## Singapore Localization

- Contact discovery is scoped to Singapore hiring context.
- Company signals prioritize Singapore-relevant market and hiring momentum.
- Outreach strategy and messaging are tuned for internship conversations in Singapore.

## Why This Matters

OpenApplyv2 is built to reduce wasted applications and improve conversion odds by helping students focus on the **right opportunities**, **right contacts**, and **right first message**.
