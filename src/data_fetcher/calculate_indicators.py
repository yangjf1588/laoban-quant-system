#!/usr/bin/env python3
"""
技术指标计算脚本
给daily_kline补充MA5/10/20/60、量比、振幅等技术指标
"""

import warnings
warnings.filterwarnings('ignore')
import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "quant.db"
DB_PATH = DB_PATH.expanduser()


def add_technical_indicators():
    """批量计算技术指标并更新"""
    conn = sqlite3.connect(DB_PATH)
    
    # 先给表加新列
    for col, dtype in [
        ('ma5', 'REAL'), ('ma10', 'REAL'), ('ma20', 'REAL'), ('ma60', 'REAL'),
        ('vol_ratio', 'REAL'), ('amplitude', 'REAL')
    ]:
        try:
            conn.execute(f"ALTER TABLE daily_kline ADD COLUMN {col} {dtype}")
        except:
            pass
    
    # 读取所有数据按股票+日期排序
    df = pd.read_sql_query("""
        SELECT id, ts_code, trade_date, close, volume, amount, high, low
        FROM daily_kline 
        ORDER BY ts_code, trade_date
    """, conn)
    
    print(f"处理 {len(df)} 条记录...")
    
    # 按股票分组计算
    results = []
    for ts_code, group in df.groupby('ts_code'):
        group = group.sort_values('trade_date')
        closes = group['close'].values
        volumes = group['volume'].values
        amounts = group['amount'].values
        highs = group['high'].values
        lows = group['low'].values
        
        ma5 = pd.Series(closes).rolling(5).mean().values
        ma10 = pd.Series(closes).rolling(10).mean().values
        ma20 = pd.Series(closes).rolling(20).mean().values
        ma60 = pd.Series(closes).rolling(60).mean().values
        
        # 量比 = 当日成交量 / 5日均量
        vol_ma5 = pd.Series(volumes).rolling(5).mean().values
        vol_ratio = volumes / vol_ma5
        vol_ratio[vol_ma5 == 0] = 1
        
        # 振幅
        prev_close = pd.Series(closes).shift(1).values
        amplitude = (highs - lows) / prev_close * 100
        amplitude[prev_close == 0] = 0
        
        for i, (_, row) in enumerate(group.iterrows()):
            results.append({
                'id': row['id'],
                'ma5': round(ma5[i], 2) if pd.notna(ma5[i]) else None,
                'ma10': round(ma10[i], 2) if pd.notna(ma10[i]) else None,
                'ma20': round(ma20[i], 2) if pd.notna(ma20[i]) else None,
                'ma60': round(ma60[i], 2) if pd.notna(ma60[i]) else None,
                'vol_ratio': round(vol_ratio[i], 2) if pd.notna(vol_ratio[i]) else None,
                'amplitude': round(amplitude[i], 2) if pd.notna(amplitude[i]) else None,
            })
    
    # 批量更新
    update_df = pd.DataFrame(results)
    conn.execute("DELETE FROM tmp_indicators")
    
    # 分批更新
    batch_size = 5000
    for i in range(0, len(update_df), batch_size):
        batch = update_df.iloc[i:i+batch_size]
        for _, r in batch.iterrows():
            conn.execute(f"""
                UPDATE daily_kline SET 
                    ma5=?, ma10=?, ma20=?, ma60=?, vol_ratio=?, amplitude=?
                WHERE id=?
            """, (r['ma5'], r['ma10'], r['ma20'], r['ma60'], r['vol_ratio'], r['amplitude'], r['id']))
        print(f"  更新 {min(i+batch_size, len(update_df))}/{len(update_df)}")
        conn.commit()
    
    conn.close()
    print("技术指标计算完成!")


if __name__ == "__main__":
    add_technical_indicators()
