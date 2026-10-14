# Phase C recovery feasibility (2026-10-14): can a missing `ret_next` on a held-but-untradeable name be bridged?

**Answer: No supported bridge exists with the data now in the repository (case 3). A bridge is technically possible only with a new source and explicit accounting assumptions (case 2), and even then it would restore the position's end value, not the intermediate account states.** Nothing was run: no historical panel, performance figure, A2 evaluation, training or cost sensitivity. Preserved: all committed results, the 5% / 25% thresholds, the lockbox. Internal researcher-led work; no external review or approval is claimed.

## 1. Governing decisions applied

1. A C1 exit or loss of C6 certification does not imply liquidation. 2. A missing `ret_next` makes the affected account return unresolved. 3. Unresolved status propagates while NAV or holdings cannot be reconstructed reliably. 4. Recovery is permitted only if authoritative data allow position value and account state to be rebuilt without zero-return imputation, unsupported prices or outcome-driven choices. 5. A later valid `ret_next` alone does not prove the intervening state is recoverable. 6. A missing C4 row stays unresolved without documented terminal-event evidence. 7. Thresholds unchanged.

## 2. Evidence (metadata, schemas, audit records, presence flags)

| Source | What it establishes |
|---|---|
| `src/alphacomb/contracts/schemas.py` (C1, C4) | C4 `ret_next`: "delisting-adjusted" forward return, nullable; `div_next`: optional, non-negative, nullable; C1 `price` and `me`: nullable floats with no stated adjustment convention |
| `docs/EXIT_POLICY_CARRY_V1_SPEC_2026-10-13.md` | no delisting, terminal-event or exit-reason field exists in C1, C4 or C6; a held name with missing `ret_next` is stale and every later month unresolved |
| `data/intl_c6/audit/C4_DAILY_ENDPOINT_BENCHMARK_AUDIT.json` | C4 was built from a raw file `data/intl_c4/raw/intl_c4_real_base_1990_2020.sas7bdat`; a daily benchmark satisfies `daily_adj_price * daily_trfd = daily_ri_local`; the benchmark covers only **investible** months (757,297 rows against 2,283,562 raw rows) |
| `data/intl_c6/audit/C6_DAILY_SEMANTICS_CERTIFICATION.json` | return-index semantics: `(prccd / ajexdi) * trfd`, daily total return = index ratio within security and currency; staging only, "no production promotion"; vendor current-vintage revisions exist and "frozen C4 is not modified" |
| `data/intl_c6/audit/C1_WRDS_ALL_SECURITY_DAILY_COVERAGE_AUDIT.json` | vendor daily data exist for 13,108 of 13,110 C1 securities, including 3,946 of 3,947 historical or dead names; per-security `actual_price_status_rows` and `carry_forward_status_rows` show the vendor can carry prices forward |
| `data/intl_c6/audit/C6_CERTIFIED_MONTHLY_DAILY_FEATURES_AUDIT.json` | the certified daily-feature panel is built for the investible-month ledger only; endpoint FX gaps are documented |
| Repository search | the raw SAS file and every `data/intl_c6/staging/*` file named in those audits are **not on disk** (repo, `drive_pull`, backups); only audits and manifests remain |
| Census v3 (`results/phase_c_census_v3_2026-10-14`) | unusable `ret_next` is 8-24% of out-of-universe C4 rows and about 0-0.4% of in-universe rows |
| New presence check (`results/phase_c_recovery_feasibility_2026-10-14/gap_runs_summary.csv`) | below |

Presence check (`tools/phase_c_recovery_presence_check.py`, 4 synthetic tests). A *gap run* is consecutive C4 months with a row present and `ret_next` unusable, 2009-01 to 2019-12.

| | DEU | IND | JPN |
|---|---|---|---|
| Gap runs | 1,792 | 7,932 | 1,623 |
| Runs that later reach a usable `ret_next` | 1,061 | 6,894 | 666 |
| Runs with no later usable return (next C4 row absent) | 731 | 1,038 | 957 |
| Runs of 1 / 2-3 / 4-12 / >12 months | 528 / 809 / 324 / 131 | 462 / 3,760 / 2,426 / 1,284 | 856 / 128 / 61 / 578 |
| Runs entirely outside the C1 universe | 1,790 | 7,932 | 1,620 |
| Runs with `div_next` unusable in **every** month | 1,792 (all) | 7,932 (all) | 1,623 (all) |
| Recovering runs with C1 `price` present at **every** run month | 0 | 1 | 0 |
| Recovering runs with C1 `price` present at the recovery month | 1,042 | 6,883 | 665 |

## 3. Classification

**Case 3: no supported bridge with available data.** Reasons, each from the evidence above:

