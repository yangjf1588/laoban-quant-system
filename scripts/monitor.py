#!/usr/bin/env python3
"""
数据采集监控脚本
功能：检查数据接口状态，记录日志
作者：大龙
时间：2026-04-23
"""

import sqlite3
import akshare as ak
from datetime import datetime
import os

DB_PATH = "/Users/yangjf/Desktop/X/laoban-quant-system/data/database/quant.db"
LOG_DIR = "/Users/yangjf/Desktop/X/laoban-quant-system/logs"

def log(msg):
    """写日志"""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = f"{LOG_DIR}/monitor_{datetime.now().strftime('%Y%m%d')}.log"
    with open(log_file, 'a') as f:
        f.write(f"[{datetime.now()}] {msg}\n")
    print(msg)

def check_database():
    """检查数据库状态"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 股票数量
        cursor.execute("SELECT COUNT(*) FROM stock_list")
        stock_count = cursor.fetchone()[0]
        
        # 实时行情数量
        cursor.execute("SELECT COUNT(*) FROM realtime_quote")
        quote_count = cursor.fetchone()[0]
        
        # 涨停记录数量
        cursor.execute("SELECT COUNT(*) FROM limit_up_record")
        limit_up_count = cursor.fetchone()[0]
        
        conn.close()
        
        log(f"数据库: 股票{stock_count}, 实时行情{quote_count}, 涨停记录{limit_up_count}")
        return True
    except Exception as e:
        log(f"❌ 数据库检查失败: {e}")
        return False

def check_akshare():
    """检查AKShare接口"""
    try:
        # 测试涨停接口
        df = ak.stock_zt_pool_em(date="20260422")
        log(f"✅ AKShare涨停接口正常: {len(df)} 只")
        return True
    except Exception as e:
        log(f"❌ AKShare接口失败: {str(e)[:50]}")
        return False

def check_eastmoney():
    """检查东方财富接口"""
    try:
        # 测试实时行情
        df = ak.stock_zh_a_spot_em()
        log(f"✅ 东方财富实时行情正常: {len(df)} 条")
        return True
    except Exception as e:
        log(f"❌ 东方财富接口失败: {str(e)[:50]}")
        return False

def main():
    """主检查"""
    log("=" * 50)
    log("开始系统检查")
    
    # 1. 检查数据库
    db_ok = check_database()
    
    # 2. 检查AKShare
    akshare_ok = check_akshare()
    
    # 3. 检查东方财富
    em_ok = check_eastmoney()
    
    # 总结
    log("=" * 50)
    if db_ok and (akshare_ok or em_ok):
        log("✅ 系统状态正常")
    else:
        log("⚠️ 系统状态异常，请检查")
    
    return db_ok and (akshare_ok or em_ok)

if __name__ == "__main__":
    main()
