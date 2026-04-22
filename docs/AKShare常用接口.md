# AKShare 数据接口测试报告

**测试时间**: 2026-04-22 23:42
**状态**: 晚间限流严重，建议白天采集

---

## 可用接口 ✅

| 接口 | 函数 | 数据量 | 备注 |
|------|------|--------|------|
| 股票列表 | stock_info_a_code_name | 5508条 | ✅ 可用 |
| 涨停股 | stock_zt_pool_em | 55条 | ✅ 可用 |
| 炸板股 | stock_zt_pool_zbg_em | 可用 | 待测 |
| 跌停股 | stock_zt_pool_zdt_em | 可用 | 待测 |

---

## 限流接口 ⏳

| 接口 | 函数 | 状态 | 建议 |
|------|------|------|------|
| 日K线 | stock_zh_a_hist | ❌ 限流 | 白天重试 |
| 实时行情 | stock_zh_a_spot_em | ❌ 限流 | 白天重试 |
| 指数数据 | stock_zh_index_spot_em | ❌ 限流 | 白天重试 |

---

## 晚间采集策略

**推荐方案**：
1. **白天（9:00-16:00）**：采集日K线和实时数据
2. **晚间（22:00后）**：只采集股票列表+涨停数据
3. **凌晨（02:00-06:00）**：批量采集历史数据

---

## 批量采集脚本框架

```python
import akshare as ak
import sqlite3
from datetime import datetime
import time

def collect_daily():
    """每日收盘后采集"""
    # 1. 涨停股
    df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
    save_to_db(df, "limit_up")
    
    # 2. 股票列表（每日更新）
    df = ak.stock_info_a_code_name()
    save_to_db(df, "stock_list")

def collect_kline白天():
    """白天采集K线（每15分钟）"""
    # 限流，间隔拉长
    time.sleep(2)
    df = ak.stock_zh_a_hist(symbol="000001", ...)
```

---

## 主流数据源对比

| 数据源 | 优点 | 缺点 |
|--------|------|------|
| AKShare | 免费、中文文档全 | 晚间限流 |
| Tushare Pro | 数据全面 | 需注册、有积分限制 |
| 东方财富 | 实时性好 | 需登录 |

**结论**: AKShare主力用，白天采集为主。
