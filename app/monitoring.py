"""
Prometheus metrics for the /query endpoint.

Logfire and LangSmith answer "what happened in this one request?". These
metrics answer the operations question: "is the system healthy right now?"
They are what the alert rules in ops/alerts.yml watch.
"""

from prometheus_client import Counter, Histogram

# Every /query ends in exactly one of these outcomes.
OUTCOMES = ("answered", "blocked", "no_context", "error")

QUERIES = Counter(
    "rag_queries_total",
    "Queries handled by /query, by outcome",
    ["outcome"],
)

QUERY_SECONDS = Histogram(
    "rag_query_duration_seconds",
    "End-to-end /query time: guardrails + planner + retrieval + LLM",
    buckets=(0.5, 1, 2, 5, 10, 20, 30, 60, 120),
)

RETRIEVED_DOCS = Histogram(
    "rag_retrieved_documents",
    "Documents passed to the responder after reranking",
    buckets=(0, 1, 2, 3, 5, 10),
)


def classify(response: dict) -> str:
    """Work out the outcome of a /query response."""
    if response.get("status") == "error":
        return "error"
    plan = " ".join(response.get("thought_process") or []).lower()
    if "guardrails fired" in plan:
        return "blocked"
    # A technical question that retrieved nothing usually means the answer
    # was made up from the model's own knowledge. Worth tracking separately.
    if "intent: technical" in plan and not response.get("sources"):
        return "no_context"
    return "answered"


def record(response: dict, seconds: float) -> str:
    """Record one finished /query. Returns the outcome, handy for logging."""
    outcome = classify(response)
    QUERIES.labels(outcome=outcome).inc()
    QUERY_SECONDS.observe(seconds)
    if outcome in ("answered", "no_context"):
        RETRIEVED_DOCS.observe(len(response.get("sources") or []))
    return outcome
