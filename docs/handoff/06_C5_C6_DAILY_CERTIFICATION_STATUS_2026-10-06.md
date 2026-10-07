# C5/C6 daily certification status — 6 October 2026

This is the current workstream-A handoff. It records working/staging artefacts
only. Nothing described here has been promoted to production or committed or
pushed to GitHub.

**Superseded for WRDS/Abdi-Ranaldo status on 7 October 2026:** see
`docs/handoff/08_C5_C6_RESUME_COMPLETION_2026-10-07.md`. The extraction is now
complete; this file is retained as the pre-resume audit state.

## Executive status

| Component | Status | Evidence |
|---|---|---|
| C1 synthetic `permno` to `(gvkey, iid)` | **PASS** | 13,110/13,110 mappings; zero conflicts |
| Investible-month `g_secd` coverage | **PASS** | 757,297/757,297 country-security-month keys |
| Daily return and traded-notional semantics | **PASS with explicit source gaps** | formula and units mechanically certified |
| C5 `MKTVOL` and `ILLIQ` working candidate | **PASS** | 1,116/1,116 country-month rows; mechanical preflight passed |
| C6 `sigma_d` and USD ADV mechanics | **PASS with explicit source gaps** | exact identity to certified daily staging panel |
| EDGE primary spread estimator | **PASS with sparse historical coverage** | authors' `bidask` 2.1.0 implementation; 85,420 strict estimates |
| Abdi–Ranaldo fallback | **CODE COMPLETE; EXTRACTION BLOCKED** | positive non-zero formula self-test passes; WRDS rejects stored credentials |
| Genuine `borrow_fee` | **BLOCKED / NULL** | visible short-volume and short-position tables are not lending-fee data |
| C6 → Workstream-B borrow integration | **HARD FAIL** | B silently converts missing fees to 0.0025; strengthened preflight now rejects this |
| C6 working candidate | **ASSEMBLED, FAIL-CLOSED, NOT READY FOR PRODUCTION** | exact 757,297-key nullable panel |

## C5 result

The daily market-state builder produced:

- `data/intl_c5/candidate_daily_market_working/C5_DAILY_MARKET_WORKING_CANDIDATE.csv`
- `data/intl_c5/candidate_daily_market_working/C5_FULL_WORKING_CANDIDATE.csv`
- `data/intl_c5/candidate_daily_market_working/C5_DAILY_MARKET_WORKING_AUDIT.json`

The result has 372 months for each of DEU, IND, and JPN. `MKTVOL` is the
one-month-lagged expanding-standardised log 21-day country-market volatility.
`ILLIQ` is the one-month-lagged expanding-standardised, detrended,
USD-market-cap-weighted 21-day Amihud state. Both use prior-month frozen daily
membership. Mechanical reconstruction confirmed both one-month lag identities,
month-end timing, unique keys, state bounds, pre-activation neutral values, and
that the merge did not alter any existing external C5 state.

Activation dates are:

| Country | `MKTVOL` | `ILLIQ` | Minimum post-activation ILLIQ market-cap coverage |
|---|---:|---:|---:|
| DEU | 1992-03-31 | 1996-10-31 | 86.00% |
| IND | 1992-03-31 | 2000-03-31 | 90.98% |
| JPN | 1992-03-31 | 1995-08-31 | 96.99% |

## C6 working candidate

The non-production candidate is:

`data/intl_c6/candidate_working/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz`

Its contract columns are `date, permno, spread, sigma_d, adv_usd, borrow_fee`,
with country and audit/source fields retained alongside them. It contains all
757,297 investible rows and 7,296 ever-investible securities. The current
spread is EDGE-only until the fallback extraction finishes; `borrow_fee` is
null for every row.

| Country | Rows | EDGE spread | `sigma_d` | USD ADV | Complete current market inputs |
|---|---:|---:|---:|---:|---:|
| DEU | 122,784 | 9,585 | 119,162 | 67,911 | 7,026 |
| IND | 71,646 | 9,715 | 71,506 | 65,214 | 9,711 |
| JPN | 562,867 | 66,120 | 561,488 | 490,339 | 66,118 |
| **Total** | **757,297** | **85,420** | **752,156** | **623,464** | **82,855** |

The strengthened independent preflight verdict is now
`FAIL_MECHANICAL_PREFLIGHT`: C5 remains `PASS`, while C6 is deliberately `FAIL`
because its all-null certified borrow fee would be silently converted to 0.0025
by the current Workstream-B consumer. Before that hard integration check, the
market-data checks confirmed exact keys,
the EDGE source hierarchy, non-negative market inputs, exact `sigma_d` identity,
USD ADV identity within CSV round-trip precision, endpoint no-look-ahead, and
the all-null borrow-fee policy.

Economic QA retained four DEU observations with `sigma_d >= 1` for bounded raw
corporate-action review. All four currently have missing ADV and spread, so
none enters the set of complete C6 market-input rows. They were not clipped,
deleted, or backfilled. Evidence is in:

- `data/intl_c6/audit/C6_DAILY_ECONOMIC_OUTLIERS.csv`
- `probe_c6_wrds_sigma_outliers.py`

## Abdi–Ranaldo fallback

`extract_c6_wrds_abdi_ranaldo.py` implements the pre-specified monthly-corrected
estimator:

`eta_t = (log(H_t) + log(L_t)) / 2`

