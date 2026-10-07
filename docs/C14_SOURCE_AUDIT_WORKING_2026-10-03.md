# C14 Historical Tax & Statutory-Charge Source Audit — WORKING

**Date:** 2026-10-03  
**Status:** NON-PRODUCTION / SOURCE AUDIT  
**Scope:** Germany (DEU), Japan (JPN), India (IND), taxable resident individual baseline unless otherwise stated.  
**Purpose:** Reconstruct dated statutory tax/charge regimes for the international identification design without projecting current law backward.

## Executive finding

The original shorthand “Germany or Japan = flat-rate country with no holding-period boundary” is too coarse for the full 1990-2020 sample.

Germany is definitely **not** a full-sample flat-rate placebo:
- through assessment year 1998, private securities gains were taxable when acquisition-to-sale was no more than **six months**;
- from 1999, the period became **one year**;
- the old private-sale regime applies to securities acquired before 1 January 2009;
- from 2009, Germany moved to the 25% Abgeltungsteuer framework, including capital gains, with the speculation-period concept removed for newly acquired securities.

Japan requires a more careful distinction between *proposals* and *enacted law*. The 2001 reform proposal included a 10% special rate for listed-stock gains held more than one year in 2003-2005. However, the enacted 2003 reform subsequently introduced a **7% national rate (10% including local tax) for listed-stock gains generally from 1 January 2003 through 31 December 2007**, and abolished the special treatments displaced by that broader concession. Later measures prolonged reduced listed-share taxation, and Ministry of Finance historical material shows 10% through 2013 and 20% from 2014. Therefore the earlier 2001 proposal must NOT be coded as an effective 2003-2005 holding-period wedge without checking the later enacted law.

The research design should therefore use **dated country × regime states**, not a timeless country label.

---

## 1. Germany

### 1990-1998 — six-month private-sale boundary

Primary evidence: German Bundestag report (Drucksache 14/8863).

The report states that, through assessment year 1998, gains on privately held securities were taxable as speculative transactions where acquisition-to-disposal was no more than six months. It also states that losses were confined to speculative gains of the same calendar year under the cited old regime.

**Candidate coding**
- `holding_period_months = 6`
- `cgt_short = unresolved_personal_marginal_rate` rather than a fabricated constant
- `cgt_long = 0` for ordinary private listed-share gains outside the speculation period, subject to historical scope/threshold rules
- annual de-minimis threshold / exact personal-rate assumption: still to freeze
- source status: PRIMARY VERIFIED for the boundary, rate value still unresolved for the paper’s representative-investor calibration

### 1999-2008 — one-year private-sale boundary

The same Bundestag report states that from assessment year 1999 the speculation period became one year.

BMF guidance confirms the old §23 securities regime applies lastly to securities acquired before 1 January 2009.

**Candidate coding**
- `holding_period_months = 12`
- `cgt_short = unresolved_personal_marginal_rate`
- `cgt_long = 0` outside the period for ordinary private gains under the old regime, subject to transition/scope rules
- loss treatment changed in 1999; exact carry-forward mechanics still to encode

### 2009-2020 — Abgeltungsteuer

BMF material states that from 2009:
- private dividends, interest and capital gains are brought into the capital-income tax framework;
- the separate rate is 25%;
- the former speculation period is removed for this regime;
- the solidarity surcharge is imposed on the tax where applicable.

For a representative high-income investor with no church tax, the mechanical combined rate is:
`0.25 * (1 + 0.055) = 0.26375`
before any investor-specific exceptions.

**Candidate coding**
- `holding_period_months = null`
- `cgt_short = cgt_long = 0.26375` for the high-income/no-church-tax calibration
- preserve `0.25` as the statutory base tax and `5.5% of tax` as a separate source component in provenance
- pre-2009 acquisition grandfathering/transition must remain explicit

### Identification consequence

Germany is a clean *rate-flat* placebo only from the 2009 regime onward for newly acquired ordinary listed shares. Treating Germany as flat over 1990-2008 would invert the historical legal architecture.

---

## 2. Japan

### Pre-2003

The Ministry of Finance’s 2001 reform outline describes:
- a then-current 26% capital-gains rate under the tax-return route (20% national + 6% local);
- abolition of the alternative separate taxation at source by end-2002;
- a planned 20% general rate from 2003;
- a planned three-year capital-loss carryover from 2003;
- special long-term provisions then in existence/planned.

This period is therefore not yet simple enough for a one-row “flat 26%” production encoding: the source-withholding alternative and long-term exemption rules must be reconstructed first.

**Candidate coding**
- 1990-2002: `status = unresolved_complex_pre2003`
- do not infer `holding_period_months = null` merely from the headline 26% rate
- no production row until the alternative-source-tax and long-term special-treatment mechanics are verified

