# Appendix A: benchmark methodology

### Own the Knowledge. Rent the Thinking. · Acropolis, a governed model of the organization · Technical Report 01

> This is the machine-readable version of Appendix A to *Own the Knowledge. Rent the Thinking.* (Acropolis Technical Report 01), v1.0. The canonical published version is the PDF in `releases/` (DOI: 10.5281/zenodo.22775192). The Markdown may continue to evolve; the release is frozen.

```
Reference v1.2 (draft 4) · 2026-09-15
Varys harness, main at draft:       93ad8b6c75d11e3679b9e7fe68c86a356fe58ccc  (merge of probe/never-refuse-contract, #65)
Parthenon, main at draft:           554ae5b18273b6a1a92b8eb7099559c60ef534f4  (merge of feat/directory-generation-revocation, #50)
Eunomia, main at draft:             549fbf122db8b19e8bde1092795a85456383ae73  (merge of test/permission-propagation-measured, #5)
Pythia, main at draft:              6742742edee9a340485194dcc34ac0ef993eb945  (merge of feat/derivation-is-coverage, #2)
Release tag:                        whitepaper-2026-09 at 93ad8b6 (varys)
Report bundle manifest (SHA-256):   230800cf9c0b72c5aed0ae57be51c39e10745dd4eccec3b1fcd013198defbd1b
```
Each published run report carries the harness and Parthenon SHAs that produced it,
which may predate the commits above; the manifest lists every report and its hashes.
The September reports record the harness commit that produced them: the LongMemEval
local rows at 187cc9e and 8e92cac (clean trees); the LoCoMo rows at cb1606a and the
BEAM 100K, never-refuse and assembly_v3 rows at 6be26f0, both flagged dirty. The dirty
flag at both commits is one uncommitted line on the bench machines, `Cargo.lock`
gaining `futures-util` for the buffered extraction stream, committed since as 460011e
on the same branch; the code that ran is the recorded commit plus that lockfile line and
nothing else. The Parthenon SHA is recorded as unknown in the ask reports (the bench
machines run a built binary, not a checkout); the manifest carries the Parthenon
version string instead. The manifest covers 2,539 reports: the September local campaign, the reference rows on
the published brains (lme-gpt41, 2026-09-07: core 89.4 and loop 91.4, six shards each,
fully retained), and what remains of the August frontier work directories lme-s and
beam-1M.
The four branches are merged to main as of 2026-09-15; the release tag names the
varys merge commit above.

Draft 4, 2026-09-15. The canonical metric definitions and correction history remain
in the VarOps benchmark metrics glossary. This appendix is the publication-specific,
frozen account of the figures and methods used in this whitepaper. In the event of a
discrepancy, the report-bundle manifest and its linked per-question run reports
control for the published figures; subsequent corrections are recorded in the
glossary. Where this appendix says "not measured", that is the finding.

## A.1 What was measured, and what was not

This appendix describes how the figures in the whitepaper were produced, in enough
detail to re-run them from the committed harness. It covers three public datasets, one harness, several model placements spanning fully
local through all-frontier (own everything, rent the answer seat, rent on refusal,
frontier readers on local brains, and the all-frontier reference), two scoring stages
(retrieval and answering), the aggregation formulas, the noise floor, the two measurement probes
(never-refuse, and a contract rewrite that nulled), and the comparisons to other
published systems.

Throughout this appendix, "local" refers to model ownership and operation, not to the
physical location of the machine: an open-weight checkpoint served by us under our own
control, with no inference sent to a model-provider API. The benchmark runs used rented
H200 hardware reached over a tunnel from the bench machines. The experiment therefore
establishes the feasibility of self-operated models in each seat; it does not claim
that a benchmark ran inside a customer's building.

Since draft 3 three properties moved from "by construction" to measured on the
committed harness and its integration tests, outside any benchmark: cross-brain
isolation under an adversarial probe (A.13), provenance of every delivered claim
(A.6), and identity resolution and permission-change propagation on a bounded fixture
(A.13). What remains unmeasured: identity at the scale of a live directory, aliases and
reorganizations, and operational outcomes in a live organization. None of the three
datasets is enterprise-shaped. All three are conversational-memory benchmarks, chosen
because they are public, reproducible, and already used by the systems we compare
against.

## A.2 Datasets

No corpus or question in this paper was authored by VarOps. Each dataset was used as
published, without modification to conversations, questions, or gold answers.

| dataset | unit under test | questions | authored by | what it exercises |
|---|---|---|---|---|
| LongMemEval-S | one multi-session chat history per question (~50 sessions, ~500 messages) | 500 | dataset authors, human-written questions | information extraction, multi-session reasoning, temporal reasoning, knowledge updates, abstention (30 unanswerable traps) |
| LoCoMo | ten very long multi-session conversations | 432 (site) / 435 (September) | dataset authors | QA over events, causality and time across sessions; 88 unanswerable |
| BEAM 1M | 35 conversations, ~1M tokens each (~35M tokens total) | 700 | dataset authors, generated per their protocol | ten abilities including summarization, event ordering, contradiction resolution, abstention |
| BEAM 100K | 20 conversations, ~100K tokens each | 400 | dataset authors, generated per their protocol | the same ten abilities, 2 questions per ability per conversation; 40 unanswerable |

