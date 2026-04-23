"""
Backtrader双均线策略示例
学习时间: 2026-04-23
"""
import backtrader as bt
import akshare as ak
import pandas as pd
from datetime import datetime


class MACrossStrategy(bt.Strategy):
    """
    双均线交叉策略
    
    金叉(buy): 短期均线从下方穿过长期均线
    死叉(sell): 短期均线从上方穿过长期均线
    """
    
    params = (
        ('fast_period', 10),   # 短期均线周期
        ('slow_period', 30),   # 长期均线周期
        ('printlog', False),    # 是否打印交易日志
    )
    
    def __init__(self):
        # 维护移动平均线
        self.fast_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.fast_period)
        self.slow_ma = bt.indicators.SimpleMovingAverage(
            self.data.close, period=self.params.slow_period)
        
        # 交叉信号
        self.crossover = bt.indicators.CrossOver(self.fast_ma, self.slow_ma)
        
        # 追踪订单
        self.order = None
        
    def log(self, txt, dt=None):
        if self.params.printlog:
            dt = dt or self.datas[0].datetime.date(0)
            print(f'[{dt.isoformat()}] {txt}')
    
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
            
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'买入, 价格: {order.executed.price:.2f}')
            else:
                self.log(f'卖出, 价格: {order.executed.price:.2f}')
                
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('订单失败')
            
        self.order = None
        
    def next(self):
        if self.order:
            return
            
        if self.crossover > 0:  # 金叉
            self.log(f'信号: 买入')
            self.order = self.buy()
        elif self.crossover < 0:  # 死叉
            self.log(f'信号: 卖出')
            self.order = self.sell()


def get_stock_data(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    获取股票历史数据
    
    Args:
        stock_code: 股票代码，如 "000001"
        start_date: 开始日期，如 "20250101"
        end_date: 结束日期，如 "20260422"
        
    Returns:
        DataFrame with OHLCV data
    """
    df = ak.stock_zh_a_hist(
        symbol=stock_code, 
        period="daily",
        start_date=start_date, 
        end_date=end_date
    )
    
    # 转换格式
    df = df[['日期', '开盘', '最高', '最低', '收盘', '成交量']]
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    return df


def run_backtest(
    stock_code: str = "000001",
    start_date: str = "20250101",
    end_date: str = "20260422",
    initial_cash: float = 1000000.0,
    fast_period: int = 10,
    slow_period: int = 30
):
    """
    运行回测
    
    Args:
        stock_code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
        initial_cash: 初始资金
        fast_period: 短期均线周期
        slow_period: 长期均线周期
    """
    print("=" * 60)
    print(f"Backtrader 回测 - {stock_code}")
    print(f"时间范围: {start_date} ~ {end_date}")
    print(f"策略参数: fast={fast_period}, slow={slow_period}")
    print("=" * 60)
    
    # 获取数据
    print("\n获取数据...")
    df = get_stock_data(stock_code, start_date, end_date)
    print(f"数据行数: {len(df)}")
    
    # 转换为Backtrader格式
    data = bt.feeds.PandasData(dataname=df)
    
    # 创建引擎
    cerebro = bt.Cerebro()
    
    # 添加策略
    cerebro.addstrategy(
        MACrossStrategy,
        fast_period=fast_period,
        slow_period=slow_period,
        printlog=False
    )
    
    # 添加数据
    cerebro.adddata(data)
    
    # 设置初始资金
    cerebro.broker.setcash(initial_cash)
    
    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annual')
    
    # 运行
    print(f"\n初始资金: {initial_cash:,.2f}")
    results = cerebro.run()
    
    # 获取结果
    final_value = cerebro.broker.getvalue()
    print(f"最终资金: {final_value:,.2f}")
    
    # 计算收益率
    return_rate = (final_value - initial_cash) / initial_cash * 100
    print(f"总收益率: {return_rate:.2f}%")
    
    # 分析器结果
    strategy = results[0]
    
    returns = strategy.analyzers.returns.get_analysis()
    drawdown = strategy.analyzers.drawdown.get_analysis()
    trades = strategy.analyzers.trades.get_analysis()
    sharpe = strategy.analyzers.sharpe.get_analysis()
    annual = strategy.analyzers.annual.get_analysis()
    
    print("\n" + "=" * 60)
    print("策略分析报告")
    print("=" * 60)
    
    print(f"\n【收益指标】")
    print(f"  总收益率: {return_rate:.2f}%")
    
    if sharpe.get('sharperatio'):
        print(f"  夏普比率: {sharpe['sharperatio']:.2f}")
    
    print(f"\n【风险指标】")
    max_dd = drawdown.get('max', {}).get('drawdown', 0)
    print(f"  最大回撤: {max_dd:.2f}%")
    
    print(f"\n【交易统计】")
    if trades:
        total = trades.get('total', {})
        won = trades.get('won', {})
        lost = trades.get('lost', {})
        
        print(f"  总交易次数: {total.get('total', 0)}")
        print(f"  盈利次数: {won.get('total', 0)}")
        print(f"  亏损次数: {lost.get('total', 0)}")
        
        total_trades = won.get('total', 0) + lost.get('total', 0)
        if total_trades > 0:
            win_rate = won.get('total', 0) / total_trades * 100
            print(f"  胜率: {win_rate:.1f}%")
    
    return {
        'final_value': final_value,
        'return_rate': return_rate,
        'max_drawdown': max_dd,
        'sharpe_ratio': sharpe.get('sharperatio'),
    }


if __name__ == '__main__':
    # 运行回测
    result = run_backtest(
        stock_code="000001",
        start_date="20250101",
        end_date="20260422",
        initial_cash=1000000.0,
        fast_period=10,
        slow_period=30
    )
