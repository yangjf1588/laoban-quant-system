#!/bin/bash
# 每日定时采集脚本
# 放在 crontab: 0 16 * * 1-5 /Users/yangjf/Desktop/X/laoban-quant-system/scripts/daily_collection.sh

DATE=$(date +%Y%m%d)
LOG_FILE="/Users/yangjf/Desktop/X/laoban-quant-system/logs/collection_$(date +%Y%m%d).log"

echo "[$(date)] 开始每日数据采集" >> $LOG_FILE

cd /Users/yangjf/Desktop/X/laoban-quant-system

# 采集股票列表
python3 scripts/data_collector.py --mode stock_list >> $LOG_FILE 2>&1

# 采集日K线（盘中每小时一次）
python3 scripts/data_collector.py --mode daily_kline --limit 100 >> $LOG_FILE 2>&1

echo "[$(date)] 数据采集完成" >> $LOG_FILE
