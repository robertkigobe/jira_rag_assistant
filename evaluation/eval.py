"""Evaluation harness for the Jira RAG pipeline, used by evaluator.py.

Two independent evaluations, both driven by evaluation/tests.py:

- Retrieval: for each test, does rag.rank_tickets surface the expected
  ground-truth ticket(s) near the top? Scored with MRR, nDCG and keyword
  coverage — no LLM calls, purely mechanical.
- Answer: for each test, rag.chat() generates a full ticket/design/plan
  response, which an LLM judge then scores 1-5 on accuracy, completeness
  and relevance. This does make real OpenAI API calls.
"""

import json
import math
from dataclasses import dataclass

import rag
from evaluation.tests import TESTS, Test

TOP_K = 5


@dataclass
class RetrievalResult:
    mrr: float
    ndcg: float
    keyword_coverage: float


@dataclass
class AnswerResult:
    accuracy: float
    completeness: float
    relevance: float


def _score_retrieval(test: Test, top_k: int = TOP_K) -> RetrievalResult:
    ranked_keys = rag.rank_tickets(test.query, top_k=top_k)

    rr = 0.0
    for i, key in enumerate(ranked_keys, start=1):
        if key in test.expected_keys:
            rr = 1.0 / i
            break

    dcg = sum(
        (1.0 if key in test.expected_keys else 0.0) / math.log2(i + 1)
        for i, key in enumerate(ranked_keys, start=1)
    )
    ideal_hits = min(len(test.expected_keys), top_k)
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, ideal_hits + 1))
    ndcg = dcg / idcg if idcg else 0.0

    if test.expected_keywords:
        retrieved_text = " ".join(rag.knowledge[key] for key in ranked_keys).lower()
        covered = sum(1 for kw in test.expected_keywords if kw.lower() in retrieved_text)
        coverage = 100.0 * covered / len(test.expected_keywords)
    else:
        coverage = 100.0

    return RetrievalResult(mrr=rr, ndcg=ndcg, keyword_coverage=coverage)


def evaluate_all_retrieval(top_k: int = TOP_K):
    total = len(TESTS)
    for i, test in enumerate(TESTS, start=1):
        yield test, _score_retrieval(test, top_k=top_k), i / total


JUDGE_SYSTEM = """You are grading an AI assistant's response to an informal bug/feature description.
The response should contain three sections: a Jira Ticket draft, a Technical Design, and a Probable Implementation plan.

Score the response from 1 (poor) to 5 (excellent) on:
- accuracy: is the technical content correct/plausible, and does it sensibly build on the retrieved precedent (if any)?
- completeness: are all three sections present with adequate, non-generic detail?
- relevance: does the response directly address the stated request rather than drifting off-topic?

Respond with ONLY a JSON object of the form:
{"accuracy": <1-5>, "completeness": <1-5>, "relevance": <1-5>}
"""


def _judge_answer(test: Test, answer: str) -> AnswerResult:
    context = rag.additional_context(test.query)
    user_prompt = (
        f"Request:\n{test.query}\n\n"
        f"Retrieved precedent shown to the assistant:\n{context}\n\n"
        f"Assistant's response:\n{answer}"
    )
    response = rag.openai.chat.completions.create(
        model=rag.MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    data = json.loads(response.choices[0].message.content)
    return AnswerResult(
        accuracy=float(data["accuracy"]),
        completeness=float(data["completeness"]),
        relevance=float(data["relevance"]),
    )


def evaluate_all_answers():
    total = len(TESTS)
    for i, test in enumerate(TESTS, start=1):
        answer = rag.chat(test.query, [])
        yield test, _judge_answer(test, answer), i / total
