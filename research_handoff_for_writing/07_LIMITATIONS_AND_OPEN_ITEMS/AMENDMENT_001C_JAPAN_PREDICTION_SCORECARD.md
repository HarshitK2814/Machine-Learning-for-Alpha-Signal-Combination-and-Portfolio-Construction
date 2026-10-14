# Amendment 001C: scorecard for the five Japan predictions (2026-10-14)

Internal researcher-led scoring of a repository-committed amendment that was **never countersigned**. Nothing here is an independent or confirmatory evaluation, and no result below is called "pre-registered" or "confirmatory". No model was trained or rerun, no return series or strategy statistic was computed, and no threshold was chosen after seeing an outcome: thresholds are copied verbatim from `docs/AMENDMENT_001C_CAPACITY_HYPOTHESIS_PREREGISTRATION.md` section 3 (commit `927e91e`, 2026-10-09 10:27 +05:30, whose section 5 records that no Japanese portfolio existed at that time). Observed values are read only from committed snapshots in `docs/attachments/`. Germany's untraceable inference row is not used. Germany's `+0.128` appears in the amendment itself as a fixed threshold.

Scores: `MET`, `NOT_MET`, `INDETERMINATE`, `NOT_SCOREABLE`. Every comparison is a **descriptive threshold comparison on point estimates**; none is a statistical test.

## 1. Scorecard

| # | Original prediction (verbatim) | Falsified if (verbatim) | Operational condition | Unambiguous? | Artifact and observed value | Score |
|---|---|---|---|---|---|---|
| **P1** | "At $1bn Japan's realised gross is a similar *fraction* of its ceiling as Germany's and India's (DEU 0.132/0.213 = 62%, IND 0.056/0.110 = 51%), i.e. roughly **0.42–0.51** in absolute terms." | "realised gross below 0.25 or above 0.70" | Japan's realised gross exposure at $1bn must lie in [0.25, 0.70] (falsification bounds); the 62%/51% examples are the optimised book's realised gross ("P / E" in `docs/RESULTS_CAPACITY_2026-10-09.md` section 4) divided by the capacity ceiling | **No.** Which book and which statistic (mean over months and cells, composite, prediction cells only) are not stated; the Germany and India examples identify it as the optimised book's realised gross | **No committed artifact** holds Japan's optimised-book realised gross at $1bn. `SUMMARY_AFTER_TAX_*` has no exposure column. A different object exists in the record (the capped **decile** book's attained gross, 0.162 of 2.0 in `AMENDMENT_001D` section 11) but it is not the quantity P1 refers to and is not substituted | **NOT_SCOREABLE** |
| **P2** | "At $1bn Japan's **net Sharpe exceeds Germany's +0.128**, because $1bn is only 2.4x past Japan's frontier against 9.4x past Germany's." | "Japan's net Sharpe at $1bn is below +0.128" | Net Sharpe of the 8 prediction-loss cells at $1bn, optimised book, as the stage-06 summary reports it (mean over the 8 cells under the zero-tax regime); the threshold is the amendment's fixed number | **Yes, with one verified definition.** The amendment's +0.128 equals the Germany $1bn cell mean in the committed snapshot (0.1282), so the same statistic is applied to Japan; the composite reading is checked as well (below) | `docs/attachments/SUMMARY_AFTER_TAX_JPN_1E9_2026-10-09.csv` (sha256 `cec2ef836ce0ea0d...`): cell-mean net Sharpe **0.0568**, 8 prediction cells, 132 months, `--max-names 600` (001B). Composite reading, `AFTER_TAX_INFERENCE_1E9_2026-10-09.csv`: **0.0550**. Both below 0.128 | **NOT_MET** (falsification condition met) |
| **P3** | "Japan's **share of names at the participation cap at $1bn is ≥95%** (already measured at 99.5–99.7% from cost inputs alone, so this is a consistency check rather than a test)." | "below 95%" | Share of names at the ADV participation cap at $1bn | **No.** The population (eligible names, held names, which months) and whether the share is from cost inputs or from the optimised weights are not defined. The amendment states its own pre-measured figure (99.5-99.7%), which cannot score itself | The only Japanese figure in the committed record is that statement inside the amendment; the capacity-frontier table that holds Japan's ceiling (0.825) is untracked and carries no cap-share column. No committed artifact | **NOT_SCOREABLE** |
| **P4** | "**The control.** At $100mn — *below* Japan's $413mn frontier, the only such point in the study — capacity does not bind, so `corr(\|w\|, adv_cap)` is **materially below Germany's +0.555** at the same AUM, and the signed alpha tilt `corr(w, alpha)` is **above Germany's +0.497**." | "Japan at $1e8 shows a liquidity correlation at or above Germany's, i.e. looks capacity-bound where theory says it is not" | Two weight-cross-section correlations of Japan's $100mn optimised book against Germany's values | **No.** "Materially below" has no numeric margin; the alpha measure for `corr(w, alpha)` and the aggregation across months and cells are not stated. Only the falsification direction (Japan's liquidity correlation not below Germany's) is directional | **No committed artifact.** These diagnostics need the optimised weights; the repository records Japan's diagnostic as not done (`docs/FINALIZATION_AUDIT_2026-10-09.md` P0-8; `realised_books_JPN.csv` described as an empty stub). The committed `SUMMARY_AFTER_TAX_JPN_1E8` carries no weight correlations | **NOT_SCOREABLE** |
| **P5** | "At $100mn, with capacity slack, **at least one of the three design axes** (representation, conditioning, uncertainty) becomes individually significant at 5%, where none is at capacity-bound scales (`RESULTS_CAPACITY` §5c: t = +0.48, −1.20, +1.53)." | "no axis significant at $1e8 in Japan either" | At $100mn in Japan, at least one design-axis contrast has an unadjusted two-sided p below 0.05 | **Partly.** The multiplicity rule (unadjusted versus Holm) is not stated and the book (decile or optimised) is not stated, though the comparison values (+0.48, -1.20, +1.53) are the optimised-book axis t-statistics at $1bn | **No committed artifact at $100mn for Japan.** `GATE2_POWER_1E9` is at $1bn only; `DESIGN_IDENTIFIABILITY` covers Germany and India decile books only. Japan's $1bn conditioning t = +2.84 is the wrong AUM and is **not** substituted | **NOT_SCOREABLE** |

Summary: 1 of 5 scoreable (P2, `NOT_MET`); 4 of 5 `NOT_SCOREABLE` from committed artifacts. The amendment's own text says a P5-only failure would indicate low power rather than falsification; no P5 result exists to apply that to.

## 2. P2 detail (descriptive)

| Quantity | Value | Source |
|---|---|---|
| Threshold in the amendment | +0.128 | amendment section 3, P2 |
| Germany $1bn, cell mean (check that the threshold is the same statistic) | 0.1282 | `SUMMARY_AFTER_TAX_DEU_1E9_2026-10-09.csv` (verbatim snapshot of an earlier untracked output; sha256 `84a8d5ff172cf1f6...`; weight identity inferred, older script) |
| Japan $1bn, cell mean | 0.0568 | `SUMMARY_AFTER_TAX_JPN_1E9_2026-10-09.csv` (tracked since commit `64a318e`; byte-identical to the local original) |
| Japan $1bn, composite (inference tool) | 0.0550 | `AFTER_TAX_INFERENCE_1E9_2026-10-09.csv` |
| Difference to threshold | -0.0712 (cell mean), -0.0730 (composite) | arithmetic |

No test statistic accompanies the comparison; Japan's net Sharpe is itself not distinguishable from zero (t = +0.18 in the composite row), so "below the threshold" is a point-estimate statement; no interval was computed.

## 3. The amendment's section 4 "what would falsify H-CAP as a whole" (not among the five predictions)

Shown because section 6 of the amendment says failures must be reported with the same prominence. Same rules (committed snapshots, descriptive).

| Condition (verbatim) | Observed | Status |
|---|---|---|
| "**P2 and P4 both failing.**" | P2 `NOT_MET`; P4 `NOT_SCOREABLE` | **INDETERMINATE** (depends on P4) |
| "A **non-monotone net Sharpe** in Japan across $1e8 / $1e9 / $1e10, where Germany's is monotone increasing (−0.116 → +0.128 → +0.271)." | Japan cell-mean net Sharpe -0.0882 ($1e8), +0.0568 ($1e9), -0.1001 ($1e10): non-monotone (`SUMMARY_AFTER_TAX_JPN_{1E8,1E9,1E10}`). Note: the committed Germany snapshots give 0.2547 / 0.1282 / 0.1855, which differ from the amendment's -0.116 / +0.271 for the $1e8 and $1e10 rungs (the amendment's figures came from earlier runs); the condition concerns Japan | the stated condition is **met** (descriptive) |
| "Japan's cost drag **failing to fall** with AUM, which would break the turnover-brake step specifically." | Japan cell-mean cost drag 166.51 -> 42.31 -> 5.48 basis points per year | condition **not met** (cost drag falls) |

