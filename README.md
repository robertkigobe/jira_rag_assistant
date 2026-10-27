# Jira Assistant (RAG demo)

Given a short, informal description of a feature or bug, this assistant:

1. Retrieves similar **past Jira tickets** (including how they were actually implemented) as grounding context — the RAG step
2. Drafts a well-formed **Jira ticket** (summary, type, priority, components, labels, description, acceptance criteria, story point estimate)
3. Proposes a **technical design**
4. Sketches a **probable implementation** plan

Retrieval is plain keyword overlap against a CSV export of historical Jira tickets — no embeddings or vector DB involved.

**Try it live:** [kigobe.net/projects/jira-assistant](https://kigobe.net/projects/jira-assistant) · [Hugging Face Space](https://huggingface.co/spaces/rkigobe/jira-assistant)

## Contents

- `jira_rag.ipynb` — the notebook containing the full pipeline and a Gradio chat UI
- `rag.py` — the pipeline extracted from the notebook, shared with the evaluation harness
- `evaluator.py`, `evaluation/` — retrieval/answer evaluation harness and test set
- `jira_fictitious_data.csv` — synthetic Jira export (50 tickets) used as the knowledge base
- `jira_rag_share.html` — a rendered/exported copy of the notebook for viewing without Jupyter
- `space/` — the public web app deployed to Hugging Face (Claude Haiku, per-visitor limits, optional upload of your own Jira export up to 5,000 issues). See [space/README.md](space/README.md); deploy with `space/deploy.sh`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then edit .env and add your real OPENAI_API_KEY
```

## Run

```bash
jupyter lab jira_rag.ipynb
```

Run all cells. The last cell launches a local Gradio web UI (opens in your browser at `http://127.0.0.1:7860`) titled "Jira Assistant" — describe a feature or bug and get back a drafted ticket, technical design, and probable implementation.
