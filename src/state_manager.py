"""
状态管理模块

负责在多次调用之间持久化和恢复系统状态
"""

import json
import os
from typing import Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """状态管理器"""
    
    def __init__(self, state_file: str = 'data/state.json', backup_enabled: bool = True):
        """
        初始化状态管理器
        
        Args:
            state_file: 状态文件路径
            backup_enabled: 是否启用备份
        """
        self.state_file = state_file
        self.backup_enabled = backup_enabled
        self.state: Dict[str, Any] = self._load_or_initialize()
        
        logger.info(f"状态管理器初始化完成 (state_file={state_file})")
    
    def _load_or_initialize(self) -> Dict[str, Any]:
        """加载或初始化状态"""
        
        # 确保目录存在
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        # 尝试加载现有状态
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                logger.info(f"从 {self.state_file} 加载状态")
                return state
            except Exception as e:
                logger.error(f"加载状态文件失败: {e}, 将创建新状态")
        
        # 初始化新状态
        return self._create_initial_state()
    
    def _create_initial_state(self) -> Dict[str, Any]:
        """创建初始状态"""
        return {
            'start_time': datetime.now().isoformat(),
            'invocation_count': 0,
            'total_trades': 0,
            'start_balance': None,  # 将在第一次运行时设置
            'last_decision': None,
            'performance_history': [],
            'position_exit_plans': {},  # 存储每个持仓的exit_plan {symbol: exit_plan}
            'metadata': {
                'version': '0.1.0',
                'created_at': datetime.now().isoformat()
            }
        }
    
    def increment_invocation(self) -> int:
        """
        增加调用计数
        
        Returns:
            新的调用次数
        """
        self.state['invocation_count'] += 1
        return self.state['invocation_count']
    
    def get_invocation_count(self) -> int:
        """获取调用次数"""
        return self.state.get('invocation_count', 0)
    
    def get_minutes_trading(self) -> int:
        """
        计算从开始到现在的交易分钟数
        
        Returns:
            交易分钟数
        """
        start_time_str = self.state.get('start_time')
        if not start_time_str:
            return 0
        
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time
        return int(elapsed.total_seconds() / 60)
    
    def set_start_balance(self, balance: float):
        """设置起始余额"""
        if self.state.get('start_balance') is None:
            self.state['start_balance'] = balance
            logger.info(f"设置起始余额: ${balance:,.2f}")
    
    def get_start_balance(self) -> float:
        """获取起始余额"""
        return self.state.get('start_balance', 0.0)
    
    def record_decision(self, decision: Dict[str, Any]):
        """
        记录决策
        
        Args:
            decision: 决策字典
        """
        self.state['last_decision'] = {
            'timestamp': datetime.now().isoformat(),
            'decision': decision
        }
        
        if decision.get('action') in ['BUY', 'SELL', 'CLOSE_POSITION']:
            self.state['total_trades'] = self.state.get('total_trades', 0) + 1
    
    def record_performance(self, metrics: Dict[str, Any]):
        """
        记录性能指标
        
        Args:
            metrics: 性能指标字典
        """
        performance_entry = {
            'timestamp': datetime.now().isoformat(),
            'metrics': metrics
        }
        
        if 'performance_history' not in self.state:
            self.state['performance_history'] = []
        
        self.state['performance_history'].append(performance_entry)
        
        # 只保留最近100条记录
        if len(self.state['performance_history']) > 100:
            self.state['performance_history'] = self.state['performance_history'][-100:]
    
    def save(self):
        """保存状态到文件"""
        try:
            # 如果启用备份,先备份现有文件
            if self.backup_enabled and os.path.exists(self.state_file):
                backup_file = f"{self.state_file}.backup"
                os.replace(self.state_file, backup_file)
            
            # 保存新状态
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
            
            logger.debug(f"状态已保存到 {self.state_file}")
            
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def get_global_state(self) -> Dict[str, Any]:
        """
        获取全局状态 (用于填充提示词)
        
        Returns:
            全局状态字典
        """
        return {
            'minutes_trading': self.get_minutes_trading(),
            'current_timestamp': datetime.now().isoformat(),
            'invocation_count': self.get_invocation_count(),
            'total_trades': self.state.get('total_trades', 0)
        }
    
    def save_position_exit_plan(self, symbol: str, exit_plan: Dict[str, Any]):
        """
        保存持仓的exit_plan
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
            exit_plan: 退出计划字典，包含profit_target, stop_loss, invalidation_condition等
        """
        if 'position_exit_plans' not in self.state:
            self.state['position_exit_plans'] = {}
        
        self.state['position_exit_plans'][symbol] = {
            'profit_target': exit_plan.get('profit_target'),
            'stop_loss': exit_plan.get('stop_loss'),
            'invalidation_condition': exit_plan.get('invalidation_condition'),
            'leverage': exit_plan.get('leverage'),
            'confidence': exit_plan.get('confidence'),
            'risk_usd': exit_plan.get('risk_usd'),
            'created_at': datetime.now().isoformat()
        }
        
        logger.info(f"保存 {symbol} 的exit_plan: 止盈={exit_plan.get('profit_target')}, 止损={exit_plan.get('stop_loss')}")
    
    def get_position_exit_plan(self, symbol: str) -> Dict[str, Any]:
        """
        获取持仓的exit_plan
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
            
        Returns:
            exit_plan字典，如果不存在则返回None
        """
        if 'position_exit_plans' not in self.state:
            self.state['position_exit_plans'] = {}
        
        return self.state['position_exit_plans'].get(symbol)
    
    def remove_position_exit_plan(self, symbol: str):
        """
        移除持仓的exit_plan（平仓后调用）
        
        Args:
            symbol: 交易对符号（如BTCUSDT）
        """
        if 'position_exit_plans' not in self.state:
            return
        
        if symbol in self.state['position_exit_plans']:
            del self.state['position_exit_plans'][symbol]
            logger.info(f"移除 {symbol} 的exit_plan")
    
    def get_all_exit_plans(self) -> Dict[str, Dict[str, Any]]:
        """
        获取所有持仓的exit_plan
        
        Returns:
            所有exit_plan的字典 {symbol: exit_plan}
        """
        if 'position_exit_plans' not in self.state:
            self.state['position_exit_plans'] = {}
        
        return self.state['position_exit_plans']


def create_state_manager() -> StateManager:
    """
    根据配置创建状态管理器
    
    Returns:
        StateManager实例
    """
    from config import StateConfig
    return StateManager(StateConfig.STATE_FILE, StateConfig.BACKUP_ENABLED)

