"""
Binance 模拟交易适配器

封装 BinanceMockExecution 实现 ExecutionInterface 接口
用于测试和验证执行层逻辑
"""

import logging
from typing import Dict, List, Any, Optional

from src.execution.interface import ExecutionInterface
from src.execution.binance_mock import BinanceMockExecution

logger = logging.getLogger(__name__)


class BinanceMockAdapter(ExecutionInterface):
    """
    Binance 模拟交易适配器
    
    封装 BinanceMockExecution 实现 ExecutionInterface 接口
    用于测试和验证执行层逻辑
    """
    
    def __init__(
        self,
        initial_balance: float = 10000.0,
        leverage: int = 10,
        taker_fee: float = 0.0004,
        maker_fee: float = 0.0002,
        state_file: Optional[str] = None
    ):
        """
        初始化模拟交易适配器
        
        Args:
            initial_balance: 初始余额 (USDT)
            leverage: 默认杠杆倍数
            taker_fee: Taker手续费率
            maker_fee: Maker手续费率
            state_file: 状态文件路径
        """
        self.mock_client = BinanceMockExecution(
            initial_balance=initial_balance,
            leverage=leverage,
            taker_fee=taker_fee,
            maker_fee=maker_fee,
            state_file=state_file
        )
        
        logger.info("✅ Binance 模拟交易适配器初始化完成")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        return self.mock_client.get_open_positions()
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        return self.mock_client.get_account_balance()
    
    def execute_order(self, decision: Any, current_price: float) -> Dict[str, Any]:
        """执行订单"""
        return self.mock_client.execute_order(decision, current_price)
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """平仓"""
        return self.mock_client.close_position(symbol, exit_price)
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """更新持仓盈亏"""
        self.mock_client.update_position_pnl(symbol, current_price)
    
    @property
    def initial_balance(self) -> float:
        """获取初始余额"""
        return self.mock_client.initial_balance
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取交易统计"""
        return self.mock_client.get_statistics()
    
    def save_state(self, filepath: Optional[str] = None):
        """保存状态"""
        self.mock_client.save_state(filepath)