### 2003-2007 — enacted broad reduced listed-share rate

The 2003 MOF enacted-law outline is the controlling source, not the earlier 2001 proposal.

It states that listed-stock gains realized from 1 January 2003 through 31 December 2007 receive a 7% national income-tax rate. MOF’s accompanying overview describes the combined national + local preferential rate as 10%.

Crucially, the enacted-law outline also states that the broader concession replaces/abolishes the superseded special treatments. This means the 2001 proposal’s >1-year 10% special rate must not be coded as a separate effective wedge after the broader 2003 reform.

**Candidate coding**
- `holding_period_months = null` for the general listed-share rate
- `cgt_short = cgt_long = 0.10` combined national/local headline rate
- carry-forward: three years, subject to the listed-share loss-offset rules
- exact treatment of exceptional/emergency exemptions remains a robustness/provenance issue

### 2008-2013 — reduced-rate extensions

MOF historical tax material reports listed-share capital-gains tax at 10% in each year 2008-2013. Legislative materials show the reduced-rate regime was repeatedly extended.

There were threshold/transition provisions in some years, so a single 10% production row should be treated as a **headline-rate candidate** until those thresholds are fully encoded.

**Candidate coding**
- `holding_period_months = null`
- headline `cgt_short = cgt_long = 0.10`
- status: `PRIMARY_MOF_HEADLINE_VERIFIED_THRESHOLD_NUANCE_OPEN`

### 2014-2020 — normal 20% rate plus reconstruction surtax

MOF historical data show the listed-share capital-gains rate rising from 10% in 2013 to 20% in 2014.

The Special Income Tax for Reconstruction adds 2.1% of the national income-tax component. Under a 15% national + 5% local structure this yields:
- national income tax 15%
- reconstruction special income tax 0.315%
- local tax 5%
- total 20.315%

**Candidate coding**
- `holding_period_months = null`
- `cgt_short = cgt_long = 0.20315`
- loss carry-forward generally three years for listed-share losses, subject to filing/offset requirements

### Identification consequence

Japan looks much closer to the intended rate-flat placebo from 2003 onward than the earlier 2001 proposal alone suggested. The design must cite enacted 2003 legislation and must not treat superseded proposals as law. Pre-2003 remains unresolved enough that it should not yet be called a clean placebo.

---

## 3. India

### Pre-October 2004 baseline

The official 2004 Finance Bill memorandum describes the pre-reform system:
- short-term securities gains taxed at applicable ordinary rates for ordinary investors;
- long-term gains generally 20% with indexation;
- for listed securities, option for 10% without indexation;
- FIIs had separate 30% short-term / 10% long-term rules.

For the paper’s taxable-resident-individual baseline, we must choose and document a representative marginal tax rate rather than silently use the FII schedule.

India already had a 12-month listed-equity holding-period classification.

### 1 March 2003 temporary listed-equity exemption

The 2003 Budget introduced a temporary exemption for qualifying listed equities acquired on/after 1 March 2003 and sold after at least one year. The enacted Section 10(36) scope was narrower than a universal all-listed-equity rule (e.g. BSE-500 / specified public-issue conditions).

Do not flatten this temporary transition into the later STT-era regime.

### From 1 October 2004 — STT / Section 111A architecture

Official Budget 2004 materials:
- long-term gains on qualifying securities transactions moved to exemption under the STT-linked regime;
- short-term gains moved to a flat 10%;
- STT became effective 1 October 2004;
- delivery-based equity STT was 0.15% total, split equally between buyer and seller under the implemented rate structure (0.075% each side).

**Candidate coding**
- `holding_period_months = 12`
- `cgt_short = 0.10`
- `cgt_long = 0`
- `stt_buy = stt_sell = 0.00075` for the initial delivery-equity rate
- exact later STT rate changes must be dated, not backfilled

### From assessment year 2009-10 — STCG 15%

Finance Act 2008 raised Section 111A short-term capital-gains tax from 10% to 15%, effective 1 April 2009 for the tax-year implementation described in official materials.

**Candidate coding**
- `cgt_short = 0.15`
- `cgt_long = 0` while Section 10(38) exemption remains applicable
- `holding_period_months = 12`

### From 1 April 2018 / FY 2018-19 — Section 112A

Budget 2018 reintroduced tax on qualifying listed-equity LTCG:
- 10% on gains exceeding ₹100,000;
- grandfathering for gains accrued through 31 January 2018;
- STCG under §111A remains 15%.

**Candidate coding**
- `cgt_short = 0.15`
- `cgt_long = 0.10`
- `holding_period_months = 12`
- `annual_exempt_local = 100000` for the §112A LTCG threshold
- preserve grandfathering in provenance; a scalar annual exemption alone is not enough to reproduce transition-lot tax exactly

### Identification consequence

