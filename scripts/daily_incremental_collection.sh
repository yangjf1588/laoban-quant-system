#!/bin/bash
# 每日增量数据采集脚本
# 定时运行：每日 16:05（收盘后）采集当日K线数据
# 把这个添加到 crontab:
# 5 16 * * 1-5 /Users/yangjf/Desktop/X/laoban-quant-system/scripts/daily_incremental_collection.sh

LOG_FILE="/Users/yangjf/Desktop/X/laoban-quant-system/logs/daily_collection_$(date +%Y%m%d).log"
DATA_DIR="/Users/yangjf/Desktop/X/laoban-quant-system"
PYTHON_BIN="/usr/bin/python3"

echo "[$(date)] 开始每日增量采集" >> "$LOG_FILE"

# 1. 增量日K线采集（只用最近2个交易日）
echo "[$(date)] 采集日K线..." >> "$LOG_FILE"
$PYTHON_BIN $DATA_DIR/src/data_fetcher/daily_kline_collector.py --recent 2 >> "$LOG_FILE" 2>&1

# 2. 更新AI板块数据
echo "[$(date)] 更新AI板块数据..." >> "$LOG_FILE"
$PYTHON_BIN $DATA_DIR/src/data_fetcher/ai_stocks_finder.py >> "$LOG_FILE" 2>&1

echo "[$(date)] 每日采集完成" >> "$LOG_FILE"
