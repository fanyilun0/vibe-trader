"""
测试数据获取脚本
Test script for verifying Aster API data fetching
"""
import sys
from config import Config
from aster_client import AsterClient
from mock_aster_client import MockAsterClient
from data_aggregator import DataAggregator


def test_api_connection():
    """测试 API 连接和数据获取"""
    print("="*100)
    print("🧪 测试 Aster API 连接和数据获取")
    print("="*100)
    
    # 决定使用真实 API 还是 Mock API
    use_mock = Config.USE_MOCK_API
    
    if use_mock:
        print("\n⚠️  使用 Mock API 模式进行测试")
        client = MockAsterClient()
    else:
        print("\n✅ 使用真实 Aster API 进行测试")
        try:
            Config.validate()
            client = AsterClient()
        except ValueError as e:
            print(f"\n❌ 配置错误: {e}")
            print("提示: 请检查 .env 文件，确保设置了 ASTER_API_KEY 和 ASTER_API_SECRET")
            print("或者设置 USE_MOCK_API=true 来使用模拟数据测试")
            sys.exit(1)
    
    print(f"\n📊 测试交易对: {', '.join(Config.TRADING_SYMBOLS)}")
    print("\n" + "-"*100)
    
    # 测试公开端点
    print("\n1️⃣  测试公开市场数据端点...")
    
    for symbol in Config.TRADING_SYMBOLS[:1]:  # 只测试第一个交易对
        print(f"\n   🪙 测试交易对: {symbol}")
        
        # 测试 K线数据
        try:
            print(f"      ├─ 获取 K线数据 (3m, 最近10根)...")
            klines = client.get_klines(symbol, interval="3m", limit=10)
            print(f"      │  ✅ 成功获取 {len(klines)} 根K线")
            if klines:
                latest = klines[-1]
                print(f"      │  最新K线: 开={latest[1]}, 高={latest[2]}, 低={latest[3]}, 收={latest[4]}, 量={latest[5]}")
        except Exception as e:
            print(f"      │  ❌ 失败: {e}")
        
        # 测试资金费率
        try:
            print(f"      ├─ 获取资金费率...")
            funding = client.get_funding_rate(symbol)
            print(f"      │  ✅ 资金费率: {funding.get('fundingRate', 'N/A')}")
        except Exception as e:
            print(f"      │  ❌ 失败: {e}")
        
        # 测试订单簿
        try:
            print(f"      └─ 获取订单簿 (深度5)...")
            order_book = client.get_order_book(symbol, limit=5)
            bids = order_book.get('bids', [])
            asks = order_book.get('asks', [])
            print(f"      ✅ 买单数: {len(bids)}, 卖单数: {len(asks)}")
            if bids and asks:
                print(f"         最佳买价: {bids[0][0]}, 最佳卖价: {asks[0][0]}")
        except Exception as e:
            print(f"         ❌ 失败: {e}")
    
    # 测试账户端点（需要认证）
    if not use_mock:
        print("\n2️⃣  测试需要认证的账户端点...")
        
        try:
            print(f"      ├─ 获取账户信息...")
            account = client.get_account_info()
            print(f"      │  ✅ 账户总余额: {account.get('totalWalletBalance', 'N/A')} USDT")
            print(f"      │  ✅ 可用余额: {account.get('availableBalance', 'N/A')} USDT")
        except Exception as e:
            print(f"      │  ❌ 失败: {e}")
            print(f"      │  提示: 如果是认证失败，请检查 API Key 和 Secret 是否正确")
        
        try:
            print(f"      └─ 获取持仓信息...")
            positions = client.get_positions()
            print(f"         ✅ 当前持仓数: {len([p for p in positions if float(p.get('positionAmt', 0)) != 0])}")
        except Exception as e:
            print(f"         ❌ 失败: {e}")
    
    # 测试完整的数据聚合器
    print("\n" + "-"*100)
    print("\n3️⃣  测试完整数据聚合功能...")
    
    try:
        aggregator = DataAggregator(client)
        print(f"   正在获取所有市场数据...")
        market_data = aggregator.fetch_all_data()
        
        print(f"   ✅ 成功获取市场数据!")
        print(f"   ├─ 交易对数量: {len(market_data.get('coins_data', {}))}")
        print(f"   ├─ 账户价值: ${market_data.get('account_info', {}).get('account_value', 0):.2f}")
        print(f"   └─ 持仓数量: {len(market_data.get('account_info', {}).get('positions', []))}")
        
        # 打印详细的市场数据
        print("\n" + "-"*100)
        print("\n4️⃣  详细市场数据输出:")
        aggregator.print_market_data(market_data)
        
        print("\n" + "="*100)
        print("✅ 测试完成！所有数据获取功能正常工作")
        print("="*100)
        
    except Exception as e:
        print(f"\n❌ 数据聚合失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_api_connection()

