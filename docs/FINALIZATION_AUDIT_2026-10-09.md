# Research finalization and publication strategy: audit of the current state

**Date:** 2026-10-09 (late). **Branch:** `feat/workstream-b-resolver-and-prereg`, head `d4bc8aa`, 88 commits
today, working tree clean, no repository job running. **Test suite:** 464 passed, 0 failed (run for this audit).

**Scope of this document.** It audits and proposes. It changes no result, rewrites no research code, edits no
existing document and launches no experiment. Every statement about the repository was checked against files
or committed outputs this session. Journal facts come from official publisher pages as returned by search
(the pages themselves block automated fetching with HTTP 403) and are marked *verify before submission*.

---

## 1. Audit of the current research state

### 1.1 What the repository establishes

| Claim | Where it stands | Evidence (committed) |
|---|---|---|
| Net-of-cost Sharpe of the optimised ML book is not distinguishable from zero at $1bn in all three markets | **Established** | t = +0.53 DEU, +0.82 IND, +0.18 JPN (`exp_after_tax_inference.py`) |
| The executable capped decile book has a significantly negative net Sharpe in DEU and JPN | **Established, with a caveat** | t = −2.29 / −1.80 / −2.56 at $1bn; that book attains only ~3% of target gross, so it is a ratio of small numbers |
| Gross decile signals are real | **Established** | gross SR +2.31 / +1.20 / +1.28, t = +7.14 / +3.19 / +4.11 |
| A binding ADV participation cap improves net risk-adjusted performance, monotonically in how hard it binds, zero where slack | **Established on solvent rungs** | matched-book accounting: +6.80 (DEU $100mn), +3.19 (IND $30mn), +6.92 (JPN $1bn); Japan pre-registered confirmation (D2) |
| Statute determines whether a holding-period channel can exist (`lt_share` = 0.0000 under both flat regimes, 0.5928 India) | **Established** (a statutory fact, no estimation) | stage 06 outputs, three countries |
| Tax-channel magnitude is ordered by statute type (flat regimes 8–19× India on the decile book) | **Descriptive** | matched-book: DEU −0.070/−0.098, JPN −0.170, IND −0.005/−0.009 |
| Tax drag level is ordered by turnover, not rate | **Descriptive** (turnover is endogenous, n = 3) | JPN > DEU > IND on both |
| Implementability frontier $106mn / $55mn / $413mn | **Descriptive**, not comparable with break-even capacities in the literature | `capacity_frontier.csv` |
| ML design axes are undetectable at this power | **Established as "not detectable", with a reach caveat (see 1.3)** | MDE table in 1.4 |
| Cost-input coverage asymmetry manufactures false cross-country positives | **Established as one worked case** | the retracted t = −6.10 |

### 1.2 Withdrawn or superseded (must not return)

| Withdrawn | Why | Where recorded |
|---|---|---|
| Capacity sign flip, crossover $3.79mn, t = −6.10 | Cost-input coverage artefact (DEU 65.1% vs 99%) | `AMENDMENT_001D` retraction header, `RESULTS_SIGN_FLIP` |
| `crossover ∝ k⁻²` "confirmation" | Property of the artefact | `RESULTS_CAPACITY_CHANNEL` §3f |
| "India has no crossover", "flip survives value-weighting" | Artefacts of the same defect / point-estimate reading | superseded |
| German/Indian **$1bn and $10bn** capacity gains (+8.92/+9.26, +5.69/+5.97) | Differences against an **insolvent** uncapped book | `PAPER` §8.8 |
| "Asymptotic channel" and the 4.58/4.82 cross-market regularity | Sharpe saturation, not an economic limit | `PAPER` §8.8 |
| "Taxes are first-order for survival", "Japan goes negative after tax" | No country's net Sharpe is distinguishable from zero | `RESULTS_TAX_THREE_COUNTRY` §4b |
| Tax placebo "match within 1%" (−0.1363 vs −0.1373) | Property of the optimised book; −0.070 vs −0.170 on the decile book | `PAPER` §8.9 |
| "Frontiers 10–100× below US estimates" | Not turnover-matched (NMV high-turnover US: $0.18–0.53bn) | tracker §C8.1 |
| "Cost beats tax 5× / 53×" | All-16-cell averages including the broken economic arm; prediction cells 2.70× / 87.4× | `PAPER` §8.4 |
| Wedge dose-response statistic; `lt_share` gradient t = −4.36 | Ill-defined; two-cluster artefact | `RESULTS_WEDGE_TEST` |
| "Capacity overwrites ML design identifiability" | India shows the same null unconstrained | `PAPER` §8.6 |
| "Absar's 456 §112A values block the result" | Engine unit-tested; none of the 456 is a binding gain | handoff 20 |
| "H-FLIP CONFIRMED" (Japan scorecard) | D3 passed vacuously on −0.0013, p = 0.370 | `AMENDMENT_001D` §11 |
| Stock-level liquidity arm as a flagship candidate | Gate 1 (mostly a size effect) and Gate 2 (power) both fail | `RESULTS_THEME_LIQUIDITY`, `RESULTS_GATE2_POWER` |

