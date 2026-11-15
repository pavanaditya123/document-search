import pandas as pd

from evals import gate

THRESHOLDS = {"faithfulness": 0.85, "answer_relevancy": 0.70}


def report(**scores):
    return {"scores": scores}


def test_summarize_averages_each_metric():
    results = {
        "faithfulness": pd.DataFrame({"question": ["a", "b"], "faithfulness": [1.0, 0.8]}),
        "answer_relevancy": pd.DataFrame({"question": ["a", "b"], "answer_relevancy": [0.6, 0.7]}),
    }
    summary = gate.summarize(results, samples=2)
    assert summary["scores"] == {"faithfulness": 0.9, "answer_relevancy": 0.65}
    assert summary["samples"] == 2


def test_passes_when_every_metric_clears_its_floor():
    assert gate.check(report(faithfulness=0.95, answer_relevancy=0.80), THRESHOLDS) == []


def test_fails_below_the_floor():
    failures = gate.check(report(faithfulness=0.80, answer_relevancy=0.80), THRESHOLDS)
    assert failures == ["faithfulness: 0.800 is below the floor of 0.85"]


def test_fails_on_a_drop_even_above_the_floor():
    baseline = report(faithfulness=0.95, answer_relevancy=0.80)
    failures = gate.check(report(faithfulness=0.88, answer_relevancy=0.80), THRESHOLDS, baseline)
    assert failures == ["faithfulness: dropped 0.070 (baseline 0.950 -> 0.880)"]


def test_small_wobble_against_baseline_is_allowed():
    baseline = report(faithfulness=0.95, answer_relevancy=0.80)
    assert gate.check(report(faithfulness=0.92, answer_relevancy=0.78), THRESHOLDS, baseline) == []


def test_missing_metric_fails():
    assert gate.check(report(faithfulness=0.95), THRESHOLDS) == ["answer_relevancy: missing from this run"]
