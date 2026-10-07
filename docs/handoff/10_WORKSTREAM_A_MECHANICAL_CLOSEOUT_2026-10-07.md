# Workstream-A mechanical closeout — 7 October 2026

## Final status

- **India TERM: PASS_WORKING_CERTIFIED_RBI_91D_CUTOFF.** Fresh RBI DBIE
  extraction produced 1,752 auctions, five missing yields, three corrected RBI
  display year rollovers, and no monthly gaps. The research-window build uses
  1,458 auctions through 2020, explicitly flags January/February 2016 failed
  auctions, and activates on 31 August 1998: 235 months earlier, with zero
  post-activation gaps.
- **Workstream-A mechanical preflight: PASS.** All 25 closeout checks pass.
- **Remaining Workstream-A blockers: exactly six human decisions.**
- No production data, frozen Workstream-B code, commit, or remote repository was
  changed.

## Frozen C5/C6 result

- C5 complete working contracts pass for DEU, IND and JPN: 372 months and 23
  contract columns each, including BEAR, DISP and all 13 FMOM states.
- Strict spread coverage is 698,908/757,297; AR adds 613,488 observations beyond
  EDGE. The remaining 58,389 observations stay null and ineligible.
- Complete observable spread + sigma + USD ADV exists for 622,817 rows.
- Four raw-confirmed sigma outliers remain preserved and fail-closed.
- Borrow fees remain all-null; the frozen consumer's implicit 25 bp fallback is
  detected and blocked.

## Exact Workstream-B changes after the six approvals

1. Add the approved six-decision configuration at
   `configs/workstream_a_frozen_decisions.json`; prohibit missing keys and
   defaults.
2. Extend canonical real-data paths/loaders to select one of the per-country
   bundles under `data/real/{DEU,IND,JPN}`.
3. Make C6 eligibility explicit: never median-fill spread, fixed-fill sigma/ADV,
   or apply `fillna(0.0025)`. Exclude security-months lacking registered
   observable market inputs from cost-aware optimisation. Apply the approved
   borrow decision; under long-only, do not consume borrow fees.
4. Integrate the checksum-frozen dated resolver, grandfathered lot basis,
   per-side statutory taxes, bucketed loss ledger, immutable loss vintages,
   inclusive expiry and local-currency/PIT-FX handling into the C12 engine.
5. Route Germany/India/Japan C14 events through the approved rate, allowance,
   FX, fee-scope and Japan-route configurations. Preserve static-regime
   compatibility for existing non-international tests.
6. Rerun the frozen pre-existing tax-aware optimiser test. Then regenerate C11
   weights where a decision affects optimisation, C12 returns and tax summaries,
   Stage 07 after-tax/adaptive outputs, and all dependent figures.

## Promotion sources

The exact source paths, intended destinations, byte sizes and SHA-256 hashes are
frozen in
`data/workstream_a_closeout/FINAL_WORKING_MANIFEST_2026-10-07.json`.
Nothing in that manifest has been promoted.

## Post-promotion validation

From the repository root, after the decisions, integration and promotion:

```powershell
$env:PYTHONPATH = (Resolve-Path '.\src').Path
.\.venv\Scripts\python.exe .\final_workstream_a_post_promotion_validate.py
```

The validator requires all six frozen decisions, validates C1–C6 per country,
rechecks exact spines, rejects the 25 bp fallback, and runs the C14, optimiser,
tax-term and manifest tests.

## Evidence

- `data/intl_c5/candidate_term_drate_working/IND_TERM_RBI_91D_CUTOFF_CERTIFICATION.json`
- `data/intl_c5/candidate_final_working/C5_FINAL_WORKING_AUDIT.json`
- `data/intl_c6/audit/C5_C6_DAILY_PREFLIGHT.json`
- `data/intl_c14/audit/C14_DATED_C12_ARCHITECTURE_FREEZE_2026-10-06.json`
- `data/workstream_a_closeout/WORKSTREAM_A_MECHANICAL_PREFLIGHT_2026-10-07.json`
- `data/workstream_a_closeout/FINAL_BLOCKER_LEDGER_2026-10-07.md`
- `data/intl_c14/audit/FINAL_HUMAN_DECISIONS_2026-10-07.md`

