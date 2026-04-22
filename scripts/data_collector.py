#!/usr/bin/env python3
"""
数据采集脚本 - AKShare
功能：采集全A股股票列表和日K线数据
作者：大龙
时间：2026-04-22
"""

import akshare as ak
import sqlite3
import os
import sys
import time
from datetime import datetime, timedelta

# 配置
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database', 'quant.db')
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')

def init_database():
    """初始化数据库表"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 股票列表表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_list (
            ts_code TEXT PRIMARY KEY,
            symbol TEXT,
            name TEXT,
            area TEXT,
            industry TEXT,
            market TEXT,
            list_date TEXT,
            created_at TEXT
        )
    """)
    
    # 日K线表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_kline (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT,
            trade_date TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            amount REAL,
            amplitude REAL,
            pct_chg REAL,
            change REAL,
            created_at TEXT,
            UNIQUE(ts_code, trade_date)
        )
    """)
    
    # 涨停记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS limit_up_record (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts_code TEXT,
            name TEXT,
            trade_date TEXT,
            close_price REAL,
            pct_chg REAL,
            volume REAL,
            amount REAL,
            created_at TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"数据库初始化完成: {DB_PATH}")

def collect_stock_list():
    """采集A股股票列表"""
    print("正在采集股票列表...")
    try:
        df = ak.stock_info_a_code_name()
        print(f"获取到 {len(df)} 只股票")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 清理旧数据
        cursor.execute("DELETE FROM stock_list")
        
        # 插入新数据
        for _, row in df.iterrows():
            cursor.execute("""
                INSERT OR REPLACE INTO stock_list 
                (ts_code, symbol, name, area, industry, market, list_date, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get('code', ''),
                row.get('code', ''),
                row.get('name', ''),
                row.get('area', ''),
                row.get('industry', ''),
                row.get('market', ''),
                row.get('list_date', ''),
                datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
        
        conn.commit()
        conn.close()
        print(f"股票列表已保存: {len(df)} 只")
        return True
    except Exception as e:
        print(f"采集股票列表失败: {e}")
        return False

def collect_daily_kline(ts_code, days=30, retries=3):
    """采集单只股票日K线（带重试）"""
    for attempt in range(retries):
        try:
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y%m%d')
            
            df = ak.stock_zh_a_hist(symbol=ts_code, start_date=start_date, end_date=end_date, adjust="qfq")
            
            if df is None or len(df) == 0:
                return None
            
            # 重命名列
            df.columns = ['trade_date', 'open', 'close', 'high', 'low', 'volume', 'amount', 'amplitude', 'pct_chg', 'change', 'turnover']
            
            return df
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # 等待2秒后重试
                continue
            print(f"  采集 {ts_code} K线失败: {e}")
            return None
    return None

def save_daily_kline(ts_code):
    """保存单只股票日K线到数据库"""
    df = collect_daily_kline(ts_code)
    if df is None:
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    for _, row in df.iterrows():
        cursor.execute("""
            INSERT OR REPLACE INTO daily_kline
            (ts_code, trade_date, open, high, low, close, volume, amount, amplitude, pct_chg, change, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ts_code,
            str(row['trade_date'])[:10] if len(str(row['trade_date'])) > 10 else str(row['trade_date']),
            row['open'],
            row['high'],
            row['low'],
            row['close'],
            row['volume'],
            row['amount'],
            row['amplitude'],
            row['pct_chg'],
            row['change'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    conn.close()
    return True

def collect_all_kline(days=30, limit=100):
    """采集所有股票日K线（限制数量用于测试）"""
    print(f"开始采集最近 {days} 天日K线数据...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT ts_code FROM stock_list LIMIT ?", (limit,))
    stock_codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    
    print(f"将采集 {len(stock_codes)} 只股票...")
    
    success = 0
    for i, code in enumerate(stock_codes):
        if (i + 1) % 10 == 0:
            print(f"进度: {i+1}/{len(stock_codes)}")
        
        if save_daily_kline(code):
            success += 1
        
        time.sleep(3)  # 避免请求过快被限流，从0.5秒增加到3秒
    
    print(f"日K线采集完成: {success}/{len(stock_codes)} 只成功")
    return success

def main():
    """主函数"""
    print("=" * 50)
    print("AKShare 数据采集工具")
    print("=" * 50)
    
    # 初始化数据库
    init_database()
    
    # 采集股票列表
    collect_stock_list()
    
    # 采集日K线（先用10只测试）
    print("\n测试模式：先采集10只股票...")
    collect_all_kline(days=30, limit=10)
    
    print("\n数据采集完成！")
    print(f"数据库位置: {DB_PATH}")

if __name__ == "__main__":
    main()
