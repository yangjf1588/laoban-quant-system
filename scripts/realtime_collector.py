#!/usr/bin/env python3
"""
实时行情采集脚本 - 腾讯证券接口
功能：采集全A股实时行情数据
作者：大龙
时间：2026-04-22
"""

import urllib.request
import sqlite3
import time
from datetime import datetime

DB_PATH = "/Users/yangjf/Desktop/X/laoban-quant-system/data/database/quant.db"

def get_stock_codes():
    """获取股票代码列表"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT symbol FROM stock_list")
    codes = [row[0] for row in cursor.fetchall()]
    conn.close()
    return codes

def get_realtime_tencent(codes):
    """
    腾讯证券实时行情接口
    codes格式: "sh600000,sh600519,sz000001"
    """
    ts_codes = []
    for code in codes:
        if code.startswith('6'):
            ts_codes.append(f"sh{code}")
        else:
            ts_codes.append(f"sz{code}")
    
    url = f"https://qt.gtimg.cn/q={','.join(ts_codes)}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode('gbk')
        return data
    except Exception as e:
        print(f"获取实时数据失败: {e}")
        return None

def parse_tencent_data(data):
    """解析腾讯证券数据"""
    stocks = []
    for line in data.split('\n'):
        if '~' in line and '=' in line:
            # 格式: v_sh600000="1~浦发银行~..."
            try:
                code_part = line.split('=')[0].replace('v_', '').strip()
                parts = line.split('"')[1].split('~')
                if len(parts) > 32:
                    stocks.append({
                        'code': code_part[2:],  # 去掉sh/sz前缀
                        'name': parts[1],
                        'price': float(parts[3]) if parts[3] else 0,
                        'yesterday_close': float(parts[4]) if parts[4] else 0,
                        'open': float(parts[5]) if parts[5] else 0,
                        'volume': int(parts[6]) if parts[6] else 0,
                        'bid1_vol': int(parts[7]) if parts[7] else 0,
                        'ask1_vol': int(parts[8]) if parts[8] else 0,
                        'pct_chg': float(parts[32]) if parts[32] else 0,
                        'update_time': parts[30] if len(parts) > 30 else '',
                    })
            except Exception as e:
                pass
    return stocks

def save_to_db(stocks):
    """保存到数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建实时行情表（如果不存在）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS realtime_quote (
            ts_code TEXT PRIMARY KEY,
            name TEXT,
            price REAL,
            yesterday_close REAL,
            open REAL,
            volume INTEGER,
            pct_chg REAL,
            update_time TEXT,
            created_at TEXT
        )
    """)
    
    for stock in stocks:
        cursor.execute("""
            INSERT OR REPLACE INTO realtime_quote
            (ts_code, name, price, yesterday_close, open, volume, pct_chg, update_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock['code'],
            stock['name'],
            stock['price'],
            stock['yesterday_close'],
            stock['open'],
            stock['volume'],
            stock['pct_chg'],
            stock['update_time'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    conn.close()
    return len(stocks)

def main():
    print(f"[{datetime.now()}] 开始采集实时行情...")
    
    # 获取股票代码
    codes = get_stock_codes()
    print(f"获取到 {len(codes)} 只股票")
    
    # 腾讯接口每次最多200只，分批获取
    batch_size = 100
    total_saved = 0
    
    for i in range(0, min(len(codes), 500), batch_size):  # 先测500只
        batch = codes[i:i+batch_size]
        data = get_realtime_tencent(batch)
        
        if data:
            stocks = parse_tencent_data(data)
            saved = save_to_db(stocks)
            total_saved += saved
            print(f"进度: {i+batch_size}/{len(codes)}, 已存: {total_saved}")
        
        time.sleep(0.5)  # 避免请求过快
    
    print(f"\n完成! 共采集 {total_saved} 只股票的实时行情")

if __name__ == "__main__":
    main()
