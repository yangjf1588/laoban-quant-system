"""
宏观经济数据采集模块
学习时间: 2026-04-23
用于市场氛围监控
"""
import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Dict, Optional


def get_gdp_data() -> pd.DataFrame:
    """
    获取中国GDP数据
    
    Returns:
        DataFrame with GDP data
    """
    try:
        df = ak.macro_china_gdp()
        return df
    except Exception as e:
        print(f"获取GDP数据失败: {e}")
        return pd.DataFrame()


def get_cpi_data() -> pd.DataFrame:
    """
    获取中国CPI数据
    
    Returns:
        DataFrame with CPI data
    """
    try:
        df = ak.macro_china_cpi()
        return df
    except Exception as e:
        print(f"获取CPI数据失败: {e}")
        return pd.DataFrame()


def get_bond_yield() -> pd.DataFrame:
    """
    获取国债收益率数据
    
    Returns:
        DataFrame with bond yield data
    """
    try:
        df = ak.bond_china_yield()
        # 只取最新的国债收益率
        df_china = df[df['曲线名称'] == '中债国债收益率曲线'].head(1)
        return df_china
    except Exception as e:
        print(f"获取国债收益率失败: {e}")
        return pd.DataFrame()


def get_margin_data(date: str) -> pd.DataFrame:
    """
    获取融资融券数据
    
    Args:
        date: 日期，格式YYYYMMDD
        
    Returns:
        DataFrame with margin data
    """
    try:
        df = ak.stock_margin_detail_szse(date=date)
        return df
    except Exception as e:
        print(f"获取融资融券数据失败: {e}")
        return pd.DataFrame()


def get_index_components(index_code: str) -> pd.DataFrame:
    """
    获取指数成分股
    
    Args:
        index_code: 指数代码，如 "000300"（沪深300）
        
    Returns:
        DataFrame with component stocks
    """
    try:
        df = ak.index_stock_cons(symbol=index_code)
        return df
    except Exception as e:
        print(f"获取指数成分股失败: {e}")
        return pd.DataFrame()


def get_hsgt_summary() -> Optional[Dict]:
    """
    获取沪深港通资金流向汇总
    
    Returns:
        Dict with northbound flow summary
    """
    try:
        df = ak.stock_hsgt_fund_flow_summary_em()
        if len(df) > 0:
            return {
                'date': df.iloc[0].get('日期', ''),
                'shanghai': df.iloc[0].get('沪股通', 0),
                'shenzhen': df.iloc[0].get('深股通', 0),
                'total': df.iloc[0].get('北上合计', 0),
            }
    except Exception as e:
        print(f"获取沪深港通数据失败: {e}")
    return None


def get_market_氛围() -> Dict:
    """
    获取市场氛围综合指标
    
    Returns:
        Dict with market sentiment indicators
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'gdp': None,
        'cpi': None,
        'bond_yield_10y': None,
        'hsgt': None,
    }
    
    # GDP
    df_gdp = get_gdp_data()
    if len(df_gdp) > 0:
        result['gdp'] = {
            'quarter': df_gdp.iloc[0]['季度'],
            'growth': df_gdp.iloc[0]['国内生产总值-同比增长'],
        }
    
    # CPI
    df_cpi = get_cpi_data()
    if len(df_cpi) > 0:
        result['cpi'] = {
            'month': df_cpi.iloc[0]['月份'],
            'yoy': df_cpi.iloc[0]['全国-同比增长'],
            'mom': df_cpi.iloc[0]['全国-环比增长'],
        }
    
    # 国债收益率
    df_bond = get_bond_yield()
    if len(df_bond) > 0:
        result['bond_yield_10y'] = df_bond.iloc[0].get('10年', None)
    
    # 北向资金
    hsgt = get_hsgt_summary()
    if hsgt:
        result['hsgt'] = hsgt
    
    return result


if __name__ == '__main__':
    print("=" * 60)
    print("宏观经济数据测试")
    print("=" * 60)
    
    print("\n【市场氛围】")
    sentiment = get_market_氛围()
    print(f"GDP: {sentiment.get('gdp')}")
    print(f"CPI: {sentiment.get('cpi')}")
    print(f"10年期国债收益率: {sentiment.get('bond_yield_10y')}")
    print(f"北向资金: {sentiment.get('hsgt')}")