* **Return levels are not stored.** Production C4 holds returns, not index levels, so a later valid `ret_next` starts a new interval; it cannot be chained across the gap (decision 5).
* **Price levels do not cover the gaps.** C1 `price` is missing in at least one month of essentially every recovering run (0 of 1,061, 1 of 6,894, 0 of 666 have it at all run months), and its adjustment convention is not documented in the contract.
* **Dividends are unavailable throughout every run**, because `div_next` is unusable together with `ret_next`. A price ratio would be a price return, which omits distributions during the gap.
* **Corporate actions are not recorded** in any production table (no split or adjustment factors).
* **Terminal events** are not recorded; the 731 / 1,038 / 957 runs with no later C4 row stay unresolved under decision 6.

**Case 2: possible only with a new source.** The vendor daily data (`prccd`, `ajexdi`, `trfd`; certified formula above) cover almost all C1 keys including dead names. A bridge from them is a new source integration and an explicit accounting assumption. It is **not** performed or proposed for adoption here.

### Mathematics, and what a case-2 bridge could and could not restore

For a held name with vendor index levels `RI(e)` at actual-price endpoints `e`, the cumulative total return over a gap from endpoint `a` to `b` is `R(a,b) = RI(b) / RI(a) - 1`, with `RI = (prccd / ajexdi) * trfd`, both endpoints on actual (not carried-forward) price status, in one currency. Temporal alignment would need the same endpoint rule as C4 (endpoint not after month end) and the FX treatment already used in C6.

* **Restored:** the position's value at `b`. Dividends and splits sit inside `RI`; no zero imputation, no price invented.
* **Not restored:** the monthly returns inside `(a, b)`, because only the cumulative is observed (unless an actual-price month-end observation exists for each intermediate month; that would also have produced a C4 `ret_next`, so its absence suggests none exists, which is unverified). Account equity at intermediate months therefore stays unobserved, and with it the dollars traded and costs of the other positions (weights are fractions of NAV), the drifted weights and any tax accrual on the lots. The bridge reconstructs the endpoint value, **not the actual portfolio-state path**: it approximates the monthly account path unless every intermediate month has an actual mark.
* **Hazards to document before any use:** carry-forward price status (not a mark); current-vintage vendor revisions versus frozen C4; entirely out-of-universe gaps where C6 and the certified daily panel have no rows; dead securities whose last actual price precedes the gap end (the open runs).

## 4. Synthetic tests

None of the six candidate-bridge tests requested was written (missing return with later valid mark; unrecoverable price gap; dividend or corporate action missing during the gap; equity and tax lots preserved across a recovery; no duplicate liquidation or stale-lot disposal; reproducibility and failure without evidence), because no bridge is supported by the data contract and writing them would test an assumed rule. The existing behaviour that a stale name is never closed at its old value and never zero-filled is covered by the `carry_v1` tests. The presence tool has 4 tests. If a case-2 source is later approved, the six tests above are the required list, with the source's evidence-unavailable case as the failing path.

## 5. Fields accessed, and a disclosed slip

Accessed for the check: C4 `date, permno, ret_next, div_next` as `isfinite` flags; C1 `date, permno, in_universe, price` as a `notna` flag; values discarded at load; nothing numeric stored. Metadata: schemas, audit JSON and CSV headers, counts.

**Slip:** while listing a header I ran `head -c 400` on `data/intl_c6/audit/C6_RETURN_INDEX_CURRENT_VINTAGE_REVISIONS.csv`, which displayed two data rows (one DEU security, month-end 2013-05: adjusted price, return-index and factor values). It is a committed audit file, not a held-position outcome, and nothing was derived from or recorded about those values. It is reported because the task said to stop before reading numerical values. I also saw a few identifier rows in the endpoint-FX-gap examples (keys, no returns).

## 6. Limitations

The presence check covers C4 and C1 only; it cannot say whether the vendor holds month-end actual prices for the gap months. Runs are counted by position, not interpreted as delistings or suspensions. The staging files cited by the audits are unavailable here, so their contents and hashes were not re-verified.

## 7. Recommended next step (for review; nothing taken)

1. Do **not** build a bridge on current data. Treat the 560 series as not estimable under decisions 1-7: a data-adequacy finding about C4 for out-of-universe holdings.
2. If the owners want recovery pursued, request separate authorisation for a **flag-level** vendor query (aggregates only): for the gap months of held names, whether an actual-price month-end observation exists, by price status, with no price, return or factor value. If most gap months have no actual mark, case 2 collapses to case 3 for the monthly path.
3. Separately, the owners may decide whether holdings that leave the universe should instead be liquidated at a certified cost (a different ruling from the one recorded).
4. Maham's acknowledgement of the exit ruling remains outstanding and is not claimed.
