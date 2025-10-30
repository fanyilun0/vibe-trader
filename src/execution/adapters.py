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
        
        # 账户数据缓存（避免重复API调用）
        self._account_data_cache = None
        self._cache_timestamp = 0
        self._cache_ttl = 1.0  # 缓存有效期1秒（同一个决策周期内可以复用）
        
        # 初始余额记录
        self._initial_balance = None
        
        if is_testnet:
            logger.info("✅ Binance 适配器初始化完成 (testnet 模式)")
            logger.info("   使用币安测试网进行模拟交易")
        else:
            logger.info("✅ Binance 适配器初始化完成 (主网模式)")
            logger.warning("⚠️  实盘交易模式 - 将执行真实订单!")
    
    def _get_cached_account_data(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        获取账户数据（带缓存）
        
        Args:
            force_refresh: 是否强制刷新缓存
            
        Returns:
            账户数据字典
        """
        import time
        current_time = time.time()
        
        # 检查缓存是否有效
        if (not force_refresh and 
            self._account_data_cache is not None and 
            (current_time - self._cache_timestamp) < self._cache_ttl):
            logger.debug("使用缓存的账户数据")
            return self._account_data_cache
        
        # 重新获取账户数据
        logger.debug("刷新账户数据缓存")
        self._account_data_cache = self.data_client.get_account_data()
        self._cache_timestamp = current_time
        
        # 记录初始余额（仅首次）
        if self._initial_balance is None:
            self._initial_balance = self._account_data_cache.get('total_wallet_balance', 0.0)
            logger.info(f"记录初始余额: ${self._initial_balance:,.2f}")
        
        return self._account_data_cache
    
    def refresh_account_data(self):
        """强制刷新账户数据缓存（在交易执行后调用）"""
        self._get_cached_account_data(force_refresh=True)
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """获取持仓"""
        logger.debug("获取币安持仓信息")
        
        try:
            account_data = self._get_cached_account_data()
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
                    'liquidation_price': pos.get('liquidation_price', 0),
                    'mark_price': pos.get('mark_price', 0),
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
            account_data = self._get_cached_account_data()
            
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
        """
        执行订单
        
        Args:
            decision: TradingDecision 对象
            current_price: 当前市场价格
            
        Returns:
            执行结果字典
        """
        logger.info(f"📝 执行Binance订单: {decision.action} {decision.symbol}")
        
        try:
            # HOLD 操作
            if decision.action == 'HOLD':
                logger.info("决策为HOLD,不执行任何操作")
                return {
                    'status': 'SKIPPED',
                    'action': 'HOLD',
                    'message': '保持观望'
                }
            
            # CLOSE_POSITION 操作
            if decision.action == 'CLOSE_POSITION':
                return self.close_position(decision.symbol, current_price)
            
            # BUY/SELL 操作
            if decision.action not in ['BUY', 'SELL']:
                raise ValueError(f"不支持的操作: {decision.action}")
            
            # 先检查是否有持仓，如果有则先平仓
            positions = self.get_open_positions()
            existing_position = None
            for pos in positions:
                if pos['symbol'] == decision.symbol:
                    existing_position = pos
                    break
            
            if existing_position:
                logger.info(f"检测到已有持仓，先平仓: {existing_position['side']} {existing_position['quantity']}")
                close_result = self.close_position(decision.symbol, current_price)
                if close_result.get('status') != 'SUCCESS':
                    logger.error(f"平仓失败: {close_result.get('message')}")
                    return close_result
            
            # 如果仓位百分比为0，只平仓不开仓
            if decision.quantity_pct == 0:
                return {
                    'status': 'SUCCESS',
                    'action': 'CLOSE_ONLY',
                    'message': '仅平仓，不开新仓'
                }
            
            # 计算交易数量
            account_data = self._get_cached_account_data()
            available_balance = account_data.get('available_balance', 0.0)
            
            if available_balance <= 0:
                raise ValueError("可用余额不足")
            
            # 获取交易对的杠杆倍数（从账户信息中获取或使用默认值）
            leverage = 10  # 默认杠杆
            
            # 计算名义价值 = 可用余额 * 仓位百分比 * 杠杆
            nominal_value = available_balance * decision.quantity_pct * leverage
            quantity = nominal_value / current_price
            
            # 确定交易方向
            side = 'BUY' if decision.action == 'BUY' else 'SELL'
            
            logger.info(f"📊 订单详情:")
            logger.info(f"   方向: {side}")
            logger.info(f"   数量: {quantity:.6f} {decision.symbol}")
            logger.info(f"   名义价值: ${nominal_value:.2f}")
            logger.info(f"   杠杆: {leverage}x")
            
            # 执行市价单
            order_result = self.client.futures_create_order(
                symbol=decision.symbol,
                side=side,
                type='MARKET',
                quantity=round(quantity, 6)  # 币安要求数量精度
            )
            
            logger.info(f"✅ 订单提交成功")
            logger.info(f"   订单ID: {order_result.get('orderId')}")
            logger.info(f"   状态: {order_result.get('status')}")
            
            # 刷新账户数据缓存
            self.refresh_account_data()
            
            # 获取更新后的持仓信息
            updated_positions = self.get_open_positions()
            current_position = None
            for pos in updated_positions:
                if pos['symbol'] == decision.symbol:
                    current_position = pos
                    break
            
            return {
                'status': 'SUCCESS',
                'action': decision.action,
                'symbol': decision.symbol,
                'side': 'LONG' if side == 'BUY' else 'SHORT',
                'quantity': quantity,
                'entry_price': current_price,
                'order_id': order_result.get('orderId'),
                'position': current_position,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 订单执行失败: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'action': decision.action,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def close_position(self, symbol: str, exit_price: float) -> Dict[str, Any]:
        """
        平仓
        
        Args:
            symbol: 交易对符号
            exit_price: 平仓价格（用于记录，实际使用市价）
            
        Returns:
            平仓结果字典
        """
        logger.info(f"📉 平仓币安持仓: {symbol}")
        
        try:
            # 获取当前持仓
            positions = self.get_open_positions()
            target_position = None
            for pos in positions:
                if pos['symbol'] == symbol:
                    target_position = pos
                    break
            
            if not target_position:
                logger.warning(f"没有找到 {symbol} 的持仓")
                return {
                    'status': 'FAILED',
                    'symbol': symbol,
                    'message': '没有持仓',
                    'timestamp': datetime.now().isoformat()
                }
            
            # 确定平仓方向（与开仓相反）
            close_side = 'SELL' if target_position['side'] == 'LONG' else 'BUY'
            quantity = target_position['quantity']
            
            logger.info(f"   持仓方向: {target_position['side']}")
            logger.info(f"   平仓数量: {quantity:.6f}")
            logger.info(f"   开仓价: ${target_position['entry_price']:.2f}")
            logger.info(f"   未实现盈亏: ${target_position['unrealized_pnl']:.2f}")
            
            # 执行市价平仓单
            order_result = self.client.futures_create_order(
                symbol=symbol,
                side=close_side,
                type='MARKET',
                quantity=round(quantity, 6),
                reduceOnly=True  # 只减仓，不开新仓
            )
            
            logger.info(f"✅ 平仓订单提交成功")
            logger.info(f"   订单ID: {order_result.get('orderId')}")
            
            # 刷新账户数据缓存
            self.refresh_account_data()
            
            return {
                'status': 'SUCCESS',
                'symbol': symbol,
                'exit_price': exit_price,
                'realized_pnl': target_position['unrealized_pnl'],
                'order_id': order_result.get('orderId'),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 平仓失败: {e}", exc_info=True)
            return {
                'status': 'FAILED',
                'symbol': symbol,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """
        更新持仓盈亏
        
        注意: Binance API 会自动更新盈亏，这里不需要手动计算
        但可以强制刷新缓存以获取最新数据
        """
        # 不执行任何操作，因为Binance会自动更新
        # 如果需要最新数据，调用方应该调用 refresh_account_data()
        pass
    
    @property
    def initial_balance(self) -> float:
        """获取初始余额"""
        if self._initial_balance is None:
            # 首次调用时获取
            account_data = self._get_cached_account_data()
            self._initial_balance = account_data.get('total_wallet_balance', 0.0)
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



