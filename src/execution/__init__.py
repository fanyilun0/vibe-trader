"""
执行层模块 (Execution Layer)

提供交易执行的抽象接口和具体实现:
- ExecutionInterface: 抽象接口
- ExecutionManager: 执行管理器
- 各平台适配器 (Adapters)
"""

from src.execution.interface import ExecutionInterface
from src.execution.manager import ExecutionManager
from src.execution.adapters import (
    BinanceAdapter,
    BinanceMockAdapter,
    HypeAdapter,
    AsterAdapter
)

__all__ = [
    'ExecutionInterface',
    'ExecutionManager',
    'BinanceAdapter',
    'BinanceMockAdapter',
    'HypeAdapter',
    'AsterAdapter'
]
