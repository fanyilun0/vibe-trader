"""
DeepSeek 日志保存功能演示
演示如何自动保存提示词和响应到本地文件
"""
from pathlib import Path
from signal_generator import SignalGenerator
from aster_client import AsterClient
from data_aggregator import DataAggregator


def main():
    """演示日志保存功能"""
    print("\n" + "="*100)
    print("📝 DeepSeek 日志保存功能演示")
    print("="*100)
    
    print("\n说明: 此功能会将每次 DeepSeek API 调用的提示词和响应保存到本地文件")
    print("用途: 方便审查 AI 决策过程、调试问题、优化提示词\n")
    
    # 1. 准备市场数据
    print("步骤 1: 准备市场数据...")
    client = AsterClient()
    aggregator = DataAggregator(client)
    market_data = aggregator.fetch_all_data()
    print(f"✅ 已获取 {len(market_data.get('coins_data', {}))} 个交易对的数据\n")
    
    # 2. 创建 SignalGenerator（启用日志）
    print("步骤 2: 初始化 SignalGenerator（日志保存已启用）...")
    signal_gen = SignalGenerator(
        api_key="demo_key_for_testing",  # 演示用
        save_logs=True
    )
    print(f"✅ 日志将保存到: {signal_gen.logs_dir.absolute()}\n")
    
    # 3. 说明会保存哪些文件
    print("步骤 3: 了解日志文件类型")
    print("="*100)
    print("\n每次调用 DeepSeek API 时，会生成以下文件（使用时间戳命名）：\n")
    
    files_info = [
        {
            "name": "prompt_YYYYMMDD_HHMMSS.txt",
            "icon": "📤",
            "desc": "发送给 DeepSeek 的提示词",
            "content": [
                "• 完整的市场数据（价格、技术指标）",
                "• 账户信息（余额、持仓）",
                "• 交易指令和规则"
            ]
        },
        {
            "name": "response_YYYYMMDD_HHMMSS.txt",
            "icon": "📥",
            "desc": "DeepSeek 的完整响应",
            "content": [
                "• API 元数据（模型、token 使用量）",
                "• AI 的分析过程",
                "• 完整的决策理由和交易信号"
            ]
        },
        {
            "name": "signal_YYYYMMDD_HHMMSS.json",
            "icon": "📊",
            "desc": "解析后的交易信号（JSON）",
            "content": [
                "• action: LONG/SHORT/HOLD/CLOSE",
                "• symbol: 交易对",
                "• entry_price, stop_loss, take_profit",
                "• confidence, leverage"
            ]
        },
        {
            "name": "signal_YYYYMMDD_HHMMSS.txt",
            "icon": "📝",
            "desc": "交易信号（可读文本）",
            "content": [
                "• 美化格式的信号展示",
                "• 包含操作、价格、置信度",
                "• 详细的决策理由"
            ]
        }
    ]
    
    for file_info in files_info:
        print(f"{file_info['icon']} {file_info['name']}")
        print(f"   说明: {file_info['desc']}")
        print(f"   内容:")
        for item in file_info['content']:
            print(f"      {item}")
        print()
    
    # 4. 实际保存示例（模拟）
    print("步骤 4: 模拟生成和保存日志")
    print("="*100)
    print("\n假设我们调用了 DeepSeek API，这是自动保存的过程：\n")
    
    # 创建一个模拟的提示词
    mock_prompt = signal_gen._construct_prompt(market_data)
    
    # 创建一个模拟的时间戳
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # 保存提示词
    print("1️⃣  保存提示词到文件...")
    signal_gen._save_prompt(mock_prompt, timestamp)
    
    # 模拟一个响应
    mock_response_text = """
Based on the current market analysis, I observe the following:

1. BTC is trading at $65,000, which is above the 20-period EMA
2. RSI(7) is at 65, indicating neutral to bullish momentum
3. MACD shows a bullish crossover
4. Funding rate is positive, suggesting long bias in the market

Given these factors, I recommend a LONG position with the following parameters:

{
  "action": "LONG",
  "symbol": "BTCUSDT",
  "reasoning": "Multiple bullish signals align...",
  "entry_price": 65000.0,
  "stop_loss": 64200.0,
  "take_profit": 66500.0,
  "confidence": 0.82,
  "leverage": 5
}
"""
    
    # 创建一个模拟的响应对象
    class MockResponse:
        def __init__(self):
            self.model = "deepseek-reasoner"
            self.id = "chatcmpl-demo123"
            self.usage = type('obj', (object,), {
                'prompt_tokens': 2500,
                'completion_tokens': 350,
                'total_tokens': 2850
            })()
    
    mock_response_obj = MockResponse()
    
    print("2️⃣  保存响应到文件...")
    signal_gen._save_response(mock_response_text, mock_response_obj, timestamp)
    
    # 保存解析后的信号
    mock_signal = {
        "action": "LONG",
        "symbol": "BTCUSDT",
        "reasoning": "Multiple bullish signals align including price above EMA20, bullish MACD crossover, and positive funding rate.",
        "entry_price": 65000.0,
        "stop_loss": 64200.0,
        "take_profit": 66500.0,
        "confidence": 0.82,
        "leverage": 5
    }
    
    print("3️⃣  保存交易信号到文件（JSON + TXT）...")
    signal_gen._save_signal(mock_signal, timestamp)
    
    # 5. 查看结果
    print("\n" + "="*100)
    print("✅ 日志保存完成！")
    print("="*100)
    
    print(f"\n📁 日志目录: {signal_gen.logs_dir.absolute()}")
    print("\n最新生成的文件:")
    
    import os
    log_files = sorted(signal_gen.logs_dir.glob("*"), key=os.path.getmtime, reverse=True)[:10]
    for i, f in enumerate(log_files, 1):
        size = f.stat().st_size
        print(f"   {i}. {f.name} ({size} bytes)")
    
    # 6. 使用建议
    print("\n" + "="*100)
    print("💡 使用建议")
    print("="*100)
    
    suggestions = [
        ("审查决策", "定期查看 response 文件，了解 AI 的分析思路"),
        ("优化提示词", "检查 prompt 文件，确保数据完整且格式正确"),
        ("分析信号", "使用 signal JSON 文件进行回测和统计分析"),
        ("调试问题", "遇到异常时，查看完整的日志追踪问题"),
        ("合规审计", "保留日志作为交易决策的完整记录"),
    ]
    
    print()
    for title, desc in suggestions:
        print(f"• {title}: {desc}")
    
    # 7. 日志管理
    print("\n" + "="*100)
    print("🗂️  日志管理")
    print("="*100)
    print()
    print("日志文件会随时间累积，建议：")
    print()
    print("1. 定期清理旧日志:")
    print("   find deepseek_logs/ -mtime +30 -delete  # 删除30天前的日志")
    print()
    print("2. 压缩归档:")
    print("   tar -czf logs_backup_$(date +%Y%m).tar.gz deepseek_logs/")
    print()
    print("3. 按需启用/禁用:")
    print("   signal_gen = SignalGenerator(save_logs=False)  # 禁用日志")
    print()
    
    print("="*100)
    print("✅ 演示完成！")
    print("="*100)
    print()
    print("下一步:")
    print("• 运行 'uv run main.py' 启动交易机器人，日志会自动保存")
    print("• 运行 'uv run test_deepseek_logs.py' 测试真实 API（需要配置 DEEPSEEK_API_KEY）")
    print("• 查看 DEEPSEEK_LOGS_README.md 了解更多详情")
    print()


if __name__ == "__main__":
    main()

