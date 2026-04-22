#!/usr/bin/env python3
"""
乌龙指防范模块

紧急需求:
1. 代码相似度提示（如 600552 vs 600522）
2. 金额超限二次确认
3. ST票特殊标识

小爱负责实现核心逻辑，大龙负责接入交易数据
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class TradeOrder:
    """交易订单"""
    stock_code: str          # 股票代码
    stock_name: str          # 股票名称
    direction: str           # 买入/卖出
    price: float            # 价格
    quantity: int           # 数量
    total_amount: float     # 总金额


class FatFingerGuard:
    """乌龙指防范检查器"""
    
    def __init__(self):
        # 单票最大金额限制（根据老板需求调整）
        self.max_single_amount = 1_000_000  # 100万
        # 相似代码阈值（编辑距离）
        self.similarity_threshold = 2
    
    def check_similar_codes(self, code: str, held_codes: list[str]) -> list[str]:
        """
        检查相似股票代码
        返回可能混淆的代码列表
        
        Example:
            check_similar_codes("600552", ["600522", "000001"])
            -> ["600522"]  # 凯盛科技 vs 中天科技
        """
        similar = []
        for held in held_codes:
            if self._edit_distance(code, held) <= self.similarity_threshold:
                similar.append(held)
        return similar
    
    def check_amount_limit(self, order: TradeOrder) -> tuple[bool, str]:
        """
        检查金额是否超限
        返回: (是否通过, 提示信息)
        """
        if order.total_amount > self.max_single_amount:
            return False, (
                f"⚠️ 金额超限！当前订单 {order.total_amount:,.0f} 元，"
                f"超过单票限制 {self.max_single_amount:,.0f} 元"
            )
        return True, "金额检查通过"
    
    def check_st_stock(self, stock_name: str) -> tuple[bool, str]:
        """
        检查是否为ST股票
        返回: (是否通过, 提示信息)
        """
        if "ST" in stock_name or "*ST" in stock_name:
            return False, f"🚨 ST股票警告！{stock_name} 是ST股票，请确认是否继续？"
        return True, "非ST股票"
    
    def full_check(self, order: TradeOrder, held_codes: list[str]) -> dict:
        """
        完整检查流程
        返回检查结果字典
        """
        results = {
            "passed": True,
            "warnings": [],
            "order": order,
        }
        
        # 1. 相似代码检查
        similar = self.check_similar_codes(order.stock_code, held_codes)
        if similar:
            results["passed"] = False
            results["warnings"].append(
                f"代码相似警告：您持仓中有相似代码 {similar}，"
                f"确认不是 {order.stock_code}({order.stock_name})？"
            )
        
        # 2. 金额超限检查
        amount_ok, amount_msg = self.check_amount_limit(order)
        if not amount_ok:
            results["passed"] = False
            results["warnings"].append(amount_msg)
        
        # 3. ST股票检查
        st_ok, st_msg = self.check_st_stock(order.stock_name)
        if not st_ok:
            results["passed"] = False
            results["warnings"].append(st_msg)
        
        return results
    
    @staticmethod
    def _edit_distance(s1: str, s2: str) -> int:
        """计算编辑距离（Levenshtein Distance）"""
        if len(s1) < len(s2):
            return FatFingerGuard._edit_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]


# 使用示例
if __name__ == "__main__":
    guard = FatFingerGuard()
    
    # 模拟订单
    order = TradeOrder(
        stock_code="600552",
        stock_name="凯盛科技",
        direction="买入",
        price=14.86,
        quantity=20200,
        total_amount=300157,
    )
    
    # 模拟持仓
    held = ["600522", "000001", "002536"]
    
    result = guard.full_check(order, held)
    print(f"检查通过: {result['passed']}")
    for w in result['warnings']:
        print(f"  ⚠️ {w}")