### 1.3 Problems found by this audit

These are findings, not fixes. None has been changed.

1. **Live documents still state withdrawn numbers.** A search of `docs/` for the withdrawn figures found
   them presented as current, outside retraction sections, in:
   * `STATUS.md` (top block): `+8.922 / +5.693` as the surviving claim, and a block headed *"first-order for
     SURVIVAL … Japan goes negative"*;
   * `PAPER_2026-10-09_FULL_ACCOUNT.md`: the §6.2.1 table row `$1bn +8.922 / +5.693`, the §6.2.4
     curvature table (`+8.922` at $1bn), and the §6.5 horse-race table (`+8.92 / +5.69`), none flagged
     insolvent at the point of use, although §8.8 corrects them later in the same file; and the §8.7
     heading still reads *"still unresolved"* above text saying it is resolved;
   * `RESULTS_CAPACITY_CHANNEL_2026-10-09.md`: the §1 claim and the §3 tables, written before the
     solvency finding;
   * `handoff/21`: quotes the pre-correction figures to the person asked to sign off.
   Older context documents (`CAPACITY_CONSTRAINT_DEU`, `PRACTITIONER_GAP`, `CANDIDATE_REFRAMING_CAPACITY`)
   predate today's corrections and carry the old cost-over-tax ratios. **A reviewer reading any of these
   would meet a withdrawn number as a live one.**
2. **A claim in the abstract overreaches.** The paper says no design axis is detectable "on an executable
   book at any mandate size (0 of 42 in each of two markets)". That was measured on the **capped decile
   book in Germany and India**. On the **optimised** book at $1bn (`gate2_power.py`), **Japan's conditioning
   axis is t = +2.84 (effect +0.515)**, never reported. It is exploratory and unreplicated (p = 0.0045; ×3
   Holm within country 0.014; ×9 Bonferroni 0.041) and the other eight axis-tests are not significant, so it
   changes nothing established, but the sentence must name the book and market and the observation must be
   disclosed.
3. **The capacity channel is partly an accounting identity.** It is the Sharpe difference between a capped
   book and an uncapped book, and the uncapped book is infeasible at institutional scale (insolvent in DEU
   and IND at $1bn). A referee can say the "channel" measures how impossible the naive portfolio is. The
   defensible value is the **dose-response in how hard the cap binds** and the **solvent-rung** magnitudes,
   not a headline Sharpe gain. A unit that stays finite (cost avoided as a share of gross alpha) is not yet
   built.
4. **Two cost-accounting codes disagree on the uncapped book.** The wedge tool and the pipeline agree to
   ~5e−4 per month on capped books but differ by up to 0.27 per month on uncapped books (the pipeline
   compounds NAV and charges drifted positions). Matched-book figures supersede the wedge-tool ones and the
   difference moved the capacity channel by 3–11%. Any table still built on the wedge tool's uncapped
   series should say so.
5. **Several tools write to fixed shared paths**, the hazard that bit the source index and stage 06 earlier:
   `exp_design_identifiability.py` (`design_identifiability_all.csv`), `exp_friction_horse_race.py`
   (`horse_race_decile_panel.csv`, `horse_race_tax_panel.csv`), `exp_112a_event_study.py` (default `--out`),
   `exp_wedge_test.py`, `exp_tals_overhang.py`, `pipelines/07_adaptive_combine.py`. Concurrent or
   subset runs overwrite each other silently.
6. **Robustness checks are uneven across markets.** The impact-coefficient sweep, the Kyle-curvature
   check and the sub-$100k ladder were run for Germany (curvature also India), not Japan. Value-weighting
   was run on the **pre-fix** universe only (open item 12.3 in `PAPER_2026-10-09_FULL_ACCOUNT.md`) and
   must not be quoted until re-run compliant.
