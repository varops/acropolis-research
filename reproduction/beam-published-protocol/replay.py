"""Replay saved Acropolis BEAM 100K evidence through ExaBase's answer prompt and judge.

The evidence is what our retrieval delivered in the September runs (claims + observation
excerpts, from the unredacted reports). Nothing is re-retrieved. The answer prompt, the per-rubric
judge, the event-ordering matcher and the Kendall tau-b score follow past.dev's harness, which
reproduces ExaBase's adapter unchanged.

    python3 -I replay.py --reports DIR [DIR...] --row core_frontier --answer MODEL --judge MODEL --out OUT
    python3 -I replay.py --check-scorer PASTDEV_RESULTS_JSONL   # no model calls
    python3 -I replay.py --dry-run ...                          # build prompts only, no calls
"""

import argparse
import ast
import asyncio
import glob
import json
import math
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import exabase_prompts  # noqa: E402  (ExaBase's prompts, not redistributed; see README.md)
except ModuleNotFoundError:
    exabase_prompts = None  # --check-scorer needs no prompts; a run stops with a clear message

import httpx  # noqa: E402
from scipy.stats import kendalltau  # noqa: E402

CATEGORIES = ["abstention", "contradiction_resolution", "event_ordering", "information_extraction",
              "instruction_following", "knowledge_update", "multi_session_reasoning",
              "preference_following", "summarization", "temporal_reasoning"]
GOLD_FIELDS = ["ideal_response", "answer", "expected_answer", "expected", "gold_answer", "reference"]
FALLBACK_GOLD_FIELDS = ["ideal_answer", "ideal_summary", "expected_compliance"]
BASE_URL = "https://openrouter.ai/api/v1"
MAX_TOKENS = 8000


# --- Dataset (past.dev's dataset.py, same field rules) ----------------------------------------

def annotations(category, item):
    result = {}
    rubric = item.get("rubric")
    if rubric:
        result["rubric"] = rubric if isinstance(rubric, list) else [str(rubric)]
    if category == "abstention":
        result["why_unanswerable"] = item.get("why_unanswerable", "")
    elif category == "instruction_following":
        result["instruction_being_tested"] = item.get("instruction_being_tested", "")
        result["compliance_indicators"] = item.get("compliance_indicators", [])
    elif category == "preference_following":
        result["preference_being_tested"] = item.get("preference_being_tested", "")
        result["compliance_indicators"] = item.get("compliance_indicators", [])
    elif category == "temporal_reasoning":
        result["time_points"] = item.get("time_points", [])
        result["calculation_required"] = item.get("calculation_required", "")
    elif category == "event_ordering":
        result["ordering_tested"] = item.get("ordering_tested", [])
    return result


def gold_answers(item):
    first = next((item[f] for f in GOLD_FIELDS if f in item), None)
    answer = "" if first is None else str(first)
    if not answer.strip():
        answer = next((str(item[f]) for f in FALLBACK_GOLD_FIELDS if item.get(f) is not None), "")
    return [answer] if answer else []


def load_questions(parquet):
    import pandas as pd
    questions = {}
    for _, row in pd.read_parquet(parquet).iterrows():
        conv = f"beam-100K-{row['conversation_id']}"
        probing = row["probing_questions"]
        if isinstance(probing, str):
            try:
                probing = json.loads(probing)
            except Exception:
                probing = ast.literal_eval(probing)
        for category in CATEGORIES:
            for index, item in enumerate(probing.get(category, [])):
                if not item.get("question"):
                    continue
                qid = f"{conv}:{category}:{index}"
                questions[qid] = {"id": qid, "category": category, "text": item["question"],
                                  "gold": gold_answers(item), "annotations": annotations(category, item)}
    return questions


# --- Evidence from our reports ----------------------------------------------------------------

def load_evidence(report_dirs, row):
    pattern = re.compile(rf"^ask_{re.escape(row)}_\d+_\d+_p\d+\.json$")
    evidence, files = {}, 0
    for directory in report_dirs:
        for path in sorted(glob.glob(os.path.join(directory, "ask_*.json"))):
            if not pattern.match(os.path.basename(path)):
                continue
            files += 1
            for q in json.load(open(path))["questions"]:
                if q["question_id"] in evidence:
                    raise SystemExit(f"duplicate question {q['question_id']} in {path}")
                evidence[q["question_id"]] = q
    return evidence, files


