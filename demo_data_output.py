"""
演示数据输出脚本
展示一次完整的市场数据获取和美化输出
"""
from config import Config
from mock_aster_client import MockAsterClient
from data_aggregator import DataAggregator


def main():
    """运行一次数据获取演示"""
    print("\n" + "="*100)
    print("🎬 Vibe Trader - 市场数据获取演示")
    print("="*100)
    print("\n使用 Mock API 进行演示...")
    
    # 使用 Mock API
    client = MockAsterClient()
    aggregator = DataAggregator(client)
    
    print("\n正在获取市场数据...")
    market_data = aggregator.fetch_all_data()
    
    print(f"✅ 成功获取 {len(market_data.get('coins_data', {}))} 个交易对的数据")
    
    # 打印详细的市场数据
    aggregator.print_market_data(market_data)
    
    print("\n" + "="*100)
    print("✅ 演示完成！")
    print("="*100)
    print("\n提示：")
    print("  - 要使用真实 API，请在 .env 文件中配置 ASTER_API_KEY 和 ASTER_API_SECRET")
    print("  - 要运行完整的交易机器人，请执行: uv run main.py")
    print("  - 要测试 API 连接，请执行: uv run test_data_fetch.py")
    print()


if __name__ == "__main__":
    main()