7. **No figures exist.** All results are markdown tables and attached CSVs.
8. **Outputs are gitignored.** Every table is reproducible only because its CSV was copied into
   `docs/attachments/`; a clean checkout cannot regenerate `outputs/` without the data contracts.
9. **Literature facts needing correction in earlier summaries.** Nechvátalová (2025) is in *International
   Review of Financial Analysis*, vol. 107, art. 104642. Jiang et al. (2024) "Global Mispricing Matters" is in
   the *Journal of International Money and Finance* and is about aggregate return prediction. Jensen–Kelly–
   Malamud–Pedersen is listed by the Swiss Finance Institute as RFS "in press" dated 20 May 2026 (earlier
   notes quoted a March online date): cite as RFS (2026) and verify the final citation.

### 1.4 Design-axis detectability (derived from the committed Gate 2 table; no new run)

Paired HAC standard errors of a Sharpe difference between two 4-cell composites, optimised book, $1bn:

| | representation | conditioning | uncertainty |
|---|---|---|---|
| Germany | 0.289 | 0.152 | 0.089 |
| India | 0.279 | 0.285 | 0.101 |
| Japan | 0.249 | 0.182 | 0.092 |

Minimum detectable effect at 80% power, 132 months: **0.25 to 0.81 Sharpe points** across axes and
markets (0.25–0.28 for the uncertainty axis, 0.43–0.80 for conditioning, 0.70–0.81 for representation).
At 72 months multiply by 1.35. So the design-axis null excludes only effects larger than roughly a quarter of
a Sharpe point (uncertainty) to four-fifths of a point (representation). That is the honest scope of the null.

---

## 2. The paper's contribution, stated with its limits

### 2.1 Statement

> We measure, on identical signals and a common investable universe, how much of a machine-learning equity
> signal's return survives three implementation frictions (AUM-indexed trading costs, an ADV participation
> constraint, and jurisdiction-specific capital-gains tax) in Germany, India and Japan over 2009–2019, using a
> dated lot-level tax engine. At a $1bn mandate the net-of-cost Sharpe ratio of the optimised book is not
> distinguishable from zero in any of the three markets. The participation constraint's effect on net
> performance is zero where it is slack and grows monotonically with how hard it binds, which Japan confirms
> out of sample against a pre-registered prediction. The tax channel is small relative to cost and capacity,
> is ordered by statute type rather than by rate, and is mechanically absent from the holding-period
> dimension under flat-rate regimes. We document a cost-input coverage asymmetry that produced a highly
> significant but spurious cross-country result, and the verification checks that catch it.

### 2.2 What it does **not** claim

* Not a new mechanism, not a profitable strategy, and not a causal tax effect.
* Not that taxes decide viability (no book is significantly viable before tax).
* Not an adjudication of Novy-Marx–Velikov versus Azevedo–Hoegner–Velikov: **we never observe the regime in
  which the constraint hurts**.
* Not that non-US markets are shallower, or that ML design does not matter (only that it is undetectable at
  the stated power).

### 2.3 Novelty against the literature (abstract-level for several rows; full text not read)

| Prior work | What it already owns | What remains for us |
|---|---|---|
| Jensen, Kelly, Malamud & Pedersen (RFS 2026) | Cost-aware ML portfolio choice, AUM-dependent costs, the implementable efficient frontier, economic feature importance; evaluated to a hypothetical $10bn, US, 1981–2020 | **Nothing on the method.** Our contribution cannot be "ML plus AUM-dependent costs". We do not benchmark against their method (blocked on the economic arm) |
| Avramov, Cheng & Metzker (MS 2023) | ML alpha concentrates in hard-to-trade stocks and falls under frictions | Our null corroborates it in three non-US markets; it does not extend it |
| Novy-Marx & Velikov (RFS 2016); Korajczyk & Sadka (JF 2004) | Capacity under price impact; buy/hold and liquidity-weighting mitigation; US | We add an AUM-indexed curve in non-US markets, the cap-slack characterisation, and the implementability frontier as a distinct object |
| Azevedo, Hoegner & Velikov | ML net of effective spreads, no AUM term | Our results are silent on the regime they occupy |
| Cakici et al. (JEDC 2023) | International ML predictability, 46 markets | "Non-US" is not a contribution; the friction measurement is |
| Nechvátalová (IRFA 2025) | International evidence that liquidity restrictions cut profitability by 60–85% and only liquid strategies survive costs | Closest on the liquidity point; our theme-by-liquidity diagnostic is weaker and largely a size effect |
| Dai, Lei, Liu & Yang (MS 2026); Moehle, Kochenderfer, Boyd & Ang (JOTA 2021) | Capital-gains tax with transaction costs; tax-lot-aware convex construction | A tax-aware optimiser is a tool, not a contribution; our tax contribution is empirical and statute-specific |
| Chen & Velikov (JFQA 2023); Lalwani et al. (EFM) | Net anomaly returns; design dispersion with 1,056–5,376 specifications | Our design null has 8 cells and is a bound, not a rival |

