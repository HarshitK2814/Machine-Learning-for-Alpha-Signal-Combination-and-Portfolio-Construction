# For Absar (workstream A): 456 India securities need a 31-Jan-2018 reference value

**From:** Harshit, workstream B
**Date:** 2026-10-09, 02:45 IST
**Blocking:** the section 112A within-country event study — the cleanest identification left in the
project. Nothing else in workstream B is blocked by this.
**What I need:** `prchd` on 2018-01-31, in INR, for the 456 permnos in
`docs/handoff/attachments/IND_112A_MISSING_REFERENCE_PERMNOS_2026-10-09.csv`, appended to
`data/intl_c14/candidate_working/IND_SECTION_112A_REFERENCE_VALUES.csv` in its existing schema.
**This is the only kind of blocker I think needs you** — it is a WRDS/Compustat lookup I have no
entitlement for. Everything else from doc 18 is answered and withdrawn (see §5).


> ## UPDATE 2026-10-09, 13:05 IST — the bounding run I promised was built wrong, and is being redone
>
> At 02:45 I said I would bound the answer by re-running the event study with the 456 missing
> values set to the two tax extremes, so that if both bounds agree your lookup stops being a
> blocker. **I ran that, both bounds came back bit-identical to full precision, and I nearly
> reported you as unblocked. The bounding was invalid.**
>
> The engine does not consume an absolute FMV. `DatedC12Patch.attach_statutory_reference` computes
>
>     statutory_reference_value = close_value_local * reference.high_to_close_ratio
>
> where `high_to_close_ratio = fmv_price_local / close_price_local`. **The ratio is the only
> lever.** My bound files set `fmv` and `close` to the *same* extreme value on all 456 rows
> (0.0001/0.0001 and 1e9/1e9), so the ratio was **1.0 in both** and the engine multiplied each
> lot's real close price by 1.0 either way. The two runs were the same run. Bit-identical output
> was the symptom, not the finding.
>
> It mattered: **422 of the 456 names are materially held in India's prediction cells and 75 are
> held after 2018-04-01**, so their deemed cost genuinely does enter the result. "The missing
> values cannot change the conclusion" was never established.
>
> Corrected bounds (`*_V2.csv`) vary the **ratio** — 1e-6 for MAXTAX (no grandfathering relief,
> deemed cost falls back to actual cost) and 1e6 for MINTAX (full relief, deemed cost reaches sale
> value) — leaving the 546 real rows untouched and bit-identical between bounds. Re-running now;
> I will report whether the bounds agree once they land.
>
> **Your lookup therefore remains outstanding and is still the one thing only you can do.** If the
> corrected bounds do agree it becomes a robustness note rather than a blocker; if they disagree it
> is back to being on the critical path. Either way the request in §2 is unchanged.

---

## 1. The error

Running the dated C14 engine on India across 2018-04-01 stops immediately:

```
alphacomb.tax.dated.MissingDatedTaxConfiguration:
missing security-specific 31-Jan-2018 reference value for IND security 320031901
```

The engine is **right to fail here** — I am not asking you to relax it. Section 112A grandfathers
gains accrued before 2018-02-01 by setting the deemed cost to the higher of actual cost and the
fair market value on 2018-01-31, so a held lot without that value has no determinable cost base.
Defaulting to actual cost would silently *overstate* tax on every grandfathered lot, in the
direction that happens to favour the paper's story. `SecurityReferenceValueStore.get` raising is
the correct behaviour.

## 2. The cause, which is a clean mismatch rather than a defect

`IND_SECTION_112A_REFERENCE_VALUES.csv` holds **546 permnos**, all dated 2018-01-31, currency INR,
`source_field = prchd`. I checked what that set is:

```
investible India universe, January 2018 : 546 names
reference file                          : 546 names
identical set                           : True
securities in the file never held       : 0
```

So the file is exactly **the investible universe as of January 2018**. That is a perfectly
reasonable basis, and it is not what the tax ledger needs.

