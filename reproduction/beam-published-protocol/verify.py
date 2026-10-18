"""Check the published re-scoring runs from their saved verdicts. No model or network calls.

    python3 verify.py ../reports/beam/100k-published-protocol-2026-10

For every run: 400 records, one per BEAM 100K question; each question's score recomputed from
its saved verdicts (rubric items rounded as ExaBase's adapter rounds them; event ordering as
Kendall tau-b over the saved order, normalized to 0-1); the summary's overall is their mean.
"""
import glob
import json
import math
import sys

from scipy.stats import kendalltau


def rubric_round(raw):
    return 1.0 if raw >= 0.75 else 0.5 if raw >= 0.25 else 0.0


def ordering(reference_count, answer_order):
    reference = [f"r{i}" for i in range(reference_count)]
    answer = [f"r{i}" if i is not None else f"u{k}" for k, i in enumerate(answer_order)]
    if not reference or not answer:
        return 0.0
    topics = list(dict.fromkeys(reference + answer))
    missing = len(topics) + 1
    ranks = lambda order: [{t: i + 1 for i, t in enumerate(order)}.get(t, missing) for t in topics]
    tau, _ = kendalltau(ranks(reference), ranks(answer), variant="b")
    return 0.0 if tau is None or math.isnan(tau) else (tau + 1) / 2


def score(record):
    judge = record.get("judge") or {}
    if record.get("error") or not judge:
        return 0.0
    if judge["method"] == "event_ordering":
        return ordering(judge["referenceItems"], judge["answerOrder"])
    items = judge.get("items") or []
    return sum(rubric_round(i["rawScore"]) if i.get("rawScore") is not None else i["score"] for i in items) / len(items) if items else 0.0


def main(root):
    bad = 0
    for path in sorted(glob.glob(f"{root}/*/*/results.jsonl")):
        rows = [json.loads(line) for line in open(path)]
        summary = json.load(open(path.replace("results.jsonl", "summary.json")))
        mismatches = sum(1 for r in rows if abs(score(r) - r["score"]) > 1e-9)
        mean = sum(r["score"] for r in rows) / len(rows)
        ok = len(rows) == 400 and len({r["questionId"] for r in rows}) == 400 and mismatches == 0 \
            and abs(mean - summary["microAverage"]) < 1e-9
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {path.split(root)[-1]:45s} {100 * mean:5.1f}  rescored-mismatches={mismatches}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1].rstrip("/"))
