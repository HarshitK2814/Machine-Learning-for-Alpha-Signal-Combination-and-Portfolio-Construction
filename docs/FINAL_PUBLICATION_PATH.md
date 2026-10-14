# Final publication path (2026-10-14)

Internal researcher-led decision record, produced from `docs/FINAL_CLAIM_EVIDENCE_MATRIX.md`. It is not an external review and implies no approval by Maham or Absar. Binding constraints observed: Phase C not run; the 560 series stay not estimable; no vendor bridge, imputation, liquidation rule or new exit policy; no thresholds, procedures, families, windows, specifications or hypotheses changed; no A2, cost sensitivity, training, re-optimisation or external access; no withdrawn claim restored.

## 1. The question

**Can the central research contribution be supported by the existing, traceable as-run evidence without Phase C?**

The central contribution, as stated in `docs/FINALIZATION_AUDIT_2026-10-09.md` section 2.1, is a like-for-like measurement of how much of a machine-learning equity signal survives three implementation frictions (AUM-indexed cost, an ADV participation constraint, statutory capital-gains tax) in Germany, India and Japan, 2009-2019, with the finding that the net-of-cost Sharpe of the optimised book is not distinguishable from zero.

## 2. What Phase C was, and why its block does not remove the contribution

Phase C was a **robustness revision** of the historical results under the 2026-10-13 exit ruling (`carry_v1`), not a source of the central findings. The block means two things only: the as-run numbers cannot be shown to be insensitive to the exit treatment, and no revised confirmatory result exists. It does not delete the as-run evidence. It does remove any right to describe the as-run numbers as robust to the exit ruling or as confirmatory under it.

## 3. Evidence audit result (details in the matrix)

| Element of the central contribution | State |
|---|---|
| Net Sharpe of the optimised book not distinguishable from zero at $1bn | Traceable for **India (t +0.82) and Japan (t +0.18)**; **Germany (t +0.53) is not traceable to any artifact**. |
| Signal is real gross; executable capped decile book is negative net | Traceable (matched-book attachments: capped net Sharpe DEU -0.709, IND -0.638, JPN -0.828 at $1bn, with the few-percent-of-target-gross caveat). |
| Capacity: effect of the ADV cap | The only usable unit is **B(A)** (`results/capacity_return_difference/`, tracked, 35 valid rungs, monotone in AUM), an accounting difference against an infeasible, near-ruined comparator. The Sharpe-point gains are withdrawn. |
| Tax: statute decides whether a holding-period channel exists | Traceable for the flat regimes (`lt_share` exactly 0.0000, 80 statutory rows); India's 0.5928 is traceable only to an untracked local file. |
| Tax channel ordering by statute type | Traceable on the executable decile book in all three countries (DEU -0.070, IND -0.009, JPN -0.170, flat regimes 8-19x India); India itself borderline. The optimised-book match and the turnover ordering are not usable. |
| Design axes undetectable at this power | Traceable (0 of 42 capped in DEU and IND; minimum detectable effect 0.25-0.81 Sharpe points); Japan conditioning axis exploratory. |
| Coverage-asymmetry worked failure | Traceable (t -6.098 in the non-compliant artifact; coverage 0.652 vs 0.989 vs 0.998 recomputed from tracked census counts). |

## 4. Decision: rule B

The paper **can be made scientifically coherent with the existing traceable as-run evidence, but only as a narrower paper.** Rule A is not met because the original headline set (Sharpe-point capacity gains, "the cap improves net performance", the clean two-placebo tax contrast, Germany's net-Sharpe t, the survival framing) is partly withdrawn and partly untraceable; the central contribution as first stated is therefore not intact. Rule C is not met because the narrower contribution does not depend on Phase C results. So:

* A **separate** manuscript candidate is prepared in `submission_candidate_as_run_only/`. The full-account paper and every historical document are untouched.
* The candidate is explicitly a **measurement and cautionary-methods paper**, not the original "how the cap improves performance" paper. What changed relative to the original framing:
  1. The capacity result is reported only in B(A) return units, as an accounting difference against an infeasible comparator, with near-ruined rungs flagged. The Sharpe-point headline is dropped, not qualified into the abstract.
  2. "No mandate size at which the cap hurts" is dropped (cost-calibration sensitivity not run).
  3. The tax claim is "statute decides whether the holding-period channel exists" plus an ordering of magnitudes by statute type on the executable decile book; the exact placebo match, the turnover ordering and the survival framing are not in the paper.
  4. The net-Sharpe null is reported for India and Japan with traceable numbers; Germany is stated as not currently traceable rather than quoted.
  5. Every as-run number is labelled `as_run` exit, with a disclosure that the revised analysis is blocked and was not run, and that sensitivity to the exit ruling is unknown.
  6. The paper is not described as a replication of, or an update to, any analysis it did not perform.
* The candidate is **not submission-ready** (section 5).

## 5. Why the candidate is not submission-ready

These items undermine or can change claims, so none is optional:

1. **Germany's net-Sharpe and optimised-book tax numbers have no artifact.** A tracked, hashed snapshot would need a regeneration of historical statistics, which requires explicit authorisation. Until then the Germany headline cannot appear as a number.
2. **Exit-treatment sensitivity is unknown and cannot currently be bounded.** A referee will ask what the as-run exit does to the numbers. The exit ruling is the owners'; the revised analysis is blocked by data (`unknown` vendor coverage). The candidate can only disclose.
3. **Pre-registration is not countersigned** (001A-001D) and 001E is a draft. The candidate says so; any "pre-registered" wording is an author decision.
4. **Closest prior art read at abstract level only** (Avramov-Cheng-Metzker, Management Science 2023, full text not obtained; several rows in the tracker). Required before submission regardless of results.
5. **The tax-literature citation records are not in the bibliography** (F6) and the candidate has no citation for them.
6. **No tracked snapshot for India's `lt_share`** or for the optimised-book summaries; the matrix flags every figure that rests on an untracked file.
7. **No LaTeX or journal template exists and no TeX toolchain is installed here**; the candidate is Markdown with a deterministic consistency check, not a compiled PDF.
8. **Contribution strength.** Even narrowed, the contribution is a measurement that corroborates published work (Avramov-Cheng-Metzker; Novy-Marx-Velikov) and a methods caution; the venue ordering in `FINALIZATION_AUDIT` section 4 stays an author decision.

## 6. What was executed because of this decision

* Claim-evidence matrix and this decision record.
* `submission_candidate_as_run_only/` (manuscript, trimmed bibliography, traceability table with hashes, README).
* `tools/check_submission_candidate.py` and its tests: citation keys resolve against the bibliography, every referenced artifact exists and matches its recorded SHA-256, every quoted headline number re-derives from the committed artifact, required disclosures are present, banned claims are absent.
* The withdrawn-claims screen extended to the candidate directory and to the Sharpe-point capacity figures.
* README corrected (stale status, test count and data-access statement).
* `docs/PROJECT_COMPLETION_REPORT.md`.