The LoCoMo figures use the dataset's published sample, two conversations per category
under the harness's fixed seed. The site counted 432 questions; three adversarial items
the harness now keeps make it 435, and every September LoCoMo row is 435 of 435. The
frontier LoCoMo row was re-run on the September brains at 435 and reads 81.8, the
site's number, so the two counts do not move the figure.

BEAM 100K was used for the local-model placement rather than BEAM 1M because a 31B
model reading million-token conversations at benchmark concurrency would have taken
weeks of GPU time for a number the 100K variant already explains. The two variants are
never compared to each other in this paper; the frontier configuration is scored on
both and each is labeled.

Dataset licenses are research licenses; the harness reads a local copy of each
published file and records its SHA-256 in every report (`dataset_sha256`), so a
re-run against a different file is refused rather than silently compared.

## A.3 The harness

All figures come from `varys bench`, a Rust harness committed in the Varys repository.
It has three commands and no others were used:

- `varys bench ingest <dataset>` — provisions one fresh Parthenon brain per
  conversation, submits every message through the production signed-intake door,
  and runs the production distillation pipeline (triage, extraction, claim proposal,
  validation) with tier budgets on. The extractor is the system under test; the
  benchmark's conversations are the only input.
- `varys bench ask <dataset>` — for each question, runs retrieval against the brain
  built for its conversation, composes an answer under the named configuration, and
  scores it.
- `varys bench retrieval <dataset>` — the standalone retrieval scorer, used for the
  alternative-reranker rows (a cross-encoder, raw embedding order) that no answering
  row consumed.

Properties that matter for reproduction:

- **One brain per conversation, fresh per run.** A conversation's brain id is derived
  from the dataset and conversation id, and since September from a campaign namespace
  as well, so two campaigns on one machine cannot collide. Re-running a campaign
  reprovisions the brain; resumed runs replay from a per-conversation checkpoint and
  never re-score. A run that mixes resumed and fresh work reports it (`resumed_claims`).
- **Projection is part of the pipeline.** Retrieval reads projections (lexical,
  semantic, graph, synopsis) built from the canonical claims after ingest. A brain that
  is ingested but not projected returns nothing, which the harness reports as zero
  candidates rather than as an abstention.
- **Sharding.** Frontier campaigns ran as 6 (LongMemEval, LoCoMo) or 8 (BEAM) shards
  across lanes on two bench machines. The September local campaign ran LongMemEval as
  192 shards, LoCoMo as one shard per conversation split into 12 question parts, and
  BEAM 100K as one shard per conversation split into two parts, so that one brain could
  be answered by several lanes at once (`--only-questions <ids>` names the part).
  Every report records its shard and part, and a multi-shard work directory records
  the whole-corpus state so the ask guard cannot read a partial ingest as complete.
- **Every report is self-describing.** It carries the dataset hash, the shard, the
  model ids for extractor, answerer and judge (the pipeline model is recorded in the
  retrieval reports, a v1.1 gap for ask reports), the compose contract, the harness and Parthenon git SHAs with a dirty-tree flag, the claim-registry
  hash, per-question rows with the retrieved claims, the delivered observations (excerpt
  capped at 2,000 characters), the question's own retrieval score (`retrieval`: first hit
  rank, Hit@5/10, strict Recall@5/10, pool size, gold in pool, gold in top 10), cost and
  latency. A report from a dirty tree says so in its provenance warnings.
- **One run yields every table.** Since 2026-09-13 the ask report carries retrieval and
  evidence per question, so the answering, retrieval, governance, escalation, provenance
  and judge-agreement tables are all derived from the same stored run; nothing is
  re-run to produce a second table. The LoCoMo and BEAM 100K campaigns were produced
  under that rule. The LongMemEval local rows predate it: their retrieval figures come
  from standalone `bench retrieval` runs on the same brains and pool, and their
  provenance audit from the delivered claims, which every report has always carried.
- **Held questions.** When a model endpoint refuses a request (timeout, outage, context
  overflow), the harness holds the question and exits with a resume code; the wrapper
  resumes up to three times. A question still held after that is absent from the
  report, and the report does not say so; only the lane log does. This bit the BEAM 100K local rows (A.9, 2026-09-14). Publication now requires that
  every report's question count equals the dataset's expected count for its shard and
  part; a mismatch fails the release gate (A.12) and the manifest records the count. A
  report field listing held ids is a v1.1 harness change.

## A.4 Models and budgets

All published numbers were produced with the following pins. Every model id names a
provider snapshot or an open-weight checkpoint; the report-bundle manifest carries the
same ids per report, and any figure whose snapshot is no longer callable is marked as
such (A.12).

