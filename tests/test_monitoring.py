from app import monitoring


def response(plan, sources=(), status="Done"):
    return {"thought_process": list(plan), "sources": list(sources), "status": status}


def test_retrieved_answer_is_answered():
    r = response(["Intent: Technical", "Search Term: hpa", "Context Retrieved"], ["chunk"])
    assert monitoring.classify(r) == "answered"


def test_technical_answer_with_no_sources_is_flagged():
    r = response(["Intent: Technical", "Search Term: hpa", "Context Retrieved"], [])
    assert monitoring.classify(r) == "no_context"


def test_small_talk_without_sources_is_fine():
    r = response(["Intent: Conversational/Memory", "Retrieval: Skipped"], [])
    assert monitoring.classify(r) == "answered"


def test_guardrails_block():
    r = response(["Intent: Guardrails Fired", "Retrieval: Skipped"])
    assert monitoring.classify(r) == "blocked"


def test_error_wins_over_everything_else():
    r = response(["Error encountered during execution."], status="error")
    assert monitoring.classify(r) == "error"


def test_record_counts_outcome_and_documents():
    before = monitoring.QUERIES.labels(outcome="answered")._value.get()
    outcome = monitoring.record(response(["Intent: Technical"], ["a", "b"]), seconds=1.5)
    assert outcome == "answered"
    assert monitoring.QUERIES.labels(outcome="answered")._value.get() == before + 1
