#!/usr/bin/env python3
"""
4.22交易回测 - 用老板真实交易记录验证纸上交易系统
"""

import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

# 添加src到路径
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from simulation import create_account
from simulation.paper_trading import Position

def load_trades_from_file(filepath: str) -> pd.DataFrame:
    """加载4.22交易记录"""
    # 文件是GBK编码的tab分隔文本
    df = pd.read_csv(filepath, sep='\t', encoding='gbk')
    return df

def run_backtest():
    """运行回测"""
    print("=" * 60)
    print("4.22 交易回测")
    print("=" * 60)
    
    # 创建账户
    acc = create_account()
    
    # 加载交易记录
    trade_file = Path("~/Desktop/x/zl/4.22xls.xls").expanduser()
    if not trade_file.exists():
        print(f"交易记录文件不存在: {trade_file}")
        return
    
    df = load_trades_from_file(str(trade_file))
    print(f"\n加载交易记录: {len(df)} 笔")
    
    # 统计买卖
    buys = df[df['买卖标志'] == '买入']
    sells = df[df['买卖标志'] == '卖出']
    print(f"买入: {len(buys)} 笔, 总金额: {buys['成交金额'].sum():.2f}")
    print(f"卖出: {len(sells)} 笔, 总金额: {sells['成交金额'].sum():.2f}")
    
    # 按时间排序执行交易
    df_sorted = df.sort_values('成交时间')
    
    print("\n--- 开始模拟交易 ---")
    for _, row in df_sorted.iterrows():
        # 处理NaN
        if pd.isna(row['证券代码']):
            continue
            
        code = str(int(row['证券代码'])).zfill(6)
        name = row['证券名称']
        direction = row['买卖标志']
        price = float(row['成交价格'])
        volume = int(row['成交数量'])
        
        if direction == '买入':
            acc.buy(code, name, price, volume)
        else:
            # 如果没有持仓，先假设有底仓（用卖出价作为成本）
            if code not in acc.positions:
                acc.positions[code] = Position(
                    code=code, name=name, volume=volume,
                    cost_price=price, current_price=price
                )
                print(f"  注意: {code} 无底仓，假设成本价{price}")
            acc.sell(code, price, volume)
    
    # 打印最终报告
    acc.print_report()
    
    # 计算真实收益
    total_buy = buys['成交金额'].sum()
    total_sell = sells['成交金额'].sum()
    real_pnl = total_sell - total_buy
    print(f"\n真实交易结果: 收益 {real_pnl:,.2f}")
    print(f"纸上系统结果: 收益 {acc.total_asset - acc.capital:,.2f}")

if __name__ == "__main__":
    run_backtest()
