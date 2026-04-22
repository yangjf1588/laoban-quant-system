#!/usr/bin/env python3
"""
完整回测 - 从2026年1月5日到4月22日的所有交易
目的: 建立正确底仓，验证纸上交易系统
"""

import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from simulation import create_account
from simulation.paper_trading import Position

def load_all_trades() -> pd.DataFrame:
    """加载所有交易记录"""
    # 加载历史记录 (1月5日 - 4月21日)
    df_hist = pd.read_csv('~/Desktop/x/zl/22.xls', sep='\t', encoding='gbk')
    df_hist['数据源'] = 'history'
    
    # 加载4.22记录
    df_422 = pd.read_csv('~/Desktop/x/zl/4.22xls.xls', sep='\t', encoding='gbk')
    df_422['数据源'] = '4.22'
    
    # 合并
    df_all = pd.concat([df_hist, df_422], ignore_index=True)
    
    # 转换日期格式
    def parse_datetime(row):
        try:
            date_str = str(int(row['成交日期'])).zfill(8)
            time_str = str(row['成交时间']).strip()
            # 补齐时间前导零
            if len(time_str.split(':')[0]) == 1:
                time_str = '0' + time_str
            return pd.to_datetime(f"{date_str} {time_str}", format='%Y%m%d %H:%M:%S')
        except:
            return pd.NaT
    
    df_all['日期时间'] = df_all.apply(parse_datetime, axis=1)
    
    # 按时间排序
    df_all = df_all.sort_values('日期时间').reset_index(drop=True)
    
    return df_all

def run_full_backtest():
    """运行完整回测"""
    print("=" * 70)
    print("完整交易回测 (2026-01-05 至 2026-04-22)")
    print("=" * 70)
    
    # 创建账户
    acc = create_account()
    
    # 加载所有交易
    df = load_all_trades()
    print(f"\n总交易笔数: {len(df)}")
    print(f"日期范围: {df['日期时间'].min()} 至 {df['日期时间'].max()}")
    
    # 统计
    buys = df[df['买卖标志'] == '买入']
    sells = df[df['买卖标志'] == '卖出']
    print(f"买入: {len(buys)} 笔, 总金额: {buys['成交金额'].sum():,.2f}")
    print(f"卖出: {len(sells)} 笔, 总金额: {sells['成交金额'].sum():,.2f}")
    
    # 按日期分组统计
    df['日期字符串'] = df['日期时间'].dt.strftime('%Y-%m-%d')
    daily_stats = df.groupby('日期字符串').agg({
        '成交金额': lambda x: x[df.loc[x.index, '买卖标志'] == '买入'].sum() - x[df.loc[x.index, '买卖标志'] == '卖出'].sum(),
        '买卖标志': 'count'
    }).rename(columns={'买卖标志': '笔数'})
    daily_stats.columns = ['净流出', '笔数']
    
    print(f"\n交易天数: {len(daily_stats)}")
    print(f"平均每日笔数: {len(df)/len(daily_stats):.1f}")
    
    # 模拟交易
    print("\n--- 开始模拟交易 ---")
    error_count = 0
    
    for idx, row in df.iterrows():
        if pd.isna(row['证券代码']):
            continue
        
        # 处理证券代码
        try:
            code = str(int(row['证券代码'])).zfill(6)
        except:
            continue
        
        name = row['证券名称']
        direction = row['买卖标志']
        price = float(row['成交价格'])
        volume = int(row['成交数量'])
        trade_time = row['日期时间']
        
        if direction == '买入':
            acc.buy(code, name, price, volume, trade_time=trade_time)
        else:
            # 检查是否有底仓
            if code not in acc.positions:
                # 无底仓卖出，假设是之前的持仓（成本价 = 卖出价，即不赢不亏）
                acc.positions[code] = Position(
                    code=code, name=name, volume=volume,
                    cost_price=price, current_price=price
                )
                error_count += 1
            
            # 检查持仓是否足够
            if acc.positions[code].volume < volume:
                # 持仓不足，可能是之前有更多底仓或数据问题
                acc.positions[code].volume = volume  # 调整到足够卖出
                error_count += 1
            
            acc.sell(code, price, volume, trade_time=trade_time)
    
    # 打印最终报告
    print(f"\n注意: {error_count} 笔交易因无历史底仓需要假设")
    acc.print_report()
    
    # 计算真实收益
    total_buy = buys['成交金额'].sum()
    total_sell = sells['成交金额'].sum()
    real_pnl = total_sell - total_buy
    print(f"\n真实交易流水: 收益 {real_pnl:,.2f}")
    print(f"纸上系统资产: {acc.total_asset:,.2f}")
    
    # 保存回测结果
    result = {
        'initial_capital': acc.capital,
        'total_asset': acc.total_asset,
        'total_trades': len(acc.trades),
        'position_count': len(acc.positions),
        'error_count': error_count
    }
    
    return result

if __name__ == "__main__":
    result = run_full_backtest()
