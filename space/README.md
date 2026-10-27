---
title: Jira Ticket Assistant
emoji: 🎫
colorFrom: yellow
colorTo: gray
sdk: gradio
sdk_version: 6.30.0
python_version: "3.12"
app_file: app.py
pinned: false
license: mit
short_description: Turn a plain-English bug or feature into a Jira ticket
---

# Jira Ticket Assistant

Describe a bug or feature in plain words and get a ready-to-paste Jira ticket (summary, type,
priority, acceptance criteria, story points), a technical design and an implementation plan,
grounded in similar past tickets.

- **Live app:** https://huggingface.co/spaces/rkigobe/jira-assistant
- **On kigobe.net:** https://kigobe.net/projects/jira-assistant

## How it works

1. **Retrieve**: your request is matched against past tickets by keyword overlap. Jira tickets are short
   and full of distinctive terms, so this finds good precedent without embeddings or a vector database.
2. **Generate**: the request plus the 3 most similar tickets go to Claude, which drafts the ticket,
   design and plan, reusing the precedent's approach and estimates.
3. **Refine**: follow-up messages ("split this into smaller stories") refine the previous answer.

It ships with a backlog of 50 **fictitious** tickets. Visitors can upload their own Jira CSV export
(up to 5,000 issues), used only for their session.

## Running cheaply

| Lever | Setting |
|---|---|
| Hosting | Hugging Face free CPU tier |
| Model | `claude-haiku-5-5` at effort `low`, well under $0.01 per request |
| Limits | `DAILY_QUESTION_LIMIT` = 10 per visitor, `GLOBAL_DAILY_LIMIT` = 300 per day |
| Uploads | `MAX_TICKETS` = 5,000 issues; files deleted within an hour |

## Run locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
.venv/bin/python app.py     # open http://127.0.0.1:7860 (uses ../jira_fictitious_data.csv)
```

## Deploy

`./deploy.sh`. The first time, add `ANTHROPIC_API_KEY` as a secret in the Space's Settings.
