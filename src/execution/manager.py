"""
执行管理器 (Execution Manager)

执行层的总协调器,负责:
1. 状态查询: 获取账户信息和持仓
2. 数据反馈: 将账户状态反馈给上层
3. 指令分派: 将交易决策传递给适配器执行

这是实现闭环、状态感知决策的关键组件
"""

import logging
from typing import Dict, List, Any, Optional

from src.execution.interface import ExecutionInterface
from src.execution.adapters import (
    BinanceAdapter,
    HypeAdapter,
    AsterAdapter
)

logger = logging.getLogger(__name__)


class ExecutionManager:
    """
    执行管理器
    
    作为执行层的协调器,管理账户状态查询和交易执行
    """
    
    def __init__(self, adapter: ExecutionInterface):
        """
        初始化执行管理器
        
        Args:
            adapter: 执行适配器实例
        """
        self.adapter = adapter
        logger.info("✅ 执行管理器初始化完成")
    
    def get_account_state(self) -> Dict[str, Any]:
        """
        获取完整的账户状态
        
        包含账户余额和持仓信息,用于构建AI提示词
        
        Returns:
            账户状态字典:
            - balance: 余额信息
            - positions: 持仓列表
            - total_equity: 总权益
            - unrealized_pnl: 未实现盈亏
        """
        logger.debug("查询账户状态...")
        
        try:
            # 获取账户余额
            balance = self.adapter.get_account_balance()
            
            # 获取持仓
            positions = self.adapter.get_open_positions()
            
            return {
                'balance': balance,
                'positions': positions,
                'total_equity': balance.get('total_equity', balance.get('total_balance', 0.0)),
                'available_balance': balance.get('available_balance', 0.0),
                'unrealized_pnl': balance.get('unrealized_pnl', 0.0),
                'position_count': len(positions)
            }
        except Exception as e:
            logger.error(f"获取账户状态失败: {e}")
            # 返回默认值
            return {
                'balance': {
                    'available_balance': 0.0,
                    'total_balance': 0.0,
                    'total_equity': 0.0,
                    'unrealized_pnl': 0.0
                },
                'positions': [],
                'total_equity': 0.0,
                'available_balance': 0.0,
                'unrealized_pnl': 0.0,
                'position_count': 0
            }
    
    def refresh_account_state(self):
        """
        刷新账户状态
        
        如果适配器支持缓存刷新，则调用刷新方法
        用于在决策周期开始时获取最新数据
        """
        if hasattr(self.adapter, 'refresh_account_data'):
            logger.debug("刷新执行层账户状态缓存")
            self.adapter.refresh_account_data()
    
    def update_positions_pnl(self, current_prices: Dict[str, float]):
        """
        更新所有持仓的未实现盈亏
        
        Args:
            current_prices: 当前价格字典 {symbol: price}
            
        注意: 对于Binance适配器，此方法不执行任何操作（API会自动更新）
        """
        positions = self.adapter.get_open_positions()
        
        for position in positions:
            symbol = position.get('symbol')
            if symbol in current_prices:
                self.adapter.update_position_pnl(symbol, current_prices[symbol])
    
    def execute_decision(
        self,
        decision: Any,
        current_price: float
    ) -> Dict[str, Any]:
        """
        执行交易决策
        
        Args:
            decision: AI 决策对象
            current_price: 当前市场价格
            
        Returns:
            执行结果字典
        """
        logger.info(f"执行管理器: 处理决策 {decision.action} {decision.symbol}")
        
        try:
            result = self.adapter.execute_order(decision, current_price)
            return result
        except Exception as e:
            logger.error(f"执行决策时发生错误: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """
        平仓
        
        Args:
            symbol: 交易对符号
            exit_price: 平仓价格
            
        Returns:
            平仓结果
        """
        logger.info(f"执行管理器: 平仓 {symbol}")
        
        try:
            result = self.adapter.close_position(symbol, exit_price)
            return result
        except Exception as e:
            logger.error(f"平仓时发生错误: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'error': str(e)
            }
    
    def save_state(self, filepath: str = None):
        """
        保存状态
        
        Args:
            filepath: 文件路径
        """
        if hasattr(self.adapter, 'save_state'):
            self.adapter.save_state(filepath)
    
    @property
    def initial_balance(self) -> float:
        """
        获取初始余额 (如果适配器支持)
        
        Returns:
            初始余额,如果不支持则返回0
        """
        if hasattr(self.adapter, 'initial_balance'):
            return self.adapter.initial_balance
        return 0.0


def create_execution_manager(binance_data_client=None) -> ExecutionManager:
    """
    创建执行管理器
    
    根据配置选择合适的适配器并创建执行管理器
    
    Args:
        binance_data_client: 可选的币安数据客户端实例（BinanceDataIngestion）
        
    Returns:
        ExecutionManager 实例
    """
    from config import ExecutionConfig, BinanceConfig
    
    # 根据平台创建相应的适配器
    platform = ExecutionConfig.PLATFORM
    
    if platform == 'binance':
        if not binance_data_client:
            raise ValueError("Binance 平台需要提供 binance_data_client 参数")
        
        # 使用配置中的测试网设置
        is_testnet = BinanceConfig.TESTNET
        
        adapter = BinanceAdapter(binance_data_client, is_testnet=is_testnet)
    
    elif platform == 'hype':
        if not ExecutionConfig.HYPE_API_KEY or not ExecutionConfig.HYPE_API_SECRET:
            raise ValueError("Hype API 密钥未配置")
        adapter = HypeAdapter(
            ExecutionConfig.HYPE_API_KEY,
            ExecutionConfig.HYPE_API_SECRET
        )
    
    elif platform == 'aster':
        if not ExecutionConfig.ASTER_API_KEY or not ExecutionConfig.ASTER_API_SECRET:
            raise ValueError("Aster API 密钥未配置")
        adapter = AsterAdapter(
            ExecutionConfig.ASTER_API_KEY,
            ExecutionConfig.ASTER_API_SECRET
        )
    
    else:
        raise ValueError(f"不支持的执行平台: {platform}")
    
    return ExecutionManager(adapter)

