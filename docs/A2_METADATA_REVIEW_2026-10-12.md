# A2 candidate (2021-2025): metadata review

**Date:** 2026-10-12. **Scope:** schemas, field classification and non-outcome quality fields only. **Sealed:** every realised
return, return-derived statistic and performance summary. Nothing was integrated into the research repo; the data sits in a
staging directory outside it. Hash validation (17 of 17) was reported separately on 11 October.

## 1. Field classification (decided from schemas before any QA file was read)

| Class | Fields | Handling |
|---|---|---|
| **Keys and identity** | `date`, `permno`, `id`, `gvkey`, `iid`, `eom`, `identity_source`, `known_frozen_key`, `country` | readable |
| **Universe and eligibility (non-outcome)** | `in_universe`, `exchcd`, `ff49`, `nyse_size_pct`, lineage flags (`history_ok`, `price_ok`, `me_ok`, `size_ok`, `stale_gt5`, `inactive_by_weight`, `present_jkp_core`, `base_in_universe`), `dldtei`, `market_last_date`, `days_before_market_close` | readable as counts and flags |
| **Market levels** | `me`, `price`, `prc`, `price_contract`, `me_contract`, FX fields (`reference_fx`, `usd_per_local`) | **not read**: price levels across months reconstruct returns |
| **Predictors, return-derived** | 153 `sig_*` columns of C2 (several are momentum, reversal, volatility or skew built from returns) | **values not read**; only the `miss_*` indicators and missingness aggregates are used |
| **Missingness indicators** | `miss_*` (int8), QA missingness CSVs | readable |
| **Outcomes: SEALED** | C4 `r_1m`, `r_3m`, `r_6m`, `r_12m`, `ret_next`, `div_next`; the daily outcome-tail records | **not read** (only non-missing counts per year from QA) |
| **Cost inputs, return-derived** | C6 `spread` (high-low / close-high-low estimators), `sigma_d` (realised volatility), `adv_usd` (traded value), `edge_21_strict`, `ar_21_strict`, `return_obs_21`, `volume_obs_21` | **values not read**; coverage and completeness counts only |
| **Certified-null fields** | C6 `borrow_fee`, `borrow_fee_source`, `shortability_status` | readable (all constant) |
| **Macro and source metadata** | C5 audit and Japan TERM overlap CSV | readable (rate series, not stock outcomes) |
| **Manifests and provenance** | all `audit/*.json` | readable |

Two QA fields touch returns and were **not used**: `max_r1_identity_error` (a return-identity check, reported as 0.0 by
the builder) and `material_negative_dividend_rows` (a count). They are noted, not analysed.

## 2. Findings

**Integrity.** 17 of 17 manifest hashes match; row counts 620,347 (C1, C2, C4), 201,107 investible, 194,578 complete C6
rows; 153 signals, 13 themes; month ends 2021-01-31 to 2025-12-31 for all three countries; `borrow_fee` non-null in 0
rows; shortability `UNKNOWN_FAIL_CLOSED` in all rows. Historical rows modified at the 2020/2021 boundary: 0 in all
three countries.

**Coverage and universe.**

| | Germany | India | Japan |
|---|---|---|---|
| C1 rows / investible | 51,608 / 21,407 | 316,285 / 39,341 | 252,454 / 140,359 |
| Complete C6 market inputs, share of investible rows | 69-71% by year | 99.7-100% | 99.7-100% |
| Rows from a name off the JKP core | 7,364 | 51,849 | 14,594 |
| New identity keys | 259 | 1,484 | 648 |

The Germany coverage asymmetry of 2009-2019 persists (about 70% against 99.7-100%). India's investible set is about
12% of its rows and averages about 500-550 names a month in 2021-2022 and 620-820 from 2023, so the 600-name cap
binds from 2023; Japan's (about 2,300-2,500 a month) exceeds it throughout; Germany's (about 330-390) never does.

**C2 signal missingness (in-universe).** Japan: 9 quarterly-earnings signals are 98.4-98.9% missing, `ivol_hxz4_21d` and
`iskew_hxz4_21d` are 100% missing, and 11 of 153 signals exceed 50% missing; whole-theme completeness is near zero for
investment, profitability, quality and profit growth (about 1%) and zero for low-risk and short-term reversal. Germany has
6 signals above 50% missing and no fully missing signal; India has 9 and none fully missing. Whether Japan's pattern also
held in 2009-2019 has not been compared.

**C4 coverage (counts only).** `r_12m` is complete for most formation months but falls in 2025 (for example Germany
5,386 of 8,669 `ret_next` rows; India 32,846 of 59,442; Japan 30,768 of 47,540), consistent with the stated right-censoring.
The latest formation month with any 12-month value is 2025-08 (Germany, Japan) and 2025-07 (India).

**Point-in-time lineage audit.** C1: no future market date (PASS). C2/C3: dated provider rows retained; the accounting
vintage is "conditional, not independently certified". C4: right-censored nulls; the risk-free and Compustat return
indexes are a current download and "may revise". C6: endpoint not after month end (PASS), strict windows (PASS), Phase 1
pilot parity 19 of 19 overlapping rows match on every audited flag.

**C5 source decisions.** Japan TERM and India CREDIT are blocked source decisions; the other states continue with
recheck conditions. See amendment 001E, section 4, for the explicit resolution and defaults.

## 3. What was not reviewed

The values of any sealed field; the C14 source-gap record beyond its status (after-tax OOS remains prohibited); the
Phase 1 pilot extract (restricted); Absar's test run (314 of 314, reported, not re-run); the 43 frozen production hashes
(reported by the data owner, not independently re-verified here).
