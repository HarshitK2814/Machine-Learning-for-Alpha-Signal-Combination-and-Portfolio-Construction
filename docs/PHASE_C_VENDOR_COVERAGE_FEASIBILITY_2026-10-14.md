# Phase C vendor coverage feasibility (2026-10-14): can the vendor source supply genuine month-end observations for the held-name gap months?

**Conclusion: `unknown`. The data contract and the evidence on disk do not establish that genuine month-end observations exist for the gap months, so the monthly-account-path question cannot be answered yes.** What the evidence does support is narrower: vendor daily rows exist for nearly every relevant security, a documented `carry-forward` status is separable from observed prices at row level, and an **endpoint valuation at best** would be conceivable, never the account path. Nothing was run: no Phase C panel, performance figure, training, A2, cost sensitivity or revised strategy evaluation. No exit rule, estimability threshold or gap population was changed. Internal researcher-led work; Maham's acknowledgement has not been received and is not claimed.

Decision proposed for review (section 7): do not integrate the vendor source; treat the gap series as not estimable unless the owners authorise a month-level flag query by someone with vendor access, or rule on liquidation at a certified cost instead.

## 1. What was and was not possible

* **Not possible here:** a month-level count. The staging files (crosswalk, certified daily panel, investible-month ledger) are not on disk, there is no `wrds` package or credential in this environment, and the repository holds the vendor data only as per-security aggregate audits. I did not attempt any external query.
* **Done:** (a) read the vendor documentation and schema records committed in the repository; (b) counted, by country, the gap population against the committed per-security vendor aggregates (counts and dates only).

## 2. Field documentation (what the repository records, not assumed)

| Field | Documented meaning (`WRDS_C6_DATA_DICTIONARY.json`) | Observation semantics documented? |
|---|---|---|
| `prccd` | "Price Close - Daily", adjusted by `ajexdi` with operator `/` | **No.** `itemdef` is null; nothing states whether a close on a non-trading day is an observation |
| `ajexdi` | "Adjustment Factor (Issue) - Cumulative by Ex-Date - Daily" | **No** definition beyond the label; corporate-action content is implied, not documented |
| `trfd` | "Daily Total Return Factor" | **No** definition of what distributions it includes; the probe lists it as an adjustment column of a separate carry-forward table (`carryfwd`, `trfd`, `datadate`, `thrudate`), whose semantics are not documented here |
| status | `prcstd` is the daily price-status code. The build audit (`C6_WRDS_MONTHLY_DAILY_FEATURES_AUDIT.json`) records the rule "`prcstd` in (3, 4, 10); status 5 carry-forward rows excluded per `comp_global_daily.r_prc_stat`" | **Partly.** The repository records the build's interpretation; the vendor reference table `r_prc_stat` itself is only named, not stored |

Every item definition field (`itemunit`, `itemdef`, `itemdefurl`) is null in the stored dictionary. The only evidence that status 5 means carry-forward is the build's own rule and the `carry_forward_status_rows` column of the coverage audit; the price statuses seen across the 13,108 securities are `10` and `10|5` only, so the repository does not show what statuses 3 and 4 look like.

## 3. Aggregate counts (`results/phase_c_vendor_coverage_2026-10-14/vendor_coverage_aggregate.json`)

The gap population is the one defined in the earlier feasibility report (consecutive C4 months with a row present and `ret_next` unusable, 2009-01 to 2019-12, unchanged). Vendor counts come from `C1_WRDS_ALL_SECURITY_DAILY_COVERAGE.csv`, **one row per security over the queried interval; there is no month-level status in it.**

| Count | DEU | IND | JPN |
|---|---|---|---|
| Gap runs | 1,792 | 7,932 | 1,623 |
| Gap months (sum of run lengths) | 7,875 | 67,213 | 17,279 |
| Securities with at least one gap run | 877 | 2,724 | 1,524 |
| ... with any vendor daily row | 876 | 2,724 | 1,524 |
| ... with any carry-forward-status row (anywhere in the interval) | 871 | 2,713 | 1,481 |
| Gap runs whose security's vendor first-to-last date range spans the run (dates only) | 1,691 | 7,289 | 952 |
| Gap runs with no vendor daily row for the security | 1 | 0 | 0 |
| Vendor daily rows, all securities | 5,465,450 | 13,907,182 | 24,447,511 |
| ... status classified actual price | 4,566,602 (83.6%) | 10,353,861 (74.4%) | 23,181,135 (94.8%) |
| ... status classified carry-forward | 898,152 (16.4%) | 3,552,057 (25.5%) | 1,261,090 (5.2%) |
| ... neither status | 696 | 1,264 | 5,286 |

Requested categories, for the **gap months**:

