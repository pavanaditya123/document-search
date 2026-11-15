from app.ingestion.chunking.splitter import chunk_text
from evals.pipeline import detect_tool


def test_detect_tool_maps_planner_output():
    assert detect_tool(["Intent: Guardrails Fired", "Retrieval: Skipped"]) == "guardrails"
    assert detect_tool(["Intent: Technical", "Search Term: hpa"]) == "retrieve_documents"
    assert detect_tool(["Intent: Conversational/Memory"]) == "direct_answer"
    assert detect_tool([]) == "unknown"


def test_chunks_never_exceed_the_limit_for_normal_paragraphs():
    text = "\n\n".join(["word " * 50] * 20)  # 20 paragraphs of ~250 chars
    chunks = chunk_text(text, chunk_size=600)
    assert len(chunks) > 1
    assert all(len(c) <= 600 for c in chunks)


def test_empty_text_gives_no_chunks():
    assert chunk_text("   ") == []
