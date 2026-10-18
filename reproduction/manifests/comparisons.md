# Comparison sources

The paper does not name other vendors. Each figure it cites is recorded here with its source and the date it was read, so every comparison can be checked.

| paper label | vendor | figure cited | source | read |
|---|---|---|---|---|
| Vendor Y (Table 3) | past.dev | BEAM 100K 92.08 overall, 400 questions; per ability as published | https://past.dev/benchmarks; harness and per-question results at https://github.com/pastdotdev/benchmarks/tree/main/beam (commit `1faac1e70fa50d92d966904358be98bb1beca0c8`, run of 2026-09-29) | 2026-10-17 |
| Vendor Z (Table 3) | Exabase (Exabase M-1) | BEAM 100K 76.9 (answer model Gemini 3 Flash, as stated) | https://exabase.io/blog/exabase-m1-achieves-state-of-the-art-on-beam-benchmark | 2026-10-17 |
| The protocol's prompts | ExaBase's published BEAM adapter | answer prompt, per-rubric judge, event-ordering equivalence prompt | https://fabric.so/p/beam-3VjBcqEVRofZyA5CeazeX (file SHA-256 `584b672d957f3e6f75e96f881ec31da22e1039da1df5fbedb53dc6a9145cfc43`); the verbatim copy used is Vendor Y's `beam/exabase_prompts.py` (SHA-256 `7c958668ebcebcfddb1209fd73aab1d530c4b6be6422d6a9ed1121d39051e457`) | 2026-10-17 |
