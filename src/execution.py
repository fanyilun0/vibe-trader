"""
抽象执行层 (Abstract Execution Layer)

定义统一的执行接口,支持多个交易平台:
- Binance
- Hype
- Aster
- Paper Trading (模拟交易)
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import json

from src.ai_decision import TradingDecision

logger = logging.getLogger(__name__)


class ExecutionInterface(ABC):
    """
    交易执行抽象接口
    所有具体的执行客户端都必须实现此接口
    """
    
    @abstractmethod
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        获取当前所有未平仓头寸
        
        Returns:
            持仓信息列表
        """
        pass
    
    @abstractmethod
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息
        
        Returns:
            包含余额信息的字典
        """
        pass
    
    @abstractmethod
    def execute_order(self, decision: TradingDecision) -> Dict[str, Any]:
        """
        根据AI决策执行订单
        
        Args:
            decision: AI生成的交易决策
            
        Returns:
            包含订单ID和状态的字典
        """
        pass
    
    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        根据订单ID取消订单
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功取消
        """
        pass
    
    @abstractmethod
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """
        平仓指定交易对的所有持仓
        
        Args:
            symbol: 交易对符号
            
        Returns:
            平仓结果
        """
        pass


class BinanceExecution(ExecutionInterface):
    """币安执行客户端"""
    
    def __init__(self, client):
        """
        初始化币安执行客户端
        
        Args:
            client: 币安客户端实例 (来自data_ingestion)
        """
        self.client = client
        logger.info("币安执行客户端初始化完成")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取当前未平仓头寸"""
        logger.info("获取币安持仓信息")
        # 实际实现将调用币安API
        # 这里提供存根实现
        return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        logger.info("获取币安账户余额")
        # 实际实现将调用币安API
        return {
            'available_balance': 0.0,
            'total_balance': 0.0
        }
    
    def execute_order(self, decision: TradingDecision) -> Dict[str, Any]:
        """执行订单"""
        logger.info(f"在币安执行订单: {decision.action} {decision.symbol}")
        
        # 这里是存根实现
        # 实际实现需要调用币安期货下单API
        # 参考: client.futures_create_order(...)
        
        logger.warning("币安订单执行 (存根模式 - 未实际下单)")
        
        return {
            'order_id': f"BINANCE_{datetime.now().timestamp()}",
            'status': 'SUBMITTED',
            'symbol': decision.symbol,
            'action': decision.action,
            'timestamp': datetime.now().isoformat()
        }
    
    def cancel_order(self, order_id: str) -> bool:
        """取消订单"""
        logger.info(f"取消币安订单: {order_id}")
        return True
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """平仓"""
        logger.info(f"平仓币安持仓: {symbol}")
        
        return {
            'symbol': symbol,
            'status': 'CLOSED',
            'timestamp': datetime.now().isoformat()
        }


class HypeExecution(ExecutionInterface):
    """Hype平台执行客户端 (存根)"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("Hype执行客户端初始化完成")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        logger.info("获取Hype持仓信息 (存根)")
        return []
    
    def get_account_balance(self) -> Dict[str, float]:
        logger.info("获取Hype账户余额 (存根)")
        return {'available_balance': 0.0, 'total_balance': 0.0}
    
    def execute_order(self, decision: TradingDecision) -> Dict[str, Any]:
        logger.info(f"在Hype执行订单: {decision.action} {decision.symbol} (存根)")
        return {
            'order_id': f"HYPE_{datetime.now().timestamp()}",
            'status': 'SUBMITTED'
        }
    
    def cancel_order(self, order_id: str) -> bool:
        logger.info(f"取消Hype订单: {order_id} (存根)")
        return True
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        logger.info(f"平仓Hype持仓: {symbol} (存根)")
        return {'symbol': symbol, 'status': 'CLOSED'}


class AsterExecution(ExecutionInterface):
    """Aster平台执行客户端 (存根)"""
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("Aster执行客户端初始化完成")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        logger.info("获取Aster持仓信息 (存根)")
        return []
    
    def get_account_balance(self) -> Dict[str, float]:
        logger.info("获取Aster账户余额 (存根)")
        return {'available_balance': 0.0, 'total_balance': 0.0}
    
    def execute_order(self, decision: TradingDecision) -> Dict[str, Any]:
        logger.info(f"在Aster执行订单: {decision.action} {decision.symbol} (存根)")
        return {
            'order_id': f"ASTER_{datetime.now().timestamp()}",
            'status': 'SUBMITTED'
        }
    
    def cancel_order(self, order_id: str) -> bool:
        logger.info(f"取消Aster订单: {order_id} (存根)")
        return True
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        logger.info(f"平仓Aster持仓: {symbol} (存根)")
        return {'symbol': symbol, 'status': 'CLOSED'}


