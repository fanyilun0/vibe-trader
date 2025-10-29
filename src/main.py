"""
Vibe Trader 主程序

系统编排与操作完整性:
1. 初始化所有模块
2. 主循环调度
3. 完整的决策-执行流程
4. 错误处理和日志记录
"""

import os
import sys
import time
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入配置 (会自动加载环境变量)
from config import Config

# 导入各模块
from src.data_ingestion import create_binance_client
from src.data_processing import create_data_processor
from src.ai_decision import create_ai_decision_core
from src.execution import get_execution_client
from src.risk_management import create_risk_manager
from src.state_manager import create_state_manager

# 配置日志
def setup_logging():
    """设置日志系统"""
    log_level = Config.logging.LEVEL
    log_file = Config.logging.LOG_FILE
    
    # 确保日志目录存在
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # 配置日志格式
    log_format = Config.logging.FORMAT
    
    # 创建根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Vibe Trader 启动")
    logger.info("=" * 80)
    
    return logger


class VibeTrader:
    """Vibe Trader 主类"""
    
    def __init__(self):
        """初始化 Vibe Trader"""
        
        # 验证配置
        is_valid, errors = Config.validate_all()
        if not is_valid:
            raise ValueError(f"配置验证失败:\n  - " + "\n  - ".join(errors))
        
        # 设置日志
        self.logger = setup_logging()
        
        # 打印配置摘要
        Config.print_summary()
        
        # 初始化各模块
        self.logger.info("初始化系统模块...")
        
        # 状态管理器
        self.state_manager = create_state_manager()
        
        # 数据摄取模块
        self.data_client = create_binance_client()
        
        # 数据处理器
        self.data_processor = create_data_processor()
        
        # AI 决策核心
        self.ai_core = create_ai_decision_core()
        
        # 执行层
        self.execution_client = get_execution_client(self.data_client.client)
        
        # 风险管理器
        self.risk_manager = create_risk_manager()
        
        # 交易配置
        self.symbols = Config.trading.SYMBOLS
        self.schedule_interval = Config.trading.SCHEDULE_INTERVAL
        
        self.logger.info("系统初始化完成!")
        self.logger.info(f"交易对: {self.symbols}")
        self.logger.info(f"调度间隔: {self.schedule_interval} 秒")
    
    def run_single_cycle(self):
        """
        执行一次完整的决策-执行周期
        
        这是系统的核心流程,包括:
        1. 数据摄取
        2. 数据处理
        3. AI 决策
        4. 风险检查
        5. 执行
        """
        self.logger.info("\n" + "=" * 80)
        self.logger.info("开始新的交易周期")
        self.logger.info("=" * 80)
        
        try:
            # 增加调用计数
            invocation_count = self.state_manager.increment_invocation()
            self.logger.info(f"第 {invocation_count} 次调用")
            
            # 步骤 1: 数据摄取
            self.logger.info("\n[步骤 1/6] 数据摄取...")
            symbol = self.symbols[0]  # 目前仅支持单个交易对
            
            # 获取市场数据
            raw_market_data = self.data_client.get_all_market_data(
                symbol=symbol,
                short_interval=Config.trading.SHORT_TERM_TIMEFRAME,
                long_interval=Config.trading.LONG_TERM_TIMEFRAME,
                short_limit=Config.trading.SHORT_TERM_LIMIT,
                long_limit=Config.trading.LONG_TERM_LIMIT
            )
            
            # 获取账户数据
            raw_account_data = self.data_client.get_account_data()
            
            # 设置起始余额 (仅第一次)
            if self.state_manager.get_start_balance() == 0:
                self.state_manager.set_start_balance(
                    raw_account_data['total_wallet_balance']
                )
            
            # 步骤 2: 数据处理与特征工程
            self.logger.info("\n[步骤 2/6] 数据处理与特征工程...")
            market_features = self.data_processor.process_market_data(
                raw_market_data, symbol
            )
            
            account_features = self.data_processor.process_account_data(
                raw_account_data,
                start_balance=self.state_manager.get_start_balance()
            )
            
            # 步骤 3: 获取全局状态
            global_state = self.state_manager.get_global_state()
            
            # 步骤 4: AI 决策
            self.logger.info("\n[步骤 3/6] AI 决策生成...")
            decision = self.ai_core.make_decision(
                market_features,
                account_features,
                global_state
            )
            
            self.logger.info(f"\nAI 决策结果:")
            self.logger.info(f"  操作: {decision.action}")
            self.logger.info(f"  交易对: {decision.symbol}")
            self.logger.info(f"  置信度: {decision.confidence:.2f}")
            self.logger.info(f"  理由: {decision.rationale}")
            
            # 记录决策
            self.state_manager.record_decision(decision.dict())
            
            # 步骤 5: 风险检查
            self.logger.info("\n[步骤 4/6] 风险管理检查...")
            
            passed, reason = self.risk_manager.validate_decision(
                decision,
                account_value=account_features['account_value'],
                current_positions=len(account_features['list_of_position_dictionaries']),
                current_price=market_features['current_price']
            )
            
            if not passed:
                self.logger.error(f"❌ 决策被风险管理器拒绝: {reason}")
                self.logger.info("本周期结束,不执行任何操作")
                return
            
            self.logger.info("✅ 风险检查通过")
            
            # 步骤 6: 执行
            self.logger.info("\n[步骤 5/6] 执行交易指令...")
            
            if decision.action == 'HOLD':
                self.logger.info("决策为 HOLD,不执行任何操作")
            else:
                result = self.execution_client.execute_order(decision)
                self.logger.info(f"执行结果: {result}")
            
            # 步骤 7: 记录性能指标
            self.logger.info("\n[步骤 6/6] 记录性能指标...")
            
            risk_metrics = self.risk_manager.get_risk_metrics(
                account_features['list_of_position_dictionaries'],
                account_features['account_value']
            )
            
            performance_metrics = {
                'account_value': account_features['account_value'],
                'total_return_pct': account_features['total_return_percent'],
                'available_cash': account_features['available_cash'],
                'risk_metrics': risk_metrics
            }
            
            self.state_manager.record_performance(performance_metrics)
            
            self.logger.info(f"账户价值: ${performance_metrics['account_value']:,.2f}")
            self.logger.info(f"总收益率: {performance_metrics['total_return_pct']:.2f}%")
            self.logger.info(f"持仓数量: {risk_metrics['total_positions']}")
            
            # 保存状态
            self.state_manager.save()
            
            self.logger.info("\n" + "=" * 80)
            self.logger.info("交易周期完成")
            self.logger.info("=" * 80 + "\n")
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            self.logger.error(f"\n❌ 周期执行失败: {e}", exc_info=True)
            self.logger.error("将继续下一个周期...\n")
    
    def run(self):
        """
        运行主循环
        
        持续执行交易周期,直到手动停止
        """
        self.logger.info("=" * 80)
        self.logger.info("Vibe Trader 主循环启动")
        self.logger.info(f"调度间隔: {self.schedule_interval} 秒")
        self.logger.info("按 Ctrl+C 停止")
        self.logger.info("=" * 80)
        
        try:
            while True:
                # 执行一次周期
                self.run_single_cycle()
                
                # 等待下一个周期
                self.logger.info(f"等待 {self.schedule_interval} 秒后执行下一个周期...")
                time.sleep(self.schedule_interval)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n收到停止信号,正在优雅退出...")
            self.state_manager.save()
            self.logger.info("状态已保存,程序退出")
        except Exception as e:
            self.logger.critical(f"严重错误: {e}", exc_info=True)
            self.state_manager.save()
            raise


def main():
    """主入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Vibe Trader - LLM驱动的量化交易系统')
    parser.add_argument('--once', action='store_true', help='仅运行一次周期后退出')
    
    args = parser.parse_args()
    
    # 创建交易器实例
    trader = VibeTrader()
    
    if args.once:
        # 仅运行一次
        trader.run_single_cycle()
    else:
        # 运行主循环
        trader.run()


if __name__ == '__main__':
    main()

