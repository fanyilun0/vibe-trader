"""
每日盈亏追踪模块 (Daily PnL Tracker)

负责按天统计和保存账户盈亏数据、交易统计快照和历史成交记录
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, date
from pathlib import Path

logger = logging.getLogger(__name__)


class DailyPnLTracker:
    """每日盈亏追踪器"""
    
    def __init__(self, pnl_dir: str = "pnl", execution_adapter=None):
        """
        初始化每日盈亏追踪器
        
        Args:
            pnl_dir: 保存盈亏数据的目录路径
            execution_adapter: 执行适配器实例（用于获取历史成交记录）
        """
        self.pnl_dir = Path(pnl_dir)
        self.execution_adapter = execution_adapter
        
        # 确保目录存在
        self.pnl_dir.mkdir(parents=True, exist_ok=True)
        
        # 当前日期缓存
        self._current_date = None
        self._today_data = None
        
        logger.debug(f"每日盈亏追踪器初始化完成，保存目录: {self.pnl_dir}")
    
    def _get_today_filename(self) -> Path:
        """
        获取今天的文件路径
        
        Returns:
            今天的JSON文件路径
        """
        today = date.today().strftime('%Y%m%d')
        return self.pnl_dir / f"{today}.json"
    
    def _load_today_data(self) -> Dict[str, Any]:
        """
        加载今天的数据（如果存在）
        
        Returns:
            今天的数据字典
        """
        filepath = self._get_today_filename()
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"加载今日数据: {filepath}")
                return data
            except Exception as e:
                logger.error(f"加载今日数据失败: {e}")
                return self._create_empty_day_data()
        else:
            return self._create_empty_day_data()
    
    def _create_empty_day_data(self) -> Dict[str, Any]:
        """
        创建空的每日数据结构
        
        Returns:
            空的每日数据字典
        """
        today = date.today().strftime('%Y-%m-%d')
        return {
            'date': today, # 日期
            'start_balance': 0.0, # 起始余额
            'end_balance': 0.0, # 结束余额
            'start_equity': 0.0, # 起始权益
            'end_equity': 0.0, # 结束权益
            'realized_pnl': 0.0, # 已实现盈亏
            'unrealized_pnl': 0.0, # 未实现盈亏
            'commission': 0.0, # 手续费
            'net_pnl': 0.0, # 净盈亏
            'total_pnl': 0.0, # 总盈亏
            'return_pct': 0.0, # 收益率
            'trades_count': 0, # 交易次数
            'cycles_count': 0, # 周期数
            'positions_opened': 0, # 开仓次数
            'positions_closed': 0, # 平仓次数
            'last_update': None, # 最后更新时间
            'snapshots': [],           # 每个周期的快照
            'trade_snapshots': [],     # 交易统计快照（每次执行交易后记录）
            'historical_trades': []    # 历史成交记录（从Binance获取）
        }
    
    def record_cycle(
        self,
        account_state: Dict[str, Any],
        trade_stats: Dict[str, Any],
        initial_balance: float,
        decision_action: Optional[str] = None
    ):
        """
        记录一个交易周期的数据
        
        Args:
            account_state: 账户状态字典
            trade_stats: 交易统计数据
            initial_balance: 初始余额（用于计算收益率）
            decision_action: 本周期的决策动作（BUY/SELL/CLOSE_POSITION/HOLD）
        """
        today = date.today()
        
        # 检查是否需要加载新的一天
        if self._current_date != today:
            self._current_date = today
            self._today_data = self._load_today_data()
            
            # 如果是新的一天，设置起始余额
            if self._today_data['cycles_count'] == 0:
                self._today_data['start_balance'] = account_state.get('available_balance', 0.0)
                self._today_data['start_equity'] = account_state.get('total_equity', 0.0)
                logger.debug(f"新的一天开始，起始权益: ${self._today_data['start_equity']:,.2f}")
        
        # 更新周期计数
        self._today_data['cycles_count'] += 1
        
        # 更新账户状态
        self._today_data['end_balance'] = account_state.get('available_balance', 0.0)
        self._today_data['end_equity'] = account_state.get('total_equity', 0.0)
        self._today_data['unrealized_pnl'] = account_state.get('unrealized_pnl', 0.0)
        
        # 更新交易统计
        self._today_data['realized_pnl'] = trade_stats.get('total_realized_pnl', 0.0)
        self._today_data['commission'] = trade_stats.get('total_commission', 0.0)
        self._today_data['trades_count'] = trade_stats.get('total_trades', 0)
        
        # 计算净盈亏和总盈亏
        self._today_data['net_pnl'] = trade_stats.get('net_pnl', 0.0)
        self._today_data['total_pnl'] = self._today_data['net_pnl'] + self._today_data['unrealized_pnl']
        
        # 计算当日收益率（基于起始权益）
        if self._today_data['start_equity'] > 0:
            equity_change = self._today_data['end_equity'] - self._today_data['start_equity']
            self._today_data['return_pct'] = (equity_change / self._today_data['start_equity']) * 100
        else:
            self._today_data['return_pct'] = 0.0
        
        # 统计开仓和平仓次数
        if decision_action in ['BUY', 'SELL']:
            self._today_data['positions_opened'] += 1
        elif decision_action == 'CLOSE_POSITION':
            self._today_data['positions_closed'] += 1
        
        # 更新时间戳
        self._today_data['last_update'] = datetime.now().isoformat()
        
        # 添加周期快照（用于详细追踪）
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'cycle': self._today_data['cycles_count'],
            'equity': self._today_data['end_equity'],
            'unrealized_pnl': self._today_data['unrealized_pnl'],
            'action': decision_action or 'HOLD'
        }
        self._today_data['snapshots'].append(snapshot)
        
        # 如果执行了交易（非HOLD），记录交易统计快照
        if decision_action and decision_action != 'HOLD':
            self._record_trade_snapshot(trade_stats)
        
        # 保存到文件
        self._save_today_data()
    
    def _record_trade_snapshot(self, trade_stats: Dict[str, Any]):
        """
        记录交易统计快照
        
        Args:
            trade_stats: 交易统计数据
        """
        trade_snapshot = {
            'timestamp': datetime.now().isoformat(),
            'cycle': self._today_data['cycles_count'],
            'realized_pnl': trade_stats.get('total_realized_pnl', 0.0),
            'commission': trade_stats.get('total_commission', 0.0),
            'net_pnl': trade_stats.get('net_pnl', 0.0),
            'trades_count': trade_stats.get('total_trades', 0),
            'total_pnl': self._today_data['total_pnl']
        }
        
        # 确保 trade_snapshots 字段存在（兼容旧数据）
        if 'trade_snapshots' not in self._today_data:
            self._today_data['trade_snapshots'] = []
        
        self._today_data['trade_snapshots'].append(trade_snapshot)
        logger.debug(f"交易统计快照已记录: 已实现盈亏=${trade_snapshot['realized_pnl']:.2f}, "
                    f"手续费=${trade_snapshot['commission']:.2f}, "
                    f"净盈亏=${trade_snapshot['net_pnl']:.2f}")
    
    def _save_today_data(self):
        """保存今天的数据到文件"""
        filepath = self._get_today_filename()
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self._today_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"每日盈亏数据已保存: {filepath}")
        except Exception as e:
            logger.error(f"保存每日盈亏数据失败: {e}")
    
    def get_today_summary(self) -> Dict[str, Any]:
        """
        获取今日摘要
        
        Returns:
            今日盈亏摘要
        """
        if self._today_data is None:
            self._today_data = self._load_today_data()
        
        return {
            'date': self._today_data['date'],
            'equity_change': self._today_data['end_equity'] - self._today_data['start_equity'],
            'return_pct': self._today_data['return_pct'],
            'total_pnl': self._today_data['total_pnl'],
            'trades': self._today_data['trades_count'],
            'cycles': self._today_data['cycles_count']
        }
    
    def get_history(self, days: int = 7) -> list:
        """
        获取历史N天的数据
        
        Args:
            days: 要获取的天数
            
        Returns:
            历史数据列表
        """
        history = []
        
        # 获取pnl目录下所有json文件
        json_files = sorted(self.pnl_dir.glob("*.json"), reverse=True)
        
        for filepath in json_files[:days]:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 只保留摘要信息
                    summary = {
                        'date': data['date'],
                        'start_equity': data['start_equity'],
                        'end_equity': data['end_equity'],
                        'total_pnl': data['total_pnl'],
                        'return_pct': data['return_pct'],
                        'trades': data['trades_count']
                    }
                    history.append(summary)
            except Exception as e:
                logger.error(f"读取历史数据失败 {filepath}: {e}")
                continue
        
        return history
    
    def update_historical_trades(self, symbols: Optional[List[str]] = None):
        """
        更新今日的历史成交记录
        
        从Binance API获取所有成交记录并保存到今日数据中
        
        Args:
            symbols: 要获取的交易对列表（如果为None，则从执行适配器获取）
        """
        if self.execution_adapter is None:
            logger.warning("未设置执行适配器，无法获取历史成交记录")
            return
        
        if self._today_data is None:
            self._today_data = self._load_today_data()
        
        # 确保 historical_trades 字段存在（兼容旧数据）
        if 'historical_trades' not in self._today_data:
            self._today_data['historical_trades'] = []
        
        try:
            # 如果没有指定交易对，尝试从执行适配器获取
            if symbols is None:
                if hasattr(self.execution_adapter, 'get_open_positions'):
                    positions = self.execution_adapter.get_open_positions()
                    symbols = list(set([pos['symbol'] for pos in positions]))
                
                # 如果仍然没有交易对，使用默认配置
                if not symbols:
                    # 从配置中获取交易对
                    try:
                        from config import Config
                        symbols = Config.trading.SYMBOLS
                        logger.debug(f"使用配置中的交易对: {symbols}")
                    except Exception as e:
                        logger.warning(f"无法从配置获取交易对: {e}")
                        return
            
            logger.debug(f"开始获取历史成交记录: {symbols}")
            
            all_trades = []
            for symbol in symbols:
                try:
                    # 使用 data_client 而不是直接调用适配器
                    if hasattr(self.execution_adapter, 'data_client'):
                        trades = self.execution_adapter.data_client.get_my_trades(symbol, limit=1000)
                    else:
                        logger.warning(f"执行适配器没有 data_client 属性，跳过 {symbol}")
                        continue
                    
                    # 保存完整的原始交易数据，添加可读时间字段
                    for trade in trades:
                        # 保留 Binance API 返回的所有原始字段
                        formatted_trade = {
                            'symbol': trade.get('symbol'),
                            'id': trade.get('id'),  # 交易ID
                            'orderId': trade.get('orderId'),  # 订单ID
                            'side': trade.get('side'),  # BUY/SELL
                            'price': trade.get('price'),  # 保留字符串格式，精度更高
                            'qty': trade.get('qty'),  # 保留字符串格式
                            'realizedPnl': trade.get('realizedPnl'),  # 已实现盈亏
                            'marginAsset': trade.get('marginAsset', 'USDT'),
                            'quoteQty': trade.get('quoteQty'),  # 成交金额
                            'commission': trade.get('commission'),  # 手续费
                            'commissionAsset': trade.get('commissionAsset'),
                            'time': trade.get('time'),  # 原始时间戳（毫秒）
                            'positionSide': trade.get('positionSide', 'BOTH'),
                            'buyer': trade.get('buyer', False),  # 是否是买方
                            'maker': trade.get('maker', False),  # 是否是挂单方
                            # 添加可读时间字段
                            'time_readable': datetime.fromtimestamp(trade.get('time', 0) / 1000).strftime('%Y-%m-%d %H:%M:%S')
                        }
                        all_trades.append(formatted_trade)
                    
                    logger.debug(f"获取 {symbol} 成交记录: {len(trades)} 条")
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 历史成交记录失败: {e}")
                    continue
            
            # 按时间排序（最新的在前）
            all_trades.sort(key=lambda x: x['time'], reverse=True)
            
            # 更新今日数据
            self._today_data['historical_trades'] = all_trades
            self._today_data['last_update'] = datetime.now().isoformat()
            
            # 保存到文件
            self._save_today_data()
            
            logger.info(f"✅ 历史成交记录已更新: 共 {len(all_trades)} 条")
            
        except Exception as e:
            logger.error(f"更新历史成交记录失败: {e}", exc_info=True)
    
    def get_today_trades(self) -> List[Dict[str, Any]]:
        """
        获取今日的历史成交记录
        
        Returns:
            今日成交记录列表
        """
        if self._today_data is None:
            self._today_data = self._load_today_data()
        
        return self._today_data.get('historical_trades', [])


def create_daily_pnl_tracker(pnl_dir: str = "pnl", execution_adapter=None) -> DailyPnLTracker:
    """
    创建每日盈亏追踪器实例
    
    Args:
        pnl_dir: 保存目录
        execution_adapter: 执行适配器实例（用于获取历史成交记录）
        
    Returns:
        DailyPnLTracker 实例
    """
    return DailyPnLTracker(pnl_dir, execution_adapter)


