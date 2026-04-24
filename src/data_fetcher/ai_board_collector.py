#!/usr/bin/env python3
"""
AI板块数据采集脚本 v3
使用同花顺概念板块获取AI相关成分股

用法:
    python3 ai_board_collector.py
"""

import warnings
warnings.filterwarnings('ignore')
import akshare as ak
import pandas as pd
import time
import os
from datetime import datetime

OUT_DIR = os.path.expanduser("~/Desktop/X/laoban-quant-system/data")
OUT_FILE = os.path.join(OUT_DIR, "ai_board_stocks.csv")
os.makedirs(OUT_DIR, exist_ok=True)

AI_KEYWORDS = 'AI|人工智能|科技|机器人|芯片|半导体|智能|互联|云计算|大数据|人形|量子|MCU|传感器'

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)

def retry_call(func, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                log(f"  ⚠️ 第{attempt+1}次失败: {str(e)[:60]}")
                time.sleep(3)
            else:
                raise
    return None


def collect_ai_board_stocks():
    """采集AI相关概念板块的成分股"""
    
    # Step 1: 获取所有概念板块
    log("获取同花顺概念板块列表...")
    all_boards = retry_call(ak.stock_board_concept_name_ths)
    if all_boards is None or all_boards.empty:
        log("获取概念板块列表失败")
        return {}
    
    # Step 2: 筛选AI相关板块
    ai_boards = all_boards[
        all_boards['name'].str.contains(AI_KEYWORDS, na=False, regex=True)
    ]
    log(f"AI相关概念板块: {len(ai_boards)} 个")
    
    # Step 3: 遍历每个AI板块，获取成分股
    ai_stocks = {}  # {code: {name, boards}}
    
    for idx, row in ai_boards.iterrows():
        board_name = row['name']
        board_code = row['code']
        
        try:
            # 获取成分股
            const_df = retry_call(ak.stock_board_concept_cons_ths, symbol=board_code)
            
            if const_df is not None and not const_df.empty:
                for _, stock_row in const_df.iterrows():
                    code = stock_row.get('代码') or stock_row.get('code')
                    name = stock_row.get('名称') or stock_row.get('name')
                    
                    if code and code not in ai_stocks:
                        ai_stocks[code] = {'name': name, 'boards': []}
                    if code:
                        ai_stocks[code]['boards'].append(board_name)
                        
                log(f"  {board_name}: {len(const_df)} 只")
            else:
                log(f"  {board_name}: 无成分股")
                
        except Exception as e:
            log(f"  {board_name} 失败: {str(e)[:40]}")
        
        time.sleep(0.5)  # 控制频率
    
    return ai_stocks


def save_results(ai_stocks):
    """保存结果"""
    if not ai_stocks:
        log("无数据，跳过保存")
        return
    
    rows = []
    for code, info in ai_stocks.items():
        rows.append({
            'code': code,
            'name': info['name'],
            'boards': '|'.join(info['boards'])
        })
    
    df = pd.DataFrame(rows)
    df.to_csv(OUT_FILE, index=False, encoding='utf-8')
    log(f"\n✅ 已保存: {OUT_FILE}")
    log(f"   AI相关股票: {len(df)} 只")
    print(df.head(15).to_string())


if __name__ == "__main__":
    log("=" * 60)
    log("AI板块数据采集 v3")
    log(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    log("=" * 60)
    
    ai_stocks = collect_ai_board_stocks()
    save_results(ai_stocks)