**Frontier placement (the site's configuration):**

| seat | model | notes |
|---|---|---|
| extractor (ingest) | gpt-4.1-mini | claims proposed from conversation messages; ~$0.06 per LongMemEval conversation |
| embeddings | nomic-ai/nomic-embed-text-v1.5 | local, CPU; semantic projection |
| pipeline (query rewrite, rerank) | gemini-3.7-flash | pinned snapshot |
| answerer, core row | gemini-3.7-flash | composes from the evidence envelope under the `assembly_v2` contract |
| answerer, agentic row | Pythia loop on gemini-3.7-flash | bounded ask / compute / extract loop over the same envelope |
| answerer, BEAM composite | gpt-5.6 (snapshot `gpt-5.6-sol`) loop, gemini-3.7-flash direct pass | see A.7 |
| judge | gemini-3.7-flash | fixed prompts, A.6 |

**Local placement (the September campaign):**

| seat | model | notes |
|---|---|---|
| extractor (ingest) | gemma-4-31b-it (open weights) | vLLM on one NVIDIA H200 per bench machine; bf16 weights, fp8 KV cache; 8 to 16 extractions in flight |
| embeddings | nomic-ai/nomic-embed-text-v1.5 | unchanged, local |
| pipeline (query rewrite, rerank) | gemma-4-31b-it | same server; "local reranker" in the tables |
| answerer, own-everything rows | gemma-4-31b-it, single call or Pythia loop | thinking enabled; `<thought>` blocks stripped before the reply is read |
| answerer, rent-the-thinking row | gemini-3.7-flash | the only frontier call; sees the evidence envelope for one question |
| judge | gemini-3.7-flash, with gemma-4-31b-it as co-judge on every stored answer | A.6, judge agreement |

The vLLM server ran with a 65,536-token context for LongMemEval and LoCoMo and was
raised to 131,072 (the model's configured maximum) for BEAM 100K, where the synthesis
envelope reaches about 57,000 tokens and the 8,000-token answer budget overflowed the
smaller context (A.9). The two bench machines are 16-core, 62 GB rented CPU boxes with no GPU; each ran up to
14 (BEAM) or 28 (LongMemEval) Parthenon lane servers beside the harness, and each was
tunnelled to its own H200. These September machines are not the August BEAM ingest
machines whose cost table Part I Section 6 reports (two Xeon 8280s, 31 GB); the boxes
were resized for the local campaign. Local tokens are priced at the frontier
list rate in every cost column so the rows are comparable; the real local cost is GPU
time, reported as latency in A.10.

Retrieval budgets are fixed at 100 lexical / 300 semantic / 100 rerank-pool candidates
for every published retrieval figure (120 rerank-pool on BEAM 100K, the synthesis
union). Observation excerpts are 2,000 characters (the 500-character default truncated
most assistant content and was the first correction in the log, A.9).

## A.5 Retrieval scoring

Retrieval is scored before any answering model runs. The system returns a ranked
top-10 list of evidence messages per question.

| metric | definition |
|---|---|
| Hit@10 / Hit@5 | at least one gold evidence unit appears in the top 10 / top 5 |
| MRR | mean reciprocal rank of the first gold unit |
| Recall@10 strict | all gold evidence units for the question appear in the top 10; full credit or none |
| Recall@10 micro | fraction of all gold evidence units that appear in the top 10 |
| gold-in-pool | diagnostic only: gold present anywhere in the candidate pool before final ranking |

Since 2026-08-24 every retrieval figure is scored on **document identity**
(`source_object_id`), never on text overlap. Each report carries `text_scored`; a
non-zero value means some questions fell back to text matching and the run is not
comparable. All published retrieval figures have `text_scored: 0`.

Two dataset-specific cautions. LongMemEval annotates gold evidence per session (one
unit that expands to about 22 messages); LoCoMo and BEAM annotate per message. Strict
recall counts annotated units, never expanded messages. BEAM questions often cite more
than ten evidence messages, so strict Recall@10 has a ceiling below 100% by
construction; it is quoted against the achievable ceiling. On BEAM 100K, 355 of the
400 questions carry evidence annotations and retrieval is scored on those.

Published retrieval figures, frontier placement (identity-scored, published budgets):

| | LongMemEval-S | LoCoMo | BEAM 1M |
|---|---|---|---|
| questions | 500 | 432 | 700 |
| Hit@10 | 99.80% | 93.06% | 44.00% |
| Hit@5 | 99.00% | 90.74% | 35.84% |
| Recall@10 strict | 95.80% | 82.64% | 16.16% |
| Recall@10 micro | 97.36% | 77.29% | 8.86% |
| MRR | 0.9846 | 0.8225 | 0.2546 |

Retrieval on the local brains (Gemma-4-31B extractor), by reranker. The in-run rows are
the retrieval each answering row actually received, scored per question inside the
run; the standalone rows are `bench retrieval` on the same pool.

| brains, reranker | LongMemEval-S Hit@5 / @10 | LoCoMo Hit@5 / @10 | BEAM 100K Hit@5 / @10 |
|---|---|---|---|
| local brains, local reranker (in run; LongMemEval standalone) | 99.4 / 99.6 | 80.6 / 85.2 | 33.5 / 43.1 |
| local brains, frontier reranker (in run; LongMemEval standalone) | 99.2 / 99.6 | 91.2 / 92.6 | 39.2 / 47.6 |
| local brains, local reranker (standalone) | 99.4 / 99.6 | 80.1 / 84.5 | 33.8 / 43.9 |
| local brains, cross-encoder (BGE reranker v2 m3, standalone) | — | 52.5 / 60.9 | — |
| local brains, no reranker, embedding order (standalone) | 96.2 / — | 40.5 / 50.7 | 22.3 / 40.8 |
| published brains, frontier reranker (standalone) | 99.0 / 99.8 | 90.7 / 93.1 | 40.6 / 49.6 |

Retrieval is identical across every answering configuration that shares a reranker:
the agentic and composite rows consume the same ranked evidence the core row does.

## A.6 Answering scoring

**LongMemEval and LoCoMo.** Each answer is judged against the dataset's gold answer by
a fixed one-word yes/no judge prompt (reproduced in A.10). The judge accepts any listed
acceptable form and ignores formatting, casing and spelled-out numerals. Accuracy is
the fraction of questions judged correct. An answer beginning with the token
`unanswerable` is an abstention; abstentions on answerable questions count as wrong.
The judge protocol is precision-first: softeners pass, narrow closed ranges pass, open
bounds and contradictions fail.

Governance metrics on LongMemEval use the dataset's 30 unanswerable trap questions
(88 on LoCoMo, 40 on BEAM 100K):

- **abstention precision** — of all abstentions in a run, the fraction that were on
  trap questions;
- **false-answer rate on unanswerable** — of the traps, the fraction that received an
  asserted answer instead of an abstention. The published "25–28 of 30 refused" is this
  metric across the four banked agentic runs.
- **fabrication** — a narrower, manually classified count: among the trap questions
  that were not refused, an answer that asserts a fact absent from the history.
  Non-refusals that are semantically correct refusals phrased without the token, or
  model transport failures, are not fabrications. The published figure is one such
  answer across the four banked agentic runs (4 × 500 judged answers, 120 trap rows),
  and it must be read as: one fabrication in the tested unanswerable-trap sample under
  the stated protocol. It is not a general hallucination rate over arbitrary questions,
  and the paper does not use it as one. This classification is the one human step in
  the scoring pipeline; it changes no score, only this count, and every non-refused
  trap row is listed in the run reports so the classification can be checked.
- **declined an answerable** — the count of abstentions on answerable questions; the
  denominator of the escalation rows (A.7).

**BEAM.** BEAM ships a per-question checklist ("the response should contain: …") and
two of its abilities ship no reference answer at all, so a gold-string judge is
unusable. Each checklist item is judged independently by a fixed per-item prompt
(A.10), meaning over wording. A verdict that cannot be read as one line per item is
refused and re-judged, never scored as zero. `event_ordering` is scored by BEAM's
published protocol, tau_b_norm × F1, with the judge used only to match events between
the gold and candidate lists; the arithmetic is deterministic and tested. Every ask
report carries both readings per question: `correct` (strict: every item satisfied)
and `rubric_score` (the fraction satisfied, or the tau score).

The **committed aggregator** (`scripts/beam-official-aggregate.py`) produces the
published BEAM 1M figures: rubric categories as the mean per-question rubric fraction;
`event_ordering` as the tau protocol score; `abstention` binary (correct iff the run
abstained on the trap); overall as the question-weighted mean across categories. The
BEAM 100K tables in Part I are stated both ways: strict correctness, the metric shared
with LongMemEval and LoCoMo, and the rubric protocol as the mean of `rubric_score` over
the non-abstention questions, with abstention reported as traps refused. Under strict
correctness event ordering and summarization read 0 to 3 of 40 for every configuration,
because a partially ordered list or a partial summary is never wholly correct; the
protocol reading gives them partial credit, and both are printed.

Cross-formula note, stated once: the committed aggregator reads the August core run
about 2.6 points below the aggregation it was published under. The core row's band
(59.0–60.6) stands under its own aggregation; the composite row is stated as a paired
delta under the committed formula. Deltas within one formula are valid; absolute
comparisons across the two are not, and the paper never makes one. The BEAM 100K
protocol figures are under the per-question `rubric_score` the harness writes, which is
the committed aggregator's per-question input; they are not compared to the 1M figures.

**Judge agreement.** Every stored LongMemEval and LoCoMo answer of the September
campaign was re-judged by gemma-4-31b-it under the identical prompt. Agreement with
gemini-3.7-flash: 98.7 to 99.2 percent on 2,223 LongMemEval answers, 95.2 percent on
1,531 LoCoMo answers, where gold answers are longer free-text spans. The local judge is
stricter on every row (by 0.4 to 2.8 points) and preserves every ordering in every
table. The scores do not hinge on which model judges.

**Provenance and evidence audit.** All 118,890 claims delivered across 2,500 stored
LongMemEval answers resolve to a stored observation with a source identity, 0
exceptions. A separate LLM audit of 2,233 answers against the evidence each was given
finds unsupported wrong assertions in about 1 in 100 answers, at the same rate for local
and frontier answerers. Both are derived from the stored reports, not from a new run.

## A.7 Configurations

The configurations in the paper share retrieval, extraction and projection within a
placement; they differ in which model fills which seat and how the answer is composed.

- **Core.** A single composition call over the evidence envelope under a fixed contract
  (`assembly_v2`). Two different guarantees apply here and the paper keeps them apart.
  What the model *sees* is bounded deterministically: the envelope is assembled by
  retrieval under the caller's authorization before any model runs, and it carries an
  explicit coverage state (answered, searched-and-empty, outside-the-ontology). Whether
  the model *asserts* beyond that envelope is a contract instruction (reply
  `UNANSWERABLE` when the material does not cover the question), not a hard gate: in the
  published answering rows the composition model is called even when coverage is empty,
  and its compliance is exactly what the abstention and fabrication metrics measure. A
  deterministic short-circuit (empty coverage scored as an abstention without calling any
  model) exists only in the harness's substrate-only mode, which is not a published row.
- **Agentic (Pythia).** A bounded loop with three tools over the same envelope, ask
  (retrieve more), compute (deterministic arithmetic and date logic), extract, with a
  mandatory `asked_at` time anchor. Same answering model as core.
- **Governed composite (BEAM 1M only).** A deterministic routing policy over two
  complete runs: the cheap direct pass's refusals and contradiction declarations ship
  as-is (150 of 700 rows); a frontier loop answers the remainder. No oracle, no
  per-question selection by score; the routing rules are three fixed signals and were
  validated live on the governance categories (abstention 71.9, contradiction 73.4 on
  the smoke set before the full run).

**Model placement rows (Part I, Figure 2).** Each is a full run, not a derivation, except the
escalation rows:

- *Own everything*: local extractor, local embeddings, local rewrite and rerank, local
  answer (single call or Pythia loop). The published figure is the better of the two.
- *Own the knowledge, rent the thinking* ("upgrade" in the run reports): everything local
  except the answer seat, which is gemini-3.7-flash in the Pythia loop.
- *Rent only when the local answer refuses* (escalation): derived by joining two stored
  runs on question id. The local row's answer is kept wherever it answered; on the
  questions it declined (an answerable question with an abstention), the frontier row's
  answer and verdict are taken instead. No question is re-asked and no selection uses
  the score. The number of questions escalated is printed beside every escalation figure.
- *Frontier in every seat, same local brains*: the frontier pipeline and answerer over
  brains the local extractor built; isolates the extractor seat.
- *Reference*: the site's configuration, frontier in every seat on gpt-4.1-mini brains.

**Contracts and probes.** The refusal posture of the agentic contract is a labeled
configuration with two measured endpoints: v0.5 (LongMemEval 90.5, BEAM abstention
50.0) and v0.6 (LongMemEval 89.4, BEAM abstention 64.3). The paper headlines v0.6 for
BEAM. One contract cannot maximize both; three contract variants scored 56.4 / 57.4 /
57.1 overall on BEAM, which is the measured statement that contract knobs redistribute
points between refusal posture and coverage rather than create them. Two further
contracts exist in the harness and are labeled in every report that used them:

- `never_refuse_probe` — assembly_v2 with the refusal deleted and inverted (the model
  must always answer). A measurement probe, never a deployment configuration; the report
  carries `is_probe`. Used once, on the LongMemEval frontier single call over the local
  brains, to measure the never-refuse protocol on our own substrate (A.11).
- `assembly_v3` — assembly_v2 plus four instructions written against the local model's
  observed mistakes on LoCoMo (read every excerpt before refusing, list every item,
  resolve relative dates, treat different dates as different events). Measured paired on
  435 LoCoMo questions: 73.0 → 72.2 on the single call, 79.6 → 77.6 on the loop, with
  the refusal count unchanged. Retired; no published row uses it.

## A.8 Noise floor and the paired-analysis rule

Two full-700 BEAM runs of byte-identical code differ by ±2–5 points per category (n=70
per category) and about 1 point overall. LongMemEval categories are n=30–150 and behave
similarly; BEAM 100K abilities are n=40 and are wider still. Consequences, applied
throughout:

- A category delta under about 5 points on a single run is not reported as a result.
- Every comparison used to interpret a small difference as a result is **paired** on
  the identical question set and inspected as gains / losses; aggregate percentages are
  still reported for readability, and a difference between two of them is not a finding
  until the paired view agrees. The v3
  contract (14 gained, 18 lost on one conversation; 6 gained, 5 lost on the other) and
  the never-refuse probe (29 gained, 33 lost) were both decided this way.
- Numbers are published as bands over repeated full runs where repeats exist:
  LongMemEval core 89.2 (band 88.4–89.6), agentic 90.5 (band 90.4–90.6, four full
  runs), BEAM core 60.2 (band 59.0–60.6). The September rows are single full runs, and
  the paper reads them at the noise floor above: the extractor-seat comparison (one to
  two points on 1,335 questions) is called a hold, not a win.
- Half-set previews are not published. The one time a half set was used to preview a
  BEAM result, the full set came in 2.4 points lower (A.9, 2026-09-01). The BEAM 100K
  half read on 2026-09-14 (200 questions) was reported as preliminary and superseded by
  the full 400 the next morning.
- Two-shard pilots (n=18 per category) were retired after mis-signalling twice; the
  September v3 probe on error-only question sets (8 of 43 and 16 of 59 flipped) is the
  same lesson: a probe on errors cannot see losses, and the full paired rows reversed it.

## A.9 Corrections log

Every correction that changed a published number, dated, with the mechanism. This
table is maintained in the VarOps benchmark metrics glossary and reproduced here
verbatim at publication; the entries below are the ones that moved a headline.

| date | correction |
|---|---|
| 2026-08-23 | Observation excerpts were truncated at 500 characters, deleting most assistant content. Fixed to 2,000. LongMemEval answering 83.4 → 89; BEAM 27 → 41 strict. |
| 2026-08-24 | Retrieval had been scored by text overlap against the excerpt; now scored by document identity. LongMemEval retrieval up; BEAM down 9 points as false hits were removed. All earlier retrieval figures withdrawn. |
| 2026-08-27 | An apparent 26% judge-noise signal came from a probe that changed two variables at once; two full runs under the fixed protocol refuted it. Rule adopted: judge rechecks must match the scoring protocol exactly. |
| 2026-08-30 | BEAM `event_ordering` moved from a rubric stand-in to the published tau protocol; the category fell from 15.1 to 11.9 (later 26.0 with the committed aggregator). The official aggregator script and one gate run's raw reports were lost to temp cleanup; the aggregator was rebuilt and committed, and a fresh gate run made on current main before any composite figure was published. |
| 2026-09-01 | Half-set BEAM preview (shards 4–7) was optimistic: composite 63.5 → 61.1 on the full 700; summarization 64.8 → 56.4. Rule adopted: full set only. |
| 2026-09-04 | Extractor swap (gemini-3.7-flash for gpt-4.1-mini) measured as a null: LongMemEval core 87.4 vs 89.2, agentic 89.2 vs 90.5 (paired 15/16, a tie). Two intermediate runs retracted before that result: one with 118 unprojected brains (69.8), one with six brains emptied by a colliding test campaign (85.8 / 88.8). Banked figures unchanged. |
| 2026-09-12 | The LongMemEval local rows' reports lacked per-question retrieval, so their retrieval table had to come from separate standalone runs on the same brains rather than from the answering run itself. Rule adopted: a report field the paper needs is a launch blocker; one run must yield every table. The harness gained retrieval and observations per question the next day, and LoCoMo and BEAM 100K were run under it. |
| 2026-09-13 | A local cross-encoder reranker (BGE reranker v2 m3) was predicted to close the local retrieval gap on LoCoMo and measured at Hit@5 52.5 against 80.6 for the local language model on the same pool. Reported as a negative result; no published row uses it. |
| 2026-09-14 | Every BEAM 100K local-answer part was short by two synthesis questions: the ~57K-token synthesis envelope plus the 8,000-token answer budget exceeded the local server's 65,536 context, and held questions were dropped from the reports without a field saying so. Context raised to 131,072, every short part re-asked from its progress file, every report verified at 10 of 10 before scoring. Lowering the answer budget was rejected because stored local answers reach 7,323 output tokens. |
| 2026-09-15 | Part I draft 5 had stated the fully local loop with escalation on refusals at 91.4 on LongMemEval; the stored join reads 88.6 (27 escalated). 91.4 is the local-retrieval, rented-answer row with escalation (21 escalated). Corrected in the draft and in the placement figure (then Figure 8, now Figure 2) before review. |
| 2026-09-15 | `assembly_v3` retired after two paired full rows (73.0 → 72.2; loop 79.6 → 77.6). The error-only probe that motivated it had shown 8 of 43 and 16 of 59 flips; the full rows showed matching losses. |

## A.10 Reproduction

Commands as run, with placeholders for machine-local paths. Model pins are those in
A.4; endpoints are the providers' OpenAI-compatible endpoints, or the local vLLM
server for the local placement.

```bash
# ingest: one brain per conversation, 6 shards (i/6), production intake door + pipeline
varys bench ingest longmemeval --file longmemeval_s.json --dir $DATA --work-dir $WORK/lme \
  --shard $i/6 --door-url http://127.0.0.1:$PORT --signing-key $KEYS/bench-intake.key \
  --tenant $TENANT --provision-cmd "$HOOKS/provision.sh {brain_id}" \
  --register-cmd "$HOOKS/register.sh {brain_id} {identity_id} {public_key}" \
  --extractor model --extractor-model gpt-4.1-mini --extractor-max-output-tokens 1500 \
  --confidence-floor 0.3 --extractor-profile episodic

# local placement: the same ingest against the vLLM server, N extractions in flight
VARYS_BRAIN_NAMESPACE=sov VARYS_EXTRACT_CONCURRENCY=16 \
varys bench ingest longmemeval ... --extractor-endpoint http://127.0.0.1:8000/v1 \
  --extractor-model gemma-4-31b-it --extractor-api-key-env GEMMA_API_KEY

# project every brain the ingest built (the ask path reads projections, not claims)
ls $WORK/lme | grep '^brn_' | xargs -P 4 -I{} parthenon project run --brain {} --dsn $DSN --owner-dsn $DSN

# ask, frontier core row (drop VARYS_PYTHIA for core; set VARYS_PYTHIA=1 for the agentic row)
varys bench ask longmemeval --file longmemeval_s.json --dir $DATA --work-dir $WORK/lme \
  --shard $i/6 --parthenon-url http://127.0.0.1:$PORT --tenant $TENANT \
  --answering full --compose-contract assembly_v2 --rewrite --rerank \
  --pipeline-model gemini-3.7-flash --answer-model gemini-3.7-flash --judge-model gemini-3.7-flash \
  --out $WORK/lme/ask_core_$i_6

# ask, own-everything row: pipeline and answer seats on the local server, judge unchanged
PARTHENON_OBSERVATION_EXCERPT_CHARS=2000 PARTHENON_OBSERVATION_LIMIT=100 VARYS_RERANK_POOL=100 \
varys bench ask longmemeval ... --compose-contract assembly_v2 --rewrite --rerank \
  --pipeline-endpoint http://127.0.0.1:8000/v1 --pipeline-model gemma-4-31b-it \
  --answer-endpoint   http://127.0.0.1:8000/v1 --answer-model   gemma-4-31b-it --answer-max-output-tokens 8000 \
  --judge-model gemini-3.7-flash --out $WORK/lme-sov/ask_core_owned_$i_192

# rent-the-thinking row: same, with --answer-model gemini-3.7-flash and VARYS_PYTHIA=1
# never-refuse probe: same as the frontier row with --compose-contract never_refuse_probe
# a question part of one conversation: --only-questions ids.txt (one question id per line)

# BEAM aggregation, committed formula
python3 scripts/beam-official-aggregate.py $WORK/beam/ask_*.json
```

Judge prompts, verbatim from the harness:

> *Gold-answer judge (LongMemEval, LoCoMo):* "You judge whether a hypothesis answer
> is correct given a question and the gold answer. The gold may list several
> acceptable forms or alternatives; answer yes if the hypothesis matches ANY
> acceptable form. Ignore formatting differences: markdown, casing, spelled-out vs
> numeric values, and extra words that do not change the meaning. Reply with exactly
> one word: yes or no."

> *Rubric judge (BEAM):* "You judge a response against a grading checklist. You are
> given a question, the response, and a numbered checklist of required elements.
> Judge EACH item independently. Judge meaning, not wording: an item is satisfied
> when the response conveys it, regardless of phrasing, order, casing, or
> formatting. Reply with one line per checklist item and nothing else, in the form
> `<number>: yes` or `<number>: no`. Do not add commentary, and do not merge items."

Cost and wall-clock, for planning a re-run. Frontier placement: LongMemEval ingest is
about $3 and 6–7 hours across six lanes with gpt-4.1-mini; a full LongMemEval ask pass
is about $7 and one hour; a full BEAM 1M campaign with the frontier loop is roughly
three to four times a LongMemEval pass in model spend. The BEAM corpus cost under $10
to ingest. Local placement, on one H200 per bench machine: LongMemEval ingest of 500
brains in about 12 hours across two machines at 48 lanes each; LoCoMo ingest 53 and 70
minutes per conversation with 16 extractions in flight; BEAM 100K ingest of 20
conversations in about three hours across two machines. Answering: the LongMemEval
local single call ran at a median of 150 seconds per question on a single lane; the
BEAM 100K local rows ran at a median of 746 (single call) and 917 seconds (loop) per
question with 14 conversations sharing one GPU, against 54 to 60 seconds for the
frontier rows. The local BEAM loop row took 6 to 13 hours per machine. Those are
throughput figures for a shared benchmark box, not single-user latencies.

## A.11 Comparisons to other systems

The paper compares to one other system, referred to as Vendor X: a commercial memory
layer (retrieval and answering over conversation history) with none of the identity,
authorization, or execution components in the Acropolis topology. Its figures are its
own published figures under its own protocol. The vendor is not named in the paper; the
report-bundle manifest records the source page and retrieval date for the cited figures
so the comparison is checkable. Three things make it cross-protocol, and the paper
labels it so wherever it appears:

1. Vendor X's protocol instructs the model never to state that information is missing,
   so a refusal can never cost it a point; Acropolis figures include honest refusals.
2. Vendor X does not publish retrieval or abstention metrics at the 1M-token scale. Its LongMemEval-S accuracy cannot have been produced under the official abstention
   rule: 30 of 500 questions are unanswerable traps, correct only when refused, so a
   never-refuse system caps at 94.0. A score of 98.0 is therefore incompatible with
   applying the official abstention rule to all 500 questions under a never-refuse
   policy.
3. BEAM figures are under two different aggregations (A.6, cross-formula note).

Both systems' guard columns (abstention, contradiction) are shown alongside overall so
the trade is visible. No third-party system was re-run by VarOps.

**The never-refuse protocol, measured on our own substrate.** One Acropolis figure was
produced under a never-refuse contract, as a labeled probe (A.7), so that the size of
the protocol difference is a measurement rather than an estimate. LongMemEval, all 500
questions, frontier single call over the local brains, same retrieval and same judge,
paired against the assembly_v2 row on identical questions:

| contract | all 500 | traps refused of 30 | traps answered | declined an answerable of 470 | answerable-only accuracy |
|---|---|---|---|---|---|
| assembly_v2 | 88.0 | 29 | 1 | 28 | 87.4 |
| never_refuse_probe | 87.2 | 0 | 30 | 0 | 92.8 |

Removing the refusal gained 29 questions (22 of the 28 wrong refusals, plus 7 others)
and lost 33 (all 30 traps, plus 3 answerable). It did not raise the headline under a
judge that scores a confident wrong answer as wrong, and it raised the answerable-only
figure, the way never-refuse systems report, by 5.4 points. The paper uses this to
state the bridge from a published never-refuse number to its own as three parts:
answerable-only scoring, a judge that does not see fabrications, and whatever model or
retrieval difference remains. The probe row is not a published configuration and
appears only in Part I's Figure 7 and here.

## A.12 Release gate for reproducibility

Reproducibility is a claim only if the artefacts are available. Before publication,
the Varys repository, the `varys bench` harness and the committed aggregator are
publicly available under the release tag named in the report-bundle manifest; the
per-question run reports behind every published figure are published alongside the
paper; dataset retrieval instructions and hashes are included; model pins name
provider snapshots or open-weight checkpoints. If any of these is missing at release, the
affected figure is marked "not independently reproducible" in the paper. Applied: the
site's banked LongMemEval figures (core 89.2 band, agentic 90.5 over four runs,
escalation 91.6) and the BEAM 1M figures (core 60.2 band, governed composite) are only
partially retained as per-shard reports, because later runs on the same work
directories overwrote shard files under reused tags and one gate run's raw reports were
lost to temp cleanup (A.9, 2026-08-30). Those figures stand as published in the
2026-09-01 numbers sheet and the glossary, are re-runnable from the tagged harness and
the named datasets, and are marked not independently auditable per question from this
bundle. Every September figure and both reference rows are fully retained. Part I marks each
table: ● full per-question artifacts in the bundle; ◐ re-runnable from the tagged harness,
historical artifacts partially retained. The
snapshot-callability check was not repeated at release; the model ids are as pinned in
A.4 and the reports. If a named
model snapshot is no longer callable by an independent reader, the affected figure is
marked the same way, even when the harness and reports remain available: the published
reports stay auditable and the aggregations stay repeatable, but the end-to-end figure
is not independently reproducible. The local placement's figures depend on an
open-weight checkpoint and a serving configuration (vLLM version, context, KV precision,
thinking on), all recorded in the manifest; they are reproducible by anyone with the
checkpoint and one comparable GPU.

The report-bundle manifest is published alongside the paper in human-readable and
machine-readable (JSON) form; its SHA-256 is printed in the reference block above. It
records the repository URL, release tag, immutable commit SHA and licence, and for every
published run report: file name, SHA-256, dataset and dataset hash, configuration name,
compose contract, model ids and snapshot identifiers, harness and Parthenon SHAs with
the dirty-tree flag, run date range, shard and part coverage, question count against
the dataset, whether resumed work was included, and the exact aggregate output file
behind each published number.

Report format: machine-readable JSON, one file per shard (and part) per configuration,
each containing the run's provenance block (dataset hash, shard, model ids and
endpoints, compose contract, harness and Parthenon SHAs with dirty-tree flag, registry
hash) and one row per question with the question id, category, gold, the answer,
abstention flag, judge verdict, strict and rubric scores where the dataset has a
rubric, the retrieved claims with their source object ids and ranks, the delivered
observations, the question's retrieval score, cost and latency, plus the run's
provenance warnings.

