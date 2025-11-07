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
                
                # 直接使用Binance API返回的清算价格
                # 注意：币安API会自动计算清算价格，考虑了所有持仓和保证金情况
                # 不需要手动计算，手动计算可能不准确（特别是多持仓情况）
                logger.debug(f"使用API返回的清算价格: {symbol} = ${liquidation_price:.2f}")
                
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
    
    def _format_quantity(self, symbol: str, quantity: float) -> float:
        """
        根据交易对精度格式化数量
        
        注意：此方法仅用于开仓时计算新订单数量。
        平仓时应直接使用API返回的原始持仓数量，以确保完全平仓。
        
        Args:
            symbol: 交易对符号
            quantity: 原始数量
            
        Returns:
            格式化后的数量
        """
        try:
            # 获取交易对精度信息
            symbol_info = self.data_client.get_symbol_info(symbol)
            precision = symbol_info['quantity_precision']
            step_size = symbol_info['step_size']
            min_quantity = symbol_info['min_quantity']
            
            # 根据步进大小调整数量
            if step_size > 0:
                quantity = (quantity // step_size) * step_size
            
            # 根据精度格式化
            formatted_quantity = round(quantity, precision)
            
            # 确保不低于最小数量
            if formatted_quantity < min_quantity:
                logger.warning(f"数量 {formatted_quantity} 低于最小值 {min_quantity}，调整为最小值")
                formatted_quantity = min_quantity
            
            logger.debug(f"数量格式化: {quantity:.8f} -> {formatted_quantity:.{precision}f} (精度={precision})")
            
            return formatted_quantity
            
        except Exception as e:
            logger.error(f"格式化数量失败: {e}，使用默认精度")
            return round(quantity, 3)
    
    def execute_order(self, decision: Any, current_price: float, decision_price: float = None) -> Dict[str, Any]:
        """
        执行订单（带滑点保护）
        
        Args:
            decision: TradingDecision 对象
            current_price: 当前市场价格
            decision_price: AI决策时的价格（用于滑点保护）
            
        Returns:
            执行结果字典
        """
        logger.info(f"📝 执行Binance订单: {decision.action} {decision.symbol}")
        
        try:
            # 滑点保护检查（仅对开仓操作）
            if decision.action in ['BUY', 'SELL'] and decision_price is not None:
                from config import RiskManagementConfig
                
                if RiskManagementConfig.ENABLE_SLIPPAGE_PROTECTION:
                    # 计算价格偏离
                    price_deviation = abs(current_price - decision_price) / decision_price
                    max_slippage = RiskManagementConfig.MAX_PRICE_SLIPPAGE_PCT
                    
                    if price_deviation > max_slippage:
                        logger.warning(f"⚠️  价格偏离过大: {price_deviation*100:.2f}% > {max_slippage*100:.2f}%")
                        logger.warning(f"   决策价格: ${decision_price:.2f}")
                        logger.warning(f"   当前价格: ${current_price:.2f}")
                        
                        # 判断偏离方向，避免追高杀跌
                        if decision.action == 'BUY' and current_price > decision_price:
                            logger.warning("   价格已上涨，跳过买入以避免追高")
                            return {
                                'status': 'SKIPPED',
                                'action': decision.action,
                                'reason': 'price_too_high',
                                'message': f'价格偏离 {price_deviation*100:.2f}% 超过阈值 {max_slippage*100:.2f}%，避免追高',
                                'decision_price': decision_price,
                                'current_price': current_price,
                                'timestamp': datetime.now().isoformat()
                            }
                        elif decision.action == 'SELL' and current_price < decision_price:
                            logger.warning("   价格已下跌，跳过卖出以避免追跌")
                            return {
                                'status': 'SKIPPED',
                                'action': decision.action,
                                'reason': 'price_too_low',
                                'message': f'价格偏离 {price_deviation*100:.2f}% 超过阈值 {max_slippage*100:.2f}%，避免追跌',
                                'decision_price': decision_price,
                                'current_price': current_price,
                                'timestamp': datetime.now().isoformat()
                            }
                        else:
                            # 价格偏离但方向有利（买入时价格下跌，卖出时价格上涨）
                            logger.info(f"✅ 价格偏离 {price_deviation*100:.2f}%，但方向有利，继续执行")
                    else:
                        logger.debug(f"✅ 滑点检查通过: {price_deviation*100:.2f}% <= {max_slippage*100:.2f}%")
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
            
            # 直接使用AI决策中的数量，不再通过百分比计算
            if decision.quantity is None or decision.quantity <= 0:
                return {
                    'status': 'FAILED',
                    'action': decision.action,
                    'message': 'AI决策中未提供有效的交易数量'
                }
            
            # 使用AI决策的数量
            quantity = decision.quantity
            
            # 使用动态精度格式化数量（确保符合API要求）
            formatted_quantity = self._format_quantity(decision.symbol, quantity)
            
            # 计算名义价值（用于日志显示）
            nominal_value = formatted_quantity * current_price
            
            # 获取杠杆（使用AI决策中的杠杆或默认值）
            leverage = decision.leverage if decision.leverage else 10
            
            # 确定交易方向
            side = 'BUY' if decision.action == 'BUY' else 'SELL'
            
            logger.info(f"📊 订单详情:")
            logger.info(f"   方向: {side}")
            logger.info(f"   AI决策数量: {quantity} {decision.symbol}")
            logger.info(f"   格式化后数量: {formatted_quantity} {decision.symbol}")
            logger.info(f"   名义价值: ${nominal_value:.2f}")
            logger.info(f"   杠杆: {leverage}x")
            
            # 先设置杠杆（必须在下单前设置）
            try:
                self.client.futures_change_leverage(
                    symbol=decision.symbol,
                    leverage=leverage
                )
                logger.info(f"✅ 杠杆设置成功: {leverage}x")
            except Exception as e:
                logger.warning(f"⚠️ 杠杆设置失败: {e}，将使用当前杠杆")
            
            # 执行市价单
            order_result = self.client.futures_create_order(
                symbol=decision.symbol,
                side=side,
                type='MARKET',
                quantity=formatted_quantity
            )
            
            logger.info(f"✅ 订单提交成功")
            logger.info(f"   订单ID: {order_result.get('orderId')}")
            logger.info(f"   状态: {order_result.get('status')}")
            
            # 设置止盈止损（如果AI决策中包含）
            if decision.exit_plan:
                try:
                    # 确定止盈止损的方向（与开仓方向相反）
                    sl_tp_side = 'SELL' if side == 'BUY' else 'BUY'
                    
                    # 设置止损单
                    if decision.exit_plan.stop_loss:
                        stop_loss_order = self.client.futures_create_order(
                            symbol=decision.symbol,
                            side=sl_tp_side,
                            type='STOP_MARKET',
                            stopPrice=decision.exit_plan.stop_loss,
                            closePosition=True
                        )
                        logger.info(f"✅ 止损单设置成功: {decision.exit_plan.stop_loss}")
                    
                    # 设置止盈单
                    if decision.exit_plan.take_profit:
                        take_profit_order = self.client.futures_create_order(
                            symbol=decision.symbol,
                            side=sl_tp_side,
                            type='TAKE_PROFIT_MARKET',
                            stopPrice=decision.exit_plan.take_profit,
                            closePosition=True
                        )
                        logger.info(f"✅ 止盈单设置成功: {decision.exit_plan.take_profit}")
                        
                except Exception as e:
                    logger.warning(f"⚠️ 止盈止损设置失败: {e}")
            
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
                'quantity': formatted_quantity,  # 使用格式化后的实际执行数量
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
            # 直接从API获取原始持仓数据（不经过格式化）
            account_data = self._get_cached_account_data(force_refresh=True)
            positions = account_data.get('positions', [])
            
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
            
            # 获取原始持仓数量（保持API返回的精度）
            position_amt = target_position['position_amt']
            
            # 确定平仓方向（与开仓相反）
            if position_amt > 0:  # 多仓
                close_side = 'SELL'
                quantity = abs(position_amt)
            else:  # 空仓
                close_side = 'BUY'
                quantity = abs(position_amt)
            
            # 计算未实现盈亏（用于记录）
            unrealized_pnl = target_position['unrealized_profit']
            entry_price = target_position['entry_price']
            
            logger.info(f"   持仓方向: {'LONG' if position_amt > 0 else 'SHORT'}")
            logger.info(f"   平仓数量: {quantity} (原始精度)")
            logger.info(f"   开仓价: ${entry_price:.2f}")
            logger.info(f"   未实现盈亏: ${unrealized_pnl:.2f}")
            
            # 执行市价平仓单（使用原始精度的数量）
            order_result = self.client.futures_create_order(
                symbol=symbol,
                side=close_side,
                type='MARKET',
                quantity=quantity,
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
                'realized_pnl': unrealized_pnl,
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
    
    def get_trade_statistics(self, symbols: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        获取交易统计数据（从历史成交记录计算）
        
        Args:
            symbols: 要统计的交易对列表（如果为None，则使用当前持仓的交易对）
            
        Returns:
            包含交易统计数据的字典：
            {
                'total_realized_pnl': float,  # 总已实现盈亏
                'total_commission': float,    # 总手续费
                'total_trades': int,          # 总交易次数（成交次数）
                'net_pnl': float,             # 净盈亏（已实现盈亏 - 手续费）
                'by_symbol': {                # 按交易对统计
                    'BTCUSDT': {
                        'realized_pnl': float,
                        'commission': float,
                        'trades': int
                    }
                }
            }
        """
        logger.debug("获取交易统计数据...")
        
        try:
            # 如果没有指定交易对，使用当前持仓的交易对
            if symbols is None:
                positions = self.get_open_positions()
                symbols = [pos['symbol'] for pos in positions]
            
            # 如果仍然没有交易对，返回空统计
            if not symbols:
                return {
                    'total_realized_pnl': 0.0,
                    'total_commission': 0.0,
                    'total_trades': 0,
                    'net_pnl': 0.0,
                    'by_symbol': {}
                }
            
            total_realized_pnl = 0.0
            total_commission = 0.0
            total_trades = 0
            by_symbol = {}
            
            # 遍历每个交易对获取历史成交记录
            for symbol in symbols:
                try:
                    trades = self.data_client.get_my_trades(symbol, limit=500)
                    
                    symbol_realized_pnl = 0.0
                    symbol_commission = 0.0
                    symbol_trades = len(trades)
                    
                    for trade in trades:
                        # 累计已实现盈亏
                        realized_pnl = float(trade.get('realizedPnl', 0))
                        symbol_realized_pnl += realized_pnl
                        
                        # 累计手续费
                        commission = float(trade.get('commission', 0))
                        symbol_commission += commission
                    
                    # 更新总计
                    total_realized_pnl += symbol_realized_pnl
                    total_commission += symbol_commission
                    total_trades += symbol_trades
                    
                    # 保存分币种统计
                    by_symbol[symbol] = {
                        'realized_pnl': symbol_realized_pnl,
                        'commission': symbol_commission,
                        'trades': symbol_trades
                    }
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 交易历史失败: {e}")
                    continue
            
            # 计算净盈亏（已实现盈亏 - 手续费）
            net_pnl = total_realized_pnl - total_commission
            
            return {
                'total_realized_pnl': total_realized_pnl,
                'total_commission': total_commission,
                'total_trades': total_trades,
                'net_pnl': net_pnl,
                'by_symbol': by_symbol
            }
            
        except Exception as e:
            logger.error(f"获取交易统计失败: {e}")
            return {
                'total_realized_pnl': 0.0,
                'total_commission': 0.0,
                'total_trades': 0,
                'net_pnl': 0.0,
                'by_symbol': {}
            }
    
    @property
    def initial_balance(self) -> float:
        """获取初始余额"""
        if self._initial_balance is None:
            # 首次调用时获取
            account_data = self._get_cached_account_data()
            self._initial_balance = account_data.get('total_wallet_balance', 0.0)
        return self._initial_balance

