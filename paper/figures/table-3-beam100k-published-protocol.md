# Table 3. BEAM 100K, 400 questions: our protocol and the published comparison protocol, on the same stored evidence

| configuration | our protocol, answerable only (as in Figure 2) | our protocol, all 400 | published protocol, gemini-3.7-flash | published protocol, gpt-5.6-luna |
|---|---|---|---|---|
| Own everything, local single call | 53.3 | 52.5 | 85.2 | 87.8 |
| Own everything, local loop | 57.3 | 56.4 | 86.8 | 87.9 |
| Own the knowledge, rent the thinking | 66.4 | 64.7 | 85.6 | 87.7 |
| Frontier single call, same local brains | 64.5 | 62.4 | 85.6 | 87.8 |
| Frontier loop, same local brains | 66.8 | 66.9 | 85.3 | 87.6 |
| Reference: frontier single call, published brains | 66.7 | 65.1 | 84.9 | 88.1 |
| Reference: frontier loop, published brains | 67.5 | 66.7 | 86.0 | 88.4 |
| Vendor Y⁴, highest published BEAM 100K figure | — | — | — | 92.1 |
| Vendor Z⁵, author of the protocol's prompts | — | — | 76.9 (Gemini 3 Flash) | — |

Added in v1.1. Per-question records: `reproduction/reports/beam/100k-published-protocol-2026-10/`. Vendor Y and Vendor Z sources: `reproduction/manifests/comparisons.md`.
