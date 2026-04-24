#!/usr/bin/env python3
"""
日K线数据采集脚本 v2
使用腾讯API获取A股日K线数据，存入quant.db
（东方财富限流时的主要方案）

用法:
    python3 daily_kline_collector.py              # 采集所有股票最近5日K线
    python3 daily_kline_collector.py --code 600000.SH  # 采集单只
    python3 daily_kline_collector.py --recent 20       # 采集最近20个交易日
"""

import warnings
warnings.filterwarnings('ignore')
import akshare as ak
import sqlite3
import os
import sys
import argparse
import time
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "quant.db"
DB_PATH = DB_PATH.expanduser()
BATCH_SIZE = 50
RETRY_TIMES = 3
RETRY_DELAY = 3


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def get_stock_list():
    """从数据库读取股票列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ts_code FROM stock_list")
    stocks = [row[0] for row in cursor.fetchall()]
    conn.close()
    return stocks


def get_last_trade_date(code):
    """获取某股票最后一条K线日期"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(trade_date) FROM daily_kline WHERE ts_code = ?", (code,))
    result = cursor.fetchone()[0]
    conn.close()
    return result


def ts_to_tx_symbol(ts_code):
    """ts_code (600000.SH) -> 腾讯格式 (sh600000)"""
    suffix = ts_code[-2:]  # SH 或 SZ
    raw = ts_code[:6]       # 股票代码
    return f'{suffix.lower()}{raw}'


def save_daily_kline(ts_code, df):
    """保存日K线数据到数据库"""
    if df is None or df.empty:
        return 0

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved = 0

    for _, row in df.iterrows():
        try:
            trade_date = str(row.get('date', ''))[:10]
            if not trade_date:
                continue

            cursor.execute("""
                INSERT OR REPLACE INTO daily_kline
                (ts_code, trade_date, open, high, low, close, volume, amount, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ts_code,
                trade_date,
                float(row['open']) if pd.notna(row.get('open')) else None,
                float(row['high']) if pd.notna(row.get('high')) else None,
                float(row['low']) if pd.notna(row.get('low')) else None,
                float(row['close']) if pd.notna(row.get('close')) else None,
                None,  # volume - 腾讯接口无此字段
                float(row['amount']) if pd.notna(row.get('amount')) else None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            saved += 1
        except Exception as e:
            continue

    conn.commit()
    conn.close()
    return saved


def fetch_daily_kline(ts_code, start_date=None, end_date=None):
    """使用腾讯API获取单只股票日K线"""
    symbol = ts_to_tx_symbol(ts_code)

    for attempt in range(RETRY_TIMES):
        try:
            df = ak.stock_zh_a_hist_tx(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            if attempt < RETRY_TIMES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                log(f"  ⚠️ {ts_code} 失败: {str(e)[:50]}")
                return None


def collect_all(recent_days=5):
    """采集所有股票的日K线"""
    stocks = get_stock_list()
    log(f"股票总数: {len(stocks)}")

    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=recent_days * 2)).strftime("%Y%m%d")

    total_saved = 0
    failed = []

    for i, ts_code in enumerate(stocks):
        if i % 100 == 0:
            log(f"进度: {i}/{len(stocks)}")

        df = fetch_daily_kline(ts_code, start_date, end_date)
        if df is not None and not df.empty:
            saved = save_daily_kline(ts_code, df)
            total_saved += saved

        if (i + 1) % 10 == 0:
            time.sleep(0.5)

    log(f"\n采集完成! 共保存 {total_saved} 条K线")
    if failed:
        log(f"失败: {len(failed)} 只")

    return total_saved


def collect_single(ts_code, recent_days=5):
    """采集单只股票日K线"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=recent_days * 2)).strftime("%Y%m%d")

    log(f"采集 {ts_code}: {start_date} ~ {end_date}")
    df = fetch_daily_kline(ts_code, start_date, end_date)

    if df is not None and not df.empty:
        saved = save_daily_kline(ts_code, df)
        log(f"保存 {saved} 条K线")
        print(df.tail(3))
    else:
        log(f"获取失败")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="日K线采集")
    parser.add_argument("--code", type=str, help="单只股票代码（如600000.SH）")
    parser.add_argument("--recent", type=int, default=5, help="采集最近N个交易日")
    args = parser.parse_args()

    log("=" * 50)
    log("日K线数据采集 v2（腾讯API）")
    log(f"数据库: {DB_PATH}")
    log("=" * 50)

    if args.code:
        collect_single(args.code, args.recent)
    else:
        collect_all(args.recent)
