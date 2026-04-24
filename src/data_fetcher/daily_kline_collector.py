#!/usr/bin/env python3
"""
日K线数据采集脚本
使用AKShare获取A股日K线数据，存入quant.db

用法:
    python3 daily_kline_collector.py              # 采集所有股票日K线
    python3 daily_kline_collector.py --code 600000  # 采集单只
    python3 daily_kline_collector.py --recent 5      # 采集最近5个交易日
"""

import warnings
warnings.filterwarnings('ignore')
import akshare as ak
import sqlite3
import os
import sys
import argparse
import time
from datetime import datetime, timedelta
from pathlib import Path

# 配置
DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "quant.db"
DB_PATH = DB_PATH.expanduser()
BATCH_SIZE = 50  # 每批采集股票数
RETRY_TIMES = 3
RETRY_DELAY = 5


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


def save_daily_kline(code, df):
    """保存日K线数据到数据库"""
    if df is None or df.empty:
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    saved = 0
    
    for _, row in df.iterrows():
        try:
            trade_date = str(row['trade_date'])[:10] if 'trade_date' in row else None
            if trade_date is None:
                continue
                
            cursor.execute("""
                INSERT OR REPLACE INTO daily_kline 
                (ts_code, trade_date, open, high, low, close, volume, amount, amplitude, pct_chg, change, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                code,
                trade_date,
                float(row['open']) if pd.notna(row.get('open')) else None,
                float(row['high']) if pd.notna(row.get('high')) else None,
                float(row['low']) if pd.notna(row.get('low')) else None,
                float(row['close']) if pd.notna(row.get('close')) else None,
                float(row['volume']) if pd.notna(row.get('volume')) else None,
                float(row['amount']) if pd.notna(row.get('amount')) else None,
                float(row['amplitude']/100) if pd.notna(row.get('amplitude')) else None,  # 幅转小数
                float(row['pct_chg']/100) if pd.notna(row.get('pct_chg')) else None,  # 百分比转小数
                float(row['change']) if pd.notna(row.get('change')) else None,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            saved += 1
        except Exception as e:
            log(f"  写入错误 {code}: {e}")
            continue
    
    conn.commit()
    conn.close()
    return saved


import pandas as pd


def fetch_daily_kline(code, start_date=None, end_date=None, retry=RETRY_TIMES):
    """使用AKShare获取单只股票日K线"""
    for attempt in range(retry):
        try:
            # 格式转换：000001 -> 000001.SZ, 600000 -> 600000.SH
            if code.startswith('6'):
                symbol = f"{code}.SH"
            else:
                symbol = f"{code}.SZ"
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            # 空数据也返回（不代表失败）
            return df
        except Exception as e:
            err_str = str(e)
            # 限流等可重试错误
            if 'Connection aborted' in err_str or 'timed out' in err_str.lower():
                log(f"  ⚠️ {code} 第{attempt+1}次失败(限流): {err_str[:50]}")
                time.sleep(RETRY_DELAY * (attempt + 1))
            else:
                # 其他错误直接跳过
                log(f"  ⚠️ {code} 失败: {err_str[:50]}")
                return None
    return None


def collect_all(recent_days=None):
    """采集所有股票的日K线"""
    stocks = get_stock_list()
    log(f"股票总数: {len(stocks)}")
    
    total_saved = 0
    failed = []
    
    # 计算日期范围
    if recent_days:
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=recent_days*2)).strftime("%Y%m%d")
    else:
        # 全部历史
        start_date = "20200101"
        end_date = datetime.now().strftime("%Y%m%d")
    
    for i, code in enumerate(stocks):
        if i % BATCH_SIZE == 0:
            log(f"进度: {i}/{len(stocks)}")
        
        # 检查是否已有最新数据
        last_date = get_last_trade_date(code)
        
        df = fetch_daily_kline(code, start_date, end_date)
        if df is not None and not df.empty:
            saved = save_daily_kline(code, df)
            total_saved += saved
        else:
            failed.append(code)
        
        # 控制频率
        if (i + 1) % 10 == 0:
            time.sleep(1)
    
    log(f"\n采集完成! 共保存 {total_saved} 条K线数据")
    if failed:
        log(f"失败: {len(failed)} 只 - {failed[:10]}...")
    
    return total_saved, failed


def collect_single(code, recent_days=5):
    """采集单只股票日K线"""
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=recent_days*2)).strftime("%Y%m%d")
    
    log(f"采集 {code}: {start_date} ~ {end_date}")
    df = fetch_daily_kline(code, start_date, end_date)
    
    if df is not None and not df.empty:
        saved = save_daily_kline(code, df)
        log(f"保存 {saved} 条K线")
    else:
        log(f"获取失败")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="日K线采集")
    parser.add_argument("--code", type=str, help="单只股票代码")
    parser.add_argument("--recent", type=int, help="采集最近N个交易日")
    args = parser.parse_args()
    
    log("=" * 50)
    log("日K线数据采集")
    log(f"数据库: {DB_PATH}")
    log("=" * 50)
    
    if args.code:
        collect_single(args.code, args.recent or 5)
    else:
        collect_all(args.recent)
