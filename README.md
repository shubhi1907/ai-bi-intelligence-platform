# AI BI Intelligence Platform

AI BI Intelligence Platform is a Streamlit proof of concept that combines executive BI reporting with AI-assisted deal, delivery, risk, ticket, and revenue intelligence.

The goal is to test whether a single AI-enabled intelligence experience can reduce manual reporting effort, replace selected Qlik dashboard workflows over time, and give leaders evidence-backed recommendations instead of static metrics alone.

## What The POC Shows

- Role-based views for a senior leader, implementation lead, and revenue leader.
- Portfolio metrics across deals, contract value, delay, open tickets, SLA breaches, and blocked tasks.
- Risk scoring that connects deals to tickets, risks, escalations, blockers, and customer value.
- Evidence panels that summarize customer, project, ticket, risk, escalation, meeting, and status-report context.
- Optional AI answers using an OpenAI API key when configured.

## Streamlit Cloud Entry Point

Use this file as the Streamlit Cloud main file:

```text
streamlit_app.py
```

The app runs from the repository root and loads the app implementation from:

```text
frontend/combined_app.py
```

## Local Run

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

The app can run without an OpenAI key. If no key is configured, it will still show dashboard metrics and retrieved evidence, but AI answer generation will return a friendly configuration message.

## Optional Secrets

For AI answer generation, configure this secret in Streamlit Cloud:

```toml
ANTHROPIC_API_KEY = "your-key"
```

Do not commit real secrets to the repository.

## Streamlit Cloud Deployment Settings

- Repository: `shubhi1907/ai-deal-intelligence-platform`
- Branch: `main`
- Main file path: `streamlit_app.py`
- Python version: use Streamlit Cloud default or Python 3.10+
- App name suggestion: `ai-bi-intelligence-platform`

## Notes For The Team

This is a POC, not a production architecture. Before scaling, the team should review data permissions, source lineage, model governance, deployment cost, and which Qlik reports are realistic candidates for replacement.
