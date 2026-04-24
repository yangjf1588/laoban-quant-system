#!/usr/bin/env python3
"""
AI相关股票识别脚本
思路：名称含AI关键词 + 近期强势（涨幅/成交量），综合识别AI概念股
"""

import warnings
warnings.filterwarnings('ignore')
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent.parent.parent / "data" / "database" / "quant.db"
DB_PATH = DB_PATH.expanduser()

AI_NAME_KEYWORDS = [
    '智能', 'AI', '人工智能', '机器人', '芯片', '半导体', '集成电路',
    '云计算', '大数据', '网络', '电子', '通信', '软件', '信息', '科技',
    '数据', '算力', '算法', '模型', '语料', '大模型', 'LLM', 'GPU', 'CPU',
    '光模块', 'CPO', '液冷', '存储', '传感器', 'MCU', 'MLCC',
    '光刻', '封测', 'IP', 'RISC', 'EDA', 'PCB',
    '汽配', '汽车电子', '无人驾驶', '车联网', '卫星', '商业航天',
    '低空', 'eVTOL', '飞行', '机器人',
    '创新药', '生物医药', '医疗器械', 'AI医疗',
    '电力', '电网', '虚拟电厂', '储能', '新能源',
]


def find_ai_stocks_by_name():
    """通过名称关键词找AI相关股票"""
    conn = sqlite3.connect(DB_PATH)
    pattern = ' OR '.join([f"name LIKE '%{k}%'" for k in AI_NAME_KEYWORDS[:15]])
    query = f"SELECT ts_code, name, industry FROM stock_list WHERE {pattern}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def find_active_stocks(recent_days=3, min_amount=500000):
    """找近期高成交额活跃股（作为概念炒作的代理指标）"""
    conn = sqlite3.connect(DB_PATH)
    
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(trade_date) FROM daily_kline")
    latest = cursor.fetchone()[0]
    start = (datetime.strptime(latest, '%Y-%m-%d') - timedelta(days=recent_days*2)).strftime('%Y-%m-%d')
    
    query = f"""
        SELECT d.ts_code, s.name, MAX(d.amount) as max_amount
        FROM daily_kline d
        JOIN stock_list s ON d.ts_code = s.ts_code
        WHERE d.trade_date >= '{start}' AND d.amount IS NOT NULL
        GROUP BY d.ts_code, s.name
        HAVING MAX(d.amount) >= {min_amount}
        ORDER BY max_amount DESC
        LIMIT 100
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"查询失败: {e}")
        df = pd.DataFrame()
    conn.close()
    return df


def main():
    print("=" * 50)
    print("AI相关股票识别")
    print("=" * 50)
    
    # 名称识别
    name_df = find_ai_stocks_by_name()
    print(f"\n名称含AI关键词: {len(name_df)} 只")
    print(name_df[['ts_code', 'name']].head(15).to_string())
    
    # 活跃识别
    strong_df = find_active_stocks()
    print(f"\n近期高成交额股(活跃股): {len(strong_df)} 只")
    if not strong_df.empty:
        print(strong_df[['ts_code', 'name', 'max_amount']].head(15).to_string())
    else:
        print("  (change字段暂无数据，跳过)")
    
    # 合并
    ai_codes = set(name_df['ts_code'].tolist())
    active_codes = set(strong_df['ts_code'].tolist()) if not strong_df.empty else set()
    
    # 名称+活跃交集（最可能是真正AI概念）
    both = ai_codes & active_codes
    name_only = ai_codes - active_codes
    
    print(f"\n=== AI概念候选股 ===")
    print(f"名称+活跃交集: {len(both)} 只 (高置信度)")
    for code in sorted(list(both))[:20]:
        name = name_df[name_df['ts_code']==code]['name'].values[0]
        print(f"  {code} {name}")
    
    print(f"\n仅名称匹配: {len(name_only)} 只 (待验证)")
    
    # 保存
    out = name_df[name_df['ts_code'].isin(ai_codes | active_codes)][['ts_code', 'name']]
    out_path = Path(__file__).parent.parent.parent / "data" / "ai_board_stocks.csv"
    out.to_csv(out_path, index=False, encoding='utf-8')
    print(f"\n已保存: {out_path}")
    print(f"共 {len(out)} 只AI相关股票")


if __name__ == "__main__":
    main()
