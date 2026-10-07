# C6 International Cost Inputs — Source & Feasibility Audit (WORKING)

**Date:** 2026-10-03  
**Status:** WORKING / NON-PRODUCTION  
**Scope:** Germany (DEU), India (IND), Japan (JPN), 1990-2020 research window  
**Contract:** `date, permno, spread, sigma_d, adv_usd, borrow_fee`

## 1. Hard conclusion from the current project tree

The current international C1 lineage is monthly. It cannot honestly produce daily volatility, daily ADV, or a daily/effective spread estimator by itself. C6 therefore needs a separate day-level market-data source and a separate securities-lending/shortability source.

No C1 field should be repurposed or imputed merely to make C6 appear complete.

## 2. Best daily market-data candidate identified

### S&P/Compustat Global Security Daily on WRDS

WRDS currently lists **Compustat Global - daily updates** as a global product with stock-price content. S&P's international daily-market-price package is explicitly a daily security-price file, and S&P Market Data describes end-of-day open, close, high, low, volume, adjustment factor, shares outstanding, and VWAP-type fields with global coverage and meaningful history from 1990.

If the team's WRDS entitlement includes Compustat Global Security Daily, this is the preferred first source to probe because it can potentially supply all market-data legs needed for:

- `sigma_d`: rolling daily volatility from split-adjusted local-currency daily returns;
- `adv_usd` (legacy name): rolling average daily traded notional, **kept in local currency for international C6** per the handoff;
- high/low/close inputs for an EOD spread estimator;
- identifier bridge via ISIN/SEDOL/ticker/GVKEY-style issue identifiers.

### What still must be verified from the live entitlement

The exact WRDS table names and field availability must be measured, not assumed from product marketing. We need to verify:

1. DEU / IND / JPN coverage by 1990;
2. local listing/security identifier stability and mapping to the C1 permanent ID;
3. daily close and split-adjustment factor;
4. daily traded shares/volume;
5. daily high and low;
6. currency / exchange fields;
7. whether bid/ask quotations exist (unlikely in the standard EOD file);
8. missingness and dead-security coverage.

A schema-only WRDS probe script accompanies this audit and does not pull research data.

## 3. Provisional C6 constructions if daily fields are available

### `sigma_d`

Use daily local-currency price returns, adjusted consistently for splits/corporate actions.

Do not freeze the exact rolling window until the live data are inspected against the existing cost calibration. The field is a **daily volatility input**, not a monthly return volatility.

Candidate implementation:
- compute daily return series;
- trailing rolling standard deviation using only days available through month-end t;
- assign month-end C6 value from the trailing window;
- no future days.

The final window length must be frozen in the C6 methods note and tested against B's cost calibration.

### `adv_usd`

Despite the legacy contract name, international handoff semantics require **local-currency traded notional**, not USD conversion.

Candidate:
`daily_value = abs(close_local) * shares_traded`
then rolling 20/21-trading-day average through formation month-end.

Need to verify whether the vendor's volume field is shares, lots, or another exchange-specific unit before calculating notional.

### `spread`

The research design/handoff says the hierarchy should be explicitly documented rather than silently mixing estimators.

For the international sample:
- true quote-based spread is preferable where a historical quote source genuinely exists;
- otherwise use a reproducible EOD estimator from the available daily OHLC fields;
- retain estimator/source flags because different eras/countries may require different methods.

Do **not** claim a TAQ-quality spread when only daily OHLC data exist.

A final estimator (EDGE / Abdi-Ranaldo / alternative) must be selected only after exact required fields are verified.

## 4. Borrow fee / shortability

### Strong modern candidate

WRDS currently lists **Markit Securities Finance** daily equity products for:
- Europe,
- Asia,
with history beginning in **2002**.

Those products use identifiers such as ISIN/SEDOL and are the strongest candidate for measured post-2002 borrow cost / utilization / on-loan information if the university entitlement includes them.

### Structural problem

The paper's international research window starts in 1990, but Markit Securities Finance begins in 2002. Therefore even with entitlement, it does **not** solve 1990-2001 borrow fees.

No zero-fee backfill is allowed. `borrow_fee=0` cannot be used to mean “unknown” or “unshortable.”

Required design choice after entitlement audit:
1. measured Markit fee where available;
2. explicit proxy regime before measured data begin, with source/assumption flags; or
3. restrict the short-side/after-borrow-cost analysis to a supported period while retaining the longer panel for other objects.

The choice changes interpretation and should be explicit in the prereg/methods rather than hidden inside C6.

## 5. Contract and economic checks that C6 must pass

For every country:
- one unique row per `(date, permno)`;
- calendar month-end dates;
- `spread` is a fraction, not bp;
- `sigma_d >= 0`;
- `adv_usd > 0` where a name is tradeable, with local-currency semantics documented;
- `borrow_fee >= 0`, annual fraction;
- unshortable and unknown are distinguishable from zero fee;
- all fields use only data available through the formation date;
- dead/delisted securities remain represented consistently with C1;
- source/estimator regime is auditable even if C6 contract itself only contains the five required variables.

## 6. Immediate execution plan

1. Run the WRDS schema/entitlement probe.
2. If Compustat Global Security Daily is available, pull a **tiny non-lockbox diagnostic sample** for each country to certify fields, identifiers, units, and daily coverage.
3. Build a deterministic C1↔daily-issue crosswalk audit before any full pull.
4. Freeze `sigma_d`, ADV window, and EOD spread estimator based on measured fields.
5. Probe Markit Securities Finance entitlement and exact fee fields.
6. Treat pre-2002 borrow-fee history as a separate research-design decision; never fabricate it.
7. Build C5 `ILLIQ` from the same certified daily liquidity machinery, so C5 and C6 do not use inconsistent liquidity definitions.

## 7. Current blocker classification

**Potentially automatable with existing institutional access:** daily prices/volume/high-low via Compustat Global Security Daily.

**Entitlement-dependent:** Markit Securities Finance.

**Likely requires a design choice even after data access:** pre-2002 borrow fee / shortability.

**Not a blocker for continuing today:** we can finish the schema probe, code skeletons, C5 semantic corrections, and C14 source research while entitlement checks are pending.

No production file changed.
No GitHub write made.