**What is left that is ours, and is not merely combination:** (i) a like-for-like three-friction accounting
on one book across three statutory regimes (we know of no paper that does this, but the search was not
exhaustive); (ii) the solvency/cap-slack characterisation of the capacity effect; (iii) the exact statutory
contrast in the holding-period channel confirmed on two independent flat-rate jurisdictions; (iv) the
documented coverage-asymmetry failure and verification protocol. The honest weakness is that (i)–(iii) are
measurement and (iv) is methodology; none overturns a published result.

---

## 3. Task audit and submission-readiness checklist

Status was verified against files and commits, not earlier plans. P0 = no external dependency.

| ID | Task | Verified status | Depends on | Deliverable | Acceptance criterion |
|---|---|---|---|---|---|
| **P0-1** | Consistency pass on live documents (§1.3.1–1.3.2) | **Not done** | none | Corrected `STATUS`, `PAPER`, `RESULTS_CAPACITY_CHANNEL`, handoff 21; a changelog | `grep` finds no withdrawn figure outside a labelled retraction; abstract names book and market for the design null |
| **P0-2** | Restate the capacity channel in a unit that survives an insolvent comparison book | **Not done** | none | Cost avoided as a share of gross alpha, by AUM and market, with inference | Finite and monotone across all rungs including insolvent ones; matches matched-book figures on solvent rungs |
| **P0-3** | Re-run value-weighting on the compliant universe | **Not done** (only pre-fix figures exist) | none; needs approval as a re-run | Compliant VW ladder, 3 markets | Same inference table as the equal-weighted ladder |
| **P0-4** | Borrow-fee sensitivity for the capacity channel | **Not done** | none; needs approval | Sweep over the configured rates 0.3%–7% | Channel stays positive and monotone, or the band is reported |
| **P0-5** | Extend robustness (impact `k`, Kyle curvature, sub-$100k) to Japan and India | **Partial** (Germany; curvature also India) | none; needs approval | Same tables for all three | Parity of the robustness table across markets |
| **P0-6** | Fix fixed-path writers (§1.3.5) | **Not done** | none | Per-country/tag filenames | Two concurrent runs cannot collide; test added |
| **P0-7** | Figures | **Not started** | P0-2 | Ladder, cap-slack, tax-by-statute, MDE figures | Each plotted from a committed CSV by a script in the repo |
| **P0-8** | Japan (and India) scale analysis | **Mostly done for Japan**: decile ladder (14 rungs) and inference; optimised-book tax ladder (3 rungs); matched-book at $1bn. **Open:** the optimised-book capacity dose-response (`corr(\|w\|, adv_cap)`, alpha tilt) exists for **Germany only**; `realised_books_JPN.csv` and `realised_books_IND.csv` are empty 2-byte stubs from before those countries had portfolios; matched-book is missing at other Japanese rungs | none; needs approval (existing tools) | Book characteristics at 1e8/1e9/1e10 for Japan and India | The optimised-book mechanism evidence is replicated in a second and third market |
| **P0-9** | Disclose and, if desired, formally test the Japan conditioning observation | **Observation found, not reported** | none | A paragraph and a pre-registered replication on the extension | Labelled exploratory until replicated untouched |
| **P1-1** | Maham: countersign 001A–001D (001D as retracted) | **Blocked on her** | Maham | Signed amendments | Countersignatures committed |
| **P1-2** | Maham: ruling on the economic-loss arm | **Blocked on her** | Maham | Debug or flag decision | Documented ruling |
| **P1-3** | Maham: sign-off on `sharpe_difference_test` (annualisation), Holm vs max-statistic bootstrap, studentised vs percentile | **Blocked on her** | Maham | Review note | Findings resolved or accepted |
| **P1-4** | Benchmark against Jensen–Kelly–Malamud–Pedersen | **Not started** | P1-2, their specification | A cost-aware ML benchmark on the same universe | Compared on identical dates and constraints |
| **P2-1** | 2020–2025 extension | **Requested from Absar** (per the team); status unknown | Absar | Panels under the existing contracts | Point-in-time correct, coverage ≥ the 2009–2019 panels, cost inputs certified |
| **P2-2** | Untouched out-of-sample evaluation | **Not started** | P2-1, new pre-registration amendment (001E) | A single frozen evaluation | Protocol and thresholds committed before the data are touched; run once |
| **P2-3** | §112A post-reform analysis | **Not started**; current sample has `n_post_years` = 1 and interaction t = −0.68 | P2-1 | Descriptive statutory counterfactual only | Reported as a mechanical counterfactual, never as a behavioural or causal effect |
| **P2-4** | US benchmark panel | **Optional ask outstanding** (handoff 22) | Absar | CRSP/Compustat through the same pipeline | Method validation against published ordering |
| **P3-1** | Read in full text: ACM2023, JKMP final, Nechvátalová, Dai et al., Moehle et al. | **Not done** (abstract-level) | none | Updated tracker | Differentiation checked against claims, not abstracts |
| **P3-2** | Manuscript | **Not started** | P0-1 … P0-7, P1-3 | Draft following §6 | Every number traceable to a committed CSV |

