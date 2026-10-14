# Final claim-evidence matrix (2026-10-14, completion sprint)

Internal researcher-led audit; not an external review. No approval by Maham or Absar beyond their documented responses is claimed (001A-001D countersignatures are withheld, 001E is a non-binding draft, Maham's acknowledgement of the exit ruling is outstanding). Nothing was re-run: every check below reads a committed artifact (or, where stated, an untracked local file) and compares the value with what the documents say. No new result, no Phase C run, no vendor access.

Starting state: HEAD `24e9a4c`, clean tree, branch `feat/workstream-b-resolver-and-prereg`; work is on `feat/completion-sprint-2026-10-14`. The source documents are `docs/PAPER_2026-10-09_FULL_ACCOUNT.md` (the only manuscript-like prose, an internal full record, not a submission draft), `docs/FINALIZATION_AUDIT_2026-10-09.md`, `docs/MANUSCRIPT_EVIDENCE_MAP_2026-10-14.md` (the claim table this matrix finalises and extends), `docs/LIVE_DOCUMENT_CORRECTIONS_2026-10-14.md`, `docs/INFERENCE_AUDIT_2026-10-13.md`, and the Phase C closeout (`docs/PHASE_C_RUN_READINESS_V2_2026-10-14.md` section 8).

Status vocabulary: `SUPPORTED_AS_RUN` (traced to a committed artifact, no material caveat), `SUPPORTED_WITH_QUALIFICATION` (traced, with a wording or scope limit that must travel with it), `WITHDRAWN`, `BLOCKED` (needs a run or data that is not available or not authorised), `UNVERIFIABLE` (the number is quoted in documents but no artifact containing it exists in the repository or in the local outputs).

## 0. Four cross-cutting qualifications that apply to every as-run number

1. **Exit treatment.** Every historical number was produced under `exit_policy = as_run` (commits through `ac669f2`). The 2026-10-13 ruling replaced it with `carry_v1`, and the revised analysis (Phase C) is blocked and not runnable (all 560 series not estimable; vendor coverage `unknown`). The sensitivity of any as-run number to the exit treatment is therefore **unknown**, not shown to be small.
2. **Cost calibration.** The S0/S1/S2 cost-calibration sensitivity has not been run. Statements about the registered calibration carry that qualifier.
3. **Pre-registration.** PLAN_001 (fingerprint `cae8140b7e2b7ee4`, N = 64) is frozen and its amendments 001A-001D are committed but **not countersigned**; 001E is a draft. "Pre-registered" means "committed to git before the data it concerns existed", not externally countersigned.
4. **Artifact hygiene.** `outputs/` is git-ignored. The tracked evidence is `docs/attachments/*.csv` (verbatim snapshots), `results/capacity_return_difference/`, `results/cost_parity_diagnostic/` and `results/figures/`. `results/capacity_return_difference/MANIFEST.json` records `git_dirty_when_written = true`.

## 1. Traceability findings of this audit (new, not in the 2026-10-14 evidence map)

| # | Finding | Consequence |
|---|---|---|
| F1 | `docs/attachments/AFTER_TAX_INFERENCE_1E9_2026-10-09.csv` (and the untracked `outputs/after_tax_inference/after_tax_inference_1e9.csv`) contain **India and Japan only**. The Germany row (net Sharpe +0.152, t +0.53, p 0.595; tax channel -0.1363, t -4.67; Holm 3/8) exists only in prose. | The Germany headline "net Sharpe not distinguishable from zero (t = +0.53)" and the Germany optimised-book tax-channel significance are **UNVERIFIABLE**. |
| F2 | `HORSE_RACE_DECILE_PANEL_2026-10-09.csv` and `HORSE_RACE_DECILE_PANEL_COV_2026-10-09.csv` are **identical** and both hold the **non-compliant (pre-fix) ladder** (Germany $100k: gross 2.763, capacity -0.811). The file named `_COV` does not contain the compliant ladder. The compliant numbers are in `CAPACITY_CHANNEL_INFERENCE_*_COV_*.csv` (Germany $100k: +0.068, t +1.22). | The paper's section 6.5 horse-race tables and any number sourced from the `HORSE_RACE_*` attachments are **UNVERIFIABLE** and must not be used. The retracted t = -6.10 is reproducible from `CAPACITY_CHANNEL_INFERENCE_DEU_2026-10-09.csv` (-6.098), which is the correct source for the worked failure. |
| F3 | The gross-signal HAC t-statistics (+7.14 / +3.19 / +4.11) and the capped-decile t-statistics of paper section 6.2.5 (-2.29 / -1.80 / -2.56) appear in no committed table. The matched-book attachments give the committed capped-decile net-vs-zero t at the solvent rungs (DEU $1bn -2.40, IND $1bn -1.81, JPN $1bn -2.74). | Use the matched-book values; the section 6.2.5 t-statistics are **UNVERIFIABLE**. |
| F4 | `SUMMARY_AFTER_TAX_*` attachments cover DEU $100mn and $10bn and JPN $100mn, $1bn, $10bn. **No India summary and no Germany $1bn summary is tracked.** India's `lt_share` 0.5928 is verifiable only in the untracked local file `outputs/summary_after_tax_IND_1e9.csv` (sha256 prefix `e2fd34229e1e8b38`, mean over the 8 prediction cells of the statutory regime, 0.5928). Germany $1bn's turnover 0.0135 is likewise only in an untracked file. | India's 0.5928 is `SUPPORTED_WITH_QUALIFICATION` (untracked source). The turnover ordering JPN > DEU > IND at $1bn is **UNVERIFIABLE** from tracked artifacts. |
| F5 | Cost-input coverage recomputed from the tracked census v3 (certified C6 / in-universe counts, mean over 132 months): DEU 0.652, IND 0.989, JPN 0.998 (paper: 0.651, 0.991, 0.998). | Reproduced; India differs by 0.002 under a different denominator. State the definition. |
| F6 | The paper cites `@AHV2025`; the bibliography key is `AHV2023` (SSRN working paper). Tax-literature keys the paper uses (SS2018, IM2012, BY2003, KS2024, HUANG2019, PISH2026, CBLO2020, and the Dai-Lei-Liu-Yang and Moehle et al. rows) are **absent** from `research/08_References/references.bib`. | The candidate cites only keys that exist in the bibliography and lists the others as pending; no citation record was invented. |

## 2. The matrix

Columns: ID; claim; status; source artifact (commit or file); configuration and scope; may it stay in a submission now; required correction.

### 2.1 Contribution and novelty

| ID | Claim | Status | Source | Scope | Keep? | Correction |
|---|---|---|---|---|---|---|
| N1 | A like-for-like measurement of three frictions (AUM-indexed cost, ADV participation constraint, statutory capital-gains tax) on identical signals and a common investable universe in DEU, IND, JPN, with a dated lot-level tax engine. | SUPPORTED_WITH_QUALIFICATION | `FINALIZATION_AUDIT` 2.1; `PAPER` 2.3 | 2009-2019, 132 months, as_run exit | **Yes, as a measurement contribution**, narrowed | State "to our knowledge"; novelty search not exhaustive; several prior-art rows are abstract-level (ACM2023 full text not read). |
| N2 | Not a new mechanism, not a profitable strategy, not a causal tax effect, no adjudication of NMV2016 versus AHV. | SUPPORTED_AS_RUN | `FINALIZATION_AUDIT` 2.2; `PAPER` 2.4 | | Yes | Keep verbatim. |
| N3 | ML plus AUM-dependent costs as a method contribution. | WITHDRAWN | `FINALIZATION_AUDIT` 2.3 (JKMP RFS 2026 owns it) | | No | Never claim. |
| N4 | "Implementability frontier" ($106mn / $55mn / $413mn) as a contribution; "10-100x below US". | WITHDRAWN (as a contribution and as a US comparison) | `PAPER` 8.5 | | No | Frontier numbers are descriptive only; source `outputs/capacity_frontier.csv` is untracked. Omitted from the candidate. |

### 2.2 Headline numerical claims

| ID | Claim | Status | Source | Scope | Keep? | Correction |
|---|---|---|---|---|---|---|
| H1a | India optimised book, $1bn: net Sharpe +0.271, t +0.82, p 0.413; after-tax +0.265, t +0.80. | SUPPORTED_WITH_QUALIFICATION | `docs/attachments/AFTER_TAX_INFERENCE_1E9_2026-10-09.csv` (composite row) | prediction cells, composite, 131 months, as_run, registered costs, 1% modelled borrow | Yes | As-run exit; own Newey-West on the standardised series. |
| H1b | Japan optimised book, $1bn: net Sharpe +0.055, t +0.18; after-tax -0.082, t -0.27. | SUPPORTED_WITH_QUALIFICATION | same | 132 months | Yes | Same. |
| H1c | Germany optimised book, $1bn: net Sharpe +0.152, t +0.53. | **UNVERIFIABLE** | none (F1) | | **No, not as a number** | State only "not distinguishable from zero in India and Japan; Germany's figure is not currently traceable". |
| H2 | Gross decile composite Sharpe +2.305 / +1.197 / +1.278 (DEU / IND / JPN). | SUPPORTED_WITH_QUALIFICATION | `MATCHED_BOOK_1E+08` (DEU gross 2.305), `MATCHED_BOOK_3E+07` (IND 1.197), `MATCHED_BOOK_1E+09` (JPN 1.278) | uncapped decile, compliant universe, equal-weighted | Yes (gross, with the value-weighting caveat) | The paper's t = +7.14 / +3.19 / +4.11 are UNVERIFIABLE (F3); omit them. Value weighting cut gross by about 80% on the pre-fix universe (NMV2016 critique); not re-run on the compliant universe. |
| H3 | Executable capped decile book has negative net Sharpe: DEU -0.709 (t -2.40), IND -0.638 (t -1.81), JPN -0.828 (t -2.74), at $1bn. | SUPPORTED_WITH_QUALIFICATION | `MATCHED_BOOK_1E+09` rows `capped` | $1bn, matched-book accounting, 131-132 months | Yes | The capped book attains only a few percent of target gross, so the Sharpe is a ratio of small numbers; quote with that caveat. |
| H4 | Uncapped decile book net Sharpe is destroyed by costs (JPN -7.745 at $1bn; DEU -7.312 at $100mn; IND -3.987 at $30mn). | SUPPORTED_WITH_QUALIFICATION | `MATCHED_BOOK_*` | solvent rungs; the comparator is near-ruined (terminal wealth 7.7e-10, 2.6e-06, 6.7e-06) | Yes as a descriptive statement about an infeasible book | Never present as a performance. |

### 2.3 Capacity and cost

| ID | Claim | Status | Source | Scope | Keep? | Correction |
|---|---|---|---|---|---|---|
| C1 | **B(A)**: annualised net-return difference (percentage points of NAV per year) between capped and uncapped decile composites, monotone increasing in AUM across the 35 valid rungs (DEU 11, IND 10, JPN 14); insolvent comparator rungs (DEU 3, IND 4, JPN 0) get no value. | SUPPORTED_WITH_QUALIFICATION | `results/capacity_return_difference/tierB_*.csv`, `tables.md`, `MANIFEST.json` (`ac669f2`); counts and monotonicity re-checked today | 2009-01 to 2019-12; equal-weighted summary of 8 independently simulated full-AUM variants; registered cost model; 1% modelled borrow; zero tax; `mean_difference_test`, 4,000 replications, block 6, seed 0, Holm within country over valid rungs | **Yes, as the primary capacity result** | Must carry: accounting difference against an infeasible/near-ruined comparator (uncapped terminal wealth below 0.1 at 6/11 DEU, 7/10 IND, 4/14 JPN rungs); not realised performance; not a Sharpe-point equivalent; at DEU $100k and $300k B is -0.52 and -0.01, not distinguishable from zero; Tier A and Tier B cost accounting differ and are "not fully explained" (C8); manifest recorded a dirty tree. |
| C2 | Sharpe-point capacity channel +6.80 (DEU $100mn), +3.19 (IND $30mn), +6.92 (JPN $1bn) "established on solvent rungs". | **WITHDRAWN** as a headline (status "unresolved - do not quote" in the evidence map) | `PAPER` 1, 8.9; `STATUS` | comparators near-ruined (terminal wealth 7.7e-10 / 2.6e-06 / 6.7e-06) | **No** | Not restored. Omitted from the candidate; the only capacity unit used is B(A). |
| C3 | German and Indian $1bn and $10bn gains (+8.92/+9.26, +5.69/+5.97), "asymptotic channel", sign flip, crossover, `crossover ~ k^-2`, "H-FLIP CONFIRMED". | WITHDRAWN | `FINALIZATION_AUDIT` 1.2; `AMENDMENT_001D` | | No | Never restate. The sign flip appears only as the worked coverage failure (A4), labelled retracted. |
| C4 | "There is no mandate size at which the cap meaningfully hurts, at the registered calibration." | BLOCKED | `PAPER` 1, 6.2 | cost calibration sensitivity not run; exit policy open | **No** | Remove. At DEU $100k B is -0.52 (not distinguishable from zero) and a cheaper calibration produces a small negative region in the Sharpe-unit ladder. |
| C5 | The cap's effect is near zero where slack and increases with how hard it binds. | SUPPORTED_WITH_QUALIFICATION | `CAPACITY_CHANNEL_LADDER_2026-10-09.csv`, `CAPACITY_CHANNEL_INFERENCE_*_COV_*.csv`; B(A) monotonicity | Sharpe-unit ladder on the compliant universe; B(A) starts at $100k (slack already 6-7% in DEU/IND) | Yes, as a pattern, with B(A) as the magnitude | The slack-zero end of the claim is on the Sharpe-unit ladder only and its readings there are noise of arbitrary sign. Monotone-in-AUM is "as found, not imposed". |
| C6 | Japan is a pre-registered out-of-sample confirmation (D2: channel positive at $1bn). **[Superseded 2026-10-14, see section 6: only 001D's D2 sign test (Sharpe units, near-ruined comparator) was met; 001C's predictions are unscored and P2 appears not to hold; Japan is not presented as a confirmation.]** | SUPPORTED_WITH_QUALIFICATION (D2 only) | `AMENDMENT_001D` section 11; `CAPACITY_CHANNEL_INFERENCE_JPN_COV` | JPN | Yes | Say: prediction committed before any Japanese portfolio existed, scored by code committed before; amendments not countersigned. D3 passed vacuously (-0.0013, p 0.370), D5 failed; both reported. "Confirmed H-FLIP" is withdrawn. |
| C7 | Cost-parity diagnostic: Tier A / Tier B cost conventions differ; closure partial. | SUPPORTED_AS_RUN | `results/cost_parity_diagnostic/` (`316464d`) | 12 rung-book pairs | Yes | Report as diagnostic; "not fully explained" stays. |
| C8 | Robustness of the Sharpe-unit capacity channel to impact coefficient and curvature (Germany, India). | SUPPORTED_WITH_QUALIFICATION | `IMPACT_K_SENSITIVITY_DEU`, `WEDGE_*_KYLE*` attachments | compliant ladder; informative columns are $100k-$3mn | Optional | Only the interpretable columns; solvency not assessed under the sensitivity cost models. Not used in the candidate's main text. |
| C9 | Value-weighting robustness of the capacity channel. | BLOCKED | `PAPER` 6.2.3, 12.3 | measured on the pre-fix universe only | **No** | Compliant re-run not done and not authorised. State the limitation only. |
| C10 | Horse-race ladder cost / capacity / tax (section 6.5). | UNVERIFIABLE | `HORSE_RACE_*` attachments are the non-compliant ladder (F2) | | No | Omit. |

### 2.4 Tax

| ID | Claim | Status | Source | Scope | Keep? | Correction |
|---|---|---|---|---|---|---|
| T1 | `lt_share_of_gains` is exactly 0.0000 under both flat statutory regimes. | SUPPORTED_AS_RUN | `SUMMARY_AFTER_TAX_{DEU_1E8, DEU_1E10, JPN_1E8, JPN_1E9, JPN_1E10}`, statutory-regime rows (verified: max abs 0.0 over 80 rows) | DEU, JPN; statute-driven structural zero | Yes | It is a statutory fact, not an estimate. In the zero-tax `tax_exempt` rows the same column is nonzero and is not the object. |
| T2 | India's `lt_share_of_gains` is 0.5928. | SUPPORTED_WITH_QUALIFICATION | untracked `outputs/summary_after_tax_IND_1e9.csv`, sha256 prefix `e2fd34229e1e8b38` (re-read today) | IND, $1bn, 8 prediction cells, statutory regime | Yes, flagged | No tracked India summary exists (F4). A tracked snapshot is required before submission. |
| T3 | Tax channel on the executable decile book (after-tax minus net Sharpe): DEU -0.070 (t -3.55), IND -0.009 (t -2.14), JPN -0.170 (t -3.67); the flat regimes are 8-19 times India's in magnitude. | SUPPORTED_WITH_QUALIFICATION | `MATCHED_BOOK_1E+09` rows `capped` (all three committed) | $1bn, capped decile composite, HIFO, accrual; the book attains few percent of target gross | Yes, as the tax-channel evidence | India is itself borderline significant (t -2.14). The ordering by statute type is the claim; "two placebos agree" is withdrawn. Turnover endogenous. |
| T4 | Optimised-book tax channel: IND -0.0054 (t -1.93, 0/8 Holm), JPN -0.1373 (t -4.99, 3/8); Germany -0.1363 (t -4.67). | SUPPORTED_WITH_QUALIFICATION for IND and JPN; **UNVERIFIABLE** for Germany | `AFTER_TAX_INFERENCE_1E9` composite rows | optimised book, $1bn | IND and JPN only | The exact match -0.1363 vs -0.1373 ("within 1%") is WITHDRAWN (a property of the optimised book). Do not quote Germany's value. |
| T5 | Drag level is ordered by turnover, not rate (JPN > DEU > IND). | UNVERIFIABLE at $1bn | Germany $1bn and India $1bn summaries untracked (F4) | n = 3, endogenous | **No** | Omit, or state as a hypothesis. |
| T6 | "Taxes are decisive/first-order for survival", "Japan goes negative after tax", "India keeps 98%". | WITHDRAWN | `PAPER` 6.3.3 | | No | Caught by the withdrawn-claims screen. |
| T7 | The 456 missing section 112A reference values cannot change the event study. | SUPPORTED_WITH_QUALIFICATION | `tests/tax/test_112a_reference_threading.py`; `IND_112A_BOUND_*_V2` attachments | Indian reform event | Optional appendix | Inference from bit-identical bounds plus unit tests; do not claim a behavioural response. |

### 2.5 Design axes

| ID | Claim | Status | Source | Scope | Keep? | Correction |
|---|---|---|---|---|---|---|
| D1 | No ML design axis is detectable at this power on the capped decile book: 0 of 42 axis-rungs significant (Holm) in each of Germany and India; uncapped book 5/42 (DEU) and 0/42 (IND). | SUPPORTED_AS_RUN (re-counted today: `p_holm < 0.05`) | `DESIGN_IDENTIFIABILITY_{DEU,IND}_2026-10-09.csv` | 14 rungs x 3 axes, DEU and IND only, decile books | Yes | "Not detectable at this power", never "no effect". Germany's uncapped 5/42 is within multiple-testing expectation (about two independent observations). |
| D2 | Minimum detectable effect 0.25-0.81 Sharpe points at 80% power with 132 months. | SUPPORTED_AS_RUN | `GATE2_POWER_1E9_2026-10-09.csv` paired SEs; 2.8 x SE re-derived (0.089 to 0.289) | optimised book, $1bn | Yes | State the formula. |
| D3 | Japan conditioning axis on the optimised book at $1bn: effect +0.515, t +2.84. | SUPPORTED_WITH_QUALIFICATION | `GATE2_POWER_1E9_2026-10-09.csv` (re-read: 0.515, t 2.838) | JPN, optimised, single AUM | Disclosed only | Exploratory, unreplicated, not pre-specified. Holm/Bonferroni p values (0.014 / 0.041) are quoted in documents; the committed table has no adjusted p, so recompute only if needed from t. Never a claim that conditioning helps. |
| D4 | "Capacity overwrites ML design identifiability." | WITHDRAWN | `PAPER` 8.6 | | No | India shows the same null unconstrained. |
| D5 | Stock-level liquidity-conditioned arm. | WITHDRAWN as a candidate (Gate 1 and Gate 2 fail) | `RESULTS_THEME_LIQUIDITY`, `RESULTS_GATE2_POWER` | | No | Not a flagship. |

### 2.6 Methods, inference and limits

| ID | Claim | Status | Source | Keep? | Correction |
|---|---|---|---|---|---|
| M1 | Frozen contract: 2x2x2x2 factorial plus five baselines, window 2009-01 to 2019-12 (132 months), prediction cells (8) only in headlines. | SUPPORTED_AS_RUN | `prereg/`, `PAPER` 5.1-5.3 | Yes | Economic-loss arm excluded (not a competent implementation, `ECONOMIC_ARM_CAPABILITY_GAP.md`). |
| M2 | Pre-registration status. | SUPPORTED_WITH_QUALIFICATION | `prereg/`, 001A-001D committed, not countersigned; 001E draft | Yes | Never describe 001E as signed or imply Maham's or Absar's approval. |
| M3 | Inference layer after the 2026-10-13 corrections (paired studentised stationary bootstrap, Holm within family, HAC). | SUPPORTED_WITH_QUALIFICATION | `INFERENCE_AUDIT_2026-10-13.md` (`26957cc`) | Yes | Intervals approximate (2-8 points under-coverage), HAC `sharpe_se` over-rejects about 10% at phi 0.4, internal validation only. Results produced before the corrections (e29 outputs) are pre-correction. |
| M4 | Exit treatment of the reported numbers. | BLOCKED | `EXIT_POLICY_*`, Phase C closeout | **Must be disclosed** | State `as_run`; `carry_v1` implemented, not run on the history, not runnable on the current data. |
| M5 | Two books and why both are needed; cost and tax measured on different books, so orders of magnitude only. | SUPPORTED_AS_RUN | `PAPER` 5.6, 6.5 | Yes | No summed decomposition. |
| M6 | Cost-input coverage asymmetry (DEU 0.652 vs IND 0.989 vs JPN 0.998) manufactured t = -6.10 that survived two robustness checks. | SUPPORTED_AS_RUN (as a worked failure; the t is retracted) | `CAPACITY_CHANNEL_INFERENCE_DEU_2026-10-09.csv` (-6.098), census v3 coverage (F5), `AMENDMENT_001D` retraction | Yes, as a methods section | Quote only as a worked failure. |
| M7 | "Test suite 464 passed". | UNVERIFIABLE as written (stale) | `PAPER` 14; last full run 667 passed at `b7b26b8` | Remove numeric counts | Tests passing is not scientific validation. |
| M8 | Revised (Phase C) analysis. | BLOCKED | Phase C closeout | Disclose | Not run; no revised number exists; no statement may imply otherwise. |

## 3. Places that still state a withdrawn or unqualified claim (full-account paper, STATUS, handoff)

These are historical records and were qualified by dated notes on 2026-10-14; they are **not** part of the submission candidate. `docs/MANUSCRIPT_EVIDENCE_MAP_2026-10-14.md` conflicts L4-L8 remain open there (L4 cost-calibration qualifier, L5 status headers, L6 design-null scope in the contribution table, L7 stale test count, L8 spec versus configuration). The candidate resolves L4, L6 and L7 by construction and treats L5 and L8 as not applicable. The full-account paper's section 14 test count (464) is stale and is superseded by the completion report.

## 4. Summary count (one row per ID; T4 is split by country)

| Status | Count | IDs |
|---|---|---|
| SUPPORTED_AS_RUN | 8 | N2, C7, T1, D1, D2, M1, M5, M6 |
| SUPPORTED_WITH_QUALIFICATION | 17 | N1, H1a, H1b, H2, H3, H4, C1, C5, C6, C8, T2, T3, T4 (IND, JPN), T7, D3, M2, M3 |
| WITHDRAWN | 7 | N3, N4, C2, C3, T6, D4, D5 (plus the exact-match sub-claim of T4) |
| BLOCKED | 4 | C4, C9, M4, M8 |
| UNVERIFIABLE | 5 | H1c, T4 (Germany), T5, C10, M7 |

## 5. Update after sprint 2 (2026-10-14, later)

| Item | Change |
|---|---|
| F4 (no tracked India or Germany $1bn summary) | Verbatim snapshots committed (`docs/attachments/SUMMARY_AFTER_TAX_{IND,DEU}_1E9_2026-10-09.csv`); contents reproduce all values the project quoted. T2 (India `lt_share` 0.5928) is now tracked and re-derived by the candidate checker: SUPPORTED_WITH_QUALIFICATION (weight identity inferred; no run-time hashes; Germany's file from an older script). |
| T5 (drag ordered by turnover at $1bn) | No longer unverifiable: turnover 0.0135 / 0.0067 / 0.0290 and tax drag 6.38 / 0.11 / 11.49 bps (Germany / India / Japan) re-derived. SUPPORTED_WITH_QUALIFICATION, descriptive only (turnover endogenous, n = 3, inferred weights). |
| F1 / H1c / T4 (Germany inference row) | Unchanged: UNVERIFIABLE. Regeneration conditions are in `docs/FINAL_NUMERICAL_TRACEABILITY_GAPS.md` (`RECOVERABLE_WITH_EXACT_REGENERATION`, conditional); not run. |
| F6 (`AHV2025` vs `AHV2023`; missing tax references) | Resolved for the candidate: same working paper, key `AHV2023`; eight tax entries added with verified metadata. Two project-record errors found (BY2003 DOI, HUANG2019 arXiv id). See `docs/FINAL_PRIOR_ART_REVIEW.md`. |
| N1 (novelty) | Narrowed: AUM indexing is not a contribution (Jensen et al.); the claim is non-US, statute-specific and constraint-based evidence, to our knowledge, on an abstract-level search for several works. The Gârleanu-Pedersen capacity attribution in the full-account paper is not supported by the text read. |
| Closest prior art (Avramov-Cheng-Metzker) | Full text not accessible; abstract level only. No detailed comparison is permitted. |

Revised counts (one row per ID, T4 split by country): SUPPORTED_AS_RUN 8; SUPPORTED_WITH_QUALIFICATION 18 (adds T5); WITHDRAWN 7; BLOCKED 4; UNVERIFIABLE 4 (H1c, T4 Germany, C10, M7).

## 6. Registration-terminology audit (2026-10-14, lockdown sprint)

Scope: `submission_candidate_as_run_only/` and the submission materials that discuss it. The historical documents (full-account paper, STATUS, handoffs) were not edited. Rule applied: a term is kept only where the cited commit or document establishes both its meaning and its timing; the project's registration documents are self-filed in the project repository, drafted by the project team on behalf of the designated statistical reviewer, not countersigned and not in an external registry, so they establish commit timing only.

| Where | Term or claim | Decision | Source and timing |
|---|---|---|---|
| Manuscript, scope note | "Pre-registration amendments are committed but not countersigned ... No claim depends on either" | **Replaced** by "no analysis reported here is presented as preregistered or confirmatory" | the amendments below; none of them specifies B(A), the tax-channel comparison on the executable book, or the design-axis ladder |
| Section 4.1 | "frozen contract" | **Kept, qualified**: parameters set in configuration; amendment 001A records them frozen before real results were inspected (self-attested, not countersigned) | `prereg/AMENDMENT_001A_international_scenario_freeze_2026-10-08.md` header (`FROZEN_PRE_RESULTS`, `REAL_RESULTS_INSPECTED_BEFORE_AMENDMENT = NO`), commit `e15695f` 2026-10-08 14:10 |
| Section 4.1 | 8 prediction cells | **Disclosed as post hoc**: PLAN_001 fixed a 16-cell grid; the exclusion followed the economic arm's observed behaviour | `prereg/PLAN_001_after_tax_attribution.json` (committed `949beac`, 2026-09-21, before any real data; N = 64); `docs/ECONOMIC_ARM_CAPABILITY_GAP.md` (`6cfff42`, 2026-10-09 02:33) |
| Section 3 | breadth cap 600 | **Kept as sourced**: stated from 001B section 2, not re-verified | `docs/AMENDMENT_001B_UNIVERSE_BREADTH_CAP.md`, commit `08590cb` 2026-10-09 01:54, "declared pre-results for the Japanese arm" |
| Section 5.2 | "Japan's positive capacity result ... prediction committed ... before any Japanese portfolio existed" | **Rewritten**: Japan was designated a held-out sample in 001C (`927e91e`, 2026-10-09 10:27; its section 5 records no Japanese portfolio existed); no scoring record for 001C's five predictions exists in the repository; on the committed $1bn summaries prediction P2 (Japan net Sharpe above Germany's +0.128) does not appear to hold (Japan +0.057); Japan is **not** presented as a confirmation. 001D's D2 (channel significantly positive at $1bn, Sharpe units, near-ruined comparator) passed; D3 passed vacuously, D4 and D5 failed; the 001D hypothesis was retracted | `docs/AMENDMENT_001C_CAPACITY_HYPOTHESIS_PREREGISTRATION.md` sections 3 and 5; `docs/AMENDMENT_001D_CAPACITY_CHANNEL_SIGN_FLIP.md` sections 4, 10, 11; commits `318c2fa` (11:54), `0e80485` (12:08, "before Japan reported"), `8dbae1b` (scorer, 12:16), `ed202c8` (result, 12:57); summaries `SUMMARY_AFTER_TAX_{DEU,JPN}_1E9` |
| Section 5.2 | B(A) | **Not pre-specified**: specification document and results arrive in one commit | `ac669f2` 2026-10-10 18:21 (`docs/CAPACITY_RETURN_DIFFERENCE_SPEC_2026-10-10.md` states results are reviewed before commit) |
| Section 5.4 | design-axis ladder | **Post hoc** (extended after earlier single-rung results) | `996ede4` 2026-10-09 13:22 |
| Section 5.4 | "exploratory, not pre-specified" for Japan's conditioning axis | **Kept**; found during an audit, single AUM | `docs/FINALIZATION_AUDIT_2026-10-09.md` section 1.3 item 2; `GATE2_POWER_1E9` |
| Section 7 item 2 | registration history | **Rewritten** with commits, self-filed status, no countersignature, no external registry; 001E unsigned draft (`4bad8e3`, 2026-10-12) | as above |
| `docs/FINAL_PUBLICATION_PATH.md`, matrix cross-cutting item 3 | "pre-registered means committed to git before the data it concerns existed" | **Superseded**: true only for PLAN_001 (a plan about a hypothesis that failed), 001B-001D as to Japan's portfolios; not true of B(A), the ladder or the tax-channel comparison | this section |

Open for the authors: formally score 001C's five predictions (P1 and P4 depend on definitions not recoverable without the original intent) and decide whether the manuscript should report that outcome; the 001C text required reporting failures with the same prominence as the failures already recorded.