| Category | Gap-month count by country |
|---|---|
| Genuinely observed month-end price | **unknown** (not derivable: row counts are per security, not per month or month-end) |
| Carried forward / non-observed price | **unknown** for gap months; carry-forward rows are 5% to 26% of all vendor rows, and 97-100% of gap securities have some, so it is not rare |
| Unknown observation status | all 7,875 / 67,213 / 17,279 gap months |
| Documented total-return / dividend coverage | **not documented** (`trfd` has only a label; `div_next` is unusable in every gap run, see the earlier report) |
| Documented corporate-action / terminal-event coverage | **not documented**: `ajexdi` has a label only; the schema probe lists columns such as `split`, `secstat`, `monthend` without semantics or counts; no terminal-event field exists in C1, C4 or C6 |

The "date range spans the run" row is a necessary condition only. It says the security has vendor rows both before and after the run; it does not say any month inside the run has an actual-price row (and the vendor date range can include carry-forward rows). It also means 5.6% / 8.1% / 41.3% of runs (DEU / IND / JPN: 101 / 643 / 671) are **not** even spanned by the vendor date range for their security. For JPN this is an informative limit on its own.

High security coverage (13,108 of 13,110 securities, 3,946 of 3,947 dead names) is **not** read as evidence of monthly coverage.

## 4. What the vendor data could support

| Level | Supported? | Reason |
|---|---|---|
| Complete monthly account path (NAV, trades, costs, tax accrual each month) | **No, not on the present evidence** | needs a genuine mark for every held name every month. Month-level status is unknown; a carry-forward price is not a mark; carry-forward is common |
| Endpoint valuation of a position at an observed endpoint | **Potentially**, only if both endpoints are genuine observations and `trfd`/`ajexdi` semantics are documented | the index identity is certified for the C4 investible months only (`C6_DAILY_SEMANTICS_CERTIFICATION.json`), which excludes these out-of-universe months |
| Neither | applies in the interim | |

**Components that remain unsupported even in the best case:** intermediate NAV (only the cumulative position value at the endpoint is observed, so account equity at intermediate months is unobserved); transaction dollars (weights are fractions of NAV); transaction costs (need the certified cost inputs, which the out-of-universe months lack); and tax accrual (lot-level dividend and gain accrual cannot be formed without monthly dividends, and `div_next` is unusable throughout every gap run). The vendor source was certified for C4-endpoint consistency and traded-share semantics on investible months, not for held-but-untradeable months.

## 5. Source limitations

1. Dictionary definitions are empty; status semantics rest on a build-time rule; `r_prc_stat` is not stored.
2. The coverage audit is security-level over bounded C1 intervals; the endpoint-FX gaps (1,004 rows, 15 dates) and current-vintage revisions (269 rows, 7 securities) show the vendor series is not frozen.
3. The raw SAS file and every staging file are missing from this tree, so audits cannot be re-verified; hashes in the audit JSON are recorded but not checkable.
4. The count of 876 / 2,724 / 1,524 securities with vendor rows is a security-level fact, nothing more.
5. Vendor "other" status rows (696 / 1,264 / 5,286) are unclassified and unexplained.

## 6. Fields accessed, tests run, slips

* **Accessed:** vendor documentation JSONs and the audit CSV count/date columns (`country, permno, daily_rows, actual_price_status_rows, carry_forward_status_rows, first_daily_date, last_daily_date`; `permno` as an in-memory join key, never written); C4 `date, permno` and `ret_next` as an `isfinite` flag. Not read or written: any price, return, dividend, factor, FX, cost, tax, NAV or performance value. No row preview was printed and no security identifier appears in any output. The coverage CSV also contains `gvkey, iid` and currency columns and a price-status text column; the status text was inspected only as two distinct labels (`10`, `10|5`) with their counts.
* **Slip disclosure (inherited):** the earlier-reported `head -c 400` display of the revisions CSV stands as disclosed; no additional value display occurred in this step. I also displayed the committed coverage audit JSON in full; its two no-daily example rows carry identifiers (country, permno, gvkey, iid, C1 months) but no price, return or other value, and none is repeated here.
* **Tests run:** `tests/tools/test_phase_c_vendor_coverage_aggregate.py` (2 synthetic tests: counts, date-range span, absent security, no identifier or value in the output). The broader tools and documentation-hygiene tests and the withdrawn-claims screen are recorded in the commit step. The full suite was **not** rerun in this step; the last full run was 667 passed at `b7b26b8`, before the 4 + 2 later tests.

## 7. Proposed decision (for review; nothing taken)

1. **Do not integrate the vendor source on this evidence.** Status: `unknown` for month-end observation, `not documented` for total-return and corporate-action semantics.
2. **If recovery is still wanted,** the next step is a month-level flag query run by someone with vendor access, for gap months only, returning counts of rows by (`prcstd` class, month-end flag) with no values, together with the vendor's own `prcstd` and `trfd` definitions stored in the repository. If the observed share of gap months is not essentially complete, the answer is `not feasible` for the monthly path.
3. **Alternatively,** the owners may rule on liquidation of a name that leaves the universe at a stated certified cost, which is a different ruling from the one recorded and needs its own addendum.
4. The 560 series remain not estimable under the recorded rules. Maham's acknowledgement is outstanding and is not claimed.
