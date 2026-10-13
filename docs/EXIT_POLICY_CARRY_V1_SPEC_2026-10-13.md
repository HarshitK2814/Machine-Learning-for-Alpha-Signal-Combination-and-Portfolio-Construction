# Implementation specification: `exit_policy = "carry_v1"`

**Date:** 2026-10-13. **Status:** implemented on synthetic fixtures, **uncommitted, awaiting review**. No historical panel has
been run. Policy input: Absar Wani's written ruling of 2026-10-13 (`EXIT_POLICY_RULING_AND_001E_RESPONSE_2026-10-13.md`),
an interpretation of the frozen-sleeve and no-imputation principles. Implementation is researcher-led; Maham's review
is outstanding. Output of this code is a **revised analysis**, not a confirmatory one.

## 1. Isolation

* `TaxConfig.exit_policy` defaults to `"as_run"`. With it, `after_tax_backtest` returns frames identical to the
  pre-change code (`tests/tax/golden/as_run_exit_scenarios.parquet`, generated from the unmodified evaluator; compared
  with `check_exact=True`). Phase 1 and Phase 2 results are untouched.
* `carry_v1` is refused for synthetic bundles. Pipeline 06 gains `--exit-policy` and refuses `carry_v1` without an
  explicit `--out`, so it cannot share the Phase 1/2 summary path (the output-collision guard also fingerprints the flag).

## 2. Schema finding (exit evidence)

Inspected by schema and contract metadata only: `universe` (C1), `targets` (C4), `cost_inputs` (C6) and the promoted
`data/intl_c{1,4,6}/production/{DEU,IND,JPN}` tables carry **no delisting, terminal-event or exit-reason field**.
C4's contract says only that `ret_next` is "delisting-adjusted" and the data-request document asks that the delisting
convention be documented. A missing C6 row or disappearance from the scored cross-section is therefore **not** treated as
evidence. `exit_evidence` (columns `permno`, `event_date`, `kind` in {`delisting`, `mandatory_corporate_action_exit`},
optional `liquidation_cost_frac`) is the only route to a confirmed exit. For the promoted panels it is `None`, so
**every panel leaver is unresolved**.

## 3. F3 investigation (as_run)

Pinned in `tests/tax/test_exit_policy_as_run.py`:

* The terminal return reaches the lot only through the last priced month's `accrue_returns`. The lot is **never
  closed**: no realisation, no tax event, it stays in the ledger (counted in `unrealised` and in end-of-sample deferred
  tax, and rescaled by costs and tax).
* The name is excluded from the return calculation from the first absent month, so the code comment "closed by the
  delisting return" holds for the return, not for the position.
* If the name reappears, the stale lot is sold and a gain realised **late, at the stale value** (a second, mis-dated
  close). The same file pins F1 (alive-uncertified names sold to zero with a realised gain), F2 (that sale is not
  charged) and F4 (a missing `ret_next` on a held name is filled with 0).

## 4. Behaviour of `carry_v1`

| Case | Treatment |
|---|---|
| Alive, uncertified (C6 row, inputs not certified) | Target = current ledger dollars. No trade, no cost, no realisation, drifts with its return. A weights-file weight is ignored. A *new* position in such a name is not opened (`n_blocked_trades`). Traded again, at normal cost, when inputs are certified. Month stays resolved (valuation exists). |
| Held name with C6 row but missing `ret_next` | Stale. Lots and quantity kept, value held at last mark (excluded from `_rescale`), no dividends, no zero return, never traded again; every later month is `unresolved`. |
| Panel leaver, documented terminal event | Closed **once** at the lot value (which already contains the C4 terminal return); gain realised once; an evidence row cannot be consumed twice. Liquidation cost is **separate**: charged only if `liquidation_cost_frac` is supplied, otherwise `cost_status = "unsupported"`. |
| Panel leaver, no documented event | `unresolved`: lots retained, not valued, not closed, not rescaled. If the name reappears it is still not closed at a stale value. |
| Shorts | Carried shorts keep accruing the modelled borrow proxy and pay short dividends. `attrs["short_availability_evidence"]` records that the borrow fee is a modelled cost, **not** evidence of availability. |

## 5. Reporting implications (NAV and returns)

New columns (carry_v1 only): `valuation_status`, `cost_status`, `n_frozen`, `frozen_gross`, `n_stale`, `stale_gross`,
`n_exit_closed`, `n_exit_unresolved`, `unresolved_exit_gross`, `n_blocked_trades`, `cost_exit`, `gross_ret_diag`,
`net_ret_diag`, `after_tax_ret_diag`, `nav_diag`.

