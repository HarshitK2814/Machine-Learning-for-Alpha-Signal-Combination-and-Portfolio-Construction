**Table S8. Provenance of the stage-06 summaries and the weights they used**

| Market | AUM | Months | Dated column | Snapshot = live file | Weights index written before summary | Strategies | Indexed run exists | Index = latest run | Indexed run predates summary | Summary SHA-256 (16) |
|---|---|---|---|---|---|---|---|---|---|---|
| Germany | $100mn | 132 | False | True | True | 16 | 16 | 0 | 16 | 12d9553d0e1657c3 |
| Germany | $1bn | 132 | absent (older code) | n/a (no snapshot at the time) | False | 16 | 16 | 0 | 16 | 84a8d5ff172cf1f6 |
| Germany | $10bn | 132 | False | True | True | 16 | 16 | 0 | 16 | 9f29ea994dc34739 |
| India | $1bn | 131 | False | n/a (no snapshot at the time) | False | 16 | 16 | 0 | 16 | e2fd34229e1e8b38 |
| Japan | $100mn | 132 | False | True | True | 16 | 16 | 0 | 16 | b37f0da8081e62ab |
| Japan | $1bn | 132 | False | True | True | 16 | 16 | 0 | 16 | cec2ef836ce0ea0d |
| Japan | $10bn | 132 | False | True | True | 16 | 16 | 16 | 16 | 9b75bdb5d8ce5be3 |

*Notes.* Recovery record for the seven stage-06 summaries (2026-10-14): which weights each summary most plausibly used. 'Index = latest run' counts strategies whose indexed run is also the newest by modification time today; zero means later runs exist, so the weight identity rests on the weights index and on modification-time ordering, not on a run-time hash. Run-time hashes of code and weights were not recorded.
