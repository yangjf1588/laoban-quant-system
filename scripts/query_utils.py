#!/usr/bin/env python3
"""
数据库查询工具 - 方便查询日K和市场情绪数据
用法:
    python3 query_utils.py --stocks 海光信息,澜起科技 --recent 10
    python3 query_utils.py --market-sentiment --recent 5
    python3 query_utils.py --top-gainers 20
    python3 query_utils.py --hot-sectors 5
"""

import warnings
warnings.filterwarnings('ignore')
import sqlite3
import argparse
import pandas as pd
from pathlib import Path

DB = Path.home() / 'Desktop/X/laoban-quant-system/data/database/quant.db'


def query_stocks(names, recent=10):
    """查询指定股票的近期K线"""
    conn = sqlite3.connect(str(DB))
    
    name_pattern = '|'.join(names) if names else None
    
    if name_pattern:
        df = pd.read_sql_query(f"""
            SELECT d.ts_code, s.name, d.trade_date, d.close, d.pct_chg, d.ma5, d.ma10, d.vol_ratio, d.amount
            FROM daily_kline d
            JOIN stock_list s ON d.ts_code = s.ts_code
            WHERE s.name LIKE '%{name_pattern}%'
            ORDER BY d.trade_date DESC
            LIMIT {recent * 10}
        """, conn)
    else:
        df = pd.read_sql_query(f"""
            SELECT ts_code, trade_date, close, pct_chg, ma5, ma10, vol_ratio, amount
            FROM daily_kline
            ORDER BY trade_date DESC
            LIMIT {recent}
        """, conn)
    
    conn.close()
    
    if name_pattern:
        # 保留每只股票最近N条
        df = df.groupby('ts_code').head(recent)
        print(f"\n{'='*60}")
        print(f"股票查询: {', '.join(names)}")
        print(f"{'='*60}")
        for name, group in df.groupby('name'):
            print(f"\n{name} ({group['ts_code'].iloc[0]}):")
            print(group[['trade_date','close','pct_chg','vol_ratio']].to_string(index=False))
    else:
        print(df)
    
    return df


def query_market_sentiment(recent=5):
    """查询近期市场情绪"""
    conn = sqlite3.connect(str(DB))
    df = pd.read_sql_query(f"""
        SELECT * FROM market_sentiment
        ORDER BY trade_date DESC
        LIMIT {recent}
    """, conn)
    conn.close()
    
    print(f"\n{'='*50}")
    print(f"市场情绪（近{recent}日）")
    print(f"{'='*50}")
    for _, r in df.iterrows():
        print(f"\n{r['trade_date']}: 涨停{r['zt_count']:3d} 跌停{r['dt_count']:3d} 上涨{r['up_count']:4d} 下跌{r['down_count']:4d} 宽度{r['market_width']:5.1f}%")
    
    return df


def query_top_gainers(n=20):
    """查询今日涨幅前N"""
    conn = sqlite3.connect(str(DB))
    df = pd.read_sql_query(f"""
        SELECT d.ts_code, s.name, d.close, d.pct_chg, d.vol_ratio, d.amount
        FROM daily_kline d
        JOIN stock_list s ON d.ts_code = s.ts_code
        WHERE d.trade_date = (SELECT MAX(trade_date) FROM daily_kline)
          AND d.pct_chg IS NOT NULL
        ORDER BY d.pct_chg DESC
        LIMIT {n}
    """, conn)
    conn.close()
    
    print(f"\n{'='*60}")
    print(f"今日涨幅TOP{n}")
    print(f"{'='*60}")
    for _, r in df.iterrows():
        print(f"  {r['pct_chg']:+6.2f}%  {r['name']:12s}  {r['ts_code']}")
    
    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='数据查询工具')
    parser.add_argument('--stocks', nargs='+', help='股票名称关键词')
    parser.add_argument('--recent', type=int, default=10, help='查询近N日')
    parser.add_argument('--market-sentiment', action='store_true', help='市场情绪')
    parser.add_argument('--top-gainers', type=int, metavar='N', help='涨幅前N')
    args = parser.parse_args()
    
    if args.market_sentiment:
        query_market_sentiment(args.recent)
    elif args.top_gainers:
        query_top_gainers(args.top_gainers)
    elif args.stocks:
        query_stocks(args.stocks, args.recent)
    else:
        parser.print_help()
