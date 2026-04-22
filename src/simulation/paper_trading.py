#!/usr/bin/env python3
"""
纸上交易系统 (Paper Trading)
初始资金: 500万
目的: 模拟真实交易，验证策略有效性

老板交易特征:
- 隔日超短，单日买卖20+笔
- 早盘10分钟决胜
- 同时持仓11只票，每日换股8-10只
- 盈亏比1:3
"""

import sqlite3
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# 初始资金
INITIAL_CAPITAL = 5_000_000

@dataclass
class Position:
    """持仓"""
    code: str
    name: str
    volume: int
    cost_price: float
    current_price: float = 0.0
    
    @property
    def market_value(self) -> float:
        return self.volume * self.current_price
    
    @property
    def profit_pct(self) -> float:
        if self.cost_price == 0:
            return 0.0
        return (self.current_price - self.cost_price) / self.cost_price * 100

@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    code: str
    name: str
    direction: str  # 'buy' or 'sell'
    price: float
    volume: int
    amount: float
    trade_time: datetime
    strategy: str = ""  # 交易策略标识

@dataclass
class Account:
    """账户"""
    capital: float = INITIAL_CAPITAL
    cash: float = INITIAL_CAPITAL
    positions: Dict[str, Position] = field(default_factory=dict)
    trades: List[Trade] = field(default_factory=list)
    daily_pnl: List[Dict] = field(default_factory=list)
    
    @property
    def total_asset(self) -> float:
        """总资产 = 现金 + 持仓市值"""
        pos_value = sum(p.market_value for p in self.positions.values())
        return self.cash + pos_value
    
    @property
    def total_profit_pct(self) -> float:
        """总收益率"""
        return (self.total_asset - INITIAL_CAPITAL) / INITIAL_CAPITAL * 100
    
    def buy(self, code: str, name: str, price: float, volume: int, 
            strategy: str = "", trade_time: datetime = None) -> bool:
        """买入"""
        if trade_time is None:
            trade_time = datetime.now()
        
        amount = price * volume
        fee = amount * 0.00025  # 万二华五手续费
        total_cost = amount + fee
        
        if total_cost > self.cash:
            print(f"买入失败: 现金不足 {self.cash:.2f} < {total_cost:.2f}")
            return False
        
        self.cash -= total_cost
        
        if code in self.positions:
            # 加仓
            pos = self.positions[code]
            total_volume = pos.volume + volume
            pos.cost_price = (pos.cost_price * pos.volume + price * volume) / total_volume
            pos.volume = total_volume
        else:
            # 新建仓位
            self.positions[code] = Position(
                code=code, name=name, volume=volume,
                cost_price=price, current_price=price
            )
        
        trade = Trade(
            trade_id=f"T{len(self.trades)+1:04d}",
            code=code, name=name, direction='buy',
            price=price, volume=volume, amount=amount,
            trade_time=trade_time, strategy=strategy
        )
        self.trades.append(trade)
        print(f"买入 {code} {name}: {volume}股 @ {price:.2f}, 费用{fee:.2f}")
        return True
    
    def sell(self, code: str, price: float, volume: int,
             strategy: str = "", trade_time: datetime = None) -> bool:
        """卖出"""
        if trade_time is None:
            trade_time = datetime.now()
        
        if code not in self.positions:
            print(f"卖出失败: 无持仓 {code}")
            return False
        
        pos = self.positions[code]
        if volume > pos.volume:
            print(f"卖出失败: 持仓不足 {pos.volume} < {volume}")
            return False
        
        amount = price * volume
        fee = amount * 0.00025
        stamp_tax = amount * 0.001  # 印花税卖方单边
        total_income = amount - fee - stamp_tax
        
        self.cash += total_income
        
        trade = Trade(
            trade_id=f"T{len(self.trades)+1:04d}",
            code=code, name=pos.name, direction='sell',
            price=price, volume=volume, amount=amount,
            trade_time=trade_time, strategy=strategy
        )
        self.trades.append(trade)
        
        # 更新持仓
        pos.volume -= volume
        if pos.volume == 0:
            del self.positions[code]
        
        profit = (price - pos.cost_price) * volume - fee - stamp_tax
        print(f"卖出 {code} {pos.name}: {volume}股 @ {price:.2f}, 收益{profit:.2f}")
        return True
    
    def update_prices(self, price_dict: Dict[str, float]):
        """更新持仓股票价格"""
        for code, price in price_dict.items():
            if code in self.positions:
                self.positions[code].current_price = price
    
    def get_portfolio_summary(self) -> Dict:
        """获取账户概览"""
        return {
            'total_asset': self.total_asset,
            'cash': self.cash,
            'position_value': sum(p.market_value for p in self.positions.values()),
            'total_profit_pct': self.total_profit_pct,
            'position_count': len(self.positions),
            'total_trades': len(self.trades)
        }
    
    def print_report(self):
        """打印账户报告"""
        print("\n" + "="*50)
        print(f"纸上交易账户报告 - {datetime.now().strftime('%Y-%m-%d')}")
        print("="*50)
        print(f"初始资金: {INITIAL_CAPITAL:,.2f}")
        print(f"总资产:   {self.total_asset:,.2f}")
        print(f"累计收益: {self.total_asset - INITIAL_CAPITAL:,.2f} ({self.total_profit_pct:.2f}%)")
        print(f"现金:     {self.cash:,.2f}")
        print(f"持仓数:   {len(self.positions)}")
        print(f"总交易笔数: {len(self.trades)}")
        
        if self.positions:
            print("\n--- 持仓明细 ---")
            for code, pos in self.positions.items():
                print(f"{code} {pos.name}: {pos.volume}股 "
                      f"成本{pos.cost_price:.2f} 现价{pos.current_price:.2f} "
                      f"浮盈{pos.profit_pct:.2f}%")
        
        print("="*50 + "\n")


def create_account() -> Account:
    """创建新账户"""
    return Account()


if __name__ == "__main__":
    # 测试
    acc = create_account()
    print("纸上交易系统已创建，初始资金 500万")
    print(f"当前资产: {acc.total_asset:,.2f}")
