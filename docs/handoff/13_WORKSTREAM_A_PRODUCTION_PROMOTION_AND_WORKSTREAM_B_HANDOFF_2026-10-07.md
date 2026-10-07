# Workstream-A production promotion and Workstream-B handoff — 7 October 2026

## Final status

```ini
WORKSTREAM_A_PRODUCTION_PROMOTION = PASS
WORKSTREAM_A_SEMANTIC_PREFLIGHT = PASS
POST_PROMOTION_VALIDATION = 14/14 PASS
FULL_REPOSITORY_TESTS = 290/290 PASS
HUMAN_DECISIONS = 6/6 FROZEN
REAL_RESULTS_INSPECTED = NO
GITHUB_COMMIT_OR_PUSH = NO
```

The sole promotion authority is
`data/workstream_a_closeout/FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json`
(SHA-256 `9fe4d029e1acf86ce7d41c65cbc1e8fa2a9f35296a2c1c8685b492ea3b2dab28`).
It authorizes two new data copies and 16 code/configuration/test files already
located at their intended integration paths. No unlisted data transformation or
`data/real` bundle materialization was performed.

## Promoted and frozen inputs

| Contract | Authoritative handoff location | Promotion treatment |
|---|---|---|
| C1 | `data/intl_c1/production/{DEU,IND,JPN}/universe.parquet` | Frozen in place; unchanged |
| C2 | `data/intl_c2/production/{DEU,IND,JPN}/signals.parquet` | Frozen in place; unchanged |
| C3 | `data/intl_c2/production/signal_meta.csv` | Frozen in place; unchanged |
| C4 | `data/intl_c4/production/{DEU,IND,JPN}/targets.parquet` | Frozen in place; unchanged |
| C5 | `data/intl_c5/candidate_final_working/{DEU,IND,JPN}/states.parquet` | Manifest does not authorize another copy; frozen and handed off in place |
| C6 | `data/intl_c6/production/C6_COST_INPUTS_WORKING_CANDIDATE.csv.gz` | Exact byte-for-byte promoted copy |
| C14 | `data/intl_c14/production/c14_regime_candidate_source_frozen.csv` | Exact byte-for-byte promoted copy |

The exact hashes and sizes of all 20 unchanged C1–C5 files are in
`data/workstream_a_closeout/WORKSTREAM_A_PRE_PROMOTION_BASELINE_2026-10-07.json`.
The promoted hashes are:

- C6: `bb296e488327b822281940ff2669ce7a46fe7a60e5d8b79f3f7c5548d758fa4c`
- C14: `992a491c3f387d8f68ed253d0258d948ccbf4b722ede37e2dedbaf6e974f775a`

The post-promotion operation ledger, including source/destination hashes for
both copies and the 16 in-place integration hashes, is
`data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_MANIFEST_2026-10-07.json`.

## Workstream-B integration requirements

1. Preserve C1 as the security-month spine. C2 and C4 have exact one-to-one C1
   keys. Join C5 by country and month, and C6 by `date, permno`.
2. Do not impute C6 market fields. A security-month is trade-eligible only when
   `spread` and `sigma_d` are finite/non-negative and `adv_usd` is finite and
   strictly positive. Missing fields remain non-tradeable.
3. Apply the same cost equations in optimization and realized C12 accounting:

   ```text
   trade cost_i = (0.5 * spread_i + commission_bps / 10000) * |Δw_i|
                + impact_k * sigma_d_i * sqrt(AUM_USD / ADV_USD_i) * |Δw_i|^1.5
   monthly borrow_i = annual_borrow_fee_i / 12 * max(-w_i, 0)
   ```

   Keep AUM and ADV in USD. The configured commission is 1 bp and
   `impact_k = 1.0`. Use the shared cost functions in
   `src/alphacomb/portfolio/cost_terms.py`; do not reimplement them in a
   separate baseline path.
4. Certified C6 `borrow_fee` remains null. Load
   `MODELLED_FLAT_BORROW_PROXY_V1` only through the experiment/C11 consumer
   configuration: 1.00% p.a. baseline, with pre-registered 0.30%, 0.60%, 4.30%
   and 7.00% sensitivities. Never persist those proxy values into C6. Verified
   unshortable security-months remain ineligible. The legacy implicit 25 bp
   fallback is prohibited.
5. Preserve the frozen dollar-neutral C11 construction (`gross_max = 2`, beta
   and industry neutrality) and route every comparator through the same
   stage-04 portfolio machinery for cost parity.
6. Use the packaged dated C12 integration in `alphacomb.tax.dated` and
   `alphacomb.tax.backtest`. Keep tax calculations in statutory local currency;
   convert at the frozen point-in-time FX boundary, using no future rate.
7. The only permitted tax-dependent international evaluation domain is
   2009-01-01 through 2019-12-31, with a cold-start tax ledger, no opening lots,
   and no pre-2009 acquisitions. The clean mechanism subwindow is 2014-01-01
   through 2018-03-31 and inherits state from the 2009 ledger inception.
   Enforce these limits at the Workstream-B input gate. The dated resolver is a
   reusable library and is not itself a general sample filter.
8. The nine earlier C14 source blockers in
   `data/intl_c14/audit/C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json` remain
   explicitly non-production. Do not impute them or extend the evaluation
   window.
9. Preserve the pre-results amendment in
   `data/intl_c14/audit/WORKSTREAM_A_PRE_RESULTS_SAMPLE_AMENDMENT_2026-10-07.md`.
   Do not run or inspect real-data outcomes without separate approval.

## Commands Harshit should run now

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe validate_workstream_a_post_promotion_2026_10_07.py
.\.venv\Scripts\python.exe validate_c14_evaluation_sample.py
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp .pytest_tmp_workstream_b_handoff
```

Expected results are `PASS` for all 14 post-promotion checks, `PASS` for the
13 C14 sample checks, and 290 passing tests. These commands validate the
handoff; they do not fit models or inspect outcomes.

Do not run a real-data model command yet. The approved manifest deliberately
does not authorize converting these sources into the legacy `data/real`
layout, changing `configs/base.yaml` from `synthetic` to `real`, or starting a
results run. That is the next separately approved Workstream-B execution step.

## Audit evidence

- Post-promotion validation:
  `data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_VALIDATION_2026-10-07.json`
  (14/14 PASS; SHA-256
  `37a2b38aacfe6476b3c98983b1a19d8a665549ed814e29ae0f74d30370b64c02`)
- Fresh full-suite JUnit:
  `data/workstream_a_closeout/WORKSTREAM_A_POST_PROMOTION_TESTS_2026-10-07.xml`
  (290 tests, zero failures/errors/skips; SHA-256
  `dee50cc7a5ad037fa6aee3e95976b110d67869064a728b18d04be5c595bd5a47`)
- Semantic preflight:
  `data/workstream_a_closeout/WORKSTREAM_A_SEMANTIC_PREFLIGHT_2026-10-07.json`
  (`PASS`, no failures)

Drive was checked for reconciliation. The matching project folder is an older
2 October snapshot and does not contain the exact current promotion authority
or current C6/C14 candidate hashes. Therefore the current local manifest-listed
files were retained as authoritative and Drive was left unchanged. No Git
commit or push was made.