* Every month stays in the index. In a `valuation_status = unresolved` month `gross_ret`, `net_ret`, `after_tax_ret` are
  **NaN**. In a `cost_status = unsupported` month `net_ret` and `after_tax_ret` are NaN.
* `nav` is NaN from the first unresolved/unsupported month onward (compounding through an unknown cannot be claimed).
  `nav_diag` and the `*_diag` columns always exist; they are **resolved-only diagnostics**, excluding stale and
  unresolved positions, and are never full-portfolio performance.
* `summarise_after_tax` switches to the diagnostic columns when any month is unresolved and then stamps
  `basis = RESOLVED_ONLY_DIAGNOSTIC_NOT_FULL_PORTFOLIO_PERFORMANCE` with the unresolved-month count; otherwise
  `FULL_PORTFOLIO_ALL_MONTHS_RESOLVED`.
* End-of-sample deferred tax includes stale and unresolved lots at their last marks; `attrs["deferred_tax_includes_unresolved_lots"]` says so.
* **Expected consequence on the real panels:** because no terminal-event field exists, the first held name that leaves
  the panel makes that month and *all later months* unresolved (its lot is retained forever) and NAV null thereafter.
  With roughly 3.7 held names leaving per month on DEU, only the early months can be fully resolved. Phase C must therefore
  pre-specify how the revised 2009-2019 analysis is reported (full-portfolio only for resolved months; diagnostics, with
  `unresolved_exit_gross` and `stale_gross` shares, otherwise) before any result is seen. This change does not add such a rule.

## 6. Review corrections (2026-10-13, second pass)

| Item | Finding | Class |
|---|---|---|
| Stale name that then leaves | Would have been closed at its last mark when evidence exists. Now unresolved (the terminal return itself may be the missing value). | defect, fixed |
| Borrow on stale shorts | Accrued on an unverified notional while unresolved-exit shorts accrued none. Now neither accrues in the resolved-only diagnostic; `unresolved_short_gross` reports the notional. Borrow is a modelled proxy, never evidence of availability. | defect, fixed |
| s475(f) mark-to-market | Booked tax on stale and unresolved marks. Now skipped (`TaxLotLedger.mark_to_market(skip=)`). | defect, fixed |
| Missing `div_next` | C4 defines it as a non-negative fraction for every row (RET - RETX), so a missing value is missing information, not zero. `carry_v1` counts it (`n_div_missing`, `div_missing_gross`), sets `tax_status`, and by default (`dividend_missing="unsupported"`) makes that month's after-tax return NaN. `"flag_only"` keeps the zero-filled value but labels it `incomplete_flagged`. Gross and net returns are unaffected. `as_run` still zero-fills silently. | defect, fixed (default strict) |
| One leaver makes all later months unresolved; `nav` NaN thereafter | Deliberate: the lot is retained, so account NAV cannot be reconstructed. The share at stake is reported every month. | policy |
| Reappearance after a gap | Old lot stays unresolved and untraded; never closed at a stale value. | policy |
| Pipeline 06 | `carry_v1` now also refuses `--out` directly in `outputs/`, `--overwrite` and an existing path, and `--save-returns` writes beside the summary (parquet + attrs json), never into the mtime-resolved `outputs/returns/` tree or through the C12 contract. | defect, fixed |
| Total-loss (-100%) terminal return | `accrue_returns` dropped the emptied lot, so the loss was never realised and a later confirmed exit found nothing to close (verified by the new test failing first). `carry_v1` now clamps the ledger price return at -100% + 1e-9 so the lot survives and is closed once, with its basis, on the documented exit date; `gross_ret` still uses the true -100%. A second processing, or the name reappearing, realises nothing further. Without evidence the surviving lot is reported unresolved. | defect, fixed (carry_v1 only) |
| `as_run` compatibility | Working tree vs `HEAD` evaluator are bit-identical on the six exit fixtures (golden, `check_exact=True`) and on the 120-stock synthetic bundle (verified with `check_exact=True`; stored as `golden/as_run_synthetic_small_panel.parquet`, compared at rtol 1e-12). | verified |

## 7. Known limits (not fixed here)

* Under `as_run` a lot whose return is -100% is dropped by `accrue_returns` without a realised loss (pinned in
  `test_exit_policy_as_run.py`; not quantified, not changed).
* An evidence row dated *after* the first absent month cannot rescue a name already marked unresolved (conservative).
* A temporary gap in C6 (one missing month) makes the name unresolved permanently under `carry_v1`; a bridging return is
  never invented.
* Confirmed-exit liquidation uses the lot value after the terminal return; no price is invented for any other treatment.