`gamma_t = (c_(t-1) - eta_(t-1)) * (c_(t-1) - eta_t)`

`spread = 2 * sqrt(max(mean(gamma), 0))`

The strict estimate uses 20 adjacent-pair moments from 21 actual-price
observations, adjusted H/L/C, and resets at currency changes. The SQL is
exact-key, annual, server-side, and downloads only one endpoint row per requested
security-month. It never downloads the full `g_secd` table. Its local self-test
uses a positive estimate and matches an independent explicit expression exactly.

The extraction cannot currently start because WRDS returns
`PAM authentication failed`. The standard `%APPDATA%\postgresql\pgpass.conf`
file is discovered, but its stored authentication is not accepted.

### Local coverage projection while WRDS is unavailable

The certified observation counts provide a conservative, value-free lower
bound for the pending fallback. Requiring 21 raw observations, 21 certified
same-currency returns, and 21 complete high/low observations identifies 651,000
strict AR-eligible rows. Because three existing EDGE estimates fall just
outside that deliberately conservative rule, projected combined spread
availability is at least 651,003/757,297 rows (85.96%). This is expected to add
at least 565,583 rows beyond the 85,420 strict EDGE estimates and raise complete
`spread + sigma_d + adv_usd` market inputs from 82,855 to at least 611,580 rows.

This projection does not create or impute any spread value. The actual
server-side extraction remains mandatory. Evidence:

- `data/intl_c6/audit/C6_PROJECTED_AR_COVERAGE_AUDIT.json`
- `data/intl_c6/audit/C6_PROJECTED_AR_COVERAGE_BY_COUNTRY_YEAR.csv`

## Borrow-fee decision

The entitlement/schema probe saw 266 accessible WRDS libraries. The only
plausible visible candidates were short-sale trading volume and disclosed
European short-position tables. Neither has a lending fee, cost-to-borrow, or
rebate-rate field, and neither is an admissible proxy. The explicit audit is:

`data/intl_c6/audit/C6_BORROW_FEE_SOURCE_AUDIT.json`

The policy remains: retain `borrow_fee = null`; never use zero, short volume, or
reported short positions as a substitute.

### Frozen-consumer compatibility gate

A read-only interface audit found that the frozen C6 schema requires all four
cost inputs to be non-null, while the current Workstream-B consumer fills a
missing `borrow_fee` with `0.0025` (25 basis points annual). That substitution
is not certified lending-fee data and is not approved by the current policy.
The preflight now implements this as
`borrow_fee_consumer_integration_hard_gate = FAIL`, and the standalone audit
returns `FAIL_HARD_BORROW_FEE_INTEGRATION`. Therefore the working candidate must not be handed to the consumer even after
spread extraction until genuine borrow-fee data are obtained or an explicit,
preregistered fallback is approved. Workstream B was not modified. Evidence:

`data/intl_c6/audit/C6_CONSUMER_COMPATIBILITY_AUDIT.json`

## Exact resume sequence after WRDS credentials are refreshed

The workflow was invoked again on 6 October 2026. The interactive retry accepted
the discovered username, then stopped before extraction at the password prompt;
no password was entered or logged. Restored account/Duo access has therefore not
been demonstrated, and no candidate or downstream audit was changed. The attempt is recorded in
`data/intl_c6/audit/C5_C6_RESUME_ATTEMPT_2026-10-06.json`.

Run from the repository root:

```powershell
.\.venv_wrds\Scripts\python.exe resume_c5_c6_after_wrds.py
```

The resume workflow runs the AR extraction, bounded sigma-outlier query, C6
rebuild, complete preflight, fallback-coverage audit, and consumer-compatibility
audit in sequence. The AR extractor is annual and cache-aware. After it completes, the C6 builder
automatically applies strict EDGE first, strict Abdi–Ranaldo second, and null
otherwise. Production promotion remains prohibited until the refreshed
preflight passes and a genuine borrow-fee source or an approved research-design
decision resolves the contractual blocker.

## Audit index

- `data/intl_c6/audit/C1_WRDS_CROSSWALK_AUDIT.json`
- `data/intl_c6/audit/C1_WRDS_ALL_SECURITY_DAILY_COVERAGE_AUDIT.json`
- `data/intl_c6/audit/C6_DAILY_SEMANTICS_CERTIFICATION.json`
- `data/intl_c6/audit/C6_WRDS_EDGE_21_AUDIT.json`
- `data/intl_c6/audit/C5_C6_DAILY_PREFLIGHT.json`
- `data/intl_c6/audit/C5_C6_DAILY_PREFLIGHT_CHECKS.csv`
- `data/intl_c6/audit/C6_BORROW_FEE_SOURCE_AUDIT.json`
- `data/intl_c6/audit/C6_PROJECTED_AR_COVERAGE_AUDIT.json`
- `data/intl_c6/audit/C6_CONSUMER_COMPATIBILITY_AUDIT.json`
- `data/intl_c6/audit/C5_C6_RESUME_ATTEMPT_2026-10-06.json`
- `data/intl_c6/candidate_working/C6_COST_INPUTS_WORKING_AUDIT.json`

The only permitted human-resolution paths for missing borrow fees are listed in
`data/intl_c14/audit/C14_C6_HUMAN_DECISION_SHEET_2026-10-06.md`; the legacy
implicit 25 bp fill and zero-fill remain prohibited.
