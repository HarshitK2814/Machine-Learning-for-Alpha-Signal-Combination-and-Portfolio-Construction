# India TERM short-leg evidence audit — 7 October 2026

## Decision

**PASS as evidence; independent production rebuild required.** The RBI 91-day
Treasury-bill auction cut-off yield is semantically admissible for the existing
India TERM contract. That contract already calls for an RBI primary-auction
91-day implicit yield, so a secondary-market quote is not required unless the
research definition is deliberately changed.

The supplied archive was not imported into C5 and no production candidate was
written. Its SHA-256 is
`12ca5933df63d9bf2aba9231cc63120ceca83a9fdfe3c0a6237ef469362a0cfa`.

## Mechanical results

- 1,752 auction observations, 8 January 1993 through 23 September 2026.
- 405 consecutive month-end observations, January 1993 through September 2026.
- Median/max issue-date staleness: 3/18 days.
- The supplied monthly series is reproduced exactly from the supplied raw rows.
- Against the current monthly-average short source over 200 overlapping months:
  correlation 0.996820, mean absolute difference 0.059913 percentage points,
  maximum absolute difference 0.719300 percentage points. These are different
  monthly statistics and are not expected to be identical.
- Under the frozen one-reference-month lag and 24-observation expanding warm-up,
  the non-production TERM preview first activates on **31 August 1998**, 235
  months earlier than the current 31 March 2018 activation, with no subsequent
  gaps.

## Required qualifications

1. Three raw issue dates at year-end were parsed into the preceding year. Adding
   one year restores valid auction-to-issue lags; the correction changes no
   selected monthly yield.
2. Five auctions have no implicit cut-off yield. In January 2016, February 2016,
   March 2023, and March 2026 the missing observation is the final auction of the
   month, so the month-end value is the preceding successful auction. This is an
   explicit stale-observation rule, not interpolation, and must remain flagged.
3. Issue-date rather than auction-date month-end keying changes 63 monthly
   values. It is conservative, and the project-level one-month lag remains in
   force.
4. The series does not solve 1990–1992. The developing character of the early
   auction market must remain in the source metadata.
5. The supplied browser scraper is UI-dependent. Production must independently
   fetch, hash, validate, and cache the RBI source rather than inherit the CSV.

## Frozen next action

Build the India 91-day series independently from RBI, enforce nonnegative
auction-to-issue lags, preserve missing-auction and staleness flags, reproduce
the audit identities above, and only then rebuild the non-production India TERM
candidate. Do not modify the existing candidate from this evidence archive.

Machine-readable audit:
`data/intl_c5/audit/INDIA_TERM_SHORT_LEG_EVIDENCE_AUDIT.json`.

