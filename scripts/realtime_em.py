#!/usr/bin/env python3
"""
实时行情采集脚本 - 东方财富接口
功能：采集全A股实时行情数据
作者：大龙
时间：2026-04-22
"""

import urllib.request
import json
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

def get_realtime_em(secids):
    """
    东方财富实时行情接口
    secids格式: "1.600000,1.600519,0.000001"
    """
    url = f"https://push2.eastmoney.com/api/qt/ulist.np/get?fltt=2&invt=2&fields=f1,f2,f3,f4,f5,f6,f12,f13,f14,f15,f16,f17,f18&secids={secids}"
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.eastmoney.com/'
        })
        resp = urllib.request.urlopen(req, timeout=30)
        data = resp.read().decode('utf-8')
        return json.loads(data)
    except Exception as e:
        print(f"获取失败: {e}")
        return None

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
            high REAL,
            low REAL,
            volume INTEGER,
            amount REAL,
            pct_chg REAL,
            update_time TEXT,
            created_at TEXT
        )
    """)
    
    for stock in stocks:
        cursor.execute("""
            INSERT OR REPLACE INTO realtime_quote
            (ts_code, name, price, yesterday_close, open, high, low, volume, amount, pct_chg, update_time, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            stock['code'],
            stock['name'],
            stock['price'],
            stock['yesterday_close'],
            stock['open'],
            stock['high'],
            stock['low'],
            stock['volume'],
            stock['amount'],
            stock['pct_chg'],
            stock['update_time'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
    
    conn.commit()
    conn.close()
    return len(stocks)

def parse_em_data(json_data):
    """解析东方财富数据"""
    stocks = []
    try:
        diff = json_data['data']['diff']
        for item in diff:
            code = item.get('f12', '')
            # 判断市场: f13=1上证, f13=0深证
            market = '.SH' if item.get('f13') == 1 else '.SZ'
            stocks.append({
                'code': code + market,
                'name': item.get('f14', ''),
                'price': item.get('f2', 0),  # 最新价
                'pct_chg': item.get('f3', 0),  # 涨跌幅
                'yesterday_close': item.get('f18', 0),  # 昨收
                'open': item.get('f17', 0),  # 开盘
                'high': item.get('f15', 0),  # 最高
                'low': item.get('f16', 0),  # 最低
                'volume': item.get('f5', 0),  # 成交量
                'amount': item.get('f6', 0),  # 成交额
                'update_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    except Exception as e:
        print(f"解析失败: {e}")
    return stocks

def main():
    print(f"[{datetime.now()}] 东方财富实时行情采集...")
    
    # 获取股票代码
    codes = get_stock_codes()
    print(f"获取到 {len(codes)} 只股票")
    
    # 东方财富接口每次最多200只
    batch_size = 100
    total_saved = 0
    
    for i in range(0, min(len(codes), 500), batch_size):
        batch = codes[i:i+batch_size]
        
        # 构建secids: 1=上证, 0=深证
        secids = []
        for code in batch:
            market = '1' if code.startswith('6') else '0'
            secids.append(f"{market}.{code}")
        
        data = get_realtime_em(','.join(secids))
        
        if data and data.get('rc') == 0:
            stocks = parse_em_data(data)
            saved = save_to_db(stocks)
            total_saved += saved
            print(f"进度: {i+batch_size}/{len(codes)}, 已存: {total_saved}")
        
        time.sleep(0.3)
    
    print(f"\n完成! 共采集 {total_saved} 只实时行情")

if __name__ == "__main__":
    main()