Critical path: **P0-1 → P0-2 → P0-7 → manuscript**, with **P1-3** and **P2-1/P2-2** running in parallel. Nothing
on the critical path needs a new model to be trained.

**Note on the 2020 data.** The bundles already contain targets through 2020-12-31. The frozen window is
2009–2019, so the frozen evaluation pipeline does not use those 12 months. I have not audited whether
earlier descriptive diagnostics (for example the E02/E03 signal-quality tables) touched them, and the
repository cannot certify that nobody has looked at them, so whether they count as untouched must be
established and declared in 001E and not assumed.

---

## 4. Journals and recommended order

Scope and requirements below are from the publishers' official pages as surfaced by search, not fetched
directly (HTTP 403). **Verify each before submitting.** No acceptance probabilities or rankings are
asserted; a paper can only be sent to one journal at a time.

| | Official scope (paraphrased) | Review and process facts | Fit with this paper |
|---|---|---|---|
| ***Quantitative Finance*** (Taylor & Francis) | Theoretical and empirical interdisciplinary work on quantitative methods of finance; listed areas include portfolio management, market microstructure, financial econometrics, behavioural finance; readership of researchers *and* practitioners | Editor screening then two anonymous referees; aims at a first decision within six months; hybrid open access | **Good.** Portfolio construction, costs and capacity are named areas; an implementation-focused empirical paper is in scope. Slowest first decision |
| ***Journal of Empirical Finance*** (Elsevier) | High-quality empirical finance; financial economics and econometrics; asset pricing, international finance, microstructure and others | Double anonymised; per the guide, about 85% of submissions rejected, 40% by the editors without review; common desk-reject reasons include topic too narrow and analysis below standard; submission fee, non-refundable, kept on desk rejection; 27-day median to first decision per the insights page; abstract ≤ 250 words, highlights required, generative-AI declaration | **Good topic fit, high bar.** International empirical asset pricing is core. Main risk is a desk rejection for incremental contribution, and the fee is lost |
| ***J. International Financial Markets, Institutions & Money*** (Elsevier) | Theoretical and empirical work on international financial markets, institutions and money; listed topics include international securities markets, foreign exchange, international banking | Double anonymised; open access with a listed APC | **Moderate.** "International securities markets" is listed, but the topic list is weighted to FX, banking and monetary topics; the paper would need an "international evidence" framing |
| ***Review of Asset Pricing Studies*** (SFS / OUP) | Asset pricing broadly: empirical methodology, liquidity and information in asset markets, microstructure, institutions as they relate to prices; substantive original contribution | Double-blind; exclusive submission | **Stretch.** Only defensible if the untouched 2020–2025 test and a JKMP benchmark produce something that is more than confirmation |

### 4.1 Recommended order and reasoning

1. **First: *Journal of Empirical Finance*** — if and only if P0-1…P0-7 and P1-3 are complete. It has the best
   scope match (empirical, international, asset pricing and implementation) and a fast first decision, which
   keeps the sequence short. The cost is a non-refundable fee and a stated high rejection rate, so submit a
   finished paper, not a draft.
2. **Second: *Quantitative Finance*.** The portfolio-management and microstructure scope fits an
   implementation paper, and it is the natural destination if JEF rejects on "topic" rather than on quality.
   Allow for the six-month first-decision target.