class PaperTradingExecution(ExecutionInterface):
    """模拟交易执行客户端"""
    
    def __init__(self, initial_balance: float = 10000.0):
        """
        初始化模拟交易客户端
        
        Args:
            initial_balance: 初始资金
        """
        self.balance = initial_balance
        self.positions: List[Dict[str, Any]] = []
        self.orders: List[Dict[str, Any]] = []
        self.trade_history: List[Dict[str, Any]] = []
        
        logger.info(f"模拟交易客户端初始化完成 (初始资金={initial_balance})")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取模拟持仓"""
        return self.positions.copy()
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取模拟账户余额"""
        return {
            'available_balance': self.balance,
            'total_balance': self.balance
        }
    
    def execute_order(self, decision: TradingDecision) -> Dict[str, Any]:
        """
        执行模拟订单
        
        在真实回测中,这里会:
        1. 记录订单详情
        2. 更新模拟持仓
        3. 更新模拟余额
        """
        logger.info(f"执行模拟订单: {decision.action} {decision.symbol}")
        
        order = {
            'order_id': f"PAPER_{len(self.orders)}_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'symbol': decision.symbol,
            'action': decision.action,
            'quantity_pct': decision.quantity_pct,
            'confidence': decision.confidence,
            'rationale': decision.rationale,
            'status': 'FILLED'
        }
        
        self.orders.append(order)
        
        # 记录交易历史
        self.trade_history.append({
            'timestamp': datetime.now().isoformat(),
            'action': decision.action,
            'symbol': decision.symbol,
            'decision': decision.dict()
        })
        
        logger.info(f"模拟订单已记录: {order['order_id']}")
        
        return order
    
    def cancel_order(self, order_id: str) -> bool:
        """取消模拟订单"""
        logger.info(f"取消模拟订单: {order_id}")
        
        for order in self.orders:
            if order['order_id'] == order_id:
                order['status'] = 'CANCELLED'
                return True
        
        return False
    
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """平仓模拟持仓"""
        logger.info(f"平仓模拟持仓: {symbol}")
        
        # 移除该symbol的所有持仓
        self.positions = [p for p in self.positions if p['symbol'] != symbol]
        
        return {
            'symbol': symbol,
            'status': 'CLOSED',
            'timestamp': datetime.now().isoformat()
        }
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """获取交易历史"""
        return self.trade_history.copy()
    
    def save_state(self, filepath: str):
        """保存模拟交易状态到文件"""
        state = {
            'balance': self.balance,
            'positions': self.positions,
            'orders': self.orders,
            'trade_history': self.trade_history
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info(f"模拟交易状态已保存到: {filepath}")


def get_execution_client(config: Dict[str, Any], binance_client=None) -> ExecutionInterface:
    """
    根据配置创建执行客户端
    
    Args:
        config: 配置字典
        binance_client: 可选的币安客户端实例
        
    Returns:
        ExecutionInterface实现
    """
    execution_config = config.get('execution', {})
    platform = execution_config.get('platform', 'papertrading')
    
    # 检查是否强制使用模拟交易
    if execution_config.get('paper_trading', True):
        logger.warning("配置中启用了模拟交易模式")
        return PaperTradingExecution()
    
    # 根据平台创建相应客户端
    if platform == 'binance':
        if not binance_client:
            raise ValueError("Binance平台需要提供binance_client参数")
        return BinanceExecution(binance_client)
    
    elif platform == 'hype':
        # 从环境变量获取密钥
        import os
        api_key = os.getenv('HYPE_API_KEY')
        api_secret = os.getenv('HYPE_API_SECRET')
        return HypeExecution(api_key, api_secret)
    
    elif platform == 'aster':
        import os
        api_key = os.getenv('ASTER_API_KEY')
        api_secret = os.getenv('ASTER_API_SECRET')
        return AsterExecution(api_key, api_secret)
    
    elif platform == 'papertrading':
        return PaperTradingExecution()
    
    else:
        raise ValueError(f"不支持的执行平台: {platform}")

