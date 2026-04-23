"""
Backtest模块 - 回测框架和学习代码
"""
from .ma_cross_strategy import MACrossStrategy, run_backtest, get_stock_data
from .macro_data import (
    get_gdp_data,
    get_cpi_data,
    get_bond_yield,
    get_margin_data,
    get_index_components,
    get_market_氛围,
)

__all__ = [
    'MACrossStrategy',
    'run_backtest', 
    'get_stock_data',
    'get_gdp_data',
    'get_cpi_data',
    'get_bond_yield',
    'get_margin_data',
    'get_index_components',
    'get_market_氛围',
]
