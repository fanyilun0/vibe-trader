"""
执行适配器 (Execution Adapters)

实现 ExecutionInterface 接口的具体平台适配器:
- BinanceAdapter: Binance 交易适配器（支持 testnet 和主网）
- BinanceMockAdapter: Binance 模拟交易适配器（用于测试）
- HypeAdapter: Hype 平台适配器
- AsterAdapter: Aster 平台适配器
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.execution.interface import ExecutionInterface
from src.execution.binance_mock import BinanceMockExecution

logger = logging.getLogger(__name__)


class BinanceAdapter(ExecutionInterface):
    """
    Binance 交易适配器
    
    将 Binance API 适配到 ExecutionInterface
    支持 testnet（模拟交易）和主网（实盘交易）
    """
    
    def __init__(self, binance_data_client, is_testnet: bool = False):
        """
        初始化 Binance 适配器
        
        Args:
            binance_data_client: BinanceDataIngestion 实例
            is_testnet: 是否使用测试网
        """
        self.data_client = binance_data_client
        self.client = binance_data_client.client
        self.is_testnet = is_testnet
        
        if is_testnet:
            logger.info("✅ Binance 适配器初始化完成 (testnet 模式)")
            logger.info("   使用币安测试网进行模拟交易")
        else:
            logger.info("✅ Binance 适配器初始化完成 (主网模式)")
            logger.warning("⚠️  实盘交易模式 - 将执行真实订单!")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        logger.debug("获取币安持仓信息")
        
        try:
            account_data = self.data_client.get_account_data()
            positions = account_data.get('positions', [])
            
            # 转换为标准格式
            formatted_positions = []
            for pos in positions:
                position_amt = pos.get('position_amt', 0)
                formatted_positions.append({
                    'symbol': pos.get('symbol'),
                    'side': 'LONG' if position_amt > 0 else 'SHORT',
                    'quantity': abs(position_amt),
                    'entry_price': pos.get('entry_price', 0),
                    'unrealized_pnl': pos.get('unrealized_profit', 0),
                    'leverage': pos.get('leverage', 1),
                    'position_side': pos.get('position_side', 'BOTH')
                })
            
            return formatted_positions
            
        except Exception as e:
            logger.error(f"获取持仓信息失败: {e}")
            return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        logger.debug("获取币安账户余额")
        
        try:
            account_data = self.data_client.get_account_data()
            
            return {
                'available_balance': account_data.get('available_balance', 0.0),
                'total_balance': account_data.get('total_wallet_balance', 0.0),
                'total_equity': account_data.get('total_margin_balance', 0.0),
                'unrealized_pnl': account_data.get('total_unrealized_profit', 0.0)
            }
            
        except Exception as e:
            logger.error(f"获取账户余额失败: {e}")
            return {
                'available_balance': 0.0,
                'total_balance': 0.0,
                'total_equity': 0.0,
                'unrealized_pnl': 0.0
            }
    
    def execute_order(self, decision: Any, current_price: float) -> Dict[str, Any]:
        """执行订单"""
        logger.info(f"在币安执行订单: {decision.action} {decision.symbol}")
        
        if decision.action == 'HOLD':
            logger.info("决策为HOLD,不执行任何操作")
            return {
                'status': 'SKIPPED',
                'action': 'HOLD',
                'message': '保持观望'
            }
        
        # TODO: 实现真实的 Binance API 下单逻辑
        # 参考: self.client.futures_create_order(...)
        logger.warning("⚠️  订单执行功能待实现")
        
        return {
            'status': 'PENDING',
            'order_id': f"BINANCE_{datetime.now().timestamp()}",
            'symbol': decision.symbol,
            'action': decision.action,
            'timestamp': datetime.now().isoformat(),
            'message': '订单执行功能待实现'
        }
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """平仓"""
        logger.info(f"平仓币安持仓: {symbol}")
        
        # TODO: 实现真实的 Binance API 平仓逻辑
        logger.warning("⚠️  平仓功能待实现")
        
        return {
            'symbol': symbol,
            'status': 'PENDING',
            'timestamp': datetime.now().isoformat(),
            'message': '平仓功能待实现'
        }
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """更新持仓盈亏 (Binance API 会自动更新)"""
        pass
    
    @property
    def initial_balance(self) -> float:
        """获取初始余额（从第一次查询的余额作为初始值）"""
        # 首次获取余额时记录为初始余额
        if not hasattr(self, '_initial_balance'):
            balance = self.get_account_balance()
            self._initial_balance = balance.get('total_balance', 0.0)
        return self._initial_balance


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


class HypeAdapter(ExecutionInterface):
    """Hype 平台适配器 (存根)"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        初始化 Hype 适配器
        
        Args:
            api_key: API 密钥
            api_secret: API 密钥
        """
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("✅ Hype 适配器初始化完成 (存根)")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        logger.info("获取 Hype 持仓信息 (存根)")
        return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        logger.info("获取 Hype 账户余额 (存根)")
        return {
            'available_balance': 0.0,
            'total_balance': 0.0,
            'total_equity': 0.0
        }
    
    def execute_order(self, decision: Any, current_price: float) -> Dict[str, Any]:
        """执行订单"""
        logger.info(f"在 Hype 执行订单: {decision.action} {decision.symbol} (存根)")
        return {
            'status': 'SUBMITTED',
            'order_id': f"HYPE_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat()
        }
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """平仓"""
        logger.info(f"平仓 Hype 持仓: {symbol} (存根)")
        return {
            'symbol': symbol,
            'status': 'CLOSED'
        }
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """更新持仓盈亏"""
        pass


class AsterAdapter(ExecutionInterface):
    """Aster 平台适配器 (存根)"""
    
    def __init__(self, api_key: str, api_secret: str):
        """
        初始化 Aster 适配器
        
        Args:
            api_key: API 密钥
            api_secret: API 密钥
        """
        self.api_key = api_key
        self.api_secret = api_secret
        logger.info("✅ Aster 适配器初始化完成 (存根)")
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        logger.info("获取 Aster 持仓信息 (存根)")
        return []
    
    def get_account_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        logger.info("获取 Aster 账户余额 (存根)")
        return {
            'available_balance': 0.0,
            'total_balance': 0.0,
            'total_equity': 0.0
        }
    
    def execute_order(self, decision: Any, current_price: float) -> Dict[str, Any]:
        """执行订单"""
        logger.info(f"在 Aster 执行订单: {decision.action} {decision.symbol} (存根)")
        return {
            'status': 'SUBMITTED',
            'order_id': f"ASTER_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat()
        }
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """平仓"""
        logger.info(f"平仓 Aster 持仓: {symbol} (存根)")
        return {
            'symbol': symbol,
            'status': 'CLOSED'
        }
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """更新持仓盈亏"""
        pass



