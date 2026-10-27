"""Core logic for the Jira Ticket Assistant: keyword retrieval over past
tickets + Claude to draft a new ticket, technical design and implementation plan.

Retrieval is plain keyword overlap (no embeddings or vector DB): Jira tickets
are short and full of distinctive terms, so word overlap finds good precedent
cheaply and predictably.
"""

import os
from pathlib import Path

import anthropic
import pandas as pd

MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-5-5")
MAX_TICKETS = int(os.environ.get("MAX_TICKETS", "5000"))
TOP_K = 3
# In the Space the sample backlog is uploaded to sample_data/ (see deploy.sh);
# in this repo it's the CSV at the root, shared with the notebook.
_HERE = Path(__file__).parent
SAMPLE_CSV = next(
    (p for p in (_HERE / "sample_data" / "jira_fictitious_data.csv",
                 _HERE.parent / "jira_fictitious_data.csv") if p.exists()),
    _HERE / "sample_data" / "jira_fictitious_data.csv",
)

_client = None


def get_client() -> anthropic.Anthropic:
    """Create the Claude client on first use (reads ANTHROPIC_API_KEY)."""
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


# ── Loading tickets ─────────────────────────────────────────────────────────

def _field(row, *names):
    """First non-empty value among the given column names."""
    for name in names:
        value = str(row.get(name, "")).strip()
        if value and value.lower() != "nan":
            return value
    return ""


def format_ticket(row) -> str:
    # Jira exports repeat some columns (e.g. several "Comment" columns, which
    # pandas renames Comment.1, Comment.2 ...), so gather them all.
    comments = " | ".join(
        str(row[c]).strip() for c in row.index
        if c.startswith("Comment") and str(row[c]).strip() not in ("", "nan")
    )
    return (
        f"Issue key: {_field(row, 'Issue key', 'Key')}\n"
        f"Type: {_field(row, 'Issue Type')} | Priority: {_field(row, 'Priority')} | "
        f"Story Points: {_field(row, 'Story Points', 'Custom field (Story Points)')}\n"
        f"Component/s: {_field(row, 'Component/s')} | Labels: {_field(row, 'Labels')}\n"
        f"Summary: {_field(row, 'Summary')}\n"
        f"Description: {_field(row, 'Description')[:1500]}\n"
        f"Resolution notes: {comments[:1500]}"
    )


def tokenize(text: str) -> set:
    cleaned = "".join(ch for ch in text if ch.isalnum() or ch.isspace())
    return set(cleaned.lower().split())


def build_index(path=None) -> dict:
    """Load a Jira CSV export (or the sample backlog) into a searchable index.
    Returns {"tickets": {key: text}, "words": {key: set}, "total": n, "used": n}."""
    path = path or SAMPLE_CSV
    try:
        df = pd.read_csv(path, low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(path, low_memory=False, encoding="cp1252")
    df = df.dropna(how="all")
    if "Summary" not in df.columns:
        raise ValueError("This doesn't look like a Jira CSV export (no \"Summary\" column).")

    total = len(df)
    df = df.head(MAX_TICKETS).fillna("")
    tickets = {}
    for i, row in df.iterrows():
        key = _field(row, "Issue key", "Key") or f"ROW-{i + 1}"
        tickets[key] = format_ticket(row)
    return {
        "tickets": tickets,
        "words": {key: tokenize(text) for key, text in tickets.items()},
        "total": total,
        "used": len(tickets),
    }


# ── Retrieval ───────────────────────────────────────────────────────────────

def rank_tickets(index: dict, message: str, top_k: int = TOP_K) -> list:
    """Ticket keys ranked by word overlap with the message, best first."""
    message_words = tokenize(message)
    scored = [(key, len(words & message_words)) for key, words in index["words"].items()]
    scored = [(key, score) for key, score in scored if score > 0]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return [key for key, _ in scored[:top_k]]


def additional_context(index: dict, message: str) -> str:
    keys = rank_tickets(index, message)
    if not keys:
        return "There are no similar past tickets relevant to this request."
    return (
        "The following past tickets may be relevant precedent (reuse their patterns, "
        "estimates and pitfalls where appropriate):\n\n"
        + "\n\n---\n\n".join(index["tickets"][k] for k in keys)
    )


# ── Generation ──────────────────────────────────────────────────────────────

SYSTEM_PREFIX = """You are a senior engineering lead triaging incoming work for a software team.
You are given a short, informal description of a feature request or bug, plus context on similar
past Jira tickets from this team (including how they were actually resolved).

Using that precedent where relevant, produce a response with exactly three sections:

## 🎫 Jira Ticket
- **Summary**: one line
- **Issue Type**: Story / Bug / Task / Sub-task / Epic
- **Priority**: Low / Medium / High / Critical
- **Component/s** and **Labels**: inferred from the description and precedent
- **Description**: a clear problem statement
- **Acceptance Criteria**: a numbered list
- **Story Point estimate**: with a one-line rationale, informed by similar past tickets' points if available

## 🏗️ Technical Design
Approach, affected components/services, key decisions and trade-offs, risks or open questions.

## 🔧 Probable Implementation
A concrete, numbered implementation plan (files/modules likely touched, key steps, tests to add).
Where a similar past ticket exists, reuse its approach explicitly instead of inventing a new one,
and mention its issue key.

If the description is vague, state your assumptions rather than asking clarifying questions.
For follow-up messages, refine the previous answer as asked.

Relevant context:
"""


def _text_of(content) -> str:
    """Gradio message content can be a string or a list of parts."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(p.get("text", "") for p in content if isinstance(p, dict))
    if isinstance(content, dict):
        return content.get("text", "")
    return str(content or "")


def draft(index: dict, message: str, history: list | None = None) -> str:
    """Answer one chat turn. History is Gradio's messages format, resent in full."""
    messages = []
    for turn in history or []:
        text = _text_of(turn.get("content")).strip()
        if turn.get("role") in ("user", "assistant") and text:
            messages.append({"role": turn["role"], "content": text})
    messages.append({"role": "user", "content": message})

    response = get_client().messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PREFIX + additional_context(index, message),
        output_config={"effort": "low"},
        messages=messages,
    )
    if response.stop_reason == "refusal":
        return "Sorry, I can't help with that request."
    return "".join(b.text for b in response.content if b.type == "text")
