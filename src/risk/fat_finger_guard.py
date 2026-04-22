#!/usr/bin/env python3
"""
乌龙指防范模块
功能：防止老板输错代码、金额超限、误买ST
作者：大龙
时间：2026-04-23
"""

import sqlite3
from datetime import datetime
import re

DB_PATH = "/Users/yangjf/Desktop/X/laoban-quant-system/data/database/quant.db"

class FatFingerGuard:
    """乌龙指防范"""
    
    def __init__(self):
        self.stocks = self._load_stock_list()
    
    def _load_stock_list(self):
        """加载股票列表"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT ts_code, name FROM stock_list")
        stocks = {row[0]: row[1] for row in cursor.fetchall()}
        conn.close()
        return stocks
    
    def check_code_similarity(self, code_input):
        """
        检查代码相似度
        返回：相似代码列表
        """
        # 标准化输入
        code = code_input.strip().upper()
        if not code.isdigit():
            return []
        
        similar = []
        for stock_code in self.stocks.keys():
            # 去掉后缀(.SH/.SZ)
            pure_code = stock_code.replace('.SH', '').replace('.SZ', '')
            
            # 长度相同且只有1位不同
            if len(pure_code) == len(code) and pure_code != code:
                diff_count = sum(1 for a, b in zip(pure_code, code) if a != b)
                if diff_count == 1:
                    # 检查是否是同一位数字容易混淆（1/I, 0/O, 2/Z, 5/S）
                    confusing_pairs = [('1','I'), ('1','L'), ('0','O'), ('2','Z'), ('5','S')]
                    for i, (a, b) in enumerate(zip(pure_code, code)):
                        if a != b:
                            # 形似但不同位置的只提醒
                            similar.append({
                                'code': stock_code,
                                'name': self.stocks[stock_code],
                                'reason': f'第{i+1}位数字相近: {a}↔{b}'
                            })
                            break
        
        return similar
    
    def is_st_stock(self, code_input):
        """
        检查是否ST股票
        返回：True是ST，False不是
        """
        code = code_input.strip().replace('.SH', '').replace('.SZ', '')
        
        for stock_code, name in self.stocks.items():
            if code in stock_code:
                # ST股识别
                name_lower = name.lower()
                if 'st' in name_lower or '*st' in name_lower or 's*st' in name_lower:
                    return True, name
                return False, name
        
        return False, None
    
    def check_amount_limit(self, code, price, quantity, max_amount=1000000):
        """
        检查金额是否超限
        默认单票最大100万
        返回：(是否超限, 当前金额, 限额)
        """
        amount = price * quantity
        
        if amount > max_amount:
            return True, amount, max_amount
        return False, amount, max_amount
    
    def full_check(self, code_input, price, quantity, max_amount=1000000):
        """
        完整检查
        返回：检查结果字典
        """
        results = {
            'pass': True,
            'warnings': [],
            'errors': []
        }
        
        # 1. 检查代码相似度
        similar = self.check_code_similarity(code_input)
        if similar:
            results['warnings'].append({
                'type': 'code_similarity',
                'message': f'代码 {code_input} 与以下代码相似',
                'similar_codes': similar
            })
            results['pass'] = False
        
        # 2. 检查ST股票
        is_st, name = self.is_st_stock(code_input)
        if is_st:
            results['errors'].append({
                'type': 'st_stock',
                'message': f'{name} 是ST股票，禁止买入！'
            })
            results['pass'] = False
        
        # 3. 检查金额超限
        over_limit, amount, limit = self.check_amount_limit(code_input, price, quantity, max_amount)
        if over_limit:
            results['warnings'].append({
                'type': 'amount_over_limit',
                'message': f'金额 {amount:,.0f} 超过限额 {limit:,}',
                'amount': amount,
                'limit': limit
            })
            results['pass'] = False
        
        return results


def main():
    """测试"""
    guard = FatFingerGuard()
    
    # 测试1：相似代码
    print("=== 测试代码相似度 ===")
    similar = guard.check_code_similarity("600552")
    print(f"600552 相似代码: {similar}")
    
    # 测试2：ST股票
    print("\n=== 测试ST股票 ===")
    is_st, name = guard.is_st_stock("*ST某某")
    print(f"*ST某某 是ST: {is_st}, 名称: {name}")
    
    # 测试3：金额超限
    print("\n=== 测试金额超限 ===")
    over, amount, limit = guard.check_amount_limit("600000", 10.0, 150000, max_amount=1000000)
    print(f"超限: {over}, 金额: {amount:,}, 限额: {limit:,}")
    
    # 测试4：完整检查
    print("\n=== 完整检查 ===")
    result = guard.full_check("600552", 10.0, 10000, max_amount=500000)
    print(f"检查结果: {result}")


if __name__ == "__main__":
    main()
