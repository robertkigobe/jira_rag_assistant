
"""Core Jira RAG pipeline: keyword retrieval + chat completion.

Extracted from jira_rag.ipynb so the evaluation harness (evaluation/eval.py,
evaluator.py) can reuse the exact same retrieval and generation logic the
notebook demo uses, without duplicating it.
"""

import os

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

# small, cheap model — good enough for drafting tickets; swap for gpt-4.1 for higher-quality designs
MODEL = "gpt-4.1-nano"
openai = OpenAI()

CSV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jira_fictitious_data.csv")

# fillna("") avoids NaN showing up as "nan" once we format rows into text below
df = pd.read_csv(CSV_PATH).fillna("")


def format_ticket(row):
    return (
        f"Issue key: {row['Issue key']}\n"
        f"Type: {row['Issue Type']} | Priority: {row['Priority']} | Story Points: {row['Story Points']}\n"
        f"Component/s: {row['Component/s']} | Labels: {row['Labels']}\n"
        f"Summary: {row['Summary']}\n"
        f"Description: {row['Description']}\n"
        f"Resolution notes: {row['Comment']}"
    )


# our "knowledge base": Issue key -> formatted ticket text
knowledge = {row["Issue key"]: format_ticket(row) for _, row in df.iterrows()}


def tokenize(text):
    cleaned = ''.join(ch for ch in text if ch.isalnum() or ch.isspace())
    return set(cleaned.lower().split())


# pre-compute each ticket's word set once, so scoring against it later is cheap
ticket_words = {key: tokenize(text) for key, text in knowledge.items()}


def rank_tickets(message, top_k=3):
    """Return the top_k ticket keys ranked by word-overlap score, best match first."""
    message_words = tokenize(message)
    scored = [(key, len(words & message_words)) for key, words in ticket_words.items()]
    scored = [(key, score) for key, score in scored if score > 0]  # drop zero-overlap tickets
    scored.sort(key=lambda pair: pair[1], reverse=True)  # best matches first
    return [key for key, _ in scored[:top_k]]


def get_relevant_tickets(message, top_k=3):
    return [knowledge[key] for key in rank_tickets(message, top_k=top_k)]


def additional_context(message, top_k=3):
    relevant_tickets = get_relevant_tickets(message, top_k=top_k)
    if not relevant_tickets:
        return "There are no similar past tickets relevant to this request."
    result = "The following past tickets may be relevant precedent (reuse their patterns, estimates and pitfalls where appropriate):\n\n"
    result += "\n\n---\n\n".join(relevant_tickets)
    return result


SYSTEM_PREFIX = """
You are a senior engineering lead triaging incoming work for a software team.
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
Where a similar past ticket exists, reuse its approach explicitly instead of inventing a new one.

If the description is vague, state your assumptions rather than asking clarifying questions.

Relevant context:
"""


def chat(message, history=None):
    history = history or []
    system_message = SYSTEM_PREFIX + additional_context(message)
    messages = [{"role": "system", "content": system_message}] + history + [{"role": "user", "content": message}]
    response = openai.chat.completions.create(model=MODEL, messages=messages)
    return response.choices[0].message.content
