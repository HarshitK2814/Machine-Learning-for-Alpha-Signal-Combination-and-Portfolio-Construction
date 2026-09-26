# Data Strategy

## 1. Principles

1. **Point-in-time or nothing.** Every variable carries the timestamp at which it was knowable.
2. **University-obtainable first.** The main paper uses WRDS-standard data plus free, documented datasets. Costly alternative data are reserved for extensions.
3. **Reproducibility.** Code must run end-to-end from raw WRDS extracts and public downloads, consistent with the JF, RFS and Management Science data/code policies (verified; see Journal Strategy).
4. **Bias register.** Every source has a bias assessment (below). Items marked [verify] must be confirmed against vendor documentation when data are pulled.

## 2. Source Assessment

| Category | Source | Availability / access | Cost to university | Historical depth | Survivorship bias | Point-in-time | Look-ahead risk | Corporate actions | Licensing |
|---|---|---|---|---|---|---|---|---|---|
| Prices, returns, volume, shares | CRSP US Stock (WRDS) | Standard subscription | Institutional licence | Monthly from 1925/26; daily history [verify range] | Low if delisted securities kept; apply delisting returns | Yes (market data) | Low; beware using end-of-month data for same-month trading | CRSP adjustment factors (cfacpr, cfacshr); distributions in returns | No redistribution of raw data |
| Fundamentals | Compustat North America (WRDS) | Standard | Institutional | 1950s; reliable coverage from ~1963 [verify] | Backfill bias in early years; require ≥2 years of history | Partial: restated data overwrite originals unless Snapshot/PIT product used | **High** if accounting lags ignored | Via CCM link table | No redistribution |
| Point-in-time fundamentals | Compustat Snapshot (WRDS) | Additional subscription [verify availability] | Additional | Shorter history [verify] | Low | **Yes** | Low | - | No redistribution |
| Link table | CRSP/Compustat Merged (CCM) | Standard | Included | Full | - | Use link dates | Medium if link dates ignored | - | - |
| Characteristics | JKP global factor/characteristics (code public; data on WRDS; factor returns at jkpfactors.com, CC BY-NC 4.0, through Dec 2025) | WRDS for stock-level; free factor returns | Free/institutional | Long US history; 93 countries | Inherits CRSP/Compustat | Construction lags per JKP code [verify] | Low if code used as is | Handled | CC BY-NC 4.0 (non-commercial) for downloadable data |
| Signals | Open Source Asset Pricing (Chen-Zimmermann) | Free download: 209 firm-level signals (+3 from CRSP), monthly/daily portfolio returns; data through Dec 2024 | Free | Varies by signal | Inherits sources | Signal code lags per original papers | Low-medium: verify each signal's timing | Handled | Cite CZ2022; CRSP-based signals excluded for licensing |
| Analyst data | I/B/E/S (WRDS) | Standard | Institutional | US detail from 1970s/80s [verify] | Low | Use announcement/activation dates | Medium (revision timestamps) | Split-adjusted vs unadjusted files | No redistribution |
| Institutional holdings | Thomson/Refinitiv 13F (WRDS) | Standard | Institutional | 1980+ | Low | Filing-date lag (45 days) | Medium if report date used instead of filing date | - | No redistribution |
| Short interest | Compustat short interest supplemental (WRDS) | Standard [verify coverage by exchange/year] | Institutional | 1970s+ for NYSE/AMEX [verify] | Low | Publication lag | Medium | - | - |
| Securities lending / borrow fees | IHS Markit Securities Finance (WRDS) | Additional licence | High | ~2000s+ [verify] | Low | Daily | Low | - | Restricted |
| Intraday / spreads | TAQ (WRDS) | Standard at many universities | Institutional | Monthly TAQ from 1993; daily TAQ from 2003 [verify] | - | Yes | Low | - | Restricted |
| Spread estimators | Chen-Velikov hf-spreads-all code (TAQ-based effective spreads); EDGE [@AGK2024] via R package bidask; Abdi-Ranaldo [@AR2017]; Corwin-Schultz [@CS2012]; Hasbrouck Gibbs [@HAS2009] | Code public; inputs CRSP/TAQ | Free code | CRSP OHLC history [verify high/low coverage pre-1993] | - | Estimated from past prices only | Low if rolling windows end at t | - | Code licences on GitHub/CRAN |
| Options | OptionMetrics IvyDB (WRDS) | Additional licence | Medium-high | 1996+ | Low | Yes | Low | - | Restricted |
| Macro / states | FRED (St. Louis Fed); Goyal predictor data; CBOE VIX; Baker-Wurgler sentiment; Pastor-Stambaugh liquidity | Free | Free | 1950s-present (VIX from 1990) | - | **Beware revisions** (use ALFRED vintages for revised macro series) | Medium for revised macro data (CPI less affected) | - | Free with attribution |
| Factor returns | Ken French data library; global-q.org q-factors; JKP themes | Free | Free | 1926+ (FF3) | - | Yes | Low | - | Free with attribution |
| News / sentiment | RavenPack (WRDS) | Additional licence | High | 2000+ | Low | Timestamped | Medium (entity mapping) | - | Restricted |
| Text | SEC EDGAR filings; Loughran-McDonald dictionaries | Free | Free | 1993/1996+ | Low | Filing timestamps | Low | - | Free |
| ESG | MSCI/Refinitiv/Sustainalytics | Licence | High | 2000s+ (short) | High (coverage expansion) | Often **not** PIT; rating revisions | **High** | - | Restricted; excluded from main study |
| Supply chain | Compustat Segments customer data (free with Compustat); FactSet Revere (licence) | Mixed | Medium-high | 1970s+ segments | Medium | Filing lags | Medium | - | Restricted |
| International equities | Compustat Global / Datastream; JKP international characteristics | Licence / WRDS | Institutional | 1990s+ for many markets | Medium (coverage changes) | JKP code lags | Medium | Vendor-specific | Restricted |
| LLM / embeddings | Public LLMs | Free/paid | Varies | - | - | **Training-data look-ahead** | **Very high** (model trained on future text) | - | Terms of use; excluded from main study |

