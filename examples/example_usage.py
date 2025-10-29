"""
Vibe Trader 使用示例

展示如何单独使用各个模块进行测试和开发
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import yaml

# 加载环境变量
load_dotenv()


def example_data_ingestion():
    """示例: 数据摄取"""
    print("\n" + "=" * 60)
    print("示例 1: 数据摄取模块")
    print("=" * 60)
    
    from src.data_ingestion import BinanceDataIngestion
    
    # 创建客户端
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ 请先设置 BINANCE_API_KEY 和 BINANCE_API_SECRET 环境变量")
        return
    
    client = BinanceDataIngestion(api_key, api_secret, testnet=False)
    
    # 获取 BTC 的 K 线数据
    print("\n获取 BTCUSDT 3分钟 K线数据...")
    klines = client.get_klines('BTCUSDT', '3m', limit=10)
    print(f"获取到 {len(klines)} 条 K 线数据")
    print(f"最新收盘价: {klines[-1][4]}")
    
    # 获取持仓量
    print("\n获取持仓量...")
    oi = client.get_open_interest('BTCUSDT')
    print(f"当前持仓量: {oi}")
    
    # 获取资金费率
    print("\n获取资金费率...")
    funding = client.get_funding_rate('BTCUSDT', limit=1)
    print(f"当前资金费率: {funding[0]['fundingRate']}")
    
    print("\n✅ 数据摄取模块测试完成")


def example_data_processing():
    """示例: 数据处理"""
    print("\n" + "=" * 60)
    print("示例 2: 数据处理与特征工程")
    print("=" * 60)
    
    from src.data_ingestion import BinanceDataIngestion
    from src.data_processing import DataProcessor
    
    api_key = os.getenv('BINANCE_API_KEY')
    api_secret = os.getenv('BINANCE_API_SECRET')
    
    if not api_key or not api_secret:
        print("❌ 请先设置环境变量")
        return
    
    # 获取数据
    client = BinanceDataIngestion(api_key, api_secret, testnet=False)
    raw_data = client.get_all_market_data('BTCUSDT')
    
    # 处理数据
    processor = DataProcessor()
    features = processor.process_market_data(raw_data, 'BTCUSDT')
    
    print("\n提取的特征:")
    print(f"  当前价格: {features['current_price']}")
    print(f"  当前 EMA20: {features['current_ema20']:.2f}")
    print(f"  当前 MACD: {features['current_macd']:.4f}")
    print(f"  当前 RSI(7): {features['current_rsi_7']:.2f}")
    print(f"  持仓量: {features['latest_open_interest']}")
    print(f"  资金费率: {features['funding_rate']}")
    
    print("\n时间序列数据:")
    print(f"  中间价列表长度: {len(features['mid_prices_list'])}")
    print(f"  EMA20列表长度: {len(features['ema20_list'])}")
    
    print("\n✅ 数据处理模块测试完成")


def example_ai_decision():
    """示例: AI 决策 (需要 Deepseek API)"""
    print("\n" + "=" * 60)
    print("示例 3: AI 决策核心")
    print("=" * 60)
    
    api_key = os.getenv('DEEPSEEK_API_KEY')
    
    if not api_key:
        print("❌ 请先设置 DEEPSEEK_API_KEY 环境变量")
        return
    
    from src.ai_decision import AIDecisionCore
    
    # 创建 AI 决策核心
    ai_core = AIDecisionCore(api_key)
    
    # 模拟特征数据
    market_features = {
        'symbol': 'BTCUSDT',
        'current_price': 68500.0,
        'current_ema20': 68300.0,
        'current_macd': 120.5,
        'current_rsi_7': 55.0,
        'latest_open_interest': 1500000000,
        'average_open_interest': 1450000000,
        'funding_rate': 0.0001,
        'mid_prices_list': [68400, 68450, 68500],
        'ema20_list': [68250, 68275, 68300],
        'macd_list': [100, 110, 120.5],
        'rsi_7_period_list': [52, 53, 55],
        'rsi_14_period_list': [50, 51, 52],
        'long_term_ema20': 67000.0,
        'long_term_ema50': 66000.0,
        'long_term_atr3': 500.0,
        'long_term_atr14': 800.0,
        'long_term_current_volume': 50000,
        'long_term_average_volume': 45000,
        'long_term_macd_list': [50, 60, 70],
        'long_term_rsi_14_period_list': [48, 49, 50],
    }
    
    account_features = {
        'total_return_percent': 5.5,
        'available_cash': 10000.0,
        'account_value': 10550.0,
        'list_of_position_dictionaries': []
    }
    
    global_state = {
        'minutes_trading': 180,
        'current_timestamp': '2025-10-29T12:00:00',
        'invocation_count': 10
    }
    
    print("\n调用 LLM 生成决策...")
    print("⚠️  注意: 这将消耗 Deepseek API 配额")
    
    try:
        decision = ai_core.make_decision(market_features, account_features, global_state)
        
        print("\nAI 决策结果:")
        print(f"  操作: {decision.action}")
        print(f"  交易对: {decision.symbol}")
        print(f"  置信度: {decision.confidence}")
        print(f"  仓位百分比: {decision.quantity_pct}")
        print(f"  理由: {decision.rationale}")
        
        if decision.exit_plan:
            print(f"\n退出计划:")
            print(f"  止盈: {decision.exit_plan.take_profit}")
            print(f"  止损: {decision.exit_plan.stop_loss}")
            print(f"  失效条件: {decision.exit_plan.invalidation_conditions}")
        
        print("\n✅ AI 决策模块测试完成")
        
    except Exception as e:
        print(f"\n❌ AI 决策失败: {e}")


def example_risk_management():
    """示例: 风险管理"""
    print("\n" + "=" * 60)
    print("示例 4: 风险管理")
    print("=" * 60)
    
    from src.ai_decision import TradingDecision, ExitPlan
    from src.risk_management import RiskManager
    
    # 创建风险管理器
    risk_config = {
        'max_position_size_pct': 0.20,
        'max_open_positions': 3,
        'min_confidence': 0.75,
        'allowed_symbols': ['BTCUSDT'],
        'max_price_slippage_pct': 0.02
    }
    
    risk_manager = RiskManager(risk_config)
    
    # 创建一个测试决策
    exit_plan = ExitPlan(
        take_profit=70000.0,
        stop_loss=67000.0,
        invalidation_conditions="如果跌破4小时EMA50"
    )
    
    decision = TradingDecision(
        rationale="BTC 突破关键阻力位,成交量放大",
        confidence=0.85,
        action="BUY",
        symbol="BTCUSDT",
        quantity_pct=0.15,
        exit_plan=exit_plan
    )
    
    print("\n测试决策:")
    print(f"  操作: {decision.action}")
    print(f"  置信度: {decision.confidence}")
    print(f"  仓位: {decision.quantity_pct * 100}%")
    
    # 验证决策
    passed, reason = risk_manager.validate_decision(
        decision,
        account_value=10000.0,
        current_positions=1,
        current_price=68500.0
    )
    
    if passed:
        print("\n✅ 决策通过风险检查")
    else:
        print(f"\n❌ 决策被拒绝: {reason}")
    
    print("\n✅ 风险管理模块测试完成")


def example_paper_trading():
    """示例: 模拟交易"""
    print("\n" + "=" * 60)
    print("示例 5: 模拟交易")
    print("=" * 60)
    
    from src.execution import PaperTradingExecution
    from src.ai_decision import TradingDecision, ExitPlan
    
    # 创建模拟交易客户端
    paper_client = PaperTradingExecution(initial_balance=10000.0)
    
    print(f"\n初始余额: ${paper_client.balance:,.2f}")
    
    # 创建一个买入决策
    exit_plan = ExitPlan(
        take_profit=70000.0,
        stop_loss=67000.0,
        invalidation_conditions="如果跌破4小时EMA50"
    )
    
    decision = TradingDecision(
        rationale="测试买入",
        confidence=0.80,
        action="BUY",
        symbol="BTCUSDT",
        quantity_pct=0.10,
        exit_plan=exit_plan
    )
    
    # 执行订单
    print("\n执行模拟买入订单...")
    result = paper_client.execute_order(decision)
    print(f"订单ID: {result['order_id']}")
    print(f"状态: {result['status']}")
    
    # 查看交易历史
    history = paper_client.get_trade_history()
    print(f"\n交易历史记录数: {len(history)}")
    
    # 保存状态
    paper_client.save_state('data/paper_trading_demo.json')
    print("\n模拟交易状态已保存")
    
    print("\n✅ 模拟交易模块测试完成")


def main():
    """运行所有示例"""
    print("\n" + "=" * 60)
    print("Vibe Trader 模块使用示例")
    print("=" * 60)
    print("\n选择要运行的示例:")
    print("1. 数据摄取")
    print("2. 数据处理与特征工程")
    print("3. AI 决策核心")
    print("4. 风险管理")
    print("5. 模拟交易")
    print("6. 运行所有示例")
    print("0. 退出")
    
    choice = input("\n请输入选项 (0-6): ").strip()
    
    if choice == '1':
        example_data_ingestion()
    elif choice == '2':
        example_data_processing()
    elif choice == '3':
        example_ai_decision()
    elif choice == '4':
        example_risk_management()
    elif choice == '5':
        example_paper_trading()
    elif choice == '6':
        example_data_ingestion()
        example_data_processing()
        example_ai_decision()
        example_risk_management()
        example_paper_trading()
    elif choice == '0':
        print("\n再见!")
        return
    else:
        print("\n无效选项")
        return
    
    print("\n" + "=" * 60)
    print("示例运行完成")
    print("=" * 60)


if __name__ == '__main__':
    main()

