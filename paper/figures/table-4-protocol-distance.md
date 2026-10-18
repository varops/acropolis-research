# Table 4. Where the distance between the two protocols comes from

Local single call on the local brains; each step changes one thing. The two right-hand columns are gemini-3.7-flash.

| step | gemini-3.7-flash | gpt-5.6-luna | six annotated abilities | four unannotated abilities |
|---|---|---|---|---|
| our protocol: our answer contract, our judge | 52.5 | 52.5 | 50.6 | 55.4 |
| the same stored answers under the comparison judge | 58.7 | 63.9 | 57.8 | 60.2 |
| comparison answer prompt on the same evidence, annotations removed | 74.1 | 74.0 | 72.3 | 76.7 |
| comparison answer prompt with the annotations, the published protocol | 85.2 | 87.8 | 91.4 | 75.9 |

Added in v1.1. Per-question records: `reproduction/reports/beam/100k-published-protocol-2026-10/` (`rejudge/`, `nohints/`, `full/`).