India remains the clearest country in the sample with a persistent holding-period tax wedge plus STT, but the wedge magnitude is regime-dependent:
- 2004-2008: 10 percentage points versus exempt LTCG;
- 2009-2017: 15 percentage points versus exempt LTCG;
- 2018-2020: 5 percentage points before exemption/grandfathering effects.

The old handoff’s constant 7.5-point India wedge belongs to a later/current tax configuration and must not be projected backward through 1990-2020.

---

## 4. C14 schema policy

The existing requested contract fields remain:
`country, effective_from, effective_to, stt_buy, stt_sell, brokerage, gst_on_brokerage, exchange_fee, regulator_fee, platform_fee_annual, cgt_short, cgt_long, holding_period_months, dividend_rate, annual_exempt_local, loss_carryforward_years, losses_ring_fenced, ordinary_income_offset`

Working audit rows additionally need:
- `legal_regime`
- `investor_scope`
- `source_status`
- `primary_source`
- `notes`

Blank means **not yet verified**, never zero.

Rates are stored as fractions in the candidate CSV.

---

## 5. Immediate consequences for the empirical design

1. Do not encode a permanent `flat_country` dummy.
2. Build a dated `tax_regime` / `holding_wedge_t` object from C14.
3. For the cleanest statutory placebo comparison, **post-2009 Germany** is the strongest currently verified segment.
4. Japan is promising as a rate-flat comparator from 2003 onward, but pre-2003 needs more legal reconstruction and 2008-2013 threshold/transition details need explicit treatment.
5. India should be regime-dated, not assigned one constant wedge.
6. The theory object `Delta = theta_short - theta_long` should be generated from dated C14 rows at each realization date.
7. Keep the full historical sample for prediction/cost analysis even if the clean tax-identification sub-sample is narrower.

---

## 6. Primary source register

Germany:
- Deutscher Bundestag, Drucksache 14/8863, historical private-securities speculation-period rules:
  https://dserver.bundestag.de/btd/14/088/1408863.pdf
- BMF, Einzelfragen zur Abgeltungsteuer, old §23 regime / pre-2009 acquisitions:
  https://lsth.bundesfinanzministerium.de/esth/2023/C-Anhaenge/Anhang-19/II/anhang-19-II.html
- BMF, Steuern von A bis Z / Abgeltungsteuer overview:
  https://www.bundesfinanzministerium.de/Content/DE/Downloads/Broschueren_Bestellservice/steuern-von-a-z.pdf
- BMF tax-policy data collection, 25% from 2009 and solidarity surcharge:
  https://www.bundesfinanzministerium.de/Content/DE/Downloads/Broschueren_Bestellservice/datensammlung-zur-steuerpolitik-2026.pdf

Japan:
- MOF, 2001 proposed reform (historical proposal, not sufficient alone for enacted 2003 coding):
  https://www.mof.go.jp/english/policy/tax_policy/others/011030a.htm
- MOF, 2003 enacted tax-law outline, broad listed-stock reduced rate:
  https://www.mof.go.jp/about_mof/bills/156diet/st150204y_b.htm
- MOF historical tax-rate evidence, 10% through 2013 / 20% from 2014:
  https://www.mof.go.jp/english/pri/publication/pp_review/ppr21_2_04.pdf
- MOF/NTA reconstruction special income-tax component (20.315% framework):
  https://www.mof.go.jp/faq/jgbs/04ca.htm

India:
- Union Budget 2003-04, temporary LTCG proposal:
  https://www.indiabudget.gov.in/budget_archive/ub2003-04/bs/speecha.htm
- Union Budget 2004-05 speech and memorandum, STT/STCG/LTCG reform:
  https://www.indiabudget.gov.in/budget_archive/ub2004-05/bs/speecha.htm
  https://www.indiabudget.gov.in/budget_archive/ub2004-05/mem/mem1.pdf
- Economic Survey 2004-05, implemented STT structure/effective date:
  https://www.indiabudget.gov.in/budget_archive/es2004-05/chapt2005/chap23.pdf
- Union Budget 2008-09, STCG increase to 15%:
  https://www.indiabudget.gov.in/budget_archive/ub2008-09/bs/speecha.htm
- Union Budget 2018-19, §112A 10% above ₹1 lakh:
  https://www.indiabudget.gov.in/budget2018-2019/ub2018-19/fb/bill.pdf

---

## 7. Open fields before C14 can be production

Still unresolved / not yet source-frozen:
- Germany exact representative-investor short-term marginal rate for 1990-2008, de-minimis thresholds by year, precise loss-carryforward mechanics, dividends, transaction fees.
- Japan pre-2003 alternative source-tax route and long-term exemptions; 2008-2013 threshold nuances; historical dividend rates; exchange/broker charges.
- India exact STT delivery-equity rate-change chronology after inception, brokerage/indirect-tax/exchange/regulator fees, pre-2004 representative resident-individual STCG calibration, dividend-tax treatment by era.
- all three countries: historical short-sale statutory restrictions/borrow availability where relevant.

