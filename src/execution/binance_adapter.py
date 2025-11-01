"""
Binance 交易适配器

实现真实的 Binance 合约交易功能
支持 testnet（测试网）和主网
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.execution.interface import ExecutionInterface

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
        # 说明：使用 total_wallet_balance（钱包余额）作为初始余额，
        #      这是账户的本金，不含未实现盈亏，用于计算总收益率
        if self._initial_balance is None:
            self._initial_balance = self._account_data_cache.get('total_wallet_balance', 0.0)
            logger.info(f"记录初始余额(钱包余额，不含未实现盈亏): ${self._initial_balance:,.2f}")
        
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
                entry_price = pos.get('entry_price', 0)
                mark_price = pos.get('mark_price', 0)
                unrealized_profit = pos.get('unrealized_profit', 0)
                leverage = pos.get('leverage', 1)
                symbol = pos.get('symbol')
                liquidation_price = pos.get('liquidation_price', 0)
                
                # 如果标记价格为0，尝试获取最新市场价格
                if mark_price == 0 and symbol:
                    try:
                        ticker = self.client.futures_symbol_ticker(symbol=symbol)
                        mark_price = float(ticker.get('price', 0))
                        logger.debug(f"从ticker获取标记价格: {symbol} = ${mark_price:.2f}")
                    except Exception as e:
                        logger.warning(f"无法获取{symbol}的标记价格: {e}")
                
                # 如果 API 返回的未实现盈亏为 0，手动计算
                # （某些情况下 Binance testnet 不返回正确的盈亏值）
                if unrealized_profit == 0 and entry_price > 0 and mark_price > 0:
                    if position_amt > 0:  # 多仓
                        unrealized_profit = (mark_price - entry_price) * position_amt
                    elif position_amt < 0:  # 空仓
                        unrealized_profit = (entry_price - mark_price) * abs(position_amt)
                
                # 计算持仓名义价值
                notional_value = abs(position_amt) * mark_price if mark_price > 0 else 0
                
                # 计算所需保证金（名义价值 / 杠杆）
                margin = notional_value / leverage if leverage > 0 else 0
                
                # 计算盈亏率（ROI）
                roi_percent = (unrealized_profit / margin * 100) if margin > 0 else 0
                
                # 计算保证金比率（需要从账户数据中获取）
                margin_ratio = 0  # 暂时设为0，需要从账户总权益计算
                
                # 计算盈亏平衡价格（包含手续费）
                # 假设开仓和平仓的手续费率总共为 0.08%（0.04% * 2）
                fee_rate = 0.0008
                if position_amt > 0:  # 多仓
                    # 盈亏平衡价 = 入场价 * (1 + 手续费率 * 2)
                    break_even_price = entry_price * (1 + fee_rate)
                else:  # 空仓
                    # 盈亏平衡价 = 入场价 * (1 - 手续费率 * 2)
                    break_even_price = entry_price * (1 - fee_rate)
                
                # 如果API返回的清算价格为0或不准确，手动计算
                # 参考: https://www.binance.com/zh-CN/support/faq/b3c689c1f50a44cabb3a84e663b81d93
                # 
                # 全仓模式清算价格公式：
                # 多仓: 清算价格 = (钱包余额 - 维持保证金金额) / (仓位数量 * (1 - 维持保证金率))
                # 空仓: 清算价格 = (钱包余额 + 维持保证金金额) / (|仓位数量| * (1 + 维持保证金率))
                #
                # 注意：这个计算假设只有单个持仓。如果有多个持仓，需要考虑所有持仓的累计维持保证金。
                
                # 总是重新计算清算价格以确保准确性（API返回的可能不准确）
                if entry_price > 0 and abs(position_amt) > 0:
                    # 获取钱包余额
                    wallet_balance = account_data.get('total_wallet_balance', 0.0)
                    
                    # 获取维持保证金率和维持保证金金额（根据仓位大小分层）
                    mmr, mm_amount = self._get_maintenance_margin_rate(symbol, notional_value)
                    
                    # 计算清算价格
                    if position_amt > 0:  # 多仓
                        # 清算价格 = (WB - TMM) / (|PA| * (1 - MMR))
                        numerator = wallet_balance - mm_amount
                        denominator = abs(position_amt) * (1 - mmr)
                        if denominator > 0:
                            calculated_liq_price = numerator / denominator
                        else:
                            calculated_liq_price = 0
                    else:  # 空仓
                        # 清算价格 = (WB + TMM) / (|PA| * (1 + MMR))
                        numerator = wallet_balance + mm_amount
                        denominator = abs(position_amt) * (1 + mmr)
                        if denominator > 0:
                            calculated_liq_price = numerator / denominator
                        else:
                            calculated_liq_price = 0
                    
                    # 使用计算的清算价格（更准确）
                    if calculated_liq_price > 0:
                        liquidation_price = calculated_liq_price
                        logger.debug(f"计算清算价格: {symbol} = ${liquidation_price:.2f} "
                                   f"(钱包={wallet_balance:.2f}, MMR={mmr*100:.2f}%, MM金额={mm_amount:.2f})")
                    
                    # 如果计算结果不合理，使用API返回的值
                    if position_amt > 0 and liquidation_price >= entry_price:
                        logger.warning(f"多仓清算价格({liquidation_price:.2f})不应高于入场价({entry_price:.2f})，使用API值")
                        liquidation_price = pos.get('liquidation_price', 0)
                    elif position_amt < 0 and liquidation_price <= entry_price and liquidation_price > 0:
                        logger.warning(f"空仓清算价格({liquidation_price:.2f})不应低于入场价({entry_price:.2f})，使用API值")
                        liquidation_price = pos.get('liquidation_price', 0)
                
                formatted_positions.append({
                    'symbol': symbol,
                    'side': 'LONG' if position_amt > 0 else 'SHORT',
                    'quantity': abs(position_amt),
                    'entry_price': entry_price,
                    'mark_price': mark_price,
                    'break_even_price': break_even_price,
                    'liquidation_price': liquidation_price,  # 添加清算价格
                    'unrealized_pnl': unrealized_profit,
                    'roi_percent': roi_percent,
                    'leverage': leverage,
                    'margin': margin,
                    'margin_ratio': margin_ratio,
                    'notional_value': notional_value,
                    'position_side': pos.get('position_side', 'BOTH')
                })
            
            return formatted_positions
            
        except Exception as e:
            logger.error(f"获取持仓信息失败: {e}")
            return []
    
    def _get_maintenance_margin_rate(self, symbol: str, notional_value: float) -> tuple:
        """
        根据仓位名义价值获取维持保证金率和维持保证金额
        
        参考币安USDT永续合约维持保证金率分层:
        https://www.binance.com/zh-CN/support/faq/b3c689c1f50a44cabb3a84e663b81d93
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
            notional_value: 仓位名义价值（USDT）
            
        Returns:
            (维持保证金率, 维持保证金额) 元组
        """
        # BTC/USDT 永续合约维持保证金率分层
        # 不同交易对有不同的分层，这里提供BTC的示例
        btc_brackets = [
            (50000, 0.004, 0),           # 0-50,000 USDT: 0.4%, 维持保证金0
            (250000, 0.005, 50),         # 50,000-250,000: 0.5%, 维持保证金50
            (1000000, 0.01, 1300),       # 250,000-1,000,000: 1%, 维持保证金1,300
            (10000000, 0.025, 16300),    # 1,000,000-10,000,000: 2.5%, 维持保证金16,300
            (20000000, 0.05, 266300),    # 10,000,000-20,000,000: 5%, 维持保证金266,300
            (50000000, 0.1, 1266300),    # 20,000,000-50,000,000: 10%, 维持保证金1,266,300
            (100000000, 0.125, 2516300), # 50,000,000-100,000,000: 12.5%, 维持保证金2,516,300
            (float('inf'), 0.15, 5016300) # 100,000,000+: 15%, 维持保证金5,016,300
        ]
        
        # ETH 和其他主流币种可以使用类似的分层
        # 这里简化处理，所有币种使用BTC的分层
        brackets = btc_brackets
        
        for max_notional, mmr, mm_amount in brackets:
            if notional_value <= max_notional:
                return mmr, mm_amount
        
        # 默认返回最高档
        return 0.15, 5016300
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息
        
        Returns:
            包含以下字段的字典：
            - available_balance: 可用余额（可用于开新仓的余额，扣除已占用保证金）
            - total_balance: 钱包余额（初始本金，不含未实现盈亏）
            - total_equity: 账户总权益（钱包余额 + 未实现盈亏）
            - unrealized_pnl: 未实现盈亏（所有持仓的浮动盈亏）
            
        说明：
            当有持仓时，available_balance 会显著小于 total_equity，
            因为持仓占用了保证金。这是正常现象。
        """
        logger.debug("获取币安账户余额")
        
        try:
            account_data = self._get_cached_account_data()
            
            return {
                'available_balance': account_data.get('available_balance', 0.0),  # 可用余额（扣除已占用保证金）
                'total_balance': account_data.get('total_wallet_balance', 0.0),   # 钱包余额（初始本金）
                'total_equity': account_data.get('total_margin_balance', 0.0),    # 账户总权益（本金+盈亏）
                'unrealized_pnl': account_data.get('total_unrealized_profit', 0.0) # 未实现盈亏
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

