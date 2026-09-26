# Reply to Absar — US C1 pilot certification, 27 September 2026

> **Status: contract v1.2.0 is MERGED to `main`** (commit `9d88e7d`, in the merge `540ce07`), so it
> is the live contract and the thing to build against.
>
> One honest note. Per section 4 of `Team_Coding_Work_Distribution.md` a Contract Change Request
> edits only `contracts/` or `tests/contracts/`, bumps `VERSION`, and needs approval from all three
> members — nobody holds extra approval rights. This went to `main` ahead of Absar's and Maham's
> sign-off, deliberately, so that there is a definite target to build against rather than a wait.
> **Ratification is still genuinely wanted:** it is two files, `src/alphacomb/contracts/schemas.py`
> and `tests/contracts/test_schemas.py`. If either of you disagrees with the `ff49=0` encoding or
> the month-end date rule, please say so before the full-history pull — a change afterwards costs a
> rebuild.

Answers verified by running the code against an injected `ff49=0` cohort, not by reading it. The
probe put Unknown on ~5% of synthetic stock-months (matching the pilot's 4.5%) and traced it through
`contracts.validate`, `StructuralRiskModel` and the stage-04 optimiser.

---

## Copy-paste reply

> **Re: US C1 pilot — all six questions answered, approved to proceed, one addition**
>
> Good work on the ConditionalType closure and the Dec-1972 diagnosis. I ran your `ff49=0` case
> through the actual code rather than reading it. Answers:
>
> **1. Does `contracts.validate` permit `ff49=0`?** Yes — it passed. But the schema was
> `Column("ff49", "int")` with **no domain at all**, so `-1` and `9999` passed silently too. The domain is
> now pinned to `{0} ∪ 1..49` (contract **v1.2.0**, merged). Important consequence for you:
> **`3999` is now rejected**, so your 38 SICCD=3999 stock-months must arrive **recoded as 0**, not
> passed through raw.
>
> **2. Dynamic or hard-coded 1..49?** Fully dynamic. The risk model builds exposures with
> `pd.get_dummies(panel["ff49"], prefix="ind")` and the optimiser iterates
> `[c for c in risk.B.columns if c.startswith("ind_")]`. Nothing anywhere assumes 49.
>
> **3. Would `0` be constrained or silently ignored?** Genuinely constrained. `ind_0` appeared in
> `risk.B`, and realised Unknown-industry exposure came out **−0.0074 against the 0.02 limit**. All
> 827 names in, 827 out — nothing dropped.
>
> **4. Does `StructuralRiskModel` use `ff49` directly?** Yes, via the same `get_dummies`. A new
> category becomes a new factor automatically.
>
> **5. Do fixtures/tests assume exactly 49?** No — synthetic uses industries 1..12. But **no test
> had ever exercised a `0` category**, so your Dec-1973 regression request was justified. Added.
>
> **6. Can we approve `0 = Unknown` and update the stack?** Approved — and note **no code change
> was needed for it to work**. Your preferred encoding was already technically safe end to end.
>
> ---
>
> **The addition, and it matters more than the ff49 question.** You wrote that the join is
> `PERMNO + YYYYMM` "because CRSP dates are last-trading-day month ends." Every contract C1–C6
> merges on `date`. Our split calendar normalises with `pd.offsets.MonthEnd(0)` and the fixtures use
> calendar month-end. **If C1 ships dated 1972-12-29 while states or costs arrive at 1972-12-31,
> every cross-contract join silently returns nothing** — both are valid dates, so no schema check,
> dtype check or test would object. It would surface as inexplicably empty panels weeks later.
>
> Please normalise every contract to **calendar month-end** on emit, and keep the true trading date
> in a separate column if you want it for QA. The validator now enforces this, so a non-month-end
> date fails loudly at handover instead of quietly downstream.
>
> ---
>
> **Approvals**
>
> 1. **1972 frozen start year — approved.** Consistent with the expanding window before our 1995
>    first test year. Agreed it should not move on the basis of model results.
> 2. **Unknown retained in the investible universe — approved.** Your reasoning is right: dropping
>    is a non-random size/exchange selection, backfilling is look-ahead.
> 3. **`ff49=0` = Unknown — approved**, domain now enforced, `3999` must be recoded.
> 4. **Validator / optimiser / risk-model treatment — verified, no change required.**
> 5. **Lockbox protocol — approved, with the line drawn explicitly** (below).
> 6. **Freeze `C1_US_RULES_v1.0` — approved once the Dec-1973 regression passes.** Please add the
>    date convention and the 3999→0 recode to the spec text.
>
> **Lockbox, explicitly.** Allowed on 2021–2025: row counts, key uniqueness, dtypes, duplicate
> reconciliation, effective-date interval matching, checksums, and structural-break *flagging*. Not
> allowed: any universe or signal rule chosen or altered because of what those years look like, any
> model fit, any return / IC / Sharpe computation. **Practical rule: QA output may be counts and
> pass/fail flags, never anything conditioned on returns.** `LockboxError` enforces it until the
> team sets `ALPHACOMB_FREEZE_TAG`.
>
> **One change to your sequence.** Agreed on "don't download more data first" — and please fold the
> date-convention decision into that same gate. It is far cheaper to settle now than after the
> full-history pull.
>
> **One caveat to record rather than act on.** Because `factor_cols = beta + themes + industries`,
> `ind_0` is not only a constraint category — it becomes an *estimated risk factor*. By your own
> diagnosis that cohort is disproportionately small Nasdaq names appearing from Dec-1972, so its
> factor return is really a size/venue/listing-cohort effect wearing an industry label, with zero
> observations in 1971–72 and then a sudden appearance. It is computationally safe (least-norm
> `lstsq` when the column is all-zero, eigenvalue clipping on F). I still recommend keeping `ind_0`
> in both places, because the alternative — zero exposure on every `ind_` column — recreates exactly
> the silent omission you are worried about: the constraint would stop binding and the book could
> load the cohort freely. But we should call it *unclassified* rather than an industry in the paper,
> and run one robustness variant excluding the cohort. Not a reason to hold the pilot.
>
> **One flag on coverage.** 84.35% mean 1972 coverage means ~16% of signal values are missing in the
> start year, so the `miss_<theme>` flags carry real information and early-year theme composites rest
> on thinner data. Acceptable, but the paper should report coverage **by year** rather than a single
> average — a referee will ask.
>
> Green light on steps 1–8 of your section 7 as written, subject to the date convention going into
> the frozen spec.

---

## What changed on my side

| Change | Detail |
|---|---|
| Contract **v1.2.0** (merged, ratification requested) | `ff49` domain `{0} ∪ 1..49`; `date` must be calendar month-end |
| `tests/contracts/test_schemas.py` | New: `0` accepted, `-1/50/999/3999` rejected, non-month-end dates rejected, genuine codes 1/25/49 pass |
| Suite | contracts 26 (+9). synthetic 5, risk 6, models 52, portfolio 30, tax 37 all green after the change |

## Still open on my side, unrelated to C1

Four falsification-audit fixes (strict null first), the theory model's paper section, inference over
the TALS overhang results, `[verify]` on every tax rate, and a stale `docs/STATUS.md`.
