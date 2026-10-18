# BEAM 100K under the published comparison protocol (v1.1)

This directory re-scores the evidence Acropolis retrieved in the September BEAM 100K runs under the answer and judge prompts that the highest published BEAM results use: ExaBase's published BEAM adapter. Nothing is re-retrieved. For each question, the answer model reads that question's stored evidence (the claims and conversation excerpts our retrieval delivered, as saved in the run report) inside ExaBase's answer prompt. A judge then scores the answer with ExaBase's per-rubric judge and, for event ordering, its matcher and Kendall tau-b score. The paper's Section 5 (v1.1 addendum) and Appendix A.11 report the results.

Results: `../reports/beam/100k-published-protocol-2026-10/`, one directory per run with `summary.json` and `results.jsonl` (400 records). Dataset-derived text (questions, answers, evidence) is withheld as SHA-256 and length, as everywhere in this bundle. Rubric verdict scores and event-ordering match positions are kept, so every score can be checked.

## Check the published runs

```bash
python3 verify.py ../reports/beam/100k-published-protocol-2026-10
```

No model or network calls. For each run, `verify.py`:

- confirms 400 records, one per question;
- recomputes every question's score from its saved verdicts;
- checks the summary's overall figure against their mean.

All 21 runs pass.

## The protocol

- **Prompts.** `exabase_prompts.py` is not redistributed here: the prompts are ExaBase's work, published in its BEAM adapter (https://fabric.so/p/beam-3VjBcqEVRofZyA5CeazeX, file SHA-256 `584b672d957f3e6f75e96f881ec31da22e1039da1df5fbedb53dc6a9145cfc43`). We used the verbatim copy in the open-source harness at github.com/pastdotdev/benchmarks (`beam/exabase_prompts.py`, commit `1faac1e`, SHA-256 `7c958668ebcebcfddb1209fd73aab1d530c4b6be6422d6a9ed1121d39051e457`). Place it beside `replay.py` to run.
- **Hints.** For six abilities the answer prompt includes the question's own dataset annotations:
  - abstention: why the question may be unanswerable;
  - event ordering: the topics to order;
  - instruction following: the instruction and its compliance indicators;
  - preference following: the preference under test;
  - summarization: the rubric items;
  - temporal reasoning: the time points and a calculation hint.

  `--no-hints` keeps the per-ability instructions but passes no annotations; the judge is unchanged.
- **Scoring.**
  - Every ability except event ordering: each rubric item scores 0, 0.5 or 1 (raw scores rounded at 0.25 and 0.75), and the question scores their mean.
  - Event ordering: the answer's list is matched to the reference topics by an equivalence judge, then scored as Kendall tau-b mapped to 0–1. An unrelated order scores about 0.5.
  - Overall is the mean over all 400 questions, abstention included.
  - `replay.py --check-scorer` reproduces the 2,000 published question scores of the harness above from its saved verdicts, with 0 mismatches.
- **Models.** Both through OpenRouter, each model answering and judging its own runs:
  - `openai/gpt-5.6-luna` with reasoning off, the configuration of the highest published figure;
  - `google/gemini-3.7-flash` with reasoning "minimal", the paper's answer and judge model (the endpoint refuses "none").
  - Output is capped at 8,000 tokens. The longest reply in the first 19,896 calls was 3,740 tokens, so no answer was truncated.
- **Questions.** The 400 questions are identical in text to that harness's 100K set. Every question is asked as of the end of its conversation; knowledge-update questions are not moved to the update turn.

## Run it

```bash
export OPENROUTER_API_KEY=...
python3 -I replay.py --parquet 100K.parquet --reports DIR [DIR...] --row agentic_owned \
  --answer openai/gpt-5.6-luna --judge openai/gpt-5.6-luna --out runs/luna-bg-agentic_owned
python3 -I replay.py ... --no-hints          # the annotations removed from the answer prompt
python3 -I replay.py ... --native-answers    # our stored answers, scored by this judge (no new answers)
```

- **`--parquet`:** BEAM's `100K` split as published on Hugging Face (`Mohammadta/BEAM`, `data/100K-00000-of-00001.parquet`), which carries the question annotations.
- **`--reports`:** the September ask reports for the configuration (`ask_<row>_<shard>_20_p<part>.json`). Running needs the unredacted reports: the evidence excerpts in this bundle are hashes. They are withheld under the licence policy in `../README.md`. BEAM's data is CC BY-SA 4.0, so a BEAM-only unredacted bundle is licence-compatible and is a separate release decision.
- **Model calls:** every call is cached in the run directory, so an interrupted run resumes without repeating calls.

The September replay cost $95.52 in model calls (32,155 calls).