Reading: one of the amendment's own whole-hypothesis falsification conditions (non-monotone Japanese net Sharpe) is met on the committed snapshots, one is not, and one is indeterminate. This does not by itself settle H-CAP: the amendment gives no rule for combining them, and each is a point-estimate statement on three AUM rungs. It does mean the candidate may not describe Japan as supporting H-CAP.

## 4. Provenance limits that apply to every row

* The Japan summaries come from the stage-06 outputs of 2026-10-09; run-time hashes of the code and of the weights do not exist, and the weight identity was recovered by modification-time ordering (`docs/PHASE_C_AFTER_TAX_CONFIGURATION_RECOVERY_2026-10-14.md`); the Japan $1bn snapshot was committed earlier and is byte-identical to the local file.
* The amendment text is a repository commit by the project team on behalf of the designated statistical reviewer; it was not countersigned and sits in no external registry. Its timing (before Japan's portfolios existed) rests on its own section 5 and on commit history, not on independent verification.
* The amendment fixed its thresholds before the Japanese portfolios existed and none was changed here; but P1, P3, P4 and P5 as written lack the definitions needed to score them mechanically, and defining them now would be choosing the operationalisation after the outcomes are known.

## 5. Author decisions needed (not taken here)

1. **P1, P3, P4:** whether to approve a descriptive aggregation of Japan's existing optimised-weights files (untracked, not committed snapshots) to score these, and if so to fix the exact definitions in writing **before** any number is read: which book, which months, which statistic, and for P4 what "materially below" means numerically. Without that decision they stay `NOT_SCOREABLE`. This would use stored weights, not new model runs, but it is still an analysis and is not performed here.
2. **P5:** whether Japan's $100mn axis contrasts may be derived from existing stored cell series (untracked), and under which multiplicity rule; otherwise `NOT_SCOREABLE`.
3. **Reporting:** how the manuscript reports the outcome (this scorecard: P2 not met; four not scoreable; one of the section 4 conditions met). The amendment required failures to be reported with the same prominence as other failures.
4. **Countersignature status:** whether the reviewer named in the amendment will countersign or comment; until then the scorecard remains internal.
