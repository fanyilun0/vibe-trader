"""
执行接口定义 (ExecutionInterface)

定义所有执行适配器必须实现的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any


class ExecutionInterface(ABC):
    """
    交易执行抽象接口
    
    所有具体的执行适配器都必须实现此接口
    这是执行层的契约 (Contract)
    """
    
    @abstractmethod
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前所有未平仓头寸
        
        Returns:
            持仓信息列表,每个持仓包含:
            - symbol: 交易对符号
            - side: 方向 ('LONG' or 'SHORT')
            - quantity: 持仓数量
            - entry_price: 开仓价格
            - unrealized_pnl: 未实现盈亏
            - margin: 占用保证金
            - liquidation_price: 强平价格
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息
        
        Returns:
            包含余额信息的字典:
            - available_balance: 可用余额
            - total_balance: 总余额
            - total_equity: 总权益
            - total_margin: 占用保证金
            - unrealized_pnl: 未实现盈亏
        """
        pass
    
    @abstractmethod
    def execute_order(self, decision: Any, current_price: float) -> Dict[str, Any]:
        """
        根据AI决策执行订单
        
        Args:
            decision: AI生成的交易决策 (TradingDecision对象)
            current_price: 当前市场价格
            
        Returns:
            包含订单ID和状态的字典:
            - status: 执行状态 ('SUCCESS', 'FAILED', 'SKIPPED')
            - action: 执行的操作
            - symbol: 交易对
            - message/error: 附加信息
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """
        平仓指定交易对的所有持仓
        
        Args:
            symbol: 交易对符号
            exit_price: 平仓价格
            
        Returns:
            平仓结果字典:
            - symbol: 交易对
            - status: 状态
            - realized_pnl: 已实现盈亏
        """
        pass
    
    @abstractmethod
    def update_position_pnl(self, symbol: str, current_price: float):
        """
        更新持仓的未实现盈亏
        
        Args:
            symbol: 交易对符号
            current_price: 当前市场价格
        """
        pass
    
    def cancel_order(self, order_id: str) -> bool:
        """
        根据订单ID取消订单 (可选实现)
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功取消
        """
        return False
    
    def save_state(self, filepath: str = None):
        """
        保存状态到文件 (可选实现)
        
        Args:
            filepath: 文件路径
        """
        pass

