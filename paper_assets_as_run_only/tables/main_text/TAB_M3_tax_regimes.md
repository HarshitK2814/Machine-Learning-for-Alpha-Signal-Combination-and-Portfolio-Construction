**Table 3. Tax regimes as run**

| Market | Regime label in the stage-06 summary | Short-term rate | Long-term rate | Long-term share of gains | Wash-sale disallowed (bp/yr) |
|---|---|---|---|---|---|
| Germany | DEU_ABGELTUNGSTEUER | 26.375% | 26.375% | 0.0000 | 0.00 |
| India | IND_STT100_LTCG_EXEMPT_STCG15 | see label | see label | 0.5928 | 0.00 |
| Japan | JPN_NORMAL_LISTED_SHARE_RATE_PLUS_RECONSTRUCTION | 20.315% | 20.315% | 0.0000 | 0.00 |

*Notes.* Rates for Germany and Japan are the configured values in src/alphacomb/tax/jurisdictions.py (flat; every numeric rate in that file is marked as unverified by the project and this is not a legal review). India's rates are not restated here: the regime label as run in stage 06 is shown verbatim. The long-term share is exactly zero under flat statutes by construction, a mechanical consequence and not an estimate. Means over the 8 prediction cells at $1bn, statutory regime rows.
