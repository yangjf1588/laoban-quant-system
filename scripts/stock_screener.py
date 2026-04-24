#!/usr/bin/env python3
"""
老板交易体系选股器 v2
基于老板的真实交易规则设计：

- 早盘10分钟决胜（9:30-9:40）
- 买入：09:32-10:52，突破确认加仓
- 卖出：9:30-9:37，不等反弹果断清仓
- 仓位：早盘≤5-6成，单票底仓1成+突破1成
- 盈亏比：做错-5%~10%，做对+2%~3%
- 做对2-3笔才能弥补1笔错误 → 胜率必须高

选股条件：
1. 趋势向上（MA多头排列）
2. 近期有涨停基因（10日内曾涨停）
3. 温和放量（量比1.2~3.0，不过度放量）
4. 股价在MA5/MA20上方（不做偏离均线的票）
5. 板块有事件催化（暂时用AI板块候选替代）
6. 结合市场情绪（市场宽度<30%时谨慎）
"""

import warnings
warnings.filterwarnings('ignore')
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime

DB = Path.home() / 'Desktop/X/laoban-quant-system/data/database/quant.db'
AI_BOARD = Path.home() / 'Desktop/X/laoban-quant-system/data/ai_board_stocks.csv'


def get_market_sentiment():
    """获取最新市场情绪"""
    conn = sqlite3.connect(str(DB))
    latest = pd.read_sql_query("SELECT MAX(trade_date) FROM market_sentiment", conn).iloc[0, 0]
    df = pd.read_sql_query(f"SELECT * FROM market_sentiment WHERE trade_date='{latest}'", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None


def get_ai_board_codes():
    """获取AI板块候选股"""
    try:
        df = pd.read_csv(AI_BOARD)
        return set(df['ts_code'].tolist()) if 'ts_code' in df.columns else set()
    except:
        return set()


def screen(
    min_pct_chg=5.0,       # 近期最大涨幅>5%
    min_vol_ratio=1.2,     # 量比下限
    max_vol_ratio=3.0,     # 量比上限（不过度放量）
    min_zt_count=1,        # 近期涨停次数
    recent_days=10,         # 考察近几日
    top_n=30,               # 输出前N只
    strict=False           # 严格模式（需同时满足AI板块）
):
    """综合选股"""
    conn = sqlite3.connect(str(DB))
    
    latest_date = pd.read_sql_query("SELECT MAX(trade_date) FROM daily_kline", conn).iloc[0, 0]
    
    ai_codes = get_ai_board_codes()
    
    query = f"""
        WITH daily_stats AS (
            SELECT 
                d.ts_code,
                s.name,
                MAX(d.pct_chg) as max_pct,
                MAX(d.vol_ratio) as max_vol_ratio,
                AVG(d.vol_ratio) as avg_vol_ratio,
                MAX(d.close) as latest_close,
                MAX(d.ma5) as latest_ma5,
                MAX(d.ma20) as latest_ma20,
                MAX(d.ma60) as latest_ma60,
                COUNT(CASE WHEN d.pct_chg >= 9.5 THEN 1 END) as zt_count,
                -- 连续上涨天数
                SUM(CASE WHEN d.pct_chg > 0 THEN 1 ELSE 0 END) as up_days,
                -- 最大连续上涨
                MAX(d.pct_chg) as best_day
            FROM daily_kline d
            JOIN stock_list s ON d.ts_code = s.ts_code
            WHERE d.trade_date >= DATE('{latest_date}', '-{recent_days} days')
              AND d.pct_chg IS NOT NULL
              AND d.close IS NOT NULL
              AND d.ma20 IS NOT NULL
              AND d.ma5 IS NOT NULL
            GROUP BY d.ts_code, s.name
        )
        SELECT 
            ts_code,
            name,
            ROUND(max_pct, 2) as 近期最大涨幅,
            ROUND(avg_vol_ratio, 2) as 平均量比,
            ROUND(zt_count, 0) as 涨停次数,
            latest_close as 最新收盘,
            ROUND(latest_ma5, 2) as MA5,
            ROUND(latest_ma20, 2) as MA20,
            ROUND(latest_ma60, 2) as MA60,
            up_days as 上涨天数,
            ROUND(best_day, 2) as 最大单日涨幅
            {", 'AI+' as tag" if ai_codes else ""}
        FROM daily_stats
        WHERE max_pct >= {min_pct_chg}
          AND avg_vol_ratio BETWEEN {min_vol_ratio} AND {max_vol_ratio}
          AND zt_count >= {min_zt_count}
          AND latest_close >= latest_ma20
          AND latest_close >= latest_ma5
        {"AND ts_code IN (" + ','.join(f"'{c}'" for c in ai_codes) + ")" if strict and ai_codes else ""}
        ORDER BY zt_count DESC, max_pct DESC, avg_vol_ratio ASC
        LIMIT {top_n}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df


def analyze_market(market):
    """分析市场情绪并给出操作建议"""
    if market is None:
        return "⚠️ 无市场情绪数据"
    
    width = market['market_width']
    zt = market['zt_count']
    dt = market['dt_count']
    
    print(f"\n{'='*55}")
    print(f"市场情绪 {market['trade_date']}")
    print(f"{'='*55}")
    print(f"  涨停: {zt}只  跌停: {dt}只  上涨: {int(market['up_count'])}家  下跌: {int(market['down_count'])}家")
    print(f"  市场宽度: {width:.1f}%")
    print(f"  总成交额: {market['total_amount']/1e8:.2f}亿")
    print()
    
    if width >= 70:
        return "🟢 强势市场（宽度>70%），积极做多"
    elif width >= 50:
        return "🟡 偏强市场（50-70%），适度参与"
    elif width >= 30:
        return "🟠 偏弱市场（30-50%），谨慎做多"
    else:
        return "🔴 弱势市场（<30%），建议空仓或极轻仓"


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  老板交易体系选股器 v2")
    print("  基于早盘决胜 + 趋势跟随 + 涨停基因")
    print("="*60)
    
    # 市场情绪
    market = get_market_sentiment()
    advice = analyze_market(market)
    print(f"  {advice}")
    
    print(f"\n{'-'*60}")
    print("筛选条件：")
    print(f"  - 10日内最大涨幅 > 5%")
    print(f"  - 量比 1.2 ~ 3.0（温和放量）")
    print(f"  - 涨停次数 >= 1")
    print(f"  - 股价在MA5和MA20上方")
    print(f"  - 按涨停次数排序（优先近期多次涨停）")
    print(f"{'-'*60}")
    
    # 执行选股
    df = screen(
        min_pct_chg=5.0,
        min_vol_ratio=1.2,
        max_vol_ratio=3.0,
        min_zt_count=1,
        recent_days=10,
        top_n=30,
        strict=False
    )
    
    if df is None or df.empty:
        print("\n⚠️ 无符合条件的股票")
    else:
        print(f"\n符合条件 {len(df)} 只：\n")
        print(f"{'代码':<12} {'名称':<10} {'涨幅':>6} {'涨停':>4} {'量比':>5} {'MA5':>7} {'MA20':>7}")
        print("-" * 65)
        for _, r in df.iterrows():
            print(f"{r['ts_code']:<12} {r['name']:<10} {r['近期最大涨幅']:>+6.1f}% {r['涨停次数']:>4.0f}次 {r['平均量比']:>5.2f} {r['MA5']:>7.2f} {r['MA20']:>7.2f}")
        
        # 强势信号：多只近期多次涨停
        multi_zt = df[df['涨停次数'] >= 2]
        if not multi_zt.empty:
            print(f"\n🚀 重点关注（近期多次涨停）:")
            for _, r in multi_zt.iterrows():
                print(f"  {r['name']:<10} {r['涨停次数']:.0f}次涨停  {r['ts_code']}")
    
    print(f"\n{'='*60}")
    print("⚠️ 仅供参考，不构成投资建议")
    print("="*60)
