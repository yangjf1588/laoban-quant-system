# 老板量化交易系统

> 个人A股隔日超短交易辅助系统

## 系统状态

| 组件 | 状态 | 说明 |
|------|------|------|
| 股票数据 | ✅ 5508只 | 东方财富实时 |
| 实时行情 | ✅ 500只 | 最近采集 |
| 涨停数据 | ✅ 110条 | 历史涨停记录 |
| 乌龙指防范 | ✅ V1.0 | 已完成 |

## 目录结构

```
laoban-quant-system/
├── src/
│   ├── data_fetcher/     # 数据采集
│   │   └── a_share_fetcher.py
│   ├── strategy/         # 选股策略
│   │   └── stock_selector.py
│   ├── risk/            # 风控模块
│   │   └── fat_finger_guard.py  # 乌龙指防范 ✅
│   └── simulation/      # 模拟交易
├── scripts/
│   ├── data_collector.py   # AKShare采集
│   ├── realtime_em.py      # 东方财富实时行情
│   ├── monitor.py          # 系统监控
│   └── daily_collection.sh  # 定时采集
├── data/
│   ├── raw/
│   ├── clean/
│   └── database/
│       └── quant.db        # SQLite数据库
├── docs/
│   ├── 数据库设计.md
│   ├── 乌龙指防范使用说明.md  # 使用文档
│   └── AKShare常用接口.md
├── tests/
└── README.md
```

## 快速开始

### 1. 安装依赖
```bash
pip install akshare pandas sqlite3
```

### 2. 采集实时行情
```bash
python3 scripts/realtime_em.py
```

### 3. 系统检查
```bash
python3 scripts/monitor.py
```

### 4. 乌龙指检查
```python
from src.risk.fat_finger_guard import FatFingerGuard

guard = FatFingerGuard()
result = guard.full_check("600552", price=10.0, quantity=10000)
print(result)
```

## 团队分工(V2.2)

| 成员 | 角色 | 职责 |
|------|------|------|
| 老板 | 总指挥 | 实盘操作、决策 |
| 小爱 | 策略主工程师 | 策略设计、代码实现 |
| 大龙 | 技术后勤 | 数据工程、系统部署 |
| 小猪 | 执行助手 | 数据清洗、辅助执行 |

## 数据库表

| 表名 | 记录数 | 说明 |
|------|--------|------|
| stock_list | 5508 | 股票列表 |
| realtime_quote | 500 | 实时行情 |
| limit_up_record | 110 | 涨停记录 |
| daily_kline | 0 | 日K线（待采集） |

## TODO

- [x] 乌龙指防范V1.0
- [x] 系统监控脚本
- [ ] AKShare日K线采集
- [ ] 定时自动采集
- [ ] GitHub远程仓库
- [ ] Docker容器化
