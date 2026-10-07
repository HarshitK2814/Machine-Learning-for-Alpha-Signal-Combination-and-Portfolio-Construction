# C5/C6 WRDS resume completion - 7 October 2026

This status supersedes the WRDS-blocked portions of
`06_C5_C6_DAILY_CERTIFICATION_STATUS_2026-10-06.md`. It covers working and audit
artifacts only. Nothing was promoted, committed, or pushed.

## Result

| Component | Result |
|---|---|
| WRDS authentication and bounded extraction | PASS |
| Abdi-Ranaldo strict extraction | PASS: 698,908/757,297 rows |
| Actual combined spread coverage | PASS: 92.2898% |
| Four extreme sigma observations | PASS: raw-reproduced and fail-closed |
| C6 working candidate rebuild | PASS |
| C5 mechanical preflight | PASS |
| C6 market-data identities and no-look-ahead | PASS |
| Genuine borrow-fee source | BLOCKED |
| C6-to-Workstream-B borrow integration | HARD FAIL as intended |

## Actual spread coverage

EDGE remains primary. Strict Abdi-Ranaldo is used only where EDGE is absent.

| Country | Rows | Strict spread | Coverage | Complete spread + sigma + ADV |
|---|---:|---:|---:|---:|
| DEU | 122,784 | 105,026 | 85.5372% | 67,699 |
| IND | 71,646 | 68,203 | 95.1944% | 65,160 |
| JPN | 562,867 | 525,679 | 93.3931% | 489,958 |
| **Total** | **757,297** | **698,908** | **92.2898%** | **622,817** |

The fallback contributes 613,488 rows beyond the 85,420 strict EDGE rows. The
remaining 58,389 spread gaps are retained as null; nothing is imputed.

Evidence:

- `data/intl_c6/audit/C6_ACTUAL_AR_COVERAGE_AUDIT.json`
- `data/intl_c6/audit/C6_ACTUAL_AR_COVERAGE_BY_COUNTRY_YEAR.csv`
- `data/intl_c6/audit/C6_WRDS_ABDI_RANALDO_21_AUDIT.json`

## Sigma outlier resolution

The exact 21-return windows reproduce all four reported sigma values within
floating-point tolerance. The shocks are present in raw `g_secd` price rows;
they are not a rolling-window or return-formula error. Every flagged row has
null strict ADV, so none can enter a complete C6 market-input record. The values
were preserved without clipping, deletion, interpolation, or backfill.

Evidence:

- `data/intl_c6/audit/C6_SIGMA_OUTLIER_RAW.csv`
- `data/intl_c6/audit/C6_SIGMA_OUTLIER_RAW_AUDIT.json`
- `data/intl_c6/audit/C6_SIGMA_OUTLIER_RESOLUTION.json`

## Final preflight state

C5 passes. C6 passes its key, identity, hierarchy, non-negativity,
no-look-ahead, and outlier-review checks. Its overall verdict remains
`FAIL_MECHANICAL_PREFLIGHT` solely because the certified all-null borrow fee
would be silently replaced with 0.0025 by the frozen Workstream-B consumer.

The genuine-source and incomplete-spread items remain explicit data blocks, but
the only mechanical failure is the borrow-fee consumer integration gate. The
current 25 bp substitution and zero-fill remain prohibited.

Evidence:

- `data/intl_c6/audit/C5_C6_DAILY_PREFLIGHT.json`
- `data/intl_c6/audit/C5_C6_DAILY_PREFLIGHT_CHECKS.csv`
- `data/intl_c6/audit/C6_CONSUMER_COMPATIBILITY_AUDIT.json`
- `data/intl_c6/audit/C5_C6_RESUME_COMPLETION_2026-10-07.json`

## Stop condition

The six fields in
`data/intl_c14/audit/C14_C6_HUMAN_DECISION_SHEET_2026-10-06.md` remain blank.
Accordingly, the frozen dated-C12 patch was not integrated and the Workstream-A
semantic preflight was not started. The checksum freeze still passes. Work is
stopped before production promotion, Workstream-B modification, or GitHub
writes.
