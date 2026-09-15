# Reproducing the numbers

Everything below is stated in full in `../paper/methodology.md`; this page is the
short form with the values you need to re-run.

## Code

| component | repository | revision at publication |
|---|---|---|
| harness (`varys bench`) and pipeline | github.com/varops/acropolis-varys | tag `whitepaper-2026-09`, commit `93ad8b6c75d11e3679b9e7fe68c86a356fe58ccc` |
| Parthenon (the record) | github.com/varops/acropolis-parthenon | `554ae5b18273b6a1a92b8eb7099559c60ef534f4` |
| Eunomia (identity) | github.com/varops/acropolis-eunomia | `549fbf122db8b19e8bde1092795a85456383ae73` |
| Pythia (answering loop) | github.com/varops/varops-pythia | `6742742edee9a340485194dcc34ac0ef993eb945` |

Every report records the harness commit that produced it and whether the tree was
dirty. The September reports read: LongMemEval local rows at `187cc9e` and `8e92cac`
(clean); LoCoMo at `cb1606a` and BEAM 100K, the never-refuse probe and `assembly_v3` at
`6be26f0`, both flagged dirty. The dirty flag at both is one uncommitted `Cargo.lock`
line (`futures-util`), committed since as `460011e`; the code that ran is the recorded
commit plus that line.

## Datasets

Not redistributed. The harness reads a local copy and refuses to run if the file's
SHA-256 does not match the one recorded in the reports.

| file | SHA-256 (as recorded in the reports) | source |
|---|---|---|
| `longmemeval_s.json` | `08d8dad4be43ee2049a22ff5674eb86725d0ce5ff434cde2627e5e8e7e117894` | LongMemEval authors' release |
| `locomo10.json` | `79fa87e90f04081343b8c8debecb80a9a6842b76a7aa537dc9fdf651ea698ff4` | LoCoMo authors' release |
| `beam_100K.json` | `759d9c618c732603ddb7873657155d511e96512feec4b7b3bc2d16c0226f09bc` | BEAM authors' release |
| `beam_1M.json` | `ca9bac4820d237b65bd0d20fccf395659b545acfc117d8c0ea5c6776fe98d292` | BEAM authors' release |

## Model seats

Frontier placement (the site's configuration): extractor gpt-4.1-mini; embeddings
nomic-ai/nomic-embed-text-v1.5 (local, CPU); rewrite and rerank gemini-3.7-flash;
answer gemini-3.7-flash, alone or in the Pythia loop; judge gemini-3.7-flash under the
fixed prompts in Appendix A.10.

Local placement: extractor, rewrite, rerank and answer on gemma-4-31b-it (open
weights) served by vLLM on one NVIDIA H200 per bench machine, bf16 weights, fp8 KV
cache, thinking enabled, `--max-model-len 65536` (131072 for BEAM 100K); embeddings
unchanged; judge gemini-3.7-flash, with gemma-4-31b-it re-judging every stored answer
for the agreement figures. "Local" means ownership and operation, not machine location:
an open-weight checkpoint served under our control, with no inference sent to a
model-provider API.

Retrieval budgets: 100 lexical / 300 semantic / 100 rerank-pool candidates (120 on
BEAM 100K). Observation excerpts 2,000 characters.

## Commands

```bash
# ingest: one brain per conversation, production intake door and pipeline
varys bench ingest longmemeval --file longmemeval_s.json --dir $DATA --work-dir $WORK/lme \
  --shard $i/6 --door-url http://127.0.0.1:$PORT --signing-key $KEYS/bench-intake.key \
  --tenant $TENANT --provision-cmd "$HOOKS/provision.sh {brain_id}" \
  --register-cmd "$HOOKS/register.sh {brain_id} {identity_id} {public_key}" \
  --extractor model --extractor-model gpt-4.1-mini --extractor-max-output-tokens 1500 \
  --confidence-floor 0.3 --extractor-profile episodic

# local placement: same ingest against the vLLM server
VARYS_BRAIN_NAMESPACE=sov VARYS_EXTRACT_CONCURRENCY=16 \
varys bench ingest longmemeval ... --extractor-endpoint http://127.0.0.1:8000/v1 \
  --extractor-model gemma-4-31b-it --extractor-api-key-env GEMMA_API_KEY

# project every brain (the ask path reads projections)
ls $WORK/lme | grep '^brn_' | xargs -P 4 -I{} parthenon project run --brain {} --dsn $DSN --owner-dsn $DSN

# ask, frontier core row (VARYS_PYTHIA=1 for the loop row)
varys bench ask longmemeval --file longmemeval_s.json --dir $DATA --work-dir $WORK/lme \
  --shard $i/6 --parthenon-url http://127.0.0.1:$PORT --tenant $TENANT \
  --answering full --compose-contract assembly_v2 --rewrite --rerank \
  --pipeline-model gemini-3.7-flash --answer-model gemini-3.7-flash --judge-model gemini-3.7-flash \
  --out $WORK/lme/ask_core_$i_6

# own-everything row: pipeline and answer seats on the local server
PARTHENON_OBSERVATION_EXCERPT_CHARS=2000 PARTHENON_OBSERVATION_LIMIT=100 VARYS_RERANK_POOL=100 \
varys bench ask longmemeval ... --compose-contract assembly_v2 --rewrite --rerank \
  --pipeline-endpoint http://127.0.0.1:8000/v1 --pipeline-model gemma-4-31b-it \
  --answer-endpoint   http://127.0.0.1:8000/v1 --answer-model   gemma-4-31b-it --answer-max-output-tokens 8000 \
  --judge-model gemini-3.7-flash --out $WORK/lme-sov/ask_core_owned_$i_192

# rent-the-thinking row: as above with --answer-model gemini-3.7-flash and VARYS_PYTHIA=1
# never-refuse probe: the frontier row with --compose-contract never_refuse_probe
# one conversation from several lanes: --only-questions ids.txt (one question id per line)

# BEAM 1M aggregation, committed formula
python3 scripts/beam-official-aggregate.py $WORK/beam/ask_*.json

# manifest of a report directory
python3 scripts/report-manifest.py --bundle $WORK --out manifest.json --md manifest.md
```

## Scoring

Strict correctness: a fixed one-word yes/no judge against the gold answer
(precision-first: softeners pass, narrow closed ranges pass, open bounds and
contradictions fail); an answer beginning `unanswerable` is an abstention, wrong on
answerable questions. BEAM protocol: per-item rubric judge, `rubric_score` = fraction
satisfied; `event_ordering` = tau_b_norm × F1 with the judge matching events only.
Retrieval: document identity against the dataset's evidence annotations, `text_scored`
must be 0. Full definitions, judge prompts and the noise-floor rules: Appendix A.5, A.6,
A.8, A.10.

## Wall-clock and cost, for planning

Frontier: LongMemEval ingest about $3 and 6 to 7 hours over six lanes; a full ask pass
about $7 and one hour; BEAM 1M three to four LongMemEval passes in model spend; BEAM
ingest under $10. Local, one H200 per bench machine: LongMemEval ingest of 500 brains
in about 12 hours over two machines; LoCoMo 53 and 70 minutes per conversation; BEAM
100K ingest about three hours over two machines; BEAM 100K local answering at a median
of 746 (single call) to 917 (loop) seconds per question with 14 conversations sharing
one GPU, 54 to 60 seconds for the frontier rows. Throughput figures for a shared box,
not single-user latencies.
