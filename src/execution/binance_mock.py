"""
Binance 模拟合约执行客户端 (Binance Mock Execution)

实现完整的模拟永续合约交易功能:
- 模拟账户管理 (余额、保证金)
- 模拟持仓跟踪 (多空仓位、杠杆)
- 模拟盈亏计算 (未实现盈亏、已实现盈亏)
- 交易历史记录
- 完整的风险管理 (保证金率、强平价格)
"""

import json
import logging
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# 统一项目根目录路径解析 (避免不同执行路径导致的问题)
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.ai_decision import TradingDecision

logger = logging.getLogger(__name__)


@dataclass
class MockPosition:
    """模拟持仓"""
    symbol: str
    side: str  # 'LONG' or 'SHORT'
    entry_price: float  # 开仓均价
    quantity: float  # 持仓数量
    leverage: int  # 杠杆倍数
    unrealized_pnl: float = 0.0  # 未实现盈亏
    liquidation_price: float = 0.0  # 强平价格
    margin: float = 0.0  # 占用保证金
    entry_time: str = ""  # 开仓时间
    mark_price: float = 0.0  # 标记价格
    break_even_price: float = 0.0  # 盈亏平衡价格
    roi_percent: float = 0.0  # 盈亏率(%)
    margin_ratio: float = 0.0  # 保证金比率
    notional_value: float = 0.0  # 名义价值
    est_funding_fee: float = 0.0  # 预计资金费
    position_side: str = "BOTH"  # 持仓方向标识
    
    def __post_init__(self):
        if not self.entry_time:
            self.entry_time = datetime.now().isoformat()
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        计算未实现盈亏和相关指标
        
        Args:
            current_price: 当前市场价格
            
        Returns:
            未实现盈亏 (USDT)
        """
        # 更新标记价格
        self.mark_price = current_price
        
        # 计算未实现盈亏
        if self.side == 'LONG':
            # 多仓: (当前价 - 开仓价) * 数量
            pnl = (current_price - self.entry_price) * self.quantity
        else:  # SHORT
            # 空仓: (开仓价 - 当前价) * 数量
            pnl = (self.entry_price - current_price) * self.quantity
        
        self.unrealized_pnl = pnl
        
        # 计算名义价值
        self.notional_value = self.quantity * current_price
        
        # 计算ROI百分比
        if self.margin > 0:
            self.roi_percent = (pnl / self.margin) * 100
        else:
            self.roi_percent = 0.0
        
        # 计算盈亏平衡价格（包含手续费 0.08%）
        fee_rate = 0.0008
        if self.side == 'LONG':
            self.break_even_price = self.entry_price * (1 + fee_rate)
        else:
            self.break_even_price = self.entry_price * (1 - fee_rate)
        
        return pnl
    
    def calculate_liquidation_price(self) -> float:
        """
        计算强平价格
        
        使用简化公式:
        - 多仓: 强平价 = 开仓价 * (1 - 0.9 / 杠杆)
        - 空仓: 强平价 = 开仓价 * (1 + 0.9 / 杠杆)
        
        Returns:
            强平价格
        """
        if self.side == 'LONG':
            liq_price = self.entry_price * (1 - 0.9 / self.leverage)
        else:  # SHORT
            liq_price = self.entry_price * (1 + 0.9 / self.leverage)
        
        self.liquidation_price = liq_price
        return liq_price
    
    def calculate_margin(self) -> float:
        """
        计算占用保证金
        
        保证金 = 名义价值 / 杠杆
        名义价值 = 开仓价 * 数量
        
        Returns:
            占用保证金 (USDT)
        """
        nominal_value = self.entry_price * self.quantity
        self.margin = nominal_value / self.leverage
        return self.margin
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


@dataclass
class MockOrder:
    """模拟订单"""
    order_id: str
    symbol: str
    side: str  # 'BUY' or 'SELL'
    order_type: str  # 'MARKET', 'LIMIT', etc.
    quantity: float
    price: float  # 实际成交价
    status: str  # 'FILLED', 'CANCELLED'
    fee: float  # 手续费
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return asdict(self)


class BinanceMockExecution:
    """
    Binance 模拟合约执行客户端
    
    模拟币安永续合约交易的完整功能
    实现ExecutionInterface接口
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
        初始化模拟执行客户端
        
        Args:
            initial_balance: 初始余额 (USDT)
            leverage: 默认杠杆倍数
            taker_fee: Taker手续费率 (默认0.04%)
            maker_fee: Maker手续费率 (默认0.02%)
            state_file: 状态文件路径 (用于持久化)
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance  # 可用余额
        self.leverage = leverage
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
        self.state_file = state_file
        
        # 持仓列表
        self.positions: Dict[str, MockPosition] = {}  # key: symbol
        
        # 订单历史
        self.orders: List[MockOrder] = []
        
        # 交易统计
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_realized_pnl = 0.0
        self.total_fees = 0.0
        
        logger.info(f"🏦 Binance模拟合约客户端初始化完成")
        logger.info(f"   初始余额: ${initial_balance:,.2f} USDT")
        logger.info(f"   杠杆倍数: {leverage}x")
        logger.info(f"   Taker费率: {taker_fee*100:.2f}%")
        
        # 尝试从文件加载状态
        if state_file:
            self._load_state()
    
    def get_account_balance(self) -> Dict[str, float]:
        """
        获取账户余额信息
        
        Returns:
            余额信息字典
        """
        # 计算总权益 = 可用余额 + 占用保证金 + 未实现盈亏
        total_margin = sum(pos.margin for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        total_equity = self.balance + total_margin + total_unrealized_pnl
        
        return {
            'available_balance': self.balance,  # 可用余额
            'total_balance': self.balance,  # 钱包余额
            'total_margin': total_margin,  # 占用保证金
            'unrealized_pnl': total_unrealized_pnl,  # 未实现盈亏
            'total_equity': total_equity,  # 总权益
            'margin_ratio': total_margin / total_equity if total_equity > 0 else 0.0  # 保证金率
        }
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓信息列表
        """
        positions = []
        for pos in self.positions.values():
            pos_dict = pos.to_dict()
            # 移除清算价格和资金费字段，保持输出简洁
            pos_dict.pop('liquidation_price', None)
            pos_dict.pop('est_funding_fee', None)
            positions.append(pos_dict)
        return positions
    
    def get_position(self, symbol: str) -> Optional[MockPosition]:
        """
        获取指定交易对的持仓
        
        Args:
            symbol: 交易对符号
            
        Returns:
            持仓对象或None
        """
        return self.positions.get(symbol)
    
    def update_position_pnl(self, symbol: str, current_price: float):
        """
        更新持仓的未实现盈亏
        
        Args:
            symbol: 交易对符号
            current_price: 当前市场价格
        """
        if symbol in self.positions:
            self.positions[symbol].calculate_unrealized_pnl(current_price)
    
    def open_position(
        self,
        symbol: str,
        side: str,
        quantity: float,
        entry_price: float,
        leverage: Optional[int] = None
    ) -> MockPosition:
        """
        开仓
        
        Args:
            symbol: 交易对符号
            side: 方向 ('LONG' or 'SHORT')
            quantity: 数量
            entry_price: 开仓价格
            leverage: 杠杆倍数 (如果为None则使用默认值)
            
        Returns:
            持仓对象
            
        Raises:
            ValueError: 如果余额不足或参数无效
        """
        if leverage is None:
            leverage = self.leverage
        
        # 创建持仓对象
        position = MockPosition(
            symbol=symbol,
            side=side,
            entry_price=entry_price,
            quantity=quantity,
            leverage=leverage
        )
        
        # 计算所需保证金
        required_margin = position.calculate_margin()
        
        # 计算手续费 (按Taker费率)
        nominal_value = entry_price * quantity
        fee = nominal_value * self.taker_fee
        
        # 检查余额是否足够
        total_required = required_margin + fee
        if self.balance < total_required:
            raise ValueError(
                f"余额不足: 需要 ${total_required:.2f}, "
                f"可用 ${self.balance:.2f}"
            )
        
        # 扣除保证金和手续费
        self.balance -= total_required
        self.total_fees += fee
        
        # 计算强平价格
        position.calculate_liquidation_price()
        
        # 保存持仓
        self.positions[symbol] = position
        
        # 记录订单
        order = MockOrder(
            order_id=f"MOCK_{symbol}_{datetime.now().timestamp()}",
            symbol=symbol,
            side='BUY' if side == 'LONG' else 'SELL',
            order_type='MARKET',
            quantity=quantity,
            price=entry_price,
            status='FILLED',
            fee=fee,
            timestamp=datetime.now().isoformat()
        )
        self.orders.append(order)
        self.total_trades += 1
        
        logger.info(f"✅ 开仓成功: {side} {quantity} {symbol} @ ${entry_price:.2f}")
        logger.info(f"   占用保证金: ${required_margin:.2f}")
        logger.info(f"   手续费: ${fee:.2f}")
        logger.info(f"   强平价格: ${position.liquidation_price:.2f}")
        
        return position
    
    def close_position(
        self,
        symbol: str,
        exit_price: float
    ) -> Dict[str, Any]:
        """
        平仓
        
        Args:
            symbol: 交易对符号
            exit_price: 平仓价格
            
        Returns:
            平仓结果字典
            
        Raises:
            ValueError: 如果没有持仓
        """
        if symbol not in self.positions:
            raise ValueError(f"没有 {symbol} 的持仓")
        
        position = self.positions[symbol]
        
        # 计算已实现盈亏
        if position.side == 'LONG':
            realized_pnl = (exit_price - position.entry_price) * position.quantity
        else:  # SHORT
            realized_pnl = (position.entry_price - exit_price) * position.quantity
        
        # 计算手续费
        nominal_value = exit_price * position.quantity
        fee = nominal_value * self.taker_fee
        
        # 最终盈亏 = 已实现盈亏 - 手续费
        final_pnl = realized_pnl - fee
        
        # 返还保证金 + 盈亏
        self.balance += position.margin + final_pnl
        self.total_realized_pnl += final_pnl
        self.total_fees += fee
        
        # 更新交易统计
        self.total_trades += 1
        if final_pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        # 记录平仓订单
        order = MockOrder(
            order_id=f"MOCK_{symbol}_CLOSE_{datetime.now().timestamp()}",
            symbol=symbol,
            side='SELL' if position.side == 'LONG' else 'BUY',
            order_type='MARKET',
            quantity=position.quantity,
            price=exit_price,
            status='FILLED',
            fee=fee,
            timestamp=datetime.now().isoformat()
        )
        self.orders.append(order)
        
        # 删除持仓
        del self.positions[symbol]
        
        pnl_emoji = "📈" if final_pnl > 0 else "📉"
        logger.info(f"{pnl_emoji} 平仓完成: {symbol} @ ${exit_price:.2f}")
        logger.info(f"   已实现盈亏: ${realized_pnl:.2f}")
        logger.info(f"   手续费: ${fee:.2f}")
        logger.info(f"   最终盈亏: ${final_pnl:.2f}")
        
        return {
            'symbol': symbol,
            'exit_price': exit_price,
            'realized_pnl': realized_pnl,
            'fee': fee,
            'final_pnl': final_pnl,
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_order(self, decision: TradingDecision, current_price: Optional[float] = None) -> Dict[str, Any]:
        """
        执行交易决策 (ExecutionInterface接口方法)
        
        Args:
            decision: AI生成的交易决策
            current_price: 当前市场价格 (如果为None则使用决策中的价格估计)
            
        Returns:
            执行结果字典
        """
        logger.info(f"📝 执行交易决策: {decision.action} {decision.symbol}")
        
        # 如果action是HOLD,不执行任何操作
        if decision.action == 'HOLD':
            logger.info("决策为HOLD,不执行交易")
            return {
                'status': 'SKIPPED',
                'action': 'HOLD',
                'message': '保持观望'
            }
        
        # 如果action是CLOSE_POSITION,平仓
        if decision.action == 'CLOSE_POSITION':
            if decision.symbol not in self.positions:
                logger.warning(f"没有 {decision.symbol} 的持仓,无法平仓")
                return {
                    'status': 'FAILED',
                    'action': 'CLOSE_POSITION',
                    'message': '没有持仓'
                }
            
            # 使用当前价格平仓
            if current_price is None:
                logger.warning("未提供当前价格,平仓可能不准确")
                current_price = self.positions[decision.symbol].entry_price
            
            result = self.close_position(decision.symbol, current_price)
            result['status'] = 'SUCCESS'
            result['action'] = 'CLOSE_POSITION'
            return result
        
        # BUY或SELL操作
        if not decision.symbol or decision.quantity is None or decision.quantity <= 0:
            raise ValueError("BUY/SELL决策必须指定symbol和有效的quantity")
        
        # 如果有持仓,先平仓
        if decision.symbol in self.positions:
            logger.info(f"检测到已有持仓,先平仓 {decision.symbol}")
            if current_price is None:
                logger.warning("未提供当前价格,平仓可能不准确")
                current_price = self.positions[decision.symbol].entry_price
            self.close_position(decision.symbol, current_price)
        
        # 使用AI决策的数量
        if current_price is None or current_price <= 0:
            raise ValueError("必须提供有效的当前价格")
        
        quantity = decision.quantity
        
        # 确定方向
        side = 'LONG' if decision.action == 'BUY' else 'SHORT'
        
        # 开仓
        try:
            position = self.open_position(
                symbol=decision.symbol,
                side=side,
                quantity=quantity,
                entry_price=current_price,
                leverage=self.leverage
            )
            
            # 移除清算价格和资金费字段，保持输出简洁
            pos_dict = position.to_dict()
            pos_dict.pop('liquidation_price', None)
            pos_dict.pop('est_funding_fee', None)
            
            return {
                'status': 'SUCCESS',
                'action': decision.action,
                'symbol': decision.symbol,
                'side': side,
                'quantity': quantity,
                'entry_price': current_price,
                'position': pos_dict,
                'timestamp': datetime.now().isoformat()
            }
            
        except ValueError as e:
            logger.error(f"开仓失败: {e}")
            return {
                'status': 'FAILED',
                'action': decision.action,
                'error': str(e)
            }
    
    def cancel_order(self, order_id: str) -> bool:
        """
        取消订单 (ExecutionInterface接口方法)
        
        在模拟交易中,订单立即成交,无法取消
        
        Args:
            order_id: 订单ID
            
        Returns:
            是否成功
        """
        logger.warning(f"模拟交易中订单立即成交,无法取消: {order_id}")
        return False
    
    def check_liquidation(self, symbol: str, current_price: float) -> bool:
        """
        检查是否触发强平
        
        Args:
            symbol: 交易对符号
            current_price: 当前价格
            
        Returns:
            是否被强平
        """
        if symbol not in self.positions:
            return False
        
        position = self.positions[symbol]
        
        # 检查是否触及强平价格
        liquidated = False
        if position.side == 'LONG' and current_price <= position.liquidation_price:
            liquidated = True
        elif position.side == 'SHORT' and current_price >= position.liquidation_price:
            liquidated = True
        
        if liquidated:
            logger.error(f"💥 强制平仓触发: {symbol} @ ${current_price:.2f}")
            logger.error(f"   强平价格: ${position.liquidation_price:.2f}")
            
            # 强平时损失全部保证金
            self.total_realized_pnl -= position.margin
            self.losing_trades += 1
            self.total_trades += 1
            
            # 删除持仓
            del self.positions[symbol]
        
        return liquidated
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取交易统计
        
        Returns:
            统计信息字典
        """
        win_rate = (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
        
        balance_info = self.get_account_balance()
        total_equity = balance_info['total_equity']
        total_return = ((total_equity - self.initial_balance) / self.initial_balance * 100)
        
        return {
            'initial_balance': self.initial_balance,
            'current_balance': self.balance,
            'total_equity': total_equity,
            'total_return_pct': total_return,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate_pct': win_rate,
            'total_realized_pnl': self.total_realized_pnl,
            'total_fees': self.total_fees,
            'open_positions': len(self.positions)
        }
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Returns:
            订单列表
        """
        return [order.to_dict() for order in self.orders]
    
    def save_state(self, filepath: Optional[str] = None):
        """
        保存状态到文件
        
        Args:
            filepath: 文件路径 (如果为None则使用初始化时的路径)
        """
        if filepath is None:
            filepath = self.state_file
        
        if not filepath:
            logger.warning("未指定状态文件路径,跳过保存")
            return
        
        state = {
            'metadata': {
                'saved_at': datetime.now().isoformat(),
                'initial_balance': self.initial_balance,
                'leverage': self.leverage
            },
            'account': {
                'balance': self.balance,
                'positions': [pos.to_dict() for pos in self.positions.values()],
            },
            'statistics': self.get_statistics(),
            'orders': [order.to_dict() for order in self.orders[-100:]]  # 只保存最近100条
        }
        
        # 确保目录存在
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 模拟交易状态已保存到: {filepath}")
    
    def _load_state(self):
        """从文件加载状态"""
        if not self.state_file or not Path(self.state_file).exists():
            logger.info("状态文件不存在,使用初始配置")
            return
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # 恢复账户信息
            account = state.get('account', {})
            self.balance = account.get('balance', self.initial_balance)
            
            # 恢复持仓
            positions_data = account.get('positions', [])
            self.positions = {}
            for pos_dict in positions_data:
                pos = MockPosition(**pos_dict)
                self.positions[pos.symbol] = pos
            
            # 恢复统计信息
            stats = state.get('statistics', {})
            self.total_trades = stats.get('total_trades', 0)
            self.winning_trades = stats.get('winning_trades', 0)
            self.losing_trades = stats.get('losing_trades', 0)
            self.total_realized_pnl = stats.get('total_realized_pnl', 0.0)
            self.total_fees = stats.get('total_fees', 0.0)
            
            # 恢复订单历史
            orders_data = state.get('orders', [])
            self.orders = [MockOrder(**order_dict) for order_dict in orders_data]
            
            logger.info(f"✅ 已从状态文件恢复: {self.state_file}")
            logger.info(f"   当前余额: ${self.balance:.2f}")
            logger.info(f"   持仓数量: {len(self.positions)}")
            
        except Exception as e:
            logger.error(f"加载状态文件失败: {e}")
            logger.warning("将使用初始配置")
    
    def print_summary(self):
        """打印账户摘要"""
        stats = self.get_statistics()
        balance_info = self.get_account_balance()
        
        print("\n" + "=" * 60)
        print("📊 Binance 模拟合约账户摘要")
        print("=" * 60)
        
        print(f"\n💰 账户信息:")
        print(f"  初始余额: ${stats['initial_balance']:,.2f}")
        print(f"  当前余额: ${stats['current_balance']:,.2f}")
        print(f"  总权益: ${stats['total_equity']:,.2f}")
        print(f"  总收益率: {stats['total_return_pct']:.2f}%")
        
        print(f"\n📈 交易统计:")
        print(f"  总交易次数: {stats['total_trades']}")
        print(f"  盈利次数: {stats['winning_trades']}")
        print(f"  亏损次数: {stats['losing_trades']}")
        print(f"  胜率: {stats['win_rate_pct']:.2f}%")
        print(f"  已实现盈亏: ${stats['total_realized_pnl']:,.2f}")
        print(f"  累计手续费: ${stats['total_fees']:,.2f}")
        
        print(f"\n📦 持仓信息:")
        if self.positions:
            for symbol, pos in self.positions.items():
                pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
                print(f"  {symbol}: {pos.side} {pos.quantity} @ ${pos.entry_price:.2f}")
                print(f"    未实现盈亏: {pnl_sign}${pos.unrealized_pnl:.2f}")
                print(f"    强平价格: ${pos.liquidation_price:.2f}")
        else:
            print("  无持仓")
        
        print("\n" + "=" * 60 + "\n")