3. **Third: *JIFMIM*.** A fallback with an explicit international framing.
4. **RAPS: not a default.** Reconsider only if the untouched evaluation and the JKMP benchmark change the
   contribution from measurement to mechanism. The contribution as it stands corroborates Avramov et al.
   and Novy-Marx–Velikov, and the RFS 2026 paper has raised the bar on the method.

This reverses the earlier internal ordering (JFQA primary), which was set before several results were
withdrawn; the user's journal list supersedes it. Recommend asking Maham for an independent view on the order.

---

## 5. Claims, analyses and experiments that must remain excluded

**Claims:** everything in §1.2, plus any wording that says taxes "decide" viability, that the cap "creates"
performance without the words "against an infeasible comparison", that the design null covers the optimised
book or Japan, or that §112A shows a behavioural response.

**Analyses to keep out of the main text:** Sharpe-point capacity gains on insolvent rungs; the asymptotic
channel; the wedge-tool uncapped series where a matched-book figure exists; value-weighted figures from the
pre-fix universe; the signal-bearing-universe ladder in any form except as the documented counter-example.

**Experiments not to run without explicit approval:** training the stock-level liquidity arm; a tax-aware
optimiser as a thesis (its ceiling is the cost gap, and a 30% recovery is ≈ t = 1); cross-market transfer
training (≈ 10 hours of compute, Gate 2 shows it could not be detected); any change to the frozen cost
contract, the 600-name cap or the evaluation window to improve a result; revisiting the economic-loss arm
before Maham rules.

---

## 6. Proposed manuscript outline (aligned with the evidence)

**Working title:** *Where does machine-learning equity alpha go? Costs, capacity and capital-gains tax in
Germany, India and Japan* (a title that promises a measurement, not a mechanism).

1. **Introduction.** The question; the framing fact (net Sharpe ≈ 0 at $1bn in all three markets); the four
   findings; what we do not claim; relation to JKMP, Avramov et al., Novy-Marx–Velikov.
2. **Related work.** Capacity and price impact; ML net of costs; international ML; tax-aware construction.
3. **Data and institutional detail.** Panels, the 168 signals, the investable universe and cost-input
   coverage, the three statutory regimes, the dated engine and §112A.
4. **Framework.** Three books (uncapped decile, capped decile, optimised); the cost model; the participation
   cap; **solvency** and the matched-book accounting; inference (paired Sharpe test, Holm, HAC).
5. **Results.** 5.1 Signal to executable portfolio (the wedge, with inference). 5.2 Capacity: dose-response
   in cap slack, solvent-rung magnitudes, Japan confirmation. 5.3 Tax: the statutory contrast, ordering by
   statute type and by turnover, scale behaviour. 5.4 Design axes with minimum detectable effects.
6. **Robustness.** Weighting, impact `k`, Kyle curvature, coverage, borrow fees, multiple testing.
7. **Verification and a cautionary case.** The coverage-asymmetry false positive and the checks that caught it,
   as a short methods section, not a thesis.
8. **Untouched out-of-sample evaluation** (if P2-2 completes).
9. **Limitations.** Low power (8 cells, 132 months); capacity channel measured against an infeasible
   benchmark; turnover endogeneity; n = 3 jurisdictions; borrow fee modelled; economic arm excluded; no
   causal tax claim.
10. **Conclusion.**

**Figures:** (F1) cost, capacity and tax channels on one book against AUM, solvent rungs marked, three
panels; (F2) capacity channel against cap slack, all markets on one axis; (F3) tax channel and `lt_share` by
statute with confidence intervals; (F4) design-axis effects with the minimum-detectable-effect band.
**Tables:** T1 data and regimes; T2 the one-book ladder; T3 inference; T4 robustness grid; T5 excluded/withdrawn
claims in an online appendix.

---

## 7. Proposed next steps for review

In priority order, none started: **(1)** approve P0-1 (consistency pass), because it removes the single
largest risk of a withdrawn number reaching a reader; **(2)** approve P0-2 (the finite capacity unit) and
P0-7 (figures); **(3)** send Maham the P1 items as one package, including the Japan conditioning observation;
**(4)** hold all P2 work until Absar's data arrives and 001E is written and committed; **(5)** decide whether
the optional US panel is worth his time. Items P0-3 to P0-5 and P0-8 are re-runs or extensions of
already-defined analyses and need approval before they are launched.
