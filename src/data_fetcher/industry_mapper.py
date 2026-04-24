#!/usr/bin/env python3
"""
行业分类采集器 - 生成统一个股-行业映射表

功能：
1. 采集东方财富行业板块 → 个股映射
2. 采集东方财富概念板块 → 个股映射
3. 生成统一格式: code, name, em_industry, em_concept
4. 支持增量更新，失败重试

使用方法：
    python3 industry_mapper.py              # 全量采集
    python3 industry_mapper.py --incremental  # 增量更新（仅交易日16:00后）

输出：
    ~/Desktop/X/laoban-quant-system/data/industry_mapping_em.csv
"""

import akshare as ak
import pandas as pd
import requests
import time
import json
import os
import sys
import warnings
from datetime import datetime, timedelta
from pathlib import Path

warnings.filterwarnings('ignore')

# 路径配置
BASE_DIR = Path.home() / "Desktop/X/laoban-quant-system"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = DATA_DIR / "industry_mapping_em.csv"

# 重试配置
MAX_RETRIES = 3
RETRY_DELAY = 5  # 秒


def log(msg):
    """打印带时间戳的日志"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def retry_call(func, *args, **kwargs):
    """带重试的函数调用"""
    last_error = None
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            log(f"  ⚠️  第{attempt+1}次失败: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    raise last_error


def get_stock_list():
    """获取A股股票列表"""
    log("获取A股股票列表...")
    df = ak.stock_info_a_code_name()
    # 统一代码格式：去掉前缀
    df['code'] = df['代码'].str.replace(r'^[shszSHXZ]+\d+', lambda m: m.group()[2:] if len(m.group()) == 10 and m.group()[:2].upper() in ('SH', 'SZ', 'BJ') else m.group(), regex=True)
    # 上海去掉SH，深圳去掉SZ
    df['code'] = df['代码'].str.extract(r'\d+(\d{6})')[0]
    df = df.rename(columns={'代码': 'code_full', '名称': 'name'})
    df = df[['code', 'name', 'code_full']]
    log(f"  股票列表: {len(df)} 只")
    return df


def get_em_industry_mapping():
    """
    获取东方财富行业板块 → 个股映射
    行业如：银行、房地产、医疗器械
    """
    log("采集东方财富行业板块...")
    
    try:
        industry_names = retry_call(ak.stock_board_industry_name_em)
    except Exception as e:
        log(f"  ❌ 获取行业板块列表失败: {e}")
        return {}
    
    log(f"  共 {len(industry_names)} 个行业板块")
    results = {}  # code -> set of industries
    
    # 限制并发，防止被封
    total = len(industry_names)
    for idx, row in industry_names.iterrows():
        bk_name = row.iloc[0] if len(row) > 0 else row.get('板块名称', '')
        if not bk_name:
            continue
        
        try:
            cons = retry_call(ak.stock_board_industry_cons_em, symbol=bk_name)
            if cons is not None and len(cons) > 0:
                codes = cons.iloc[:, 0].astype(str).tolist()
                for code in codes:
                    # 标准化代码
                    code = code.zfill(6)
                    if code not in results:
                        results[code] = set()
                    results[code].add(f"行业:{bk_name}")
            log(f"  [{idx+1}/{total}] {bk_name}: {len(cons) if cons is not None else 0}只", )
        except Exception as e:
            log(f"  [{idx+1}/{total}] {bk_name}: 失败({e})")
        
        time.sleep(0.5)  # 避免请求过快
    
    log(f"  行业映射完成: {len(results)} 只股票有行业分类")
    return results


def get_em_concept_mapping():
    """
    获取东方财富概念板块 → 个股映射
    概念如：人工智能、云计算、芯片
    """
    log("采集东方财富概念板块...")
    
    try:
        concept_names = retry_call(ak.stock_board_concept_name_em)
    except Exception as e:
        log(f"  ❌ 获取概念板块列表失败: {e}")
        return {}
    
    log(f"  共 {len(concept_names)} 个概念板块")
    results = {}  # code -> set of concepts
    
    total = len(concept_names)
    for idx, row in concept_names.iterrows():
        concept = row.iloc[0] if len(row) > 0 else row.get('板块名称', '')
        if not concept:
            continue
        
        try:
            cons = retry_call(ak.stock_board_concept_cons_em, symbol=concept)
            if cons is not None and len(cons) > 0:
                # 东方财富概念成分股格式可能不同，尝试获取代码列
                if '代码' in cons.columns:
                    codes = cons['代码'].astype(str).tolist()
                elif len(cons.columns) > 0:
                    codes = cons.iloc[:, 0].astype(str).tolist()
                else:
                    codes = []
                
                for code in codes:
                    code = code.zfill(6)
                    if code not in results:
                        results[code] = set()
                    results[code].add(f"概念:{concept}")
            log(f"  [{idx+1}/{total}] {concept}: {len(cons) if cons is not None else 0}只")
        except Exception as e:
            log(f"  [{idx+1}/{total}] {concept}: 失败({e})")
        
        time.sleep(0.5)
    
    log(f"  概念映射完成: {len(results)} 只股票有概念分类")
    return results


def build_mapping():
    """构建完整的行业/概念映射表"""
    log("=" * 60)
    log("开始采集东方财富行业/概念分类")
    log("=" * 60)
    
    # 获取股票列表
    stock_list = get_stock_list()
    all_codes = set(stock_list['code'].tolist())
    
    # 采集行业映射
    industry_map = get_em_industry_mapping()
    
    # 采集概念映射
    concept_map = get_em_concept_mapping()
    
    # 构建最终映射
    rows = []
    for _, row in stock_list.iterrows():
        code = row['code']
        name = row['name']
        
        industries = sorted(industry_map.get(code, set())) 
        concepts = sorted(concept_map.get(code, set()))
        
        rows.append({
            'code': code,
            'name': name,
            'em_industry': ';'.join([i.replace('行业:', '') for i in industries]),
            'em_concept': ';'.join([c.replace('概念:', '') for c in concepts]),
            'has_industry': len(industries) > 0,
            'has_concept': len(concepts) > 0,
        })
    
    df = pd.DataFrame(rows)
    
    # 统计
    industry_count = df['has_industry'].sum()
    concept_count = df['has_concept'].sum()
    both_count = (df['has_industry'] & df['has_concept']).sum()
    
    log("=" * 60)
    log("采集完成!")
    log(f"  总股票: {len(df)} 只")
    log(f"  有行业分类: {industry_count} 只 ({industry_count/len(df)*100:.1f}%)")
    log(f"  有概念分类: {concept_count} 只 ({concept_count/len(df)*100:.1f}%)")
    log(f"  两者都有: {both_count} 只")
    log(f"  无任何分类: {len(df) - both_count} 只")
    
    # 保存
    df_output = df[['code', 'name', 'em_industry', 'em_concept']]
    df_output.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    log(f"已保存到: {OUTPUT_FILE}")
    
    return df


def show_sample():
    """显示样本数据"""
    if not OUTPUT_FILE.exists():
        log("映射文件不存在，请先运行全量采集")
        return
    
    df = pd.read_csv(OUTPUT_FILE)
    log(f"\n样本数据 (前10条):")
    print(df[df['has_industry'] | df['has_concept']].head(10).to_string())


if __name__ == "__main__":
    if "--sample" in sys.argv:
        show_sample()
    else:
        build_mapping()
        show_sample()