def context_json(q):
    """The evidence as our retrieval delivered it, in delivered order, as compact JSON
    (past.dev passes its recall response the same way)."""
    claims = [{"type": c.get("claim_type"), "status": c.get("status"), "subject": c.get("subject"),
               "statement": c.get("object"), "validFrom": c.get("valid_from")}
              for c in q.get("claims") or []]
    observations = []
    for rank, o in enumerate(q.get("observations") or [], 1):
        source = o.get("source_object_id") or ""
        turn = source.rsplit("/", 1)[-1] if "/" in source else None
        observations.append({"rank": rank, "turn": turn, "occurredAt": o.get("occurred_at"),
                             "content": o.get("excerpt")})
    return json.dumps({"claims": claims, "observations": observations}, ensure_ascii=False,
                      separators=(",", ":"))


# --- Model calls (past.dev's llm.py shape, with a call cache for resume) ----------------------

class Model:
    def __init__(self, name, effort, cache_path, concurrency):
        self.name, self.effort = name, effort
        self.cache_path = cache_path
        self.cache = {}
        if cache_path.exists():
            for line in cache_path.read_text().splitlines():
                rec = json.loads(line)
                self.cache[rec["key"]] = rec
        self.slots = asyncio.Semaphore(concurrency)
        self.http = None
        self.usd = sum(r.get("usd", 0) for r in self.cache.values())
        self.calls = 0

    def client(self):
        if self.http is None:
            key = os.environ.get("OPENROUTER_API_KEY", "").strip()
            if not key:
                raise SystemExit("OPENROUTER_API_KEY is required")
            self.http = httpx.AsyncClient(base_url=BASE_URL, timeout=120,
                                          headers={"Authorization": f"Bearer {key}"})
        return self.http

    async def call(self, key, prompt, schema=None):
        if key in self.cache:
            return self.cache[key]["text"]
        # A cap on output length, so OpenRouter reserves less credit per in-flight request. The
        # longest reply in the first 19,896 calls was 3,740 tokens; this cap never truncates.
        payload = {"model": self.name, "usage": {"include": True}, "max_tokens": MAX_TOKENS,
                   "messages": [{"role": "user", "content": prompt}]}
        if self.effort:
            payload["reasoning"] = {"effort": self.effort}
        if schema:
            payload["response_format"] = {"type": "json_schema", "json_schema": {
                "name": "benchmark_response", "strict": True,
                "schema": {"type": "object", "properties": schema["properties"],
                           "required": schema["required"], "additionalProperties": False}}}
            payload["provider"] = {"require_parameters": True}
        delays = (1, 2, 4, 8, 16)
        async with self.slots:
            for attempt in range(len(delays) + 1):
                try:
                    r = await self.client().post("/chat/completions", json=payload)
                    if r.status_code in (401, 402, 403):
                        raise SystemExit(f"account refused ({r.status_code}): {r.text[:300]}")
                    if r.status_code == 429 or r.status_code >= 500:
                        raise RuntimeError(f"retryable {r.status_code}")
                    r.raise_for_status()
                    data = r.json()
                    if data.get("error") or not data.get("choices"):
                        raise RuntimeError(f"bad response: {str(data)[:300]}")
                    content = data["choices"][0]["message"].get("content") or ""
                    if isinstance(content, list):
                        content = "".join(p.get("text", "") for p in content if isinstance(p, dict))
                    if not content.strip():
                        raise RuntimeError("empty reply")
                    usage = data.get("usage") or {}
                    rec = {"key": key, "text": content, "usd": usage.get("cost") or 0,
                           "in": usage.get("prompt_tokens"), "out": usage.get("completion_tokens")}
                    break
                except (httpx.HTTPError, RuntimeError, json.JSONDecodeError) as error:
                    if attempt == len(delays):
                        raise RuntimeError(f"{self.name}: {error}") from error
                    await asyncio.sleep(delays[attempt])
        self.cache[key] = rec
        self.usd += rec["usd"]
        self.calls += 1
        with self.cache_path.open("a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        return content


def parse_json(text):
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start >= 0 and end > start:
            return json.loads(text[start:end + 1])
        raise


# --- Scoring (past.dev's scoring.py, which is ExaBase's adapter) ------------------------------

def round_rubric_score(raw):
    return 1.0 if raw >= 0.75 else 0.5 if raw >= 0.25 else 0.0


def list_items(text):
    items = []
    for line in text.strip().splitlines():
        item = re.sub(r"^\s*(?:\d+[.)]\s*|[-*]\s*)", "", line).strip()
        if item:
            items.append(item)
    return items


def ordering_score(reference, answer_order):
    topics = list(dict.fromkeys(reference + answer_order))
    missing = len(topics) + 1

    def ranks(order):
        position = {topic: i + 1 for i, topic in enumerate(order)}
        return [position.get(topic, missing) for topic in topics]

    tau_b, _ = kendalltau(ranks(reference), ranks(answer_order), variant="b")
    return 0.0 if tau_b is None or math.isnan(tau_b) else float((tau_b + 1) / 2)


async def score(judge, q, answer, tag):
    if q["category"] == "event_ordering":
        reference = q["annotations"].get("ordering_tested") or []
        if not reference and q["gold"]:
            reference = list_items(q["gold"][0])
        items = list_items(answer)
        if not reference or not items:
            return 0.0, {"method": "event_ordering", "reference": reference, "answer": items}
        matched, renamed = set(), []
        for i, item in enumerate(items):
            match = None
            for j, topic in enumerate(reference):
                if j in matched:
                    continue
                try:
                    text = await judge.call(f"{tag}|eq|{q['id']}|{i}|{j}",
                                            exabase_prompts.equivalence_prompt(topic, item),
                                            exabase_prompts.EQUIVALENCE_SCHEMA)
                    same = parse_json(text).get("answer", "").strip().upper().startswith("YES")
                except Exception:
                    same = False
                if same:
                    match = j
                    break
            if match is None:
                renamed.append(item)
            else:
                renamed.append(reference[match])
                matched.add(match)
        return ordering_score(reference, renamed), {"method": "event_ordering", "reference": reference,
                                                     "answer": renamed}

    rubric = q["annotations"].get("rubric") or []
    if not rubric and q["gold"]:
        rubric = [f"LLM response should contain: {q['gold'][0]}"]
    if not rubric:
        return 0.0, {"method": "rubric", "note": "no rubric"}
    verdicts = []
    for i, item in enumerate(rubric):
        try:
            text = await judge.call(f"{tag}|rubric|{q['id']}|{i}",
                                    exabase_prompts.rubric_item_prompt(q["text"], answer, item),
                                    exabase_prompts.RUBRIC_SCHEMA)
            v = parse_json(text)
            raw = float(v.get("score", 0))
            verdicts.append({"rubricItem": item, "rawScore": raw, "score": round_rubric_score(raw),
                             "reason": v.get("reason", "")})
        except Exception as error:
            verdicts.append({"rubricItem": item, "score": 0.0, "error": str(error)[:300]})
    return sum(v["score"] for v in verdicts) / len(verdicts), {"method": "rubric", "items": verdicts}


def summarize(rows):
    by = defaultdict(list)
    for r in rows:
        by[r["category"]].append(r["score"])
    cats = {c: {"questions": len(s), "mean": sum(s) / len(s)} for c, s in sorted(by.items())}
    scores = [r["score"] for r in rows]
    return {"questions": len(scores),
            "failedAnswers": sum(1 for r in rows if r.get("error")),
            "failedVerdicts": sum(1 for r in rows for i in (r.get("judge") or {}).get("items", []) if i.get("error")),
            "microAverage": sum(scores) / len(scores), "macroAverage": sum(c["mean"] for c in cats.values()) / len(cats),
            "categories": cats}


# --- Checks -----------------------------------------------------------------------------------

def check_scorer(results_jsonl):
    """Recompute past.dev's saved scores from their saved verdicts with our scoring functions."""
    bad = n = 0
    for line in open(results_jsonl):
        r = json.loads(line)
        j = r["judge"]
        if j.get("method") == "event_ordering":
            s = ordering_score(j["reference"], j["answer"]) if j.get("reference") and j.get("answer") else 0.0
        else:
            items = j.get("items") or []
            s = sum(round_rubric_score(i["rawScore"]) if "rawScore" in i else i["score"] for i in items) / len(items) if items else 0.0
        n += 1
        if abs(s - r["score"]) > 1e-9:
            bad += 1
    print(f"scorer check: {n} rows, {bad} mismatches")
    return bad == 0


# --- Run --------------------------------------------------------------------------------------

async def run(args):
    if exabase_prompts is None:
        raise SystemExit("exabase_prompts.py is missing: place ExaBase's prompt file beside replay.py (see README.md)")
    questions = load_questions(args.parquet)
    evidence, files = load_evidence(args.reports, args.row)
    expected = set(questions)
    got = set(evidence)
    if got != expected:
        raise SystemExit(f"question sets differ: missing {sorted(expected - got)[:5]} ({len(expected - got)}), "
                         f"extra {sorted(got - expected)[:5]} ({len(got - expected)})")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    answerer = Model(args.answer, args.answer_effort, out / "calls-answer.jsonl", args.concurrency)
    judge = answerer if (args.judge == args.answer and args.judge_effort == args.answer_effort) else \
        Model(args.judge, args.judge_effort, out / "calls-judge.jsonl", args.concurrency)
    order = sorted(questions)
    if args.limit:
        order = order[:args.limit]
    prompts = {qid: exabase_prompts.answer_prompt(questions[qid]["text"], context_json(evidence[qid]),
                                                  questions[qid]["category"],
                                                  {} if args.no_hints else questions[qid]["annotations"])
               for qid in order}
    if args.dry_run:
        lens = sorted(len(p) for p in prompts.values())
        print(f"{len(prompts)} prompts from {files} report files; chars p50={lens[len(lens)//2]} max={lens[-1]} "
              f"total={sum(lens)} (~{sum(lens)/4/1e6:.1f}M tokens)")
        sample = prompts[order[0]]
        (out / "sample-prompt.txt").write_text(sample)
        return
    started = time.time()

    async def one(qid):
        q = questions[qid]
        row = {"questionId": qid, "category": q["category"], "question": q["text"], "goldAnswers": q["gold"]}
        try:
            if args.native_answers:
                # Our September composer's own answer, as the report saved it; nothing is regenerated.
                answer = evidence[qid].get("hypothesis") or ""
                if not answer:
                    raise RuntimeError("no saved answer: empty in the stored report")
            else:
                answer = await answerer.call(f"answer|{qid}", prompts[qid])
        except Exception as error:
            row.update(answer="", score=0.0, judge={}, error=str(error)[:300])
            return row
        s, verdict = await score(judge, q, answer, f"judge:{args.judge}")
        row.update(answer=answer, score=s, judge=verdict)
        return row

    rows = await asyncio.gather(*(one(qid) for qid in order))
    with (out / "results.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = summarize(rows)
    summary.update({"row": args.row, "reports": args.reports, "answerModel": args.answer,
                    "answerReasoning": args.answer_effort, "judgeModel": args.judge,
                    "judgeReasoning": args.judge_effort, "noHints": args.no_hints, "nativeAnswers": args.native_answers, "maxTokens": MAX_TOKENS, "promptsSha256": args.prompts_sha,
                    "usd": round(answerer.usd + (judge.usd if judge is not answerer else 0), 4),
                    "seconds": round(time.time() - started)})
    (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({k: summary[k] for k in ("questions", "failedAnswers", "failedVerdicts", "microAverage", "usd")}))
    for http in {answerer.http, judge.http} - {None}:
        await http.aclose()


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--parquet")
    p.add_argument("--reports", nargs="+")
    p.add_argument("--row")
    p.add_argument("--answer", default="openai/gpt-5.6-luna")
    p.add_argument("--judge", default="openai/gpt-5.6-luna")
    p.add_argument("--answer-effort", default="none")
    p.add_argument("--judge-effort", default="none")
    p.add_argument("--out")
    p.add_argument("--concurrency", type=int, default=24)
    p.add_argument("--limit", type=int, default=0)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--check-scorer")
    p.add_argument("--prompts-sha", default="")
    # Keep ExaBase's per-category instructions but pass no dataset annotations into the answer
    # prompt; the judge still scores against them. Isolates the hints from the prompt.
    p.add_argument("--no-hints", action="store_true")
    # Score the saved native answers with ExaBase's judge: isolates our judge from our composer.
    p.add_argument("--native-answers", action="store_true")
    args = p.parse_args()
    if args.check_scorer:
        sys.exit(0 if check_scorer(args.check_scorer) else 1)
    asyncio.run(run(args))


if __name__ == "__main__":
    main()
