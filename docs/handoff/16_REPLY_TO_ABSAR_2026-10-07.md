# Reply to Absar — 7 October 2026

Chat-ready. Full evidence in
[`14_WORKSTREAM_B_RECEIPT_AND_INTEGRATION_2026-10-07.md`](14_WORKSTREAM_B_RECEIPT_AND_INTEGRATION_2026-10-07.md).

---

Absar — document 13 accepted as the authoritative Workstream-A handoff, earlier A status
docs treated as audit history where they conflict. Good work closing C5/C6 and freezing
the six decisions.

**Found the Drive upload — it's all there.** I walked the folder directly and confirmed
the complete promoted repo: both validators (`validate_workstream_a_post_promotion_2026_10_07.py`
16:16, `validate_c14_evaluation_sample.py` 15:51), all of `src/alphacomb/` including
`tax/dated.py` (33 KB, 15:51), `configs/base.yaml` (16:29), the new `tests/c14/` and
`tests/portfolio/` (16:31), and the full `data/workstream_a_closeout/` with
`FINAL_PRODUCTION_PROMOTION_MANIFEST_2026-10-07.json` at 16:09. Every file size matches
your manifest.

Worth flagging: **Drive's search is broken for this folder** — both the API and the web
UI. Searching `dated.py` returns only the manifest that mentions it, not the actual file.
I initially concluded from that the folder was empty and that you hadn't transported
anything. That was my error; an empty search result there means nothing. Had to walk the
tree directory by directory. Flagging it so you don't trust a Drive search either.

I'm downloading it now and will run the verifier
(`tools/verify_workstream_a_receipt.py`, re-derives SHA-256 from the downloaded bytes
against your manifest plus the five digests pinned from doc 13), then your three
commands, and report back either `RECEIPT_VERIFIED_PASS` or the exact files that
disagree.

**Three things I need from you:**

**1. Which duplicates are authoritative?** `data/` has `intl_c6` twice and `intl_c14`
three times, and they are *not* equivalent. Of the three `intl_c14`: one has only a 4 KB
working CSV, one has `audit`/`candidate`/`reference` all from 3 Oct, and one has
`audit`/`candidate_working`/`production` modified 16:38 with the correct 11 KB
`c14_regime_candidate_source_frozen.csv` at 13:09. I'll take that third one, but confirm
— and tell me which `intl_c6` to use. Easiest fix would be deleting or renaming the stale
copies so nobody picks wrong later.

**2. Does your `cost_terms.py` fix all four fields?** My 27 Sep `cost_inputs_for`
median-imputes `spread`, `sigma_d` and `adv_usd` *and* applies the prohibited
`fillna(0.0025)` borrow fallback — violating doc 13 reqs 2 and 4, and presumably the
exact gate that held C6 at `FAIL_MECHANICAL_PREFLIGHT`. Yours is 7,127 B to my 3,612 B;
I'm assuming it removes the market-field imputation too, not just borrow. Confirm?

**3. Is the `intl_c*` layout final, and are DEU/IND/JPN pooled or separate?** Doc 13
prohibits materialising `data/real`, but `FINAL_WORKING_MANIFEST` still lists
`post_approval_destination` as `data/real/DEU/universe.parquet` etc., and every
Workstream-B reader (`contracts/paths.py`, `configs/base.yaml`, pipelines 02/04/06/07)
resolves a flat `data/<mode>/` path with no country dimension. I need to write a
country-aware resolver, and pooled-vs-separate changes the resolver, the clustering of
standard errors and what a baseline means. Raising it in the group so Maham is in on it.

**One suggestion:** the code is only ~170 KB. Pushing it to GitHub as well would give us
real version history and stop us comparing file sizes in a Drive listing to work out
what's current. Your call — the data obviously stays on Drive.

I've deliberately not reimplemented any of your files; your manifest pins each to a
digest and a locally-written `cost_terms.py` would create a second divergent copy of the
cost path we froze contracts to protect.

Nothing committed or pushed on my side. No real results inspected.
