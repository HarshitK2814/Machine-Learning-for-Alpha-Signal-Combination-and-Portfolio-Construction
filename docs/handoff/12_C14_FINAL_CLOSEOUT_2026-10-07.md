# C14 final closeout — 7 October 2026

## Terminal status

```ini
C14 = BLOCKED_SOURCE_FACT
WORKSTREAM_A_SEMANTIC_PREFLIGHT = BLOCKED
DATED_C12_INTEGRATION = PASS
C1-C6 = READY_FOR_PRODUCTION_PROMOTION
HUMAN_DECISIONS = 6/6 FROZEN
REAL_RESULTS_INSPECTED = NO
```

The only failing semantic-preflight checks are the incomplete C14 numeric
configuration and the bounded source-fact gate. No C1-C6, India TERM, borrow,
human-decision or unrelated Workstream-B component was changed in this pass.

## Mechanical closeout

The dated production path now:

- resolves realised capital-gain events through `DatedC12Patch`;
- carries acquisition/applied rule IDs with lots;
- routes dated losses through `LossCarryforwardBook` with immutable vintages,
  inclusive expiry and asymmetric India ST/LT buckets;
- keys overrides by applied rule ID (including effective date) and field;
- resolves dividend rates by event date and fails closed on missing rates;
- validates a field-level India section 112A reference contract;
- keeps statutory computations in local currency with point-in-time FX at the
  adapter boundary; and
- retains the static `_YearBook`/`TaxLotLedger` path when no dated engine is
  configured.

The full repository suite passed 285/285 tests (0 failures, 0 errors). The C14
suite passed 29/29, including eight packaged production-integration tests.

## India section 112A reference contract

The statutory field is `prchd`: the highest quoted exchange price on
31 January 2018, or on the immediately preceding traded date when there was no
trade on that date. The builder used only the frozen 2018 daily cache and wrote
546 unique India security rows. Every row is INR, positive, non-forward-looking
and carries the source-cache SHA-256. No market data were fetched.

## Remaining source facts

The bounded primary-source pass ended with nine grouped blockers:

1. Germany 1990 Börsenumsatzsteuer operative listed-equity rate and statutory
   buyer/seller incidence.
2. Germany 1990-2008 complete annual top-marginal CGT/dividend path, including
   solidarity-surcharge chronology and the changing dividend tax base.
3. Germany 1999-2008 exact section-10d carryback/forward horizons, caps and
   cash/refund mechanics.
4. Japan 1990-2003-03 complete 5A comprehensive-return dividend rate and
   dividend-credit schedule.
5. Japan 2001-10 through 2002 exact enacted conditions/effective dates for the
   one-million-yen long-term special treatment and emergency relief.
6. Japan 2003-01 through 2003-03 dividend rate before the 2003-04-01 reduced
   listed-dividend regime.
7. India complete dated top-marginal base/surcharge/cess path for pre-STT years
   and 2020-04 through 2020-12 dividends.
8. India historical indexation inputs and pre-2000 basis/deduction rules needed
   to compare the conditional indexed and unindexed LTCG computations.
9. India section 10(36) security-level BSE-500/IPO and purchase/sale-venue
   qualification data.

No scalar was inserted for a conditional rule, and no later rate was projected
backward.

## Audit artefacts

- `data/intl_c14/audit/C14_FINAL_CLOSEOUT_VALIDATION_2026-10-07.json`
- `data/intl_c14/audit/C14_BOUNDED_PRIMARY_SOURCE_PASS_2026-10-07.json`
- `data/intl_c14/candidate_working/C14_DECISION_1A_DATED_RATE_SCHEDULE.csv`
- `data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv`
- `data/workstream_a_closeout/WORKSTREAM_A_SEMANTIC_PREFLIGHT_2026-10-07.json`
- `data/workstream_a_closeout/WORKSTREAM_A_FULL_TESTS_2026-10-07.xml`

No production promotion, commit, push or real-data result inspection occurred.
