"""
执行适配器 (Execution Adapters)

这个文件保持向后兼容，从具体的适配器模块中导入
推荐直接从具体模块导入：
- from src.execution.binance_adapter import BinanceAdapter
- from src.execution.hype_adapter import HypeAdapter
- from src.execution.aster_adapter import AsterAdapter
"""

# 从具体模块导入适配器
from src.execution.binance_adapter import BinanceAdapter
from src.execution.hype_adapter import HypeAdapter
from src.execution.aster_adapter import AsterAdapter

# 导出所有适配器
__all__ = [
    'BinanceAdapter',
    'HypeAdapter',
    'AsterAdapter',
]
