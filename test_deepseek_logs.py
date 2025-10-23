"""
测试 DeepSeek 日志保存功能
Test DeepSeek prompt and response logging
"""
from config import Config
from aster_client import AsterClient
from data_aggregator import DataAggregator
from signal_generator import SignalGenerator


def main():
    """测试 DeepSeek 日志保存功能"""
    print("\n" + "="*100)
    print("🧪 测试 DeepSeek 日志保存功能")
    print("="*100)
    
    # 使用 Aster DEX API 获取市场数据
    print("\n1️⃣  准备市场数据...")
    client = AsterClient()
    aggregator = DataAggregator(client)
    market_data = aggregator.fetch_all_data()
    print(f"   ✅ 已获取 {len(market_data.get('coins_data', {}))} 个交易对的数据")
    
    # 创建信号生成器（启用日志保存）
    print("\n2️⃣  初始化 SignalGenerator (日志保存已启用)...")
    
    # 检查是否配置了 DeepSeek API Key
    if not Config.DEEPSEEK_API_KEY or Config.DEEPSEEK_API_KEY == "":
        print("\n⚠️  未检测到 DeepSeek API Key")
        print("   提示: 在 .env 文件中设置 DEEPSEEK_API_KEY 以使用真实 API")
        print("   当前将演示日志保存功能的目录结构...\n")
        
        # 创建一个带日志保存的实例（即使没有真实 API Key）
        signal_gen = SignalGenerator(
            api_key="demo_key",  # 演示用
            save_logs=True
        )
        
        print("\n3️⃣  日志保存功能说明:")
        print(f"   📁 日志目录: {signal_gen.logs_dir.absolute()}")
        print("\n   每次调用 DeepSeek API 时，会生成以下文件：")
        print("   ├── prompt_YYYYMMDD_HHMMSS.txt      # 发送给 DeepSeek 的提示词")
        print("   ├── response_YYYYMMDD_HHMMSS.txt    # DeepSeek 的完整响应")
        print("   ├── signal_YYYYMMDD_HHMMSS.json     # 解析后的交易信号 (JSON)")
        print("   └── signal_YYYYMMDD_HHMMSS.txt      # 交易信号的可读版本")
        
        print("\n   文件内容示例：")
        print("   • prompt 文件：包含完整的市场数据和交易指令")
        print("   • response 文件：包含 DeepSeek 的分析过程和决策")
        print("   • signal JSON：结构化的交易信号数据")
        print("   • signal TXT：美化格式的信号，包含操作、价格、置信度等")
        
        print("\n✅ 功能说明完成")
        print("\n💡 要测试真实 API，请：")
        print("   1. 在 .env 文件中设置 DEEPSEEK_API_KEY")
        print("   2. 重新运行此脚本")
        
    else:
        print("   ✅ 检测到 DeepSeek API Key")
        
        # 创建信号生成器
        signal_gen = SignalGenerator(save_logs=True)
        
        print(f"\n3️⃣  调用 DeepSeek API 生成交易信号...")
        print("   (提示词和响应将自动保存到本地文件)")
        
        try:
            # 生成信号
            signal = signal_gen.get_signal(market_data)
            
            print(f"\n✅ 信号生成成功!")
            print(f"\n📋 生成的信号:")
            print(f"   Action: {signal.get('action')}")
            print(f"   Symbol: {signal.get('symbol')}")
            print(f"   Confidence: {signal.get('confidence', 0):.2%}")
            print(f"   Entry: {signal.get('entry_price')}")
            print(f"   Stop Loss: {signal.get('stop_loss')}")
            print(f"   Take Profit: {signal.get('take_profit')}")
            
            print(f"\n📁 日志文件已保存到: {signal_gen.logs_dir.absolute()}")
            print("\n   可以查看以下文件:")
            import os
            from datetime import datetime
            
            # 列出最新的日志文件
            log_files = sorted(signal_gen.logs_dir.glob("*"), key=os.path.getmtime, reverse=True)[:4]
            for f in log_files:
                print(f"   • {f.name}")
            
        except Exception as e:
            print(f"\n❌ 生成信号时出错: {e}")
            print(f"   错误信息已保存到日志文件")
    
    print("\n" + "="*100)
    print("✅ 测试完成!")
    print("="*100)
    print()


if __name__ == "__main__":
    main()

