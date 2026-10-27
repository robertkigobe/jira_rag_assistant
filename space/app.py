"""Gradio web UI for the Jira Ticket Assistant (runs as a Hugging Face Space).

Run locally:   .venv/bin/python app.py      then open http://127.0.0.1:7860
"""

import os
import time
from collections import defaultdict

import gradio as gr
from dotenv import load_dotenv

load_dotenv()  # load ANTHROPIC_API_KEY etc. from .env before importing core

import core  # noqa: E402

# Cost controls: each request costs well under a cent on Claude Haiku 5.5.
DAILY_QUESTION_LIMIT = int(os.environ.get("DAILY_QUESTION_LIMIT", "10"))    # per visitor
GLOBAL_DAILY_LIMIT = int(os.environ.get("GLOBAL_DAILY_LIMIT", "300"))       # all visitors

SAMPLE_INDEX = core.build_index()

EXAMPLES = [
    "Users get logged out when their token expires mid-session",
    "Add a CSV export button to the monthly reports page",
    "The checkout page is very slow on mobile",
]

_usage = defaultdict(int)


def _client_ip(request: gr.Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or request.client.host


def on_upload(file):
    """Use the visitor's own Jira export for this session (or go back to the sample)."""
    if file is None:
        return SAMPLE_INDEX, _sample_status()
    try:
        index = core.build_index(file)
    except Exception as e:
        return SAMPLE_INDEX, f"⚠️ Could not read that file: {e} Using the sample backlog instead."
    status = f"✅ Using **your export**: {index['used']:,} tickets."
    if index["total"] > index["used"]:
        status += f" ⚠️ Your file has {index['total']:,} tickets; this free tool uses the first {core.MAX_TICKETS:,}."
    return index, status


def _sample_status():
    return f"Using the **sample backlog** ({SAMPLE_INDEX['used']} fictitious tickets). Upload your own Jira CSV export to use your team's history."


def respond(message, history, index, request: gr.Request):
    if not message or not message.strip():
        return "Please describe a bug or feature."
    today = time.strftime("%Y-%m-%d")
    visitor, everyone = (_client_ip(request), today), ("*", today)
    if _usage[everyone] >= GLOBAL_DAILY_LIMIT:
        return "The free requests for today have all been used. Please come back tomorrow!"
    if _usage[visitor] >= DAILY_QUESTION_LIMIT:
        return f"You've used today's {DAILY_QUESTION_LIMIT} free requests. Come back tomorrow!"

    _usage[visitor] += 1
    _usage[everyone] += 1
    try:
        answer = core.draft(index or SAMPLE_INDEX, message.strip()[:2000], history)
    except Exception as e:
        return f"⚠️ Something went wrong: {e}"
    left = DAILY_QUESTION_LIMIT - _usage[visitor]
    return f"{answer}\n\n<sub>{left} free requests left today.</sub>"


with gr.Blocks(title="Jira Ticket Assistant · kigobe.net", delete_cache=(1800, 3600)) as demo:
    index_state = gr.State(SAMPLE_INDEX)

    gr.Markdown(
        "# 🎫 Jira Ticket Assistant\n"
        "Describe a bug or feature in plain words. You'll get a ready-to-paste **Jira ticket**, "
        "a **technical design** and an **implementation plan**, based on similar past tickets.\n\n"
        "<sub>By [Robert Kigobe](https://kigobe.net). Uploaded files are deleted within an hour; "
        "only your request and up to 3 similar tickets are sent to the AI.</sub>"
    )

    with gr.Accordion("📂 Use your own Jira export (optional)", open=False):
        gr.Markdown(
            "In Jira, open a filter of past issues → **Export → CSV (all fields)**. "
            "Up to 5,000 issues are used. Columns used: Summary, Issue key, Issue Type, Priority, "
            "Story Points, Component/s, Labels, Description, Comment."
        )
        upload = gr.File(label="Jira CSV export", file_types=[".csv"], type="filepath")
    status = gr.Markdown(_sample_status())

    gr.ChatInterface(
        respond,
        additional_inputs=[index_state],
        examples=[[e, None] for e in EXAMPLES],
        cache_examples=False,
    )

    upload.change(on_upload, upload, [index_state, status])


demo.queue(default_concurrency_limit=2, max_size=20)

if __name__ == "__main__":
    demo.launch(ssr_mode=False, theme=gr.themes.Soft(primary_hue="amber"))
