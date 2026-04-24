#!/usr/bin/env python3
"""
市场情绪数据采集
每日收盘后采集：涨跌停数量、成交额、市场宽度等指标
"""

import warnings
warnings.filterwarnings('ignore')
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "quant.db"
DB_PATH = DB_PATH.expanduser()


def get_latest_trade_date():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT MAX(trade_date) FROM daily_kline")
    date = cur.fetchone()[0]
    conn.close()
    return date


def collect_market_sentiment(trade_date=None):
    """采集某日市场情绪数据"""
    if trade_date is None:
        trade_date = get_latest_trade_date()
    
    conn = sqlite3.connect(DB_PATH)
    
    # 涨跌停统计
    zt_count = pd.read_sql_query(f"""
        SELECT COUNT(*) FROM daily_kline 
        WHERE trade_date='{trade_date}' AND pct_chg >= 9.5
    """, conn).iloc[0, 0]
    
    dt_count = pd.read_sql_query(f"""
        SELECT COUNT(*) FROM daily_kline 
        WHERE trade_date='{trade_date}' AND pct_chg <= -9.5
    """, conn).iloc[0, 0]
    
    # 上涨/下跌家数
    up_count = pd.read_sql_query(f"""
        SELECT COUNT(*) FROM daily_kline 
        WHERE trade_date='{trade_date}' AND pct_chg > 0
    """, conn).iloc[0, 0]
    
    down_count = pd.read_sql_query(f"""
        SELECT COUNT(*) FROM daily_kline 
        WHERE trade_date='{trade_date}' AND pct_chg < 0
    """, conn).iloc[0, 0]
    
    # 总成交额
    total_amount = pd.read_sql_query(f"""
        SELECT SUM(amount) FROM daily_kline 
        WHERE trade_date='{trade_date}'
    """, conn).iloc[0, 0]
    
    # 成交额前10（市场最强板块代理）
    top_amount = pd.read_sql_query(f"""
        SELECT s.industry, SUM(d.amount) as total
        FROM daily_kline d
        JOIN stock_list s ON d.ts_code = s.ts_code
        WHERE d.trade_date='{trade_date}' AND d.amount IS NOT NULL
        GROUP BY s.industry
        ORDER BY total DESC
        LIMIT 5
    """, conn)
    
    conn.close()
    
    result = {
        'trade_date': trade_date,
        'zt_count': int(zt_count),
        'dt_count': int(dt_count),
        'up_count': int(up_count),
        'down_count': int(down_count),
        'total_amount': float(total_amount) if total_amount else 0,
        'market_width': round((up_count / (up_count + down_count)) * 100, 2) if (up_count + down_count) > 0 else 0,
        'created_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return result, top_amount


if __name__ == "__main__":
    result, top_industry = collect_market_sentiment()
    print(f"\n市场情绪 {result['trade_date']}:")
    print(f"  涨停: {result['zt_count']}  跌停: {result['dt_count']}")
    print(f"  上涨: {result['up_count']}  下跌: {result['down_count']}")
    print(f"  市场宽度: {result['market_width']}%")
    print(f"  总成交额: {result['total_amount']/1e8:.2f}亿")
    print(f"\n资金流向TOP5板块:")
    for _, row in top_industry.iterrows():
        print(f"  {row['industry']}: {row['total']/1e8:.2f}亿")
