# Workstream-A final integration gate — 7 October 2026

## Outcome

The six human choices are frozen as `1A, 2C, 3A, 4A, 5A, 6B`, and the
borrow-fee policy is fully integrated without changing certified C6 values.
The full repository suite passes **281/281**. No real-data result was run or
inspected, no production candidate was promoted, and no Git commit or push was
performed.

The final semantic gate nevertheless remains **BLOCKED**, rather than recording
a false production-ready status for C14.

```ini
WORKSTREAM_A_SEMANTIC_PREFLIGHT = BLOCKED
HUMAN_DECISIONS = 6/6 FROZEN
C1-C6 = READY_FOR_PRODUCTION_PROMOTION
C14 = BLOCKED
DATED_C12_INTEGRATION = BLOCKED
LEGACY_25BP_BORROW_FALLBACK = ABSENT/BLOCKED
REAL_RESULTS_INSPECTED = NO
```

## Completed integration

- `MODELLED_FLAT_BORROW_PROXY_V1` is explicit consumer configuration: 1.00%
  p.a. baseline and 0.30%, 0.60%, 4.30%, 7.00% sensitivities.
- Certified C6 `borrow_fee` remains all-null; the proxy is applied only to an
  in-memory consumer copy.
- The implicit 25 bp fallback is absent. Missing spread/sigma/positive USD ADV
  makes the security-month ineligible.
- The checksum-frozen dated architecture is packaged under
  `alphacomb.tax.dated`; transition, reference-value, side-tax, ring-fencing,
  inclusive-expiry and immutable-vintage tests pass.
- C12 charges dated side-specific statutory transaction taxes and fixes the
  existing vintage refresh/final-year defects.
- India TERM remains certified at 1998-08-31 with zero post-activation gaps.

## Concrete blockers found by the final semantic test

1. The C12 backtest invokes the dated engine for transaction taxes, but its
   capital-gain events, dividend events and bucketed annual loss book still use
   the static path. The packaged mechanics therefore are not yet fully wired
   through the result-producing C12 loop.
2. The selected C14 path contains **53 unresolved required numeric fields**:
   Germany 12, India 22 and Japan 19. These include pre-regime capital-gain and
   dividend rates, Germany's 1990 transaction tax, and historical loss rules.
   Decision 1A selects the *kind* of rate path; it does not supply those dated
   numeric rates. No blank was converted to zero.
3. The required security-level India 31-Jan-2018 reference-value input for
   §55(2)(ac)/§112A is not present.

These are source/configuration and result-path gaps, not additional human
portfolio-design choices. The instruction not to invent defaults is preserved.

## Audit and promotion boundary

- Semantic audit:
  `data/workstream_a_closeout/WORKSTREAM_A_SEMANTIC_PREFLIGHT_2026-10-07.json`
- Promotion manifest:
  `data/workstream_a_closeout/FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json`
- Full test result:
  `data/workstream_a_closeout/WORKSTREAM_A_FULL_TESTS_2026-10-07.xml`

The promotion manifest is intentionally `BLOCKED_BEFORE_PROMOTION`.
