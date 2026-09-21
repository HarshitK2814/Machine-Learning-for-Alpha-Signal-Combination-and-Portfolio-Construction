"""After-tax evaluation layer (workstream B).

The published machine-learning asset-pricing literature reports returns gross of tax. For a
strategy that turns over more than 100% a year, the tax bill of a taxable investor can be the same
order of magnitude as the trading cost, so "net of costs" is not the same as "net". This package
answers the question the literature skips: what does the investor actually keep?
"""
from .backtest import TaxConfig, after_tax_backtest, compare_regimes, summarise_after_tax  # noqa: F401
from .jurisdictions import (CHINA_A, GERMANY, HONG_KONG, INDIA, JAPAN, JURISDICTIONS,  # noqa: F401
                            SINGAPORE, TAIWAN, UNITED_KINGDOM, UNITED_STATES, Jurisdiction, LossRelief,
                            TransactionTaxes, get_jurisdiction, identification_table)
from .lots import Lot, LotMethod, RealisedGain, TaxLotLedger  # noqa: F401
from .regimes import (FUND_OFFSHORE, REGIMES, TAXABLE_US, TAX_EXEMPT, TRADER_475F,  # noqa: F401
                      TaxRegime, get_regime)

__all__ = [
    "CHINA_A", "FUND_OFFSHORE", "GERMANY", "HONG_KONG", "INDIA", "JAPAN", "JURISDICTIONS",
    "Jurisdiction", "LossRelief", "SINGAPORE", "TAIWAN", "TransactionTaxes", "UNITED_KINGDOM", "UNITED_STATES",
    "get_jurisdiction", "identification_table", "Lot", "LotMethod", "REGIMES", "RealisedGain", "TAXABLE_US", "TAX_EXEMPT",
    "TRADER_475F", "TaxConfig", "TaxLotLedger", "TaxRegime", "after_tax_backtest", "compare_regimes",
    "get_regime", "summarise_after_tax",
]
