# AKShare 常用接口速查

**学习时间**: 2026-04-22
**状态**: 待网络恢复后测试

---

## 1. 股票列表

```python
import akshare as ak

# 获取所有A股股票列表
df = ak.stock_info_a_code_name()
# 返回: code, name, area, industry, market, list_date
```

## 2. 日K线数据

```python
# 历史日K线
df = ak.stock_zh_a_hist(
    symbol="000001",      # 股票代码
    start_date="20260401", # 开始日期
    end_date="20260422",   # 结束日期
    adjust="qfq"           # 前复权
)
# 返回: 日期, 开, 收, 高, 低, 成交量, 成交额, 振幅, 涨跌幅, 涨跌额, 换手率
```

## 3. 实时行情

```python
# 个股实时行情
df = ak.stock_zh_a_spot_em()
# 返回: 代码, 名称, 最新价, 涨跌幅, 成交量, 成交额, 开盘, 最高, 最低, 昨收...

# 单只股票
df = ak.stock_zh_a_spot_em(symbol="000001")
```

## 4. 实时分时

```python
# 分时数据
df = ak.stock_zh_a_hist_min_em(
    symbol="000001",
    start_date="2026-04-22 09:30:00",
    end_date="2026-04-22 15:00:00",
    period="5"  # 5分钟
)
```

## 5. 涨停板

```python
# 今日涨停股
df = ak.stock_zt_pool_em(date="20260422")
# 返回: 代码, 名称, 涨停价, 流通市值, 涨停统计...

# 炸板股
df = ak.stock_zt_pool_zbg_em(date="20260422")
```

## 6. 指数数据

```python
# 上证指数
df = ak.stock_zh_index_spot_em(symbol="上证指数")

# 沪深300
df = ak.stock_zh_index_spot_em(symbol="沪深300")
```

## 7. 批量获取

```python
# 获取多只股票K线
stocks = ["000001", "000002", "600000"]
for code in stocks:
    df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
    time.sleep(0.5)  # 避免限流
```

---

## 注意事项

1. **限流**: 晚间22:00-02:00容易被限流，白天较好
2. **重试**: 加 `time.sleep()` 延时，多次重试
3. **复权**: `adjust="qfq"` 前复权，`adjust="hfq"` 后复权
4. **存储**: 建议用SQLite，采集后直接入库

---

## 测试记录

| 接口 | 状态 | 时间 |
|------|------|------|
| stock_info_a_code_name | ✅ 成功 | 23:17 |
| stock_zh_a_hist | ❌ 限流 | 23:xx |
| stock_zh_a_spot_em | ❌ 限流 | 23:xx |