## 3. Minimum Viable Dataset for the Main Paper

1. CRSP monthly and daily (1963-2025), including delisting file.
2. Compustat annual and quarterly with CCM links.
3. JKP characteristics (WRDS) **or** OpenAP firm-level signals plus CRSP. Recommended: JKP as the primary library for its theme structure and global extension; OpenAP for signal replication checks and publication dates.
4. TAQ-based effective spreads (1993+) plus EDGE/AR estimators from CRSP OHLC for the full history.
5. Ken French factors, q-factors and JKP theme factors.
6. FRED, Goyal, VIX, Baker-Wurgler and Pastor-Stambaugh state variables.

Optional: IBES, 13F and short interest (for crowding and limits-to-arbitrage mechanism tests); Markit borrow fees; JKP international for robustness.

## 4. Point-in-Time Engineering Rules

| Issue | Rule |
|---|---|
| Accounting availability | Annual items usable ≥ 4 months after fiscal year-end (follow JKP code conventions; verify); quarterly items at RDQ if available, else ≥ 4 months after quarter-end |
| Restatements | Main: Compustat as provided with lags. Robustness: Compustat Snapshot if available |
| Market equity | Month-end t price × shares outstanding (CRSP) |
| Delisting | CRSP dlret; missing performance-related delisting returns set to −30% (NYSE/AMEX convention per Shumway 1997; verify NASDAQ convention) |
| Survivorship | Universe built at t from all securities trading at t |
| Corporate actions | CRSP total returns; adjustment factors for prices/shares in signals |
| Microcaps | Main universe excludes stocks below NYSE 20th size percentile and price < $5 at t |
| Signal publication | Flag signals by original publication year (OpenAP metadata); gated library robustness |
| Macro revisions | Use ALFRED vintages for revised series (industrial production, GDP) if used; prefer market-based states |
| Regime labels | No smoothed (full-sample) regime probabilities; only filtered or threshold states |
| Standardisation | Cross-sectional ranks at t only; time-series standardisation with expanding windows |
| Hyperparameters | Chosen on validation windows strictly before test year |
| Missing data | Median/zero imputation after ranking plus missing indicators; robustness with cross-sectional/time-series imputation [@BLLP2025; @FHNW2025] |

## 5. Data Quality Tests (acceptance criteria for Phase 2)

- Rebuilt market, size and value factors correlate > 0.95 with Ken French series (monthly, 1972-2025).
- Signal long-short t-statistics reproduce OpenAP/JKP values: regression slope and R² comparable to @CZ2022.
- No return observations after a delisting date; no duplicate PERMNO-months.
- Accounting variables never used before their availability date (automated unit tests).
- Spread estimates: cross-sectional correlation with TAQ effective spreads reported for the 1993+ overlap.
