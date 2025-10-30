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

# 统一项目根目录路径解析 (避免不同执行路径导致的问题)
_current_file = Path(__file__).resolve()
_project_root = _current_file.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

# 导入配置 (会自动加载环境变量)
from config import Config

# 导入各模块
from src.data_ingestion import create_binance_client
from src.data_processing import create_data_processor
from src.ai_decision import create_ai_decision_core
from src.execution.manager import create_execution_manager
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
        
        # 执行管理器 (新架构)
        # 注意: 传递 data_client (BinanceDataIngestion) 而不是 data_client.client
        self.execution_manager = create_execution_manager(self.data_client)
        
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
            
            # 获取市场数据（只读模式：仅获取市场交易数据）
            raw_market_data = self.data_client.get_all_market_data(
                symbol=symbol,
                short_interval=Config.trading.SHORT_TERM_TIMEFRAME,
                long_interval=Config.trading.LONG_TERM_TIMEFRAME,
                short_limit=Config.trading.SHORT_TERM_LIMIT,
                long_limit=Config.trading.LONG_TERM_LIMIT
            )
            
            # 步骤 2: 数据处理与特征工程
            self.logger.info("\n[步骤 2/6] 数据处理与特征工程...")
            market_features = self.data_processor.process_market_data(
                raw_market_data, symbol
            )
            
            # 步骤 2.5: 获取账户状态 (通过执行管理器)
            self.logger.info("\n[步骤 2.5/6] 获取账户状态...")
            
            # 刷新账户状态（仅调用一次API）
            self.execution_manager.refresh_account_state()
            
            # 获取完整账户状态（使用缓存数据）
            account_state = self.execution_manager.get_account_state()
            
            self.logger.info(f"账户总权益: ${account_state['total_equity']:,.2f}")
            self.logger.info(f"可用余额: ${account_state['available_balance']:,.2f}")
            self.logger.info(f"持仓数量: {account_state['position_count']}")
            
            # 显示持仓详情
            if account_state['position_count'] > 0:
                self.logger.info("\n📦 当前持仓:")
                for pos in account_state['positions']:
                    pnl_sign = "+" if pos['unrealized_pnl'] >= 0 else ""
                    roi_sign = "+" if pos.get('roi_percent', 0) >= 0 else ""
                    
                    self.logger.info(f"   {pos['symbol']} Perp {pos['leverage']}x")
                    self.logger.info(f"      方向/数量: {pos['side']} {pos['quantity']:.6f}")
                    self.logger.info(f"      入场价格: ${pos['entry_price']:.2f}")
                    self.logger.info(f"      盈亏平衡: ${pos.get('break_even_price', 0):.2f}")
                    self.logger.info(f"      标记价格: ${pos.get('mark_price', 0):.2f}")
                    self.logger.info(f"      清算价格: ${pos.get('liquidation_price', 0):.2f}")
                    self.logger.info(f"      保证金:   ${pos.get('margin', 0):.2f} USDT")
                    self.logger.info(f"      盈亏:     {pnl_sign}${pos['unrealized_pnl']:.2f} ({roi_sign}{pos.get('roi_percent', 0):.2f}%)")
                    if pos.get('est_funding_fee', 0) != 0:
                        funding_sign = "+" if pos.get('est_funding_fee', 0) >= 0 else ""
                        self.logger.info(f"      预计资金费: {funding_sign}${pos.get('est_funding_fee', 0):.2f} USDT")
                    self.logger.info("")
            else:
                self.logger.info("   无持仓")
            
            # 计算总收益率
            initial_balance = self.execution_manager.initial_balance
            total_equity = account_state['total_equity']
            total_return_pct = ((total_equity - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
            
            # 构建账户特征（用于AI决策提示词）
            account_features = {
                'total_return_percent': total_return_pct,
                'available_cash': account_state['available_balance'],
                'account_value': total_equity,
                'list_of_position_dictionaries': account_state['positions']
            }
            
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
            
            # 步骤 6: 执行交易
            self.logger.info("\n[步骤 5/6] 执行交易...")
            
            # 检查是否为测试网模式
            is_testnet = Config.binance.TESTNET if Config.execution.PLATFORM == 'binance' else False
            
            if decision.action == 'HOLD':
                self.logger.info("💡 决策: HOLD - 保持观望")
            else:
                # 显示决策信息
                self.logger.info("📝 AI 交易决策:")
                self.logger.info(f"   操作: {decision.action} {decision.symbol}")
                self.logger.info(f"   置信度: {decision.confidence:.2f}")
                self.logger.info(f"   建议仓位: {decision.quantity_pct * 100 if decision.quantity_pct else 0:.1f}%")
                self.logger.info(f"   理由: {decision.rationale}")
                if decision.exit_plan:
                    self.logger.info(f"   止损: {decision.exit_plan.stop_loss}")
                    if decision.exit_plan.take_profit:
                        self.logger.info(f"   止盈: {decision.exit_plan.take_profit}")
                
                # 执行订单 (通过执行管理器)
                try:
                    # 获取当前价格用于执行
                    current_price = market_features['current_price']
                    
                    # 调用执行管理器
                    execution_result = self.execution_manager.execute_decision(decision, current_price)
                    
                    # 显示执行结果
                    if execution_result.get('status') == 'SUCCESS':
                        self.logger.info(f"✅ 交易执行成功!")
                        if is_testnet:
                            self.logger.info(f"   模式: 测试网模拟交易")
                        
                        # 如果是开仓,显示持仓信息
                        if 'position' in execution_result:
                            pos = execution_result['position']
                            self.logger.info(f"   持仓: {pos['side']} {pos['quantity']:.4f} {pos['symbol']}")
                            self.logger.info(f"   开仓价: ${pos['entry_price']:.2f}")
                            self.logger.info(f"   强平价: ${pos['liquidation_price']:.2f}")
                    elif execution_result.get('status') == 'SKIPPED':
                        self.logger.info(f"ℹ️  {execution_result.get('message', '跳过执行')}")
                    else:
                        self.logger.warning(f"⚠️  执行失败: {execution_result.get('error', '未知错误')}")
                    
                except Exception as e:
                    self.logger.error(f"❌ 执行交易时发生错误: {e}", exc_info=True)
            
            # 步骤 7: 记录周期信息
            self.logger.info("\n[步骤 6/6] 周期总结...")
            self.logger.info(f"当前市场价格: ${market_features.get('current_price', 0):,.2f}")
            self.logger.info(f"市场趋势: EMA20={market_features.get('current_ema20', 0):.2f}, RSI={market_features.get('current_rsi_7', 0):.2f}")
            
            # 显示最终账户状态（如果刚执行过交易，显示更新后的状态）
            if decision.action != 'HOLD':
                try:
                    # 如果执行了交易，刷新账户状态
                    self.execution_manager.refresh_account_state()
                    final_account_state = self.execution_manager.get_account_state()
                    
                    self.logger.info(f"\n💰 最终账户状态:")
                    self.logger.info(f"   总权益: ${final_account_state['total_equity']:,.2f}")
                    self.logger.info(f"   可用余额: ${final_account_state['available_balance']:,.2f}")
                    if final_account_state['unrealized_pnl'] != 0:
                        pnl = final_account_state['unrealized_pnl']
                        pnl_sign = "+" if pnl >= 0 else ""
                        self.logger.info(f"   未实现盈亏: {pnl_sign}${pnl:.2f}")
                    
                    # 显示持仓变化
                    if final_account_state['position_count'] > 0:
                        self.logger.info(f"   持仓数量: {final_account_state['position_count']}")
                except Exception as e:
                    self.logger.warning(f"获取最终账户状态失败: {e}")
            
            # 保存状态
            self.state_manager.save()
            
            # 保存执行管理器状态
            try:
                self.execution_manager.save_state()
            except Exception as e:
                self.logger.warning(f"保存执行状态失败: {e}")
            
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

