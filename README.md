# Own the Knowledge, Rent the Thinking.

### Separating institutional understanding from frontier intelligence.

> **Acropolis, a governed model of the organization**

- Technical Report 01
- Ran Aroussi, VarOps LLC
- September 2026, version 1.0


This repository holds the paper, the methodology, and every benchmark report behind its numbers.

The paper's claim in one line: institutional understanding and frontier reasoning can be separated. A locally operated 31B open-weight model can build the organizational record; a frontier model can be rented only for per-question reasoning over that record. Across LongMemEval-S, LoCoMo and BEAM 100K, keeping everything local retains 84 to 96 percent of all-frontier performance, and renting only the answer seat retains 96 to 99 percent.
The Markdown under `paper/` is the source of truth and can evolve; the PDFs under `releases/` are the frozen, citable v1.0. This repository is not Acropolis source code.

It is the evidence the paper promises to publish: per-question run reports, their hashes, the code revisions and model pins that produced them, and enough of the method to re-run it.

## Layout

| path | what it holds |
|---|---|
| `paper/README.md` | the paper, Markdown, source of truth |
| `paper/index.html` | the paper and Appendix A as one self-contained web page (canvas charts, sidebar navigation) |
| `paper/methodology.md` | Appendix A, benchmark methodology (reference v1.2) |
| `paper/figures/acropolis-figures.html` | the figure set, self-contained HTML (Figures 1 to 9, Tables 1 and 2) |
| `paper/references.bib` | references |
| `reproduction/README.md` | harness, revisions, model pins, dataset hashes, commands |
| `reproduction/manifests/` | the public manifest over the published reports, and the manifest of the unredacted bundle |
| `reproduction/reports/` | 2,539 per-question run reports, one JSON per shard or part |
| `releases/` | the frozen v1.0: `acropolis-v1.0.pdf` (paper and Appendix A in one document, the citable object) and its Word source |
| `CITATION.cff` | how to cite |

## Results

`reproduction/reports/<benchmark>/<campaign>/<bench-machine>/<report>.json`, exactly as the harness wrote them, with one change described below.

| directory | what | retention |
|---|---|---|
| `longmemeval/local-campaign-2026-09` | every model placement on the local (Gemma-4-31B) brains: own everything, rent the thinking, frontier readers on local brains, the never-refuse probe; standalone retrieval rows | full |
| `longmemeval/reference-published-brains-2026-09` | the all-frontier reference on the published (gpt-4.1-mini) brains: core 89.4, loop 91.4, plus the other September runs on that work directory | full |
| `longmemeval/site-banked-2026-08-partial` | what remains of the August runs behind the site's banked 89.2 / 90.5 / 91.6 | partial, see below |
| `locomo/local-campaign-2026-09` | LoCoMo, all placements, 435 questions per row, including the retired `assembly_v3` rows | full |
| `beam/100k-local-brains-2026-09` | BEAM 100K on the local brains, all placements, 400 questions per row | full |
| `beam/100k-published-brains-2026-09` | BEAM 100K frontier rows on the published brains | full |
| `beam/1m-site-banked-2026-08-partial` | what remains of the August BEAM 1M runs behind the site's 60.2 and the governed composite | partial, see below |

Each report carries the dataset hash, shard and part, compose contract, model ids, harness commit with its dirty flag, cost and latency, and one row per question with the answer, the verdict, the strict and rubric scores where the dataset has a rubric, the claims delivered, the observations delivered, and (LoCoMo and BEAM) the question's own retrieval score. `reproduction/manifests/manifest.json` lists every file with its SHA-256 and maps each published figure to the files behind it; `manifest.md` beside it is the readable version.

**Partial retention.** The site's August figures (LongMemEval core 89.2, agentic 90.5, escalation 91.6; BEAM 1M core 60.2 and the governed composite) are only partially retained as per-shard reports: later runs reused tags on the same work directories and overwrote shard files, and one gate run was lost to temp cleanup. Those figures stand as published in the paper's numbers sheet and corrections log, are re-runnable from the tagged harness, and are marked in the paper as not independently auditable per question from this bundle (Appendix A.12). Every September figure and both reference rows are fully retained.

**Dataset text is withheld.** The reports are published verbatim except for two fields that reproduce benchmark text: each observation's `excerpt` (a conversation passage from the dataset) and each question's `gold` answer. Both are replaced by an object holding the SHA-256 and character count of the original, so a reader who holds the dataset can verify every one of them per question. Nothing else is altered: ids, our answers, verdicts, scores, retrieval rows, extracted claims and provenance are as written. The `reproduction/manifests/manifest-full-bundle.json` file is the manifest of the unredacted bundle (SHA-256 `230800cf9c0b72c5aed0ae57be51c39e10745dd4eccec3b1fcd013198defbd1b`, the value printed in Appendix A); its per-file hashes are of the full reports and will not match the published files. `reproduction/manifests/manifest.json` is the manifest of what is published here.

## Reading a report

```python
import json
r = json.load(open("reproduction/reports/beam/100k-local-brains-2026-09/lon1/ask_agentic_upgrade_10_20_p0.json"))
r["compose_contract"], r["reproducibility"]["answer_model"], r["scores"]["overall_accuracy"]
q = r["questions"][0]
q["question_id"], q["correct"], q["abstained"], q.get("rubric_score"), q.get("retrieval")
```

Strict correctness (`correct`) is the metric shared across all three benchmarks; BEAM's own protocol is `rubric_score` per question (rubric fraction, or Kendall tau times F1 for event ordering). Aggregation rules and the noise floor are in Appendix A.6 and A.8.

## Reproduction

`reproduction/README.md` has the harness location and release tag, the exact commit and dirty state of every run, the model pins per seat, the dataset files and hashes the harness checks before it runs, and the commands. The harness is `varys bench` in [acropolis-varys](https://github.com/varops/acropolis-varys) at tag `whitepaper-2026-09`.

## License

The paper, methodology, figures and results in this repository are released under CC BY 4.0 (see `LICENSE`). Benchmark datasets are not redistributed; see `reproduction/README.md` for their sources and hashes.

## Diagrams

The two diagram figures (Figure 1, the boundary; Figure 4, the request path) are kept as Mermaid sources in `paper/figures/*.mmd` and embedded in `paper/README.md`, so the graph that generated a figure can be read and edited, not only looked at. The chart figures (retrieval, answering, the placement table, BEAM by ability, the cost tiles) are data tables in the paper and rendered in `paper/figures/acropolis-figures.html`.

## Citation

If you use the results, the methodology or the reports, please cite the report.

Aroussi, R. (2026). *Own the Knowledge, Rent the Thinking. Separating institutional understanding from frontier intelligence.* Acropolis, a governed model of the organization: Technical Report 01, version 1.0. VarOps LLC. https://doi.org/10.5281/zenodo.22775192

```bibtex
@techreport{aroussi2026ownknowledge,
  title       = {Own the Knowledge, Rent the Thinking. Separating institutional understanding from frontier intelligence},
  author      = {Aroussi, Ran},
  institution = {VarOps LLC},
  number      = {Acropolis, a governed model of the organization: Technical Report 01},
  year        = {2026},
  month       = {9},
  version     = {1.0},
  doi         = {10.5281/zenodo.22775192},
  url         = {https://github.com/varops/acropolis-research}
}
```

`CITATION.cff` at the root carries the same metadata for GitHub's "Cite this repository" button and for reference managers.
