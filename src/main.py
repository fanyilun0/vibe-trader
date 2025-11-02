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
    """设置日志系统，按时间戳创建不同的日志文件"""
    log_level = Config.logging.LEVEL
    base_log_file = Config.logging.LOG_FILE
    
    # 生成带时间戳的日志文件名
    log_dir = os.path.dirname(base_log_file)
    log_filename = os.path.basename(base_log_file)
    log_name, log_ext = os.path.splitext(log_filename)
    
    # 生成时间戳
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    timestamped_log_file = os.path.join(log_dir, f"{log_name}_{timestamp}{log_ext}")
    
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 配置日志格式
    log_format = Config.logging.FORMAT
    
    # 验证日志级别
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    if log_level not in valid_levels:
        print(f"警告: 无效的日志级别 '{log_level}'，使用默认级别 INFO")
        log_level = 'INFO'
    
    # 创建根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level),
        format=log_format,
        handlers=[
            logging.FileHandler(timestamped_log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        force=True  # 强制重新配置，避免其他模块的配置影响
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 80)
    logger.info("Vibe Trader 启动")
    logger.info(f"日志级别: {log_level}")
    logger.info(f"日志文件: {timestamped_log_file}")
    logger.info("=" * 80)
    
    # 如果是DEBUG级别，额外提示
    if log_level == 'DEBUG':
        logger.debug("🔍 DEBUG 模式已启用，将显示详细调试信息")
    
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
            
            # 步骤 1: 数据摄取（多币种）
            self.logger.info("\n[步骤 1/6] 数据摄取...")
            market_features_by_coin = {}
            
            for symbol in self.symbols:
                self.logger.info(f"  获取 {symbol} 数据...")
                try:
                    # 获取市场数据（只读模式：仅获取市场交易数据）
                    raw_market_data = self.data_client.get_all_market_data(
                        symbol=symbol,
                        short_interval=Config.trading.SHORT_TERM_TIMEFRAME,
                        long_interval=Config.trading.LONG_TERM_TIMEFRAME,
                        short_limit=Config.trading.SHORT_TERM_LIMIT,
                        long_limit=Config.trading.LONG_TERM_LIMIT
                    )
                    
                    # 步骤 2: 数据处理与特征工程
                    market_features = self.data_processor.process_market_data(
                        raw_market_data, symbol
                    )
                    
                    # 提取币种符号（去除USDT后缀）
                    coin_symbol = symbol.replace('USDT', '')
                    market_features_by_coin[coin_symbol] = market_features
                    
                except Exception as e:
                    self.logger.error(f"  处理 {symbol} 数据失败: {e}")
                    continue
            
            if not market_features_by_coin:
                self.logger.error("所有币种数据获取失败，跳过本周期")
                return
            
            self.logger.info(f"\n[步骤 2/6] 数据处理完成，成功处理 {len(market_features_by_coin)} 个币种")
            
            # 步骤 2.5: 获取账户状态 (通过执行管理器)
            self.logger.info("\n[步骤 2.5/6] 获取账户状态...")
            
            # 获取完整账户状态（会自动刷新缓存，内部已避免重复调用API）
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
                    # 显示清算价格（如果可用）
                    liq_price = pos.get('liquidation_price', 0)
                    if liq_price > 0:
                        # 计算到清算价格的距离百分比
                        current_price = pos.get('mark_price', 0)
                        if current_price > 0:
                            if pos['side'] == 'LONG':
                                distance_pct = ((current_price - liq_price) / current_price) * 100
                            else:  # SHORT
                                distance_pct = ((liq_price - current_price) / current_price) * 100
                            self.logger.info(f"      清算价格: ${liq_price:.2f} (距离: {distance_pct:.1f}%)")
                        else:
                            self.logger.info(f"      清算价格: ${liq_price:.2f}")
                    self.logger.info(f"      保证金:   ${pos.get('margin', 0):.2f} USDT")
                    self.logger.info(f"      盈亏:     {pnl_sign}${pos['unrealized_pnl']:.2f} ({roi_sign}{pos.get('roi_percent', 0):.2f}%)")
                    self.logger.info("")
            else:
                self.logger.info("   无持仓")
            
            # 计算总收益率
            initial_balance = self.execution_manager.initial_balance
            total_equity = account_state['total_equity']
            total_return_pct = ((total_equity - initial_balance) / initial_balance * 100) if initial_balance > 0 else 0.0
            
            # 步骤 3: 获取全局状态和exit_plans
            global_state = self.state_manager.get_global_state()
            exit_plans = self.state_manager.get_all_exit_plans()
            
            # 从exit_plans中提取订单ID信息并补充到持仓数据中
            enriched_positions = []
            for pos in account_state['positions']:
                symbol = pos.get('symbol')
                # 创建持仓副本
                enriched_pos = pos.copy()
                
                # 从exit_plan获取订单ID信息（如果存在）
                if symbol in exit_plans:
                    exit_plan = exit_plans[symbol]
                    enriched_pos['sl_oid'] = exit_plan.get('sl_oid', -1)
                    enriched_pos['tp_oid'] = exit_plan.get('tp_oid', -1)
                    enriched_pos['entry_oid'] = exit_plan.get('entry_oid', -1)
                    enriched_pos['wait_for_fill'] = exit_plan.get('wait_for_fill', False)
                
                enriched_positions.append(enriched_pos)
            
            # 计算夏普比率（从状态管理器获取）
            sharpe_ratio = self.state_manager.calculate_sharpe_ratio()
            
            # 构建账户特征（用于AI决策提示词）
            account_features = {
                'total_return_percent': total_return_pct,
                'available_cash': account_state['available_balance'],
                'account_value': total_equity,
                'list_of_position_dictionaries': enriched_positions,
                'sharpe_ratio': sharpe_ratio
            }
            
            # 步骤 4: AI 决策（多币种）
            self.logger.info("\n[步骤 3/6] AI 决策生成...")
            decisions = self.ai_core.make_decisions_multi(
                market_features_by_coin,
                account_features,
                global_state,
                exit_plans
            )
            
            self.logger.info(f"\nAI 决策结果 ({len(decisions)} 个币种):")
            for coin, decision in decisions.items():
                self.logger.info(f"  [{coin}]")
                self.logger.info(f"    操作: {decision.action}")
                self.logger.info(f"    交易对: {decision.symbol}")
                self.logger.info(f"    置信度: {decision.confidence:.2f}")
                self.logger.info(f"    理由: {decision.rationale[:100]}..." if len(decision.rationale) > 100 else f"    理由: {decision.rationale}")
            
            # 检查是否有任何决策
            if not decisions:
                self.logger.warning("⚠️  AI未返回任何决策，本周期保持观望")
                self.logger.info("本周期结束，不执行任何操作\n")
                return
            
            # 选择最高置信度的非HOLD决策执行
            # 如果都是HOLD，则选第一个
            decision = None
            non_hold_decisions = [(coin, d) for coin, d in decisions.items() if d.action != 'HOLD']
            
            if non_hold_decisions:
                # 按置信度排序，选最高的
                non_hold_decisions.sort(key=lambda x: x[1].confidence, reverse=True)
                coin, decision = non_hold_decisions[0]
                self.logger.info(f"\n✨ 选择执行: {coin} ({decision.action}, 置信度={decision.confidence:.2f})")
            else:
                # 都是HOLD，选第一个
                coin = list(decisions.keys())[0]
                decision = decisions[coin]
                self.logger.info(f"\n💤 所有币种都为 HOLD，保持观望")
            
            # 记录决策和exit_plan（记录所有币种的决策）
            for coin, d in decisions.items():
                self.state_manager.record_decision({
                    **d.model_dump(),
                    'coin': coin
                })
                
                # 保存或移除exit_plan
                symbol = f"{coin}USDT"
                
                # 检查该币种是否有持仓
                has_position = any(pos.get('symbol') == symbol for pos in account_features['list_of_position_dictionaries'])
                
                if d.action in ['BUY', 'SELL'] and d.exit_plan:
                    # 新开仓，保存exit_plan
                    exit_plan_dict = {
                        'profit_target': d.exit_plan.take_profit,
                        'stop_loss': d.exit_plan.stop_loss,
                        'invalidation_condition': d.exit_plan.invalidation_conditions,
                        'leverage': d.leverage if d.leverage else 20,
                        'confidence': d.confidence,
                        'risk_usd': d.risk_usd if d.risk_usd else 0
                    }
                    self.state_manager.save_position_exit_plan(symbol, exit_plan_dict)
                elif d.action == 'HOLD' and d.exit_plan and has_position:
                    # HOLD 时如果有持仓且提供了 exit_plan，则更新/补充 exit_plan
                    # 这处理了 AI 为已有持仓补充退出计划的情况
                    exit_plan_dict = {
                        'profit_target': d.exit_plan.take_profit,
                        'stop_loss': d.exit_plan.stop_loss,
                        'invalidation_condition': d.exit_plan.invalidation_conditions,
                        'leverage': d.leverage if d.leverage else 20,
                        'confidence': d.confidence,
                        'risk_usd': d.risk_usd if d.risk_usd else 0
                    }
                    self.state_manager.save_position_exit_plan(symbol, exit_plan_dict)
                    self.logger.info(f"✅ 为 {symbol} 持仓更新退出计划: 止盈={d.exit_plan.take_profit}, 止损={d.exit_plan.stop_loss}")
                elif d.action == 'CLOSE_POSITION':
                    # 平仓，移除exit_plan
                    self.state_manager.remove_position_exit_plan(symbol)
            
            # 保存状态（确保exit_plan被持久化）
            self.state_manager.save()
            
            # 步骤 5: 风险检查
            self.logger.info("\n[步骤 4/6] 风险管理检查...")
            
            # 获取当前决策币种的价格
            if decision.symbol:
                coin_symbol = decision.symbol.replace('USDT', '')
                current_price = market_features_by_coin[coin_symbol]['current_price']
            else:
                # HOLD 决策，使用第一个币种的价格
                first_coin = list(market_features_by_coin.keys())[0]
                current_price = market_features_by_coin[first_coin]['current_price']
            
            passed, reason = self.risk_manager.validate_decision(
                decision,
                account_value=account_features['account_value'],
                current_positions=len(account_features['list_of_position_dictionaries']),
                current_price=current_price
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
                self.logger.info(f"   交易数量: {decision.quantity} {decision.symbol.replace('USDT', '') if decision.quantity else 'N/A'}")
                self.logger.info(f"   理由: {decision.rationale}")
                if decision.exit_plan:
                    self.logger.info(f"   止损: {decision.exit_plan.stop_loss}")
                    if decision.exit_plan.take_profit:
                        self.logger.info(f"   止盈: {decision.exit_plan.take_profit}")
                
                # 执行订单 (通过执行管理器)
                try:
                    # current_price 已经在风险检查部分获取了，直接使用
                    
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
                    elif execution_result.get('status') == 'SKIPPED':
                        self.logger.info(f"ℹ️  {execution_result.get('message', '跳过执行')}")
                    else:
                        self.logger.warning(f"⚠️  执行失败: {execution_result.get('error', '未知错误')}")
                    
                except Exception as e:
                    self.logger.error(f"❌ 执行交易时发生错误: {e}", exc_info=True)
            
            # 步骤 7: 记录周期信息
            self.logger.info("\n[步骤 6/6] 周期总结...")
            
            # 显示所有币种的市场状态
            for coin_symbol, features in market_features_by_coin.items():
                self.logger.info(f"[{coin_symbol}] 价格: ${features.get('current_price', 0):,.2f}, "
                               f"EMA20={features.get('current_ema20', 0):.2f}, "
                               f"RSI={features.get('current_rsi_7', 0):.2f}")
            
            # 记录性能数据
            try:
                # 如果执行了交易，需要刷新账户状态
                if decision.action != 'HOLD':
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
                    
                    # 使用最新的账户状态记录性能
                    performance_metrics = {
                        'account_value': final_account_state['total_equity'],
                        'available_balance': final_account_state['available_balance'],
                        'unrealized_pnl': final_account_state['unrealized_pnl'],
                        'position_count': final_account_state['position_count'],
                        'total_return': ((final_account_state['total_equity'] - initial_balance) / initial_balance) if initial_balance > 0 else 0
                    }
                else:
                    # 如果没有交易，使用当前账户状态记录性能
                    performance_metrics = {
                        'account_value': account_state['total_equity'],
                        'available_balance': account_state['available_balance'],
                        'unrealized_pnl': account_state['unrealized_pnl'],
                        'position_count': account_state['position_count'],
                        'total_return': ((account_state['total_equity'] - initial_balance) / initial_balance) if initial_balance > 0 else 0
                    }
                
                self.state_manager.record_performance(performance_metrics)
                
            except Exception as e:
                self.logger.warning(f"记录性能数据失败: {e}")
            
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