The release does not redistribute datasets whose licenses prohibit redistribution; it
provides the official source, required file names and SHA-256 hashes for each.

## A.13 Shipped, specified, measured

For every path the paper or website names, its status at publication:

| path | status |
|---|---|
| signed intake door, distillation pipeline, claims with evidence and supersession | shipped; exercised by every benchmark run |
| projections (lexical, semantic, graph, synopsis) and retrieval at published budgets | shipped; exercised by every run |
| coverage states in the answer envelope (answered / searched-and-empty / outside-the-ontology) | shipped; the abstention figures depend on it |
| Pythia loop (ask / compute / extract, `asked_at` anchor) | shipped in the harness host; the agentic row |
| governed composite routing (refusal and contradiction signals) | shipped as a deterministic policy in the harness; validated live |
| per-brain isolation, fails closed | shipped; measured by an adversarial probe against live per-brain servers: five brain pairs, nine cases each, 45 of 45 refused or contained (wrong tenant, foreign key, tampered, expired and missing assertions refused with no data; an assertion replayed against another brain's server returns none of the first brain's claims; naming another brain or another principal's scope refused) |
| graduated disclosure ladders | shipped; rungs derived at write time, never redacted at read time; 18 integration tests including an adversarial reconstruction over 22 reader-visible tables; end to end, a finance reader's envelope carries the precise value and a sales reader's carries the band and trend on the same subject with no byte of the precise value |
| task-scoped context (`ask_batch`, `context(subjects)`, validity token, `revalidate`) | shipped and drilled over the wire; no public benchmark exercises the two-stage ask, so measured by mechanism, not by score |
| identity resolution and permission-change propagation | measured on a bounded fixture: 1,000 people across 3 namespaces, 50 evidence-backed merges, 20 conflicting handles; 3,030 references resolved, 0 wrong, 0 missing, conflicts surfaced as typed ambiguity; directory change reaches the next assertion at 0 ms (cache off) or within the TTL; an issued assertion refused within the generation-feed poll interval (976 ms at a 1 s poll, 3 s default); feed outage honoured through a grace window then fails closed. Live directories, aliases at scale and reorganizations not exercised |
| self-operated open-weight placement | measured across the extractor, pipeline and answer seats on rented H200 infrastructure (one per bench machine, two machines) on all three benchmarks; the rent-the-thinking rows place the frontier model in the answer seat by design (Part I, Figure 2) |

## A.14 Validation this paper does not contain

Listed so the reader knows what would change the assessment, in rough order of what
the harness could measure next:

1. Red-team tests that unauthorized facts never enter model context through policy,
   cache, retry and failure paths (the isolation probe covers the assertion and brain
   boundaries; not the caching and retry paths).
2. Contradictory-source and supersession tests on authored corpora.
3. Identity resolution against a live directory, with aliases at scale and
   reorganizations.
4. A live enterprise pilot with measured operational outcomes.
5. Independent review of the signed intake, policy engine, audit trail and endpoint
   execution boundaries.
6. A second open-weight model in the reading seats, and BEAM 1M under the local
   placement, to bound how much of the local gap is this model rather than local
   models.
