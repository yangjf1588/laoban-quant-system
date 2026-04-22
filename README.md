# 老板量化交易系统

> 个人A股隔日超短交易辅助系统

## 系统架构

```
数据采集层          策略分析层          执行层
─────────          ─────────          ──────
AKShare/Tushare ──▶ SQLite ──▶ Python策略脚本 ──▶ 老板决策
     │                                  │
     └── 定时采集(cron)                 └── 预警推送
```

## 目录结构

```
laoban-quant-system/
├── src/
│   ├── data_fetcher/    # 数据采集模块
│   │   └── a_share_fetcher.py
│   ├── strategy/        # 选股策略
│   │   └── stock_selector.py
│   └── risk/           # 风控模块
│       └── fat_finger_guard.py
├── data/
│   ├── raw/            # 原始数据
│   ├── clean/          # 清洗后数据
│   └── database/       # SQLite数据库
│       └── quant.db
├── scripts/
│   ├── data_collector.py    # AKShare数据采集
│   └── daily_collection.sh  # 每日定时脚本
├── logs/               # 日志
├── docs/               # 文档
│   └── 数据库设计.md
├── tests/              # 测试
└── README.md
```

## 快速开始

### 1. 安装依赖
```bash
pip install akshare tushare pandas sqlite3
```

### 2. 初始化数据库
```bash
python3 scripts/data_collector.py
```

### 3. 采集数据
```bash
# 采集股票列表
python3 scripts/data_collector.py --mode stock_list

# 采集日K线
python3 scripts/data_collector.py --mode daily_kline --limit 100
```

## 数据库表

| 表名 | 说明 |
|------|------|
| stock_list | 股票列表(5508只) |
| daily_kline | 日K线数据 |
| limit_up_record | 涨停记录 |

## 团队分工(V2.2)

- **老板**: 实盘操作、决策
- **小爱**: 策略设计、代码实现
- **大龙**: 技术架构、数据工程
- **小猪**: 数据清洗、辅助执行

## TODO

- [ ] AKShare数据接口调通
- [ ] Tushare Pro数据接入
- [ ] 选股策略V1实现
- [ ] 乌龙指防范功能
- [ ] 每日自动采集
