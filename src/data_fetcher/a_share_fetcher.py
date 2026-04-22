#!/usr/bin/env python3
"""
A股数据抓取模块
大龙负责实现数据抓取，小爱负责调用

数据源:
- 实时行情: 东方财富、同花顺 (browser抓取)
- 日频数据: Yahoo Finance (stock-market-pro)
- 板块资金: 东方财富
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path

# 数据目录配置
DATA_DIR = Path(os.getenv("QUANT_DATA_DIR", "~/Desktop/X/data")).expanduser()
DAILY_DIR = DATA_DIR / "daily"
REALTIME_DIR = DATA_DIR / "realtime"
HISTORICAL_DIR = DATA_DIR / "historical"


def save_daily_data(data: list[dict], filename: str = None):
    """保存日频数据到CSV"""
    if filename is None:
        filename = f"{datetime.now().strftime('%Y%m%d')}_daily.csv"
    
    filepath = DAILY_DIR / filename
    if not data:
        return filepath
    
    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    
    return filepath


def save_realtime_snapshot(data: dict, filename: str = None):
    """保存实时行情快照到JSON"""
    if filename is None:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_snapshot.json"
    
    filepath = REALTIME_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return filepath


def load_stock_list() -> list[str]:
    """加载股票代码列表（示例）"""
    # TODO: 从配置文件或数据库加载
    return [
        "000001",  # 平安银行
        "000002",  # 万科A
        "600000",  # 浦发银行
    ]


def fetch_market_sentiment() -> dict:
    """
    获取市场情绪数据
    - 涨停数 / 跌停数
    - 上涨家数 / 下跌家数
    - 成交额
    
    TODO: 大龙用 browser skill 实现抓取
    """
    return {
        "date": datetime.now().strftime("%Y%m%d"),
        "limit_up": 0,
        "limit_down": 0,
        "up_count": 0,
        "down_count": 0,
        "volume": 0,
    }


def fetch_sector_flow() -> list[dict]:
    """
    获取板块资金流向
    
    TODO: 大龙用 browser skill 实现抓取
    """
    return []


if __name__ == "__main__":
    # 测试
    print(f"数据目录: {DATA_DIR}")
    print(f"日频目录: {DAILY_DIR}")
    print(f"实时目录: {REALTIME_DIR}")