The ledger holds **1,002 distinct India securities** across 2009-2019, because a position persists
after its name leaves the investible universe — the frozen sleeve, documented in
`docs/NON_TRADEABLE_TREATMENT.md`. Those lots are still on the books when 2018-01-31 passes, and
they still need a deemed cost. Hence:

| population | securities | missing a reference |
|---|---|---|
| ever held by the 16 India cells | 1,002 | **456 (45.5%)** |
| held in 2017-12 .. 2018-04 | 582 | 36 (6.2%) |
| **held across 2018-01-31 itself** | — | **22** |

## 3. What I need, precisely

`docs/handoff/attachments/IND_112A_MISSING_REFERENCE_PERMNOS_2026-10-09.csv` has one row per
missing permno with `first_held`, `last_held`, `months` (position-months across the 16 cells), and
`held_across_2018_01_31`, sorted so the ones that matter most are first.

* **Minimum to unblock:** the **22** permnos with `held_across_2018_01_31 = True`. Those are the
  lots actually open on the grandfathering date. The largest by exposure are 320486701 (1,579
  position-months, held 2009-04 to 2019-02), 321127502 (1,502), 327025901 (1,170) and 320366602
  (1,150) — long-held core positions, not fringe names.
* **Preferred, so this cannot recur:** all **456**. A different AUM arm, a different cell, or
  Japan's and Germany's equivalents will hold a different subset, and I would rather not come back
  to you each time. If it is cheap, "every India permno with a `prchd` on 2018-01-31" is the
  version that never needs revisiting.

Same schema as the existing file, please — `SecurityReferenceValueStore.from_validated_csv`
enforces `source_field = prchd` and INR and rejects anything else, which is how I know the contract
is being checked rather than assumed.

## 4. What I am doing in the meantime

Not waiting on you for the rest. Germany's arm of the event study is **already run** and does not
need any of this, because Abgeltungsteuer has no grandfathering clause and no holding-period
boundary. Its result is in `docs/RESULTS_WEDGE_TEST.md` §9 — and worth your knowing that the German
*control* arm does not come back clean: the levels outcome gives t = −1.24 year-clustered but
t = −2.18 cell-clustered, a borderline gradient in a country whose law did not change on that date.

If the reference values turn out to be slow to get, the fallback I would use is to **bound** the
result rather than invent a number: run the India arm twice with the 22 missing lots' deemed cost
set to each extreme (actual cost, giving maximum tax; and a high FMV, giving minimum tax). If the
conclusion is unchanged at both bounds the gap does not matter for the finding. That needs an
override hook in a frozen component, so I would rather have the real values — but it means this is
not a hard stop if WRDS access is awkward this week.

## 5. Your doc-18 queue is clear — both questions answered and withdrawn

Your `data/intl_c6/audit/` files were already in my checkout and I had not opened them. They
answer both of my outstanding questions, so please don't spend time on either:

1. **ADV coverage.** Monthly `adv_usd` requires a complete 21-day volume window, and only Germany
   fails it — 65.09%, which matches the 65.2% I measured. India is 99.19% and Japan 99.80%. Not a
   promotion gap, nothing to fix. **Withdrawn.**
2. **Borrow fees.** You probed 266 WRDS libraries and no securities-lending fee source is entitled.
   So `MODELLED_FLAT_BORROW_PROXY_V1` is the only available option rather than a shortcut I took,
   and the paper can now cite your audit for that. **Withdrawn.**

Thank you — both saved me from writing something wrong about the data.

## 6. One thing you may want to know about, no action needed

Japan's promoted panel carries data from **1996**, while Germany's and India's effectively begin at
the frozen window. With default `--years` a Japanese stage-02 run evaluates **300 months** against
the other two arms' 132. That is not a defect in your promotion — the data is simply longer — but
anyone running Japan on defaults gets a window mismatch, so I now pass `--years 2009 2019`
explicitly and recorded it in `docs/AMENDMENT_001B_UNIVERSE_BREADTH_CAP.md` §1a. Flagging it in
case it bites another consumer.