No production C14 file has been created.
No tax module has been altered.
No GitHub write has been made.


---

## 9. Japan pre-1999 transaction-tax rates and German private-sale threshold/loss rules

### Japan — seller-side Type-2 listed-share transaction-tax rates now source-frozen

MOF's historical tax-policy record defines two transfer classes. For our ordinary investor selling stock through a securities company, NTA's historical glossary places the transaction in **Type 2**, with the securities company collecting and remitting the tax on the investor's transfer.

The primary-source Type-2 share-rate chronology is:

- 1990-01-01 through 1996-03-31: **0.30% of transfer value**;
- 1996-04-01 through 1998-03-31: **0.21%**;
- 1998-04-01 through 1999-03-31: **0.10%**;
- from 1999-04-01: **0%**, because Securities Transaction Tax and Bourse Tax were abolished on 31 March 1999.

For C14 this is represented as:
- `stt_buy = 0`;
- `stt_sell = 0.0030`, then `0.0021`, then `0.0010`, then `0`.

This is not a symmetric two-sided tax: the historical tax is imposed on the transferor/seller and collected by the broker for ordinary investor sales.

Primary support:
- MOF historical tax-rate table, which gives Type-2 shares at 0.30% in Heisei 1 (1989), 0.21% from FY1996, 0.10% in FY1998, then abolition;
- NTA historical definitions, which state that Type 2 means transfers other than securities-company-as-transferor, and that special collection applies when a non-securities-company seller transfers through or to a securities company.

### Germany — threshold and loss-treatment detail

The Bundestag/Bundesrechnungshof 2002 report gives several additional historical facts needed for C14 interpretation:

- through assessment year 1998, private securities gains inside the six-month speculation period were taxable only if aggregate annual speculative gain reached **DM 1,000**;
- pre-1999 losses could be offset only against speculative gains of the **same calendar year**;
- from assessment year 1999 the period became one year and unused losses could be carried backward/forward under §10d, but only against the same private-sale-income category;
- from assessment year 2002, the then `Halbeinkünfteverfahren` generally brought only half of share-related private-sale gains and losses into the income-tax assessment;
- contemporary forms describe the DM 1,000 threshold as EUR 512 after currency conversion.

These are material enough that Germany 1990-2008 should not be compressed into a single scalar `cgt_short` without an explicit representative-investor calibration. The legal boundary is source-frozen; the paper-level marginal-rate calibration remains open.

No production C14 row has been promoted.


---

## 10. Dividend-tax treatment — first source-frozen blocks

### Investor-tax versus company DDT

For C14 `dividend_rate`, the relevant object is the tax borne by the investor on the dividend cash flow. A company-level dividend distribution tax (DDT) must not be charged again as an investor-level dividend tax in the after-tax ledger. Where dividends are statutorily exempt in the shareholder's hands, `dividend_rate = 0` even though the distributing company may separately owe DDT.

### India

Primary Finance Act / Income Tax Department / Union Budget material establishes:

- Finance Act 1997 inserted the distributed-profits tax from 1 June 1997 and inserted the shareholder dividend exemption for dividends referred to in §115-O.
- The DDT regime applied through 31 March 2002.
- For FY 2002-03 the distribution tax was removed and dividends were taxed in recipients' hands at their applicable rates.
- From 1 April 2003, DDT was restored and dividends were again tax-free in shareholders' hands.
- Budget 2020 removed DDT and restored classical taxation in recipients' hands from FY 2020-21.

Working C14 consequence:
- 1997-06-01 through 2002-03-31: shareholder `dividend_rate = 0`;
- 2002-04-01 through 2003-03-31: shareholder rate unresolved / applicable personal rate;
- 2003-04-01 through 2020-03-31: shareholder `dividend_rate = 0`;
- from 2020-04-01: shareholder rate unresolved / applicable personal rate.

The unresolved periods are deliberately left blank. The 10% TDS quoted in historical Budget material is withholding, not automatically the final investor tax rate.

### Germany

For the working high-income / no-church-tax post-2009 calibration, ordinary private dividend income falls under the same 25% Abgeltungsteuer base plus solidarity surcharge treatment used for capital income. The candidate therefore codes `dividend_rate = 0.26375` from 2009 for that calibration.

Pre-2009 German dividend taxation remains historically more complex (imputation / half-income regimes) and is not yet scalar-coded.

### Japan

No dividend-rate row has yet been source-frozen. Listed-share dividend taxation has separate withholding / self-assessment rules and preferential-rate periods, so blanks remain unresolved rather than being copied from capital-gain rates.

