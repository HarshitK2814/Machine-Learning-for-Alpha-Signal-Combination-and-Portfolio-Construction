**Table 4. Portfolio construction and friction specification as committed**

| Parameter | Value | Key in the committed configuration |
|---|---|---|
| Gross exposure limit | 2.0 | configs/base.yaml portfolio.gross_max |
| Per-name weight cap | 0.01 | portfolio.weight_abs_max |
| ADV participation limit | 0.05 | portfolio.adv_participation_max |
| Target volatility (annual) | 0.1 | portfolio.target_vol_annual |
| Dollar neutral | True | portfolio.dollar_neutral |
| Beta limit (absolute) | 0.05 | portfolio.beta_abs_max |
| Industry limit (absolute) | 0.02 | portfolio.industry_abs_max |
| Commission (basis points) | 1.0 | costs.commission_bps |
| Impact coefficient k | 1.0 | costs.impact_k |
| Impact exponent | 1.5 | costs.impact_power |
| Flat borrow rate (annual) | 0.01 | costs.borrow_fee_model.annual_rate |
| Risk aversion gamma | 25.0 | configs/portfolio.yaml risk_aversion_gamma |
| Objective | mean_variance_minus_tc | configs/portfolio.yaml objective |

*Notes.* Read from the committed configuration files; the manuscript states the same gross, cap, volatility, commission, impact and borrow values (Section 4.1). Run-time hashes of the configuration used on 2026-10-09 were not recorded, so this is the configuration as committed, not a certified record of the runs. Amendment 001A records the contract parameters as frozen by the project team, an attestation that has not been countersigned. Impact is k x sigma x sqrt(AUM/ADV) |dw|^1.5 as stated in the manuscript.
